"""Run the benchmark.

    # local model through Ollama (free):
    python scripts/run_benchmark.py --backend openai --model qwen2.5-coder:7b
    # Claude (needs ANTHROPIC_API_KEY):
    python scripts/run_benchmark.py --backend anthropic --model <model id>
    # replay the recorded responses of the published run (no model needed):
    python scripts/run_benchmark.py --backend replay

Writes results/answers.csv, results/run.json, results/benchmark_report.md and records
every model response in results/responses.jsonl so the run can be replayed exactly.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gab.benchmark import run  # noqa: E402
from gab.llm import Recorder, make_llm  # noqa: E402
from gab.report import write_report  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--backend", choices=["openai", "anthropic", "replay"], default="openai")
    p.add_argument("--model")
    p.add_argument("--base-url", default="http://localhost:11434/v1")
    p.add_argument("--only", nargs="*", help="question ids, e.g. q01 q05")
    p.add_argument("--out", default=str(ROOT / "results"))
    args = p.parse_args()

    out = Path(args.out)
    responses = out / "responses.jsonl"
    if args.backend == "replay":
        llm = make_llm("replay", None, None, responses)
    else:
        if responses.exists():
            responses.unlink()
        llm = Recorder(make_llm(args.backend, args.model, args.base_url, None), responses)
    run(ROOT / "data" / "warehouse.duckdb", ROOT / "data" / "semantic_manifest.json",
        ROOT / "questions" / "questions.yml", llm, out, args.only)
    print(write_report(out).split("## Outcome by question")[0])


if __name__ == "__main__":
    main()
