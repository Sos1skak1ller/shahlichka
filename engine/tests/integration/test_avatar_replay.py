"""T017 / SC-005 — детерминизм state-machine аватара и стрика.

Прогоняем golden-истории синтетических покупок и сверяем итоговую проекцию профиля.
Также проверяем инвариант «число заходов в приложение не влияет на прогресс»
(модель движка вообще не имеет такого входа) и повторный replay даёт тот же результат.
"""

from __future__ import annotations

import pytest

from gaming_engine import Engine

from tests.conftest import load_histories, make_event

HISTORIES = load_histories()


def _run(history: dict) -> Engine:
    eng = Engine()
    u = history["user"]
    eng.register_user(u["user_id"], archetype=u.get("archetype", "mixed"))
    for raw in history["events"]:
        ev = make_event(
            raw["receipt_id"],
            user_id=u["user_id"],
            timestamp=raw["timestamp"],
            saved_amount=raw["saved_amount"],
            corrects_receipt_id=raw.get("corrects_receipt_id"),
        )
        res = eng.ingest(ev)
        assert res.accepted, f"{raw['receipt_id']} rejected: {res.reason}"
    return eng


@pytest.mark.parametrize("name,history", HISTORIES, ids=[n for n, _ in HISTORIES])
def test_history_matches_golden(name: str, history: dict) -> None:
    eng = _run(history)
    exp = history["expected"]
    view = eng.get_profile_view(history["user"]["user_id"])

    assert view.savings.total_saved_amount == pytest.approx(exp["total_saved_amount"])
    assert view.avatar.level == exp["level"]
    assert view.avatar.visual_stage == exp["visual_stage"]
    assert view.avatar.state == exp["state"]
    assert view.streak.streak_count == exp["streak_count"]
    assert view.streak.last_active_week == exp["last_active_week"]

    if exp.get("has_correction_transition"):
        reasons = [t.reason for t in eng.avatar_state(history["user"]["user_id"]).transition_history]
        assert "correction" in reasons
    if "min_unlocked_customizations" in exp:
        assert len(view.avatar.unlocked_customizations) >= exp["min_unlocked_customizations"]


@pytest.mark.parametrize("name,history", HISTORIES, ids=[n for n, _ in HISTORIES])
def test_replay_is_deterministic(name: str, history: dict) -> None:
    a = _run(history).get_profile_view(history["user"]["user_id"]).model_dump()
    b = _run(history).get_profile_view(history["user"]["user_id"]).model_dump()
    assert a == b


def test_app_opens_do_not_exist_as_input() -> None:
    """Инвариант принципа I: у движка нет входа «открытие приложения»."""
    import inspect

    from gaming_engine.contracts import PurchaseEvent

    fields = set(PurchaseEvent.model_fields)
    assert not {"app_open", "app_opens", "session_count", "visits"} & fields
    # ingest принимает только событие покупки
    sig = inspect.signature(Engine.ingest)
    assert list(sig.parameters)[1] == "event"


def test_more_receipts_same_week_do_not_inflate_streak() -> None:
    eng = Engine()
    eng.register_user("z1", archetype="loyalist")
    for i in range(5):
        eng.ingest(
            make_event(f"r{i}", "z1", timestamp=f"2026-03-02T1{i}:00:00Z", saved_amount=50.0)
        )
    assert eng.get_profile_view("z1").streak.streak_count == 1
