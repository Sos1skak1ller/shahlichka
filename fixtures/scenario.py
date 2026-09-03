"""Скриптовый демо-сценарий: детерминированная последовательность событий, из которой
собираются экранные фикстуры и с которой сверяется симуляция (check-parity).

Расширяется по мере готовности пользовательских историй. Сейчас: US1 (аватар).
"""

from __future__ import annotations

from dataclasses import dataclass

from gaming_engine import Engine

DEMO_USER = "demo-parent-01"


def _event(
    receipt_id: str,
    ts: str,
    saved: float,
    *,
    categories: list[str] | None = None,
    corrects: str | None = None,
) -> dict:
    return {
        "receipt_id": receipt_id,
        "user_id": DEMO_USER,
        "store_code": "s-pyat-014",
        "chain_code": "TS5",
        "district_code": "d-msk-042",
        "timestamp": ts,
        "sku_list": [f"sku-{receipt_id}"],
        "category_list": categories or ["baby_food"],
        "total_sum": max(saved, 0.0) * 9,
        "saved_amount": saved,
        "device_id_hash": "dev-demo-01",
        "payment_instrument_hash": "pay-demo-01",
        "corrects_receipt_id": corrects,
    }


# Демо-журнал: родитель с ребёнком до 3 лет, 4 недели покупок детских категорий.
# Накопленная экономия ~1 720 ₽ → уровень 2, стрик 4 недели.
DEMO_EVENTS: list[dict] = [
    _event("d1", "2026-03-02T10:15:00Z", 260.0, categories=["baby_food", "diapers"]),
    _event("d2", "2026-03-04T18:40:00Z", 180.0, categories=["hygiene"]),
    _event("d3", "2026-03-09T09:05:00Z", 320.0, categories=["baby_food"]),
    _event("d4", "2026-03-12T20:10:00Z", 150.0, categories=["dairy", "baby_food"]),
    _event("d5", "2026-03-16T11:30:00Z", 300.0, categories=["diapers"]),
    _event("d6", "2026-03-19T17:25:00Z", 130.0, categories=["baby_food"]),
    _event("d7", "2026-03-23T08:50:00Z", 250.0, categories=["baby_food", "hygiene"]),
    _event("d8", "2026-03-26T19:00:00Z", 130.0, categories=["baby_food"]),
]


@dataclass
class DemoScenario:
    engine: Engine
    user_id: str


# Момент выдачи персонального челленджа — начало недели W13.
CHALLENGE_AT = "2026-03-23T07:00:00Z"


def build_scenario(*, gaming_layer_enabled: bool = True) -> DemoScenario:
    eng = Engine(gaming_layer_enabled=gaming_layer_enabled)
    eng.register_user(
        DEMO_USER,
        archetype="loyalist",
        segment="parents_0_3",
        chain_code="TS5",
        display_name="Анна",  # никнейм для демо, не ПДн (FR-029)
    )
    for ev in DEMO_EVENTS:
        if ev["timestamp"] >= CHALLENGE_AT and eng.challenges.active(DEMO_USER) is None:
            eng.generate_challenge(DEMO_USER, CHALLENGE_AT)
        res = eng.ingest(ev)
        assert res.accepted, res.reason
    if eng.challenges.active(DEMO_USER) is None:
        eng.generate_challenge(DEMO_USER, CHALLENGE_AT)

    _demo_referrals(eng)
    return DemoScenario(engine=eng, user_id=DEMO_USER)


def _demo_referrals(eng: Engine) -> None:
    """Демо-реферал: один друг довёл путь до награды, второй — только зарегистрировался."""
    r1 = eng.create_invite(DEMO_USER, "2026-03-10T09:00:00Z")
    eng.register_referral(
        r1.invitee_token, "friend-anna", "2026-03-11T10:00:00Z",
        invitee_device_hash="dev-anna", invitee_payment_hash="pay-anna",
    )
    eng.ingest(
        {
            "receipt_id": "friend-anna-r1", "user_id": "friend-anna", "store_code": "s-pyat-020",
            "chain_code": "TS5", "district_code": "d-msk-051", "timestamp": "2026-03-14T18:00:00Z",
            "sku_list": ["sku-a1", "sku-a2"], "category_list": ["baby_food"],
            "total_sum": 1400.0, "saved_amount": 210.0,
            "device_id_hash": "dev-anna", "payment_instrument_hash": "pay-anna",
            "corrects_receipt_id": None,
        }
    )
    r2 = eng.create_invite(DEMO_USER, "2026-03-20T09:00:00Z")
    eng.register_referral(
        r2.invitee_token, "friend-oleg", "2026-03-21T10:00:00Z",
        invitee_device_hash="dev-oleg", invitee_payment_hash="pay-oleg",
    )


def key_numbers(scn: DemoScenario) -> dict:
    """Ключевые числа для инварианта паритета demo ↔ sim (SC-006)."""
    pv = scn.engine.get_profile_view(scn.user_id)
    return {
        "total_saved_amount": pv.savings.total_saved_amount,
        "avatar_level": pv.avatar.level,
        "streak_count": pv.streak.streak_count,
    }
