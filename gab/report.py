"""Write results/benchmark_report.md from results/answers.csv."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pandas as pd

LABEL = {"raw_sql": "LLM + raw SQL", "governed": "LLM + governed metrics"}
CATS = {"funnel": "Revenue funnel", "cx": "Customer experience", "workforce": "Workforce",
        "unanswerable": "Not answerable (should refuse)"}


def pct(x: float) -> str:
    return f"{x * 100:.0f}%"


def show(v) -> str:
    """Display value: floats to 6 significant digits, so summation-order noise does not show."""
    if not isinstance(v, str):
        return "-"
    try:
        x = float(v)
    except ValueError:
        return v
    return str(int(x)) if x.is_integer() and "e" not in v.lower() else f"{x:.6g}"


def write_report(out_dir: Path) -> str:
    df = pd.read_csv(out_dir / "answers.csv")
    meta = json.loads((out_dir / "run.json").read_text(encoding="utf-8"))
    acc = df.groupby("agent")["correct"].mean()
    n = df["id"].nunique()
    trap = df[df["trap"].fillna("") != ""]
    lines = [
        "# Benchmark results",
        "",
        f"Run {date.today().isoformat()} · model `{meta['model']}` · {n} questions · temperature 0 · one retry after an error.",
        "",
        "| | " + " | ".join(LABEL[a] for a in ["raw_sql", "governed"]) + " |",
        "|---|---|---|",
        "| **Correct answers** | " + " | ".join(f"**{pct(acc.get(a, 0))}** ({int(df[(df.agent == a)].correct.sum())}/{n})" for a in ["raw_sql", "governed"]) + " |",
    ]
    for cat, label in CATS.items():
        sub = df[df.category == cat]
        if sub.empty:
            continue
        k = sub["id"].nunique()
        lines.append(f"| {label} ({k}) | " + " | ".join(pct(sub[sub.agent == a].correct.mean()) for a in ["raw_sql", "governed"]) + " |")
    if not trap.empty:
        k = trap["id"].nunique()
        lines.append(f"| Questions with a definition trap ({k}) | " + " | ".join(pct(trap[trap.agent == a].correct.mean()) for a in ["raw_sql", "governed"]) + " |")
    inv = df[df.outcome == "invented_answer"].groupby("agent").size()
    lines.append("| Invented an answer to an unanswerable question | " + " | ".join(str(int(inv.get(a, 0))) for a in ["raw_sql", "governed"]) + " |")
    err = df[df.outcome == "execution_error"].groupby("agent").size()
    lines.append("| Failed to produce a valid query after one retry | " + " | ".join(str(int(err.get(a, 0))) for a in ["raw_sql", "governed"]) + " |")
    lines += ["", "## Outcome by question", "",
              "| # | Question | Raw SQL | Governed | Gold |", "|---|---|---|---|---|"]
    for qid, grp in df.groupby("id", sort=True):
        r = grp.set_index("agent")
        def cell(a):
            row = r.loc[a]
            mark = "✅" if row.correct else "❌"
            if row.refused:
                ans = "refused"
            elif not isinstance(row.answer, str) and row.correct:
                ans = "empty result"
            else:
                ans = show(row.answer)
            if len(ans) > 26:
                ans = ans[:26] + "…"
            return f"{mark} {ans}" + ("" if row.correct else f" ({row.outcome.replace('_', ' ')})")
        gold = show(r.iloc[0].gold) if isinstance(r.iloc[0].gold, str) else "refuse"
        if isinstance(gold, str) and len(gold) > 26:
            gold = gold[:26] + "…"
        lines.append(f"| {qid} | {r.iloc[0].question} | {cell('raw_sql')} | {cell('governed')} | {gold} |")
    lines += ["", "## Where the raw-SQL agent went wrong", ""]
    wrong = df[(df.agent == "raw_sql") & (~df.correct)]
    for r in wrong.itertuples():
        lines.append(f"**{r.id}. {r.question}** — {r.outcome.replace('_', ' ')}. "
                     + (f"Trap: {r.trap} " if isinstance(r.trap, str) and r.trap else "")
                     + (f"Answer {show(r.answer)}, gold {show(r.gold)}." if isinstance(r.answer, str) and isinstance(r.gold, str) else ""))
        if isinstance(r.query, str) and r.query:
            lines += ["", "```sql", r.query.strip(), "```", ""]
    lines += ["", "## Where the governed agent went wrong", ""]
    wrong = df[(df.agent == "governed") & (~df.correct)]
    if wrong.empty:
        lines.append("Nowhere in this run.")
    for r in wrong.itertuples():
        lines.append(f"**{r.id}. {r.question}** — {r.outcome.replace('_', ' ')}. "
                     + (f"Answer {show(r.answer)}, gold {show(r.gold)}. " if isinstance(r.answer, str) and isinstance(r.gold, str) else "")
                     + (f"Request: `{r.query}`" if isinstance(r.query, str) and r.query else "")
                     + (f" Error: {r.error}" if isinstance(r.error, str) and r.error else ""))
        lines.append("")
    text = "\n".join(lines) + "\n"
    (out_dir / "benchmark_report.md").write_text(text, encoding="utf-8")
    return text
