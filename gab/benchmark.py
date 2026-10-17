"""Run both agents (and the oracle reference plans) over the question set."""

from __future__ import annotations

import json
import time
from pathlib import Path

import duckdb
import pandas as pd
import yaml

from .agents import GovernedAgent, RawSQLAgent, first_cell
from .scoring import score
from .semantic import Request, SemanticLayer


def load_questions(path: Path) -> list[dict]:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))["questions"]


def gold_answer(con: duckdb.DuckDBPyConnection, q: dict):
    if q["kind"] == "refuse":
        return None
    return first_cell(con.execute(q["gold_sql"]).fetchdf())


def reference_answer(con, layer: SemanticLayer, q: dict):
    ref = q["reference"]
    if ref.get("refuse"):
        return None
    req = Request.from_dict(ref)
    df = layer.query(con, req)
    if req.group_by and q["expects"] == "label":
        return first_cell(df)
    return first_cell(df[[req.metrics[0]]])


def run(warehouse: Path, manifest: Path, questions_path: Path, llm, out_dir: Path,
        only: list[str] | None = None) -> pd.DataFrame:
    con = duckdb.connect(str(warehouse), read_only=True)
    layer = SemanticLayer.from_file(manifest)
    questions = [q for q in load_questions(questions_path) if not only or q["id"] in only]
    agents = [RawSQLAgent(llm, con), GovernedAgent(llm, con, layer)]
    rows = []
    for q in questions:
        gold = gold_answer(con, q)
        for agent in agents:
            t0 = time.time()
            r = agent.answer(q["question"], q["expects"])
            ok, outcome = score(q, r.refused, r.answer, r.error, gold)
            rows.append({
                "id": q["id"], "category": q["category"], "question": q["question"], "kind": q["kind"],
                "trap": q.get("trap", ""), "agent": agent.name, "correct": ok, "outcome": outcome,
                "answer": None if r.answer is None else str(r.answer), "gold": None if gold is None else str(gold),
                "refused": r.refused, "attempts": r.attempts, "error": r.error, "query": r.query,
                "seconds": round(time.time() - t0, 2),
            })
            print(f"{q['id']} {agent.name:<9} {outcome:<16} answer={rows[-1]['answer']!s:<24} gold={rows[-1]['gold']}", flush=True)
    df = pd.DataFrame(rows)
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_dir / "answers.csv", index=False)
    meta = {"model": getattr(llm, "model", "unknown"), "questions": len(questions)}
    (out_dir / "run.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    con.close()
    return df
