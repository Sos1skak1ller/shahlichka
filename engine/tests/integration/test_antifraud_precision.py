"""T041 / SC-004 — precision антифрода на фрод-классе ≥ 0.90 на помеченном наборе
синтетических паттернов. Recall выводится, но не гейтит.
"""

from __future__ import annotations

from gaming_engine.antifraud import AntifraudService, precision_recall_on_labeled
from gaming_engine.contracts import PurchaseEvent

from tests.conftest import make_event


def _receipt(**kw) -> PurchaseEvent:
    return PurchaseEvent.model_validate(make_event(**kw))


def _build_labeled_set() -> list[tuple[bool, str]]:
    af = AntifraudService()
    preds: list[tuple[bool, str]] = []

    # --- 80 нормальных чеков: уникальные хэши, обычные суммы, без всплесков ---
    for i in range(80):
        ev = _receipt(
            receipt_id=f"ok-{i}",
            user_id=f"good-{i}",
            timestamp=f"2026-03-02T{i % 24:02d}:{(i * 7) % 60:02d}:00Z",
            saved_amount=180.0 + (i % 5) * 15,
            device_id_hash=f"dev-good-{i}",
            payment_instrument_hash=f"pay-good-{i}",
        )
        fs = af.score_receipt(ev, archetype="loyalist")
        preds.append((False, fs.decision))

    # --- фрод-кольцо: 4 «разных» пользователя на одном устройстве и карте,
    #     всплеск чеков в течение часа, аномальные суммы ---
    for u in range(4):
        for k in range(6):
            ev = _receipt(
                receipt_id=f"ring-{u}-{k}",
                user_id=f"ring-user-{u}",
                timestamp=f"2026-03-05T10:{k * 8:02d}:00Z",
                saved_amount=1500.0,  # сильное отклонение от архетипа
                device_id_hash="dev-ring",
                payment_instrument_hash="pay-ring",
            )
            fs = af.score_receipt(ev, archetype="loyalist")
            preds.append((True, fs.decision))

    return preds


def test_precision_on_fraud_class_meets_target() -> None:
    preds = _build_labeled_set()
    precision, recall = precision_recall_on_labeled(preds)
    assert precision >= 0.90, f"precision={precision:.3f} recall={recall:.3f}"
    # хотя бы часть фрод-паттернов должна быть поймана
    assert recall > 0.0


def test_normal_receipts_are_not_flagged() -> None:
    af = AntifraudService()
    flagged = 0
    for i in range(50):
        ev = _receipt(
            receipt_id=f"n-{i}",
            user_id=f"u-{i}",
            timestamp=f"2026-03-02T{i % 24:02d}:00:00Z",
            saved_amount=200.0,
            device_id_hash=f"d-{i}",
            payment_instrument_hash=f"p-{i}",
        )
        if af.score_receipt(ev, archetype="loyalist").decision != "pass":
            flagged += 1
    assert flagged == 0


def test_self_referral_hash_match_scores_high() -> None:
    af = AntifraudService()
    fs = af.score_referral(
        referral_id="ref-self",
        inviter_user_id="inv",
        at="2026-03-02T10:00:00Z",
        inviter_device_hash="dev-x",
        invitee_device_hash="dev-x",
        inviter_payment_hash="pay-x",
        invitee_payment_hash="pay-x",
    )
    assert fs.feature_vector["device_hash_collision"] == 1.0
    assert fs.feature_vector["payment_hash_collision"] == 1.0
    assert fs.decision in ("review", "block")
    # объяснение суммируется в score
    assert abs(sum(fs.explanation.values()) - fs.score) < 1e-6
