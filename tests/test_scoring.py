import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gab.agents import extract_json  # noqa: E402
from gab.scoring import score  # noqa: E402

RATE = {"kind": "rate", "expects": "number"}
MONEY = {"kind": "money", "expects": "number"}
LABEL = {"kind": "label", "expects": "label"}
REFUSE = {"kind": "refuse", "expects": "number"}


def test_rate_tolerance_is_absolute():
    assert score(RATE, False, 0.6131, "", 0.6120)[0]
    assert not score(RATE, False, 0.6200, "", 0.6120)[0]


def test_rate_given_as_percent_is_accepted():
    assert score(RATE, False, 61.2, "", 0.612)[0]


def test_money_tolerance_is_relative():
    assert score(MONEY, False, 1009.0, "", 1000.0)[0]
    assert not score(MONEY, False, 1020.0, "", 1000.0)[0]


def test_labels_compare_case_insensitively_and_months_by_yyyy_mm():
    assert score(LABEL, False, "phoenix", "", "Phoenix")[0]
    assert score(LABEL, False, date(2025, 5, 1), "", "2025-05")[0]
    assert score(LABEL, False, "2025-05-01 00:00:00", "", "2025-05")[0]


def test_unanswerable_questions():
    assert score(REFUSE, True, None, "", None) == (True, "correct")
    assert score(REFUSE, False, 42.0, "", None) == (False, "invented_answer")
    assert score(REFUSE, False, None, "", None) == (True, "correct")  # empty result is not an invented number


def test_failure_outcomes():
    assert score(RATE, True, None, "", 0.5) == (False, "false_refusal")
    assert score(RATE, False, None, "Binder Error", 0.5) == (False, "execution_error")
    assert score(RATE, False, None, "", 0.5) == (False, "no_answer")


def test_extract_json_tolerates_fences_and_prose():
    assert extract_json('Sure!\n```json\n{"sql": "select 1"}\n```') == {"sql": "select 1"}
    assert extract_json('{"refuse": true, "reason": "no {data}"}')["refuse"] is True
