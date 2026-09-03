"""T028 / FR-019, US3 сценарий 5 — челлендж со стоимостью награды выше ожидаемого
прироста маржи отклоняется до показа пользователю.
"""

from __future__ import annotations

from gaming_engine import Engine, config

from tests.conftest import make_event


def _feed(eng: Engine, user: str) -> None:
    for i, ts in enumerate(
        ["2026-03-02T10:00:00Z", "2026-03-04T10:00:00Z", "2026-03-06T10:00:00Z"]
    ):
        eng.ingest(
            make_event(f"{user}-r{i}", user, timestamp=ts, saved_amount=300.0, categories=["baby_food"])
        )


def test_challenge_over_margin_uplift_is_rejected(monkeypatch) -> None:
    # ожидаемый прирост маржи от челленджа искусственно занижен → любой челлендж не проходит
    monkeypatch.setitem(config.EXPECTED_MARGIN_UPLIFT_BY_MECHANIC, "challenge", 1.0)

    eng = Engine()
    eng.register_user("u", archetype="loyalist", segment="parents_0_3")
    _feed(eng, "u")

    rec = eng.generate_challenge("u", "2026-03-09T10:00:00Z")
    assert rec.status == "rejected_economy"
    assert rec.within_budget is False

    view = eng.get_challenge_view("u", "2026-03-09T10:00:00Z")
    assert view.challenge is None  # не показывается

    wl = eng.ledger.week("u", "2026-W11", "loyalist")
    assert any(r.reason == "economy_invariant_violation" for r in wl.rejections)


def test_challenge_within_budget_is_shown() -> None:
    eng = Engine()
    eng.register_user("u", archetype="loyalist", segment="parents_0_3")
    _feed(eng, "u")
    rec = eng.generate_challenge("u", "2026-03-09T10:00:00Z")
    assert rec.status == "active"
    assert rec.within_budget is True
    view = eng.get_challenge_view("u", "2026-03-09T10:00:00Z")
    assert view.challenge is not None
    assert view.challenge.reward_amount <= config.EXPECTED_MARGIN_UPLIFT_BY_MECHANIC["challenge"]


def test_completed_challenge_accrues_within_cap() -> None:
    eng = Engine()
    eng.register_user("u", archetype="loyalist", segment="parents_0_3")
    _feed(eng, "u")
    rec = eng.generate_challenge("u", "2026-03-09T10:00:00Z")
    # выполняем челлендж покупками нужной категории на той же неделе
    for i in range(rec.target):
        eng.ingest(
            make_event(
                f"done-{i}", "u", timestamp="2026-03-10T1%d:00:00Z" % i,
                saved_amount=120.0, categories=[rec.category],
            )
        )
    assert eng.challenges.latest_visible("u").status == "completed"
    wl = eng.ledger.week("u", rec.iso_week, "loyalist")
    assert wl.spent_to_date == rec.reward_amount
    assert wl.spent_to_date <= wl.budget_cap
