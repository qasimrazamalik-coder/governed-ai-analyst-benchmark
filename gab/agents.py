"""The two analysts being compared. Both get the same question, the same answer-format
hint and one retry after an error. They differ only in what they can see and do.

RawSQLAgent      sees the warehouse tables and columns; writes DuckDB SQL.
GovernedAgent    sees the governed metric catalogue; sends a structured request that the
                 semantic layer compiles. It cannot write SQL or name an undefined metric.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

import duckdb
import pandas as pd

from .semantic import Request, SemanticError, SemanticLayer

FORMAT_HINT = {
    "number": "The answer is a single number: return it in the first column of the first row.",
    "label": "The answer is a name or label: return it in the first column of the first row "
             "(for a month, use YYYY-MM).",
}


@dataclass
class AgentResult:
    refused: bool = False
    answer: object = None
    query: str = ""
    error: str = ""
    attempts: int = 0
    raw_responses: list = field(default_factory=list)
    seconds: float = 0.0


def extract_json(text: str) -> dict:
    """First JSON object in a model reply (tolerates code fences and prose around it)."""
    text = re.sub(r"```(?:json)?", "", text)
    start = text.find("{")
    while start != -1:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i + 1])
                    except json.JSONDecodeError:
                        break
        start = text.find("{", start + 1)
    raise ValueError("no JSON object in response")


def first_cell(df: pd.DataFrame):
    if df is None or df.empty or df.shape[1] == 0:
        return None
    v = df.iat[0, 0]
    if hasattr(v, "item"):
        v = v.item()
    return v


def schema_text(con: duckdb.DuckDBPyConnection, schemas=("marts",)) -> str:
    rows = con.execute(
        "select table_schema, table_name, column_name, data_type from information_schema.columns "
        f"where table_schema in ({', '.join(repr(s) for s in schemas)}) "
        "and table_name not like 'metricflow%' order by table_schema, table_name, ordinal_position"
    ).fetchall()
    tables: dict[str, list[str]] = {}
    for s, t, c, dt in rows:
        tables.setdefault(f"{s}.{t}", []).append(f"{c} {dt.lower()}")
    return "\n".join(f"{t}({', '.join(cols)})" for t, cols in tables.items())


RAW_SYSTEM = """You are a senior data analyst answering business questions with DuckDB SQL.
The warehouse covers a broadband company's sales leads, dial attempts, customer contacts
(bot, chat, voice) and agent workforce, January to June 2025. Dates are contact-center local dates.

Tables (name(columns)):
{schema}

Reply with JSON only, one of:
{{"sql": "<one DuckDB SELECT statement>"}}
{{"refuse": true, "reason": "<why the data cannot answer this>"}}
Refuse if the tables do not contain the data needed. Do not guess."""

GOVERNED_SYSTEM = """You are a senior data analyst. You answer business questions ONLY through the
company's governed metric layer. You cannot write SQL. The data covers a broadband company's sales
leads, customer contacts (bot, chat, voice) and agent workforce, January to June 2025.

{catalog}

Reply with JSON only, one of:
{{"metrics": ["<metric>"], "group_by": ["<dimension>"], "where": [{{"dimension": "<dimension>", "op": "=", "value": "<value>"}}],
  "start": "YYYY-MM-DD", "end": "YYYY-MM-DD", "order_by": {{"metric": "<metric>", "desc": true}}, "limit": 1}}
{{"refuse": true, "reason": "<why no governed metric answers this>"}}
Omit keys you do not need. For a "which ..." question, group by the dimension, order by the metric and use limit 1.
Refuse if no metric in the list measures what is asked. Do not approximate with a different metric."""


class RawSQLAgent:
    name = "raw_sql"

    def __init__(self, llm, con: duckdb.DuckDBPyConnection):
        self.llm = llm
        self.con = con
        self.system = RAW_SYSTEM.format(schema=schema_text(con))

    def answer(self, question: str, expects: str) -> AgentResult:
        res = AgentResult()
        user = f"Question: {question}\n{FORMAT_HINT[expects]}"
        for attempt in (1, 2):
            res.attempts = attempt
            c = self.llm.complete(self.system, user)
            res.seconds += c.seconds
            res.raw_responses.append(c.text)
            try:
                msg = extract_json(c.text)
            except ValueError as e:
                res.error = str(e)
                user = f"Question: {question}\n{FORMAT_HINT[expects]}\nYour last reply was not valid JSON. Reply with JSON only."
                continue
            if msg.get("refuse"):
                res.refused, res.error = True, ""
                return res
            res.query = str(msg.get("sql", ""))
            try:
                res.answer = first_cell(self.con.execute(res.query).fetchdf())
                res.error = ""
                return res
            except Exception as e:  # noqa: BLE001 - any database error is fed back once
                res.error = f"{type(e).__name__}: {e}"[:500]
                user = (f"Question: {question}\n{FORMAT_HINT[expects]}\n"
                        f"Your previous SQL failed:\n{res.query}\nError: {res.error}\nReply with corrected JSON.")
        return res


class GovernedAgent:
    name = "governed"

    def __init__(self, llm, con: duckdb.DuckDBPyConnection, layer: SemanticLayer):
        self.llm = llm
        self.con = con
        self.layer = layer
        self.system = GOVERNED_SYSTEM.format(catalog=layer.catalog_text())

    def answer(self, question: str, expects: str) -> AgentResult:
        res = AgentResult()
        user = f"Question: {question}\n{FORMAT_HINT[expects]}"
        for attempt in (1, 2):
            res.attempts = attempt
            c = self.llm.complete(self.system, user)
            res.seconds += c.seconds
            res.raw_responses.append(c.text)
            try:
                msg = extract_json(c.text)
            except ValueError as e:
                res.error = str(e)
                user = f"Question: {question}\n{FORMAT_HINT[expects]}\nYour last reply was not valid JSON. Reply with JSON only."
                continue
            if msg.get("refuse"):
                res.refused, res.error = True, ""
                return res
            res.query = json.dumps(msg)
            try:
                req = Request.from_dict(msg)
                df = self.layer.query(self.con, req)
                if df.empty:
                    res.answer = None
                elif req.group_by and expects == "label":
                    res.answer = first_cell(df)
                else:
                    res.answer = first_cell(df[[req.metrics[0]]])
                res.error = ""
                return res
            except (SemanticError, KeyError, TypeError, ValueError, duckdb.Error) as e:
                res.error = f"{type(e).__name__}: {e}"[:500]
                user = (f"Question: {question}\n{FORMAT_HINT[expects]}\n"
                        f"Your previous request was rejected:\n{res.query}\nError: {res.error}\nReply with corrected JSON.")
        return res
