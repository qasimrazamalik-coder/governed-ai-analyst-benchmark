"""Integration tests: the governed layer must reproduce every hand-written gold answer.

This checks two things at once: the gold SQL encodes the governed definitions, and the
semantic-layer compiler is correct. Needs data/ from scripts/bootstrap_warehouse.py
(skipped otherwise).
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gab.benchmark import gold_answer, load_questions, reference_answer  # noqa: E402
from gab.scoring import score  # noqa: E402
from gab.semantic import Request, SemanticError, SemanticLayer  # noqa: E402

DATA = ROOT / "data"
pytestmark = pytest.mark.skipif(not (DATA / "warehouse.duckdb").exists(), reason="run scripts/bootstrap_warehouse.py first")

QUESTIONS = [q for q in load_questions(ROOT / "questions" / "questions.yml") if q["kind"] != "refuse"]


@pytest.fixture(scope="module")
def env():
    import duckdb
    con = duckdb.connect(str(DATA / "warehouse.duckdb"), read_only=True)
    yield con, SemanticLayer.from_file(DATA / "semantic_manifest.json")
    con.close()


@pytest.mark.parametrize("q", QUESTIONS, ids=[q["id"] for q in QUESTIONS])
def test_reference_plan_matches_gold(env, q):
    con, layer = env
    gold = gold_answer(con, q)
    ref = reference_answer(con, layer, q)
    ok, outcome = score(q, False, ref, "", gold)
    assert ok, f"{q['id']}: governed={ref} gold={gold} ({outcome})"


def test_unknown_names_are_rejected_with_the_valid_options(env):
    _con, layer = env
    with pytest.raises(SemanticError, match="unknown metric 'nps'.*Valid metrics"):
        layer.compile(Request(metrics=["nps"]))
    with pytest.raises(SemanticError, match="not available"):
        layer.compile(Request(metrics=["contact_rate"], group_by=["contact__handling_path"]))


def test_catalog_lists_only_labelled_metrics(env):
    _con, layer = env
    text = layer.catalog_text()
    assert "bot_true_resolution_rate" in text
    assert "- fcr_eligible_contacts:" not in text  # helper metric, hidden


def test_time_filters_are_typed(env):
    con, layer = env
    # a non-date value fails loudly instead of matching nothing
    with pytest.raises(SemanticError, match="not a date"):
        layer.compile(Request(metrics=["unique_leads"], where=[{"dimension": "metric_time__month", "op": "=", "value": "2025-03"}]))
    with pytest.raises(SemanticError, match="not a date"):
        layer.compile(Request(metrics=["conversion_rate"], where=[{"dimension": "metric_time__quarter", "value": "Q2"}]))
    # the period start date filters the same rows as the equivalent date range
    by_filter = layer.query(con, Request(metrics=["unique_leads"],
                                         where=[{"dimension": "metric_time__month", "op": "=", "value": "2025-03-01"}]))
    by_range = layer.query(con, Request(metrics=["unique_leads"], start="2025-03-01", end="2025-03-31"))
    assert by_filter.iat[0, 0] == by_range.iat[0, 0] > 0
