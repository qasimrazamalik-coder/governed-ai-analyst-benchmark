"""A small compiler for the dbt semantic layer (a subset of the MetricFlow spec).

It reads the warehouse's `semantic_manifest.json` and turns a structured request
(metrics, group-by dimensions, filters, date range) into SQL. The governed agent can
only ask through this interface, so it cannot invent a metric definition or a column:
an unknown name is rejected with the list of valid ones.

Supported: simple, ratio and derived metrics; measures with sum, count, count_distinct,
average, min, max; categorical dimensions of the metric's own semantic model and of
models joined through a foreign entity; metric_time at day/week/month/quarter/year;
equality and IN filters; inclusive date ranges; order by a metric; limit.

Naming follows MetricFlow: `<entity>__<dimension>` (for example
`contact_driver__driver_l3`), and `metric_time__month`.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import duckdb
import pandas as pd

AGG_SQL = {"sum": "sum({})", "count": "count({})", "count_distinct": "count(distinct {})",
           "average": "avg({})", "avg": "avg({})", "min": "min({})", "max": "max({})"}
GRAINS = ("day", "week", "month", "quarter", "year")


class SemanticError(ValueError):
    """The request names something the governed layer does not define."""


@dataclass
class SemanticModel:
    name: str
    table: str
    primary_entity: str | None
    primary_expr: str | None
    foreign: dict[str, str]  # entity -> expr
    dimensions: dict[str, dict]  # name -> {"expr", "type"}
    measures: dict[str, dict]  # name -> {"agg", "expr"}
    agg_time_dimension: str | None
    description: str = ""


@dataclass
class Request:
    metrics: list[str]
    group_by: list[str] = field(default_factory=list)
    where: list[dict] = field(default_factory=list)
    start: str | None = None
    end: str | None = None
    order_by: str | None = None
    descending: bool = True
    limit: int | None = None

    @classmethod
    def from_dict(cls, d: dict) -> "Request":
        order = d.get("order_by")
        desc = True
        if isinstance(order, dict):
            desc = bool(order.get("desc", True))
            order = order.get("metric")
        return cls(
            metrics=list(d.get("metrics") or []),
            group_by=list(d.get("group_by") or []),
            where=list(d.get("where") or []),
            start=d.get("start"),
            end=d.get("end"),
            order_by=order,
            descending=desc,
            limit=d.get("limit"),
        )


def _q(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _literal(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    return "'" + str(v).replace("'", "''") + "'"


def _check_date(dimension: str, value) -> str:
    s = str(value).strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        raise SemanticError(
            f"{dimension} filter value {value!r} is not a date. Time filters take the period's start date as "
            f"YYYY-MM-DD (e.g. 2025-04-01 for April or for Q2 2025); for a date range use start and end.")
    return s


class SemanticLayer:
    def __init__(self, manifest: dict):
        self.models: dict[str, SemanticModel] = {}
        self.measure_model: dict[str, str] = {}
        for sm in manifest["semantic_models"]:
            rel = sm["node_relation"]
            primary = next((e for e in sm.get("entities", []) if e["type"] in ("primary", "unique", "natural")), None)
            model = SemanticModel(
                name=sm["name"],
                table=f'{rel["schema_name"]}.{rel["alias"]}',
                primary_entity=primary["name"] if primary else None,
                primary_expr=(primary.get("expr") or primary["name"]) if primary else None,
                foreign={e["name"]: e.get("expr") or e["name"] for e in sm.get("entities", []) if e["type"] == "foreign"},
                dimensions={d["name"]: {"expr": d.get("expr") or d["name"], "type": d["type"]} for d in sm.get("dimensions", [])},
                measures={m["name"]: {"agg": m["agg"], "expr": m.get("expr") or m["name"]} for m in sm.get("measures", [])},
                agg_time_dimension=(sm.get("defaults") or {}).get("agg_time_dimension"),
                description=sm.get("description") or "",
            )
            self.models[model.name] = model
            for m in model.measures:
                self.measure_model[m] = model.name
        self.metrics: dict[str, dict] = {m["name"]: m for m in manifest["metrics"]}
        self.by_primary_entity = {m.primary_entity: m for m in self.models.values() if m.primary_entity}

    @classmethod
    def from_file(cls, path: str | Path) -> "SemanticLayer":
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    # ------------------------------------------------------------- catalogue
    def measures_for(self, metric: str) -> set[str]:
        if metric not in self.metrics:
            raise SemanticError(f"unknown metric {metric!r}. Valid metrics: {', '.join(sorted(self.metrics))}")
        m = self.metrics[metric]
        tp = m.get("type_params") or {}
        if m["type"] == "simple":
            return {tp["measure"]["name"]}
        if m["type"] == "ratio":
            return self.measures_for(tp["numerator"]["name"]) | self.measures_for(tp["denominator"]["name"])
        if m["type"] == "derived":
            out: set[str] = set()
            for ref in tp["metrics"]:
                out |= self.measures_for(ref["name"])
            return out
        raise SemanticError(f"metric type {m['type']!r} is not supported")

    def dimensions_of_model(self, model: SemanticModel) -> dict[str, tuple[str, str | None]]:
        """Dimension name -> (sql expression, joined model name or None)."""
        out: dict[str, tuple[str, str | None]] = {}
        if model.primary_entity:
            for d, spec in model.dimensions.items():
                if spec["type"] == "categorical":
                    out[f"{model.primary_entity}__{d}"] = (f"t0.{spec['expr']}", None)
        for entity, _expr in model.foreign.items():
            target = self.by_primary_entity.get(entity)
            if not target:
                continue
            for d, spec in target.dimensions.items():
                if spec["type"] == "categorical":
                    out[f"{entity}__{d}"] = (f"{entity}.{spec['expr']}", target.name)
        if model.agg_time_dimension:
            time_expr = f"t0.{model.dimensions[model.agg_time_dimension]['expr']}"
            for g in GRAINS:
                out[f"metric_time__{g}"] = (f"cast(date_trunc('{g}', {time_expr}) as date)", None)
        return out

    def dimensions_for(self, metrics: list[str]) -> list[str]:
        common: set[str] | None = None
        for model_name in {self.measure_model[m] for metric in metrics for m in self.measures_for(metric)}:
            dims = set(self.dimensions_of_model(self.models[model_name]))
            common = dims if common is None else common & dims
        return sorted(common or [])

    def catalog_text(self) -> str:
        """The menu shown to the governed agent: every metric with its definition and dimensions."""
        lines = ["METRICS (name: label - definition) [dimensions you can group or filter by]"]
        for name in sorted(self.metrics):
            m = self.metrics[name]
            if not m.get("label") or m["label"] == name:
                continue  # helper metrics created from measures (create_metric) stay out of the menu
            desc = (m.get("description") or "").replace("\n", " ").strip()
            dims = ", ".join(d for d in self.dimensions_for([name]) if not d.startswith("metric_time__") or d.endswith(("__month", "__quarter")))
            lines.append(f"- {name}: {m['label']} - {desc} [{dims}]")
        lines.append("Time: filter any metric with start/end dates (inclusive); group by metric_time__day|week|month|quarter|year.")
        return "\n".join(lines)

    # --------------------------------------------------------------- compile
    def _metric_expr(self, metric: str) -> str:
        m = self.metrics[metric]
        tp = m.get("type_params") or {}
        if m["type"] == "simple":
            return _q("m__" + tp["measure"]["name"])
        if m["type"] == "ratio":
            num = self._metric_expr(tp["numerator"]["name"])
            den = self._metric_expr(tp["denominator"]["name"])
            return f"(cast({num} as double) / nullif({den}, 0))"
        expr = tp["expr"]
        for ref in sorted(tp["metrics"], key=lambda r: -len(r["name"])):
            expr = re.sub(rf"\b{re.escape(ref['name'])}\b", f"cast({self._metric_expr(ref['name'])} as double)", expr)
        return f"({expr})"

    def compile(self, req: Request) -> str:
        if not req.metrics:
            raise SemanticError("request has no metrics")
        for metric in req.metrics:
            self.measures_for(metric)
        valid_dims = self.dimensions_for(req.metrics)
        for d in req.group_by + [w.get("dimension") for w in req.where]:
            if d not in valid_dims:
                raise SemanticError(
                    f"dimension {d!r} is not available for {', '.join(req.metrics)}. Valid: {', '.join(valid_dims)}")
        if req.order_by and req.order_by not in req.metrics:
            raise SemanticError("order_by must be one of the requested metrics")

        by_model: dict[str, set[str]] = {}
        for metric in req.metrics:
            for measure in self.measures_for(metric):
                by_model.setdefault(self.measure_model[measure], set()).add(measure)

        ctes = []
        keys = [f"g{i}" for i in range(len(req.group_by))]
        for idx, (model_name, measures) in enumerate(sorted(by_model.items())):
            model = self.models[model_name]
            dims = self.dimensions_of_model(model)
            joins = {}
            for d in req.group_by + [w["dimension"] for w in req.where]:
                expr, joined = dims[d]
                if joined:
                    entity = d.split("__")[0]
                    target = self.models[joined]
                    joins[entity] = (f"left join {target.table} as {entity} "
                                     f"on {entity}.{target.primary_expr} = t0.{model.foreign[entity]}")
            selects = [f"{dims[d][0]} as {k}" for d, k in zip(req.group_by, keys)]
            for measure in sorted(measures):
                spec = model.measures[measure]
                selects.append(AGG_SQL[spec["agg"]].format(f"({spec['expr']})") + f" as {_q('m__' + measure)}")
            filters = []
            if req.start or req.end:
                if not model.agg_time_dimension:
                    raise SemanticError(f"{model_name} has no time dimension to filter on")
                t = f"cast(t0.{model.dimensions[model.agg_time_dimension]['expr']} as date)"
                if req.start:
                    filters.append(f"{t} >= date {_literal(req.start)}")
                if req.end:
                    filters.append(f"{t} <= date {_literal(req.end)}")
            for w in req.where:
                expr = dims[w["dimension"]][0]
                op = (w.get("op") or "=").lower()
                if w["dimension"].startswith("metric_time__"):
                    # Time is typed: compare as dates, and reject a value that is not one
                    # (comparing '2025-03' to a date as text would silently match nothing).
                    if op not in ("=", "!=", "<>", "in"):
                        raise SemanticError(f"filter operator {op!r} not supported (use = or in, or start/end for ranges)")
                    vals = w["value"] if op == "in" else [w["value"]]
                    vals = vals if isinstance(vals, list) else [vals]
                    lits = ", ".join(f"date {_literal(_check_date(w['dimension'], v))}" for v in vals)
                    filters.append(f"{expr} {'in' if op == 'in' else ('=' if op == '=' else '<>')} ({lits})")
                    continue
                if op in ("=", "!=", "<>"):
                    filters.append(f"cast({expr} as varchar) {'=' if op == '=' else '<>'} {_literal(str(w['value']))}")
                elif op == "in":
                    vals = ", ".join(_literal(str(v)) for v in w["value"])
                    filters.append(f"cast({expr} as varchar) in ({vals})")
                else:
                    raise SemanticError(f"filter operator {op!r} not supported (use = or in)")
            sql = f"select {', '.join(selects)}\nfrom {model.table} as t0\n" + "\n".join(joins.values())
            if filters:
                sql += "\nwhere " + " and ".join(filters)
            if keys:
                sql += "\ngroup by " + ", ".join(str(i + 1) for i in range(len(keys)))
            ctes.append((f"q{idx}", sql))

        with_sql = "with " + ",\n".join(f"{name} as (\n{sql}\n)" for name, sql in ctes)
        first = ctes[0][0]
        from_sql = first
        for name, _ in ctes[1:]:
            if keys:
                on = " and ".join(f"{first}.{k} is not distinct from {name}.{k}" for k in keys)
                from_sql += f"\nfull outer join {name} on {on}"
            else:
                from_sql += f"\ncross join {name}"
        key_cols = [f"coalesce({', '.join(f'{n}.{k}' for n, _ in ctes)}) as {_q(d)}" for k, d in zip(keys, req.group_by)]
        metric_cols = [f"{self._metric_expr(m)} as {_q(m)}" for m in req.metrics]
        sql = f"{with_sql}\nselect {', '.join(key_cols + metric_cols)}\nfrom {from_sql}"
        if req.order_by:
            sql += f"\norder by {_q(req.order_by)} {'desc' if req.descending else 'asc'} nulls last"
        if req.limit:
            sql += f"\nlimit {int(req.limit)}"
        return sql

    def query(self, con: duckdb.DuckDBPyConnection, req: Request | dict) -> pd.DataFrame:
        if isinstance(req, dict):
            req = Request.from_dict(req)
        return con.execute(self.compile(req)).fetchdf()
