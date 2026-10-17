"""Score an agent's answer against the gold answer."""

from __future__ import annotations

import math
from datetime import date, datetime

TOLERANCE = {
    "rate": {"abs": 0.0015},    # 0.15 percentage points
    "money": {"rel": 0.01},
    "count": {"rel": 0.0005},
    "duration": {"rel": 0.01},
}


def normalise_label(v) -> str:
    if isinstance(v, (date, datetime)):
        return v.strftime("%Y-%m")
    s = str(v).strip().lower()
    if len(s) >= 7 and s[4] == "-" and s[:4].isdigit():
        return s[:7]
    return s


def to_number(v):
    if v is None:
        return None
    if isinstance(v, bool):
        return None
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(x) else x


def score(question: dict, refused: bool, answer, error: str, gold) -> tuple[bool, str]:
    """Returns (correct, outcome). Outcomes:
    correct | wrong_value | invented_answer | false_refusal | execution_error | no_answer
    """
    kind = question["kind"]
    if kind == "refuse":
        if refused:
            return True, "correct"
        if error:
            return False, "execution_error"
        # An empty result (e.g. filtering on a campaign that does not exist) is not an invented number.
        if answer is None:
            return True, "correct"
        return False, "invented_answer"
    if refused:
        return False, "false_refusal"
    if error:
        return False, "execution_error"
    if answer is None:
        return False, "no_answer"
    if kind == "label":
        return (normalise_label(answer) == normalise_label(gold)), ("correct" if normalise_label(answer) == normalise_label(gold) else "wrong_value")
    a, g = to_number(answer), to_number(gold)
    if a is None or g is None:
        return False, "wrong_value"
    tol = TOLERANCE[kind]
    if kind == "rate" and a > 1.5 and g <= 1:
        a = a / 100  # accept 61.3 for 0.613
    ok = abs(a - g) <= tol["abs"] if "abs" in tol else abs(a - g) <= tol["rel"] * abs(g)
    return ok, "correct" if ok else "wrong_value"
