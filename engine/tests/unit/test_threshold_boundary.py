"""T044 / research.md R4 — на границе решение принимается СТРОЖЕ:
score ровно на пороге блокировки → block, ровно на пороге ревью → review.
"""

from __future__ import annotations

from gaming_engine import config
from gaming_engine.antifraud import _decide


def test_exact_block_threshold_blocks() -> None:
    assert _decide(config.FRAUD_THRESHOLDS["block"]) == "block"


def test_just_below_block_is_review() -> None:
    assert _decide(config.FRAUD_THRESHOLDS["block"] - 1e-3) == "review"


def test_exact_review_threshold_is_review() -> None:
    assert _decide(config.FRAUD_THRESHOLDS["review"]) == "review"


def test_just_below_review_is_pass() -> None:
    assert _decide(config.FRAUD_THRESHOLDS["review"] - 1e-3) == "pass"


def test_zero_is_pass() -> None:
    assert _decide(0.0) == "pass"
