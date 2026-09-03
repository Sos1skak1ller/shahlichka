"""T043 / FR-015a — полоса «на ревью» удерживает награду и авто-разрешается
по детерминированному правилу; новый сигнал риска в окне удержания → block.
"""

from __future__ import annotations

import pytest

from gaming_engine import config
from gaming_engine.antifraud import AntifraudService


@pytest.fixture(autouse=True)
def wide_review_band(monkeypatch):
    # делаем полосу review легко достижимой и явной для теста
    monkeypatch.setitem(config.FRAUD_THRESHOLDS, "review", 0.40)
    monkeypatch.setitem(config.FRAUD_THRESHOLDS, "block", 0.90)


def _referral(af: AntifraudService, rid: str, at: str, *, payment_collision: bool) -> str:
    fs = af.score_referral(
        referral_id=rid,
        inviter_user_id="inv",
        at=at,
        inviter_device_hash="dev-x",
        invitee_device_hash="dev-x",  # device collision → 0.25
        inviter_payment_hash="pay-x",
        invitee_payment_hash="pay-x" if payment_collision else "pay-y",
    )
    return fs.decision


def test_review_band_holds_reward_then_resolves_pass() -> None:
    af = AntifraudService()
    d = _referral(af, "ref-1", "2026-03-02T10:00:00Z", payment_collision=True)
    assert d == "review"  # 0.25 + 0.20 = 0.45 ≥ 0.40

    # награда «висит» до истечения REVIEW_HOLD
    af.tick("2026-03-03T00:00:00Z")
    assert af.effective_decision("ref-1") == "review"

    # после REVIEW_HOLD и без новых сигналов → pass
    resolved = af.tick("2026-03-08T00:00:00Z")
    assert [r.entity_id for r in resolved] == ["ref-1"]
    assert af.effective_decision("ref-1") == "pass"
    assert af._by_entity["ref-1"].review_outcome == "pass"
    assert af._by_entity["ref-1"].review_resolved_at == "2026-03-08T00:00:00Z"


def test_new_risk_signal_in_hold_window_forces_block() -> None:
    af = AntifraudService()
    assert _referral(af, "ref-2", "2026-03-02T10:00:00Z", payment_collision=True) == "review"
    # новый сигнал риска у того же пользователя внутри окна удержания
    assert _referral(af, "ref-2b", "2026-03-03T10:00:00Z", payment_collision=True) == "review"

    af.tick("2026-03-10T00:00:00Z")
    assert af._by_entity["ref-2"].review_outcome == "block"
    assert af.effective_decision("ref-2") == "block"


def test_counters_shape() -> None:
    af = AntifraudService()
    _referral(af, "r", "2026-03-02T10:00:00Z", payment_collision=True)
    assert set(af.counters()) == {"blocked", "review", "review_auto_resolved"}
    assert af.counters()["review"] == 1
