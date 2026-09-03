"""T061 / FR-017/FR-021..FR-024 — реферальная state-machine: награда только после
подтверждённой покупки; self-referral блокируется; окно истекает без награды.
"""

from __future__ import annotations

from gaming_engine import Engine

from tests.conftest import make_event


def _buy(eng: Engine, user: str, ts: str, *, dev="dev-x", pay="pay-x") -> None:
    eng.ingest(
        make_event(
            f"{user}-{ts}", user, timestamp=ts, saved_amount=200.0,
            categories=["baby_food"], device_id_hash=dev, payment_instrument_hash=pay,
        )
    )


def test_reward_only_after_confirmed_purchase() -> None:
    eng = Engine()
    eng.register_user("inviter", archetype="loyalist")
    _buy(eng, "inviter", "2026-03-02T09:00:00Z", dev="dev-inv", pay="pay-inv")

    ref = eng.create_invite("inviter", "2026-03-02T10:00:00Z")
    assert ref.status == "invited"
    assert eng.referrals.released_total("inviter") == 0.0

    ref = eng.register_referral(
        ref.invitee_token, "friend", "2026-03-03T10:00:00Z",
        invitee_device_hash="dev-friend", invitee_payment_hash="pay-friend",
    )
    assert ref.status == "registered"
    assert ref.window_deadline is not None
    assert eng.referrals.released_total("inviter") == 0.0  # ещё нет награды (FR-021)

    _buy(eng, "friend", "2026-03-05T12:00:00Z", dev="dev-friend", pay="pay-friend")
    ref = eng.referrals._by_id[ref.referral_id]  # noqa: SLF001
    assert ref.status == "reward_released"
    assert ref.reward_amount > 0
    assert eng.referrals.released_total("inviter") == ref.reward_amount


def test_self_referral_blocked_by_device_hash() -> None:
    eng = Engine()
    eng.register_user("inviter", archetype="loyalist")
    _buy(eng, "inviter", "2026-03-02T09:00:00Z", dev="dev-shared", pay="pay-inv")
    ref = eng.create_invite("inviter", "2026-03-02T10:00:00Z")
    ref = eng.register_referral(
        ref.invitee_token, "alt", "2026-03-03T10:00:00Z",
        invitee_device_hash="dev-shared", invitee_payment_hash="pay-alt",
    )
    assert ref.status == "blocked"
    assert ref.block_reason == "self_referral"


def test_self_referral_blocked_by_payment_hash() -> None:
    eng = Engine()
    eng.register_user("inviter", archetype="loyalist")
    _buy(eng, "inviter", "2026-03-02T09:00:00Z", dev="dev-inv", pay="pay-shared")
    ref = eng.create_invite("inviter", "2026-03-02T10:00:00Z")
    ref = eng.register_referral(
        ref.invitee_token, "alt", "2026-03-03T10:00:00Z",
        invitee_device_hash="dev-alt", invitee_payment_hash="pay-shared",
    )
    assert ref.status == "blocked"
    assert ref.block_reason == "self_referral"


def test_window_expiry_closes_without_reward() -> None:
    eng = Engine()
    eng.register_user("inviter", archetype="loyalist")
    _buy(eng, "inviter", "2026-03-02T09:00:00Z", dev="dev-inv", pay="pay-inv")
    ref = eng.create_invite("inviter", "2026-03-02T10:00:00Z")
    ref = eng.register_referral(
        ref.invitee_token, "slow", "2026-03-03T10:00:00Z",
        invitee_device_hash="dev-slow", invitee_payment_hash="pay-slow",
    )
    # покупка сильно позже окна (30 дней)
    _buy(eng, "slow", "2026-05-01T12:00:00Z", dev="dev-slow", pay="pay-slow")
    ref = eng.referrals._by_id[ref.referral_id]  # noqa: SLF001
    assert ref.status == "expired"
    assert eng.referrals.released_total("inviter") == 0.0


def test_referral_view_shape() -> None:
    eng = Engine()
    eng.register_user("inviter", archetype="loyalist")
    _buy(eng, "inviter", "2026-03-02T09:00:00Z", dev="dev-inv", pay="pay-inv")
    r = eng.create_invite("inviter", "2026-03-02T10:00:00Z")
    eng.register_referral(
        r.invitee_token, "friend", "2026-03-03T10:00:00Z",
        invitee_device_hash="dev-friend", invitee_payment_hash="pay-friend",
    )
    view = eng.get_referral_view("inviter")
    assert view.user_id == "inviter"
    assert view.invite_link.startswith("https://")
    assert len(view.referrals) == 1
    assert view.referrals[0].status == "registered"
