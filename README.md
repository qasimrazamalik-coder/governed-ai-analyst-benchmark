# Governed AI Analyst Benchmark

**Does an LLM give more trustworthy business answers when it has to go through a governed metric layer instead of writing SQL against the warehouse?**

This repo measures that on one warehouse, one question set and one model. The same model answers the same 40 questions twice:

| Agent | What it sees | What it sends |
|---|---|---|
| **LLM + raw SQL** | every table and column in the `marts` schema | one DuckDB `SELECT` |
| **LLM + governed metrics** | the governed metric catalogue (names, descriptions, dimensions) | a structured request (`metrics`, `group_by`, `where`, dates, `order_by`, `limit`) that a semantic-layer compiler turns into SQL |

Both get the same answer-format hint, temperature 0 and one retry after an error. Either may refuse when the data cannot answer the question.

## Result (one run, one local model)

Model: **Qwen2.5-Coder-7B-Instruct** (Q4_K_M GGUF) served by llama.cpp `llama-server` (build b11714, Vulkan) on a laptop RTX 5060. Temperature 0, one retry after an error. Full table: [`results/benchmark_report.md`](results/benchmark_report.md).

| | LLM + raw SQL | LLM + governed metrics |
|---|---|---|
| **Correct answers** | **60%** (24/40) | **70%** (28/40) |
| Revenue funnel (16) | 38% | 75% |
| Customer experience (15) | 60% | 67% |
| Workforce (4) | 100% | 25% |
| Not answerable, should refuse (5) | 100% | 100% |
| Questions with a definition trap (19) | 58% | 68% |
| **Returned a wrong number or label** | **11** | **4** |
| Returned nothing (error after retry, empty result, or refused an answerable question) | 5 | 8 |
| Invented an answer to an unanswerable question | 0 | 0 |

**What this run shows**

- **The governed agent was wrong less often, and when it failed it mostly failed loudly.** The raw-SQL agent gave 11 confident wrong answers; the governed agent gave 4. Eight of the governed agent's 12 misses returned no number at all (a rejected request after its retry, or a filter value that matched nothing), which a person notices. A wrong number does not get noticed.
- **The raw-SQL misses are definition errors, not syntax errors.** Activation rate divided by leads instead of sales (q10: 11% vs 91%), "share of sales never activated" divided by leads (q08), FCR, contact rate and conversion read off the first row of a monthly KPI table (q02, q03, q14, q19), bot resolution taken from a resolved flag without the no-repeat rule (q21: 73% vs 60%). Each query ran and returned a plausible number. The metric layer removes that whole class of error because the definition is not the model's to choose.
- **The governed agent's misses are interface errors.** It filtered on values that do not exist (`entry_channel = 'Billing'`, `speed_to_lead_band = '5 business minutes'`, `tier = 'tier_1'`), grouped by quarter when it wanted the whole half-year and then took the first row (q19, q23), used `>=` on a time filter instead of start/end (q32), or sorted the wrong way for "lower" (q35). Those mistakes cost it three of the four workforce questions, which raw SQL got all right. Better dimension-value hints in the catalogue are the obvious next step; they are not in this run.
- **Neither agent invented an answer** to the five questions the data cannot answer (NPS, web visitors, a campaign that does not exist).

**How far to trust it.** This is one 7B model, one run, 40 questions, on simulated data. The two agents disagree on 14 questions (9 go to governed, 5 to raw SQL); an exact McNemar test on those gives p ≈ 0.42, so the headline 60% vs 70% is **not** statistically significant. The gap in wrong answers (11 vs 4) and the kind of mistakes each agent makes are the more useful findings. llama.cpp output at temperature 0 is not bit-for-bit repeatable across runs, which is why every response is recorded and CI replays the recording instead of calling a model. A larger model would likely score higher on both sides; whether the gap holds then is what a `--backend anthropic` run would test (not run here: it needs an API key).

**One change made during the run.** The first attempt was stopped after three questions: the governed agent filtered `metric_time__month = '2025-03'`, and the compiler compared that text with a date, silently matched nothing, and reported "no answer". That is a bug in the layer, not a model error, so time filters are now typed (a value that is not a `YYYY-MM-DD` date is rejected with a message, which triggers the retry), a test covers it, and the benchmark was rerun from the first question. The results above are from that full rerun.

## The data and the questions

- **Warehouse:** [cx-journey-warehouse](https://github.com/qasimrazamalik-coder/cx-journey-warehouse), built at a pinned commit (`scripts/bootstrap_warehouse.py`). It is **simulated data** for a broadband sales and service operation, January to June 2025: leads, dial attempts, bot / chat / voice contacts, agents, spend.
- **Semantic layer:** the warehouse's dbt `semantic_models` and `metrics`. `gab/semantic.py` compiles requests against its `semantic_manifest.json`. It implements the subset of MetricFlow this benchmark needs (simple, ratio and derived metrics, time grains, dimension filters, ordering) so the benchmark runs with no MetricFlow server. It is not MetricFlow.
- **Questions:** `questions/questions.yml` — 40 questions written as a business user would ask them: 16 revenue funnel, 15 customer experience, 4 workforce, and 5 the data cannot answer (the right response is to refuse).
- **Gold answers:** hand-written DuckDB SQL per question, written independently of the semantic layer. 19 questions carry a *definition trap*: the obvious column or table gives a plausible wrong number (activation divided by leads instead of sales, the agent's "resolved" flag instead of outcome-based FCR, containment read as resolution, daily adherence percentages averaged). Five of the 19 are the unanswerable questions.
- **Reference plans:** each answerable question also has the governed request a careful analyst would send. `tests/test_reference_plans.py` checks that every one returns the gold answer, so gold SQL and the layer validate each other, and a governed miss is the model's choice, not a gap in the layer.
- **Scoring** (`gab/scoring.py`): rates within 0.15 percentage points, money and durations within 1%, counts within 0.05%, labels exact (months as `YYYY-MM`). An unanswerable question scores correct on a refusal or an empty result and wrong on any invented number.

## Run it

```bash
python -m venv .venv && . .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/bootstrap_warehouse.py --scale 1.0  # builds the upstream warehouse into data/
pytest -q                                          # scoring + every reference plan vs gold

# replay the published run exactly (no model, no key) — this is what CI does
python scripts/run_benchmark.py --backend replay

# any OpenAI-compatible server, e.g. llama.cpp's llama-server or Ollama
python scripts/run_benchmark.py --backend openai --base-url http://127.0.0.1:8080/v1 --model qwen2.5-coder-7b-instruct-q4_k_m

# Claude (needs ANTHROPIC_API_KEY)
python scripts/run_benchmark.py --backend anthropic --model <model id>
```

A live run rewrites `results/` and records every model response in `results/responses.jsonl`, so the run can be replayed without the model.

## Layout

```
gab/semantic.py     semantic-layer compiler over semantic_manifest.json
gab/agents.py       the two agents, prompts, one-retry loop
gab/llm.py          backends: anthropic, openai-compatible, replay (+ recorder)
gab/scoring.py      tolerances and outcome labels
gab/benchmark.py    runs both agents over the questions
gab/report.py       writes results/benchmark_report.md
questions/          the 40 questions, gold SQL and reference plans
results/            answers.csv, run.json, responses.jsonl, benchmark_report.md
```

## License

MIT
