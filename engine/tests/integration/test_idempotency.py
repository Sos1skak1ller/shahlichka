"""T018 / FR-030a — повторная доставка события с тем же receipt_id учитывается
ровно один раз и не двигает прогресс аватара, стрик или накопление.
"""

from __future__ import annotations

from gaming_engine import Engine

from tests.conftest import make_event


def test_duplicate_receipt_is_ignored() -> None:
    eng = Engine()
    eng.register_user("u1", archetype="loyalist")
    ev = make_event("r1", "u1", timestamp="2026-03-02T10:00:00Z", saved_amount=600.0)

    first = eng.ingest(ev)
    assert first.accepted

    before = eng.get_profile_view("u1").model_dump()

    for _ in range(3):
        again = eng.ingest(ev)
        assert not again.accepted
        assert again.reason == "duplicate_receipt"

    after = eng.get_profile_view("u1").model_dump()
    assert before == after
    assert after["savings"]["total_saved_amount"] == 600.0
    assert after["avatar"]["level"] == 1
    assert len(eng.log.user_events("u1")) == 1


def test_duplicate_does_not_advance_streak_or_transitions() -> None:
    eng = Engine()
    eng.register_user("u1")
    ev = make_event("r1", "u1", timestamp="2026-03-02T10:00:00Z", saved_amount=100.0)
    eng.ingest(ev)
    eng.ingest(ev)
    eng.ingest(ev)
    assert eng.get_profile_view("u1").streak.streak_count == 1
    assert eng.avatar_state("u1").transition_history == []


def test_orphan_correction_is_rejected() -> None:
    eng = Engine()
    eng.register_user("u1")
    corr = make_event(
        "c1", "u1", timestamp="2026-03-09T10:00:00Z", saved_amount=-50.0,
        corrects_receipt_id="does-not-exist",
    )
    res = eng.ingest(corr)
    assert not res.accepted
    assert res.reason == "orphan_correction"
    assert eng.total_saved("u1") == 0.0
