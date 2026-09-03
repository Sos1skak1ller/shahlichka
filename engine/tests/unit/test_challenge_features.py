"""T026 — построение RFM-признаков пользователя из событийного лога."""

from __future__ import annotations

from gaming_engine.challenge.features import build
from gaming_engine.contracts import PurchaseEvent

from tests.conftest import make_event


def _ev(rid: str, ts: str, saved: float, cats: list[str]) -> PurchaseEvent:
    return PurchaseEvent.model_validate(
        make_event(rid, "u1", timestamp=ts, saved_amount=saved, categories=cats)
    )


def test_rfm_by_category() -> None:
    evs = [
        _ev("r1", "2026-03-02T10:00:00Z", 100.0, ["baby_food"]),
        _ev("r2", "2026-03-09T10:00:00Z", 150.0, ["baby_food", "diapers"]),
        _ev("r3", "2026-03-16T10:00:00Z", 90.0, ["diapers"]),
    ]
    f = build(evs, archetype="loyalist", avatar_level=1, as_of_week="2026-W12")
    assert f.has_history
    assert f.by_category["baby_food"].frequency == 2
    assert f.by_category["baby_food"].monetary == 250.0
    assert f.by_category["diapers"].frequency == 2
    # recency: последняя покупка baby_food на W11, as_of W12 → 1 неделя
    assert f.by_category["baby_food"].recency_weeks == 1
    assert f.by_category["diapers"].recency_weeks == 0
    assert f.top_categories(1)[0] in {"baby_food", "diapers"}


def test_zero_and_correction_events_ignored() -> None:
    evs = [
        _ev("r1", "2026-03-02T10:00:00Z", 0.0, ["baby_food"]),
        PurchaseEvent.model_validate(
            make_event(
                "c1", "u1", timestamp="2026-03-09T10:00:00Z", saved_amount=-50.0,
                corrects_receipt_id="r1", categories=["baby_food"],
            )
        ),
    ]
    f = build(evs, archetype="mixed", avatar_level=0, as_of_week="2026-W12")
    assert not f.has_history
    assert f.total_events == 0


def test_empty_history() -> None:
    f = build([], archetype="sleeper", avatar_level=0, as_of_week="2026-W10")
    assert not f.has_history
    assert f.top_categories() == []
