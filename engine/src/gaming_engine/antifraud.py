"""Антифрод: взвешенный scorecard с фиксированным явным порогом и объяснением по
каждой фиче (data-model §10, FR-015/FR-015a/FR-016/FR-017/FR-020, research.md R4).

Метрика приёмки — precision на фрод-классе (не accuracy). Полоса «на ревью»
удерживает награду и авто-разрешается через фиксированную задержку модельного
времени по детерминированному правилу.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from gaming_engine import config
from gaming_engine.contracts import PurchaseEvent

_W = config.FRAUD_FEATURE_WEIGHTS
_WSUM = sum(_W.values())

# Иллюстративная «нормальная» недельная экономия по архетипу для archetype_deviation.
_ARCHETYPE_SAVED_MEAN = {
    "bargain_hunter": 250.0,
    "loyalist": 220.0,
    "sleeper": 120.0,
    "cross_shopper": 300.0,
    "mixed": 200.0,
}


def _parse(ts: str) -> datetime:
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


@dataclass
class FraudScore:
    entity_type: str  # "receipt" | "referral"
    entity_id: str
    user_id: str
    at: str
    score: float
    threshold_used: dict[str, float]
    decision: str  # "pass" | "review" | "block"
    feature_vector: dict[str, float]
    explanation: dict[str, float]
    review_outcome: str | None = None
    review_resolved_at: str | None = None


def _decide(score: float) -> str:
    # На границе — строже: >= block → block (research.md R4).
    if score >= config.FRAUD_THRESHOLDS["block"] - 1e-9:
        return "block"
    if score >= config.FRAUD_THRESHOLDS["review"] - 1e-9:
        return "review"
    return "pass"


@dataclass
class AntifraudService:
    _scores: list[FraudScore] = field(default_factory=list)
    _by_entity: dict[str, FraudScore] = field(default_factory=dict)
    _device_users: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    _payment_users: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    _user_receipt_ts: dict[str, list[datetime]] = field(
        default_factory=lambda: defaultdict(list)
    )
    _user_invite_ts: dict[str, list[datetime]] = field(
        default_factory=lambda: defaultdict(list)
    )
    _pending_review: list[FraudScore] = field(default_factory=list)

    # ---------------------------------------------------------------- #
    def _score(
        self,
        *,
        entity_type: str,
        entity_id: str,
        user_id: str,
        at: str,
        features: dict[str, float],
    ) -> FraudScore:
        vec = {k: float(features.get(k, 0.0)) for k in _W}
        contrib = {k: _W[k] * vec[k] / _WSUM for k in _W}
        score = sum(contrib.values())
        fs = FraudScore(
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            at=at,
            score=round(score, 6),
            threshold_used=dict(config.FRAUD_THRESHOLDS),
            decision=_decide(score),
            feature_vector=vec,
            explanation={k: round(v, 6) for k, v in contrib.items()},
        )
        self._scores.append(fs)
        self._by_entity[entity_id] = fs
        if fs.decision == "review":
            self._pending_review.append(fs)
        return fs

    # ---------------------------- receipts --------------------------- #
    def score_receipt(self, ev: PurchaseEvent, *, archetype: str) -> FraudScore:
        now = _parse(ev.timestamp)
        self._device_users[ev.device_id_hash].add(ev.user_id)
        self._payment_users[ev.payment_instrument_hash].add(ev.user_id)

        recent = [t for t in self._user_receipt_ts[ev.user_id] if now - t <= timedelta(hours=1)]
        velocity = min(len(recent) / 5.0, 1.0)  # 5+ чеков/час → максимум
        self._user_receipt_ts[ev.user_id].append(now)

        mean = _ARCHETYPE_SAVED_MEAN.get(archetype, 200.0)
        deviation = min(abs(ev.saved_amount - mean) / mean, 1.0) if mean else 0.0

        dev_collision = 1.0 if len(self._device_users[ev.device_id_hash]) >= 2 else 0.0
        pay_collision = 1.0 if len(self._payment_users[ev.payment_instrument_hash]) >= 2 else 0.0

        return self._score(
            entity_type="receipt",
            entity_id=ev.receipt_id,
            user_id=ev.user_id,
            at=ev.timestamp,
            features={
                "receipt_velocity": velocity,
                "archetype_deviation": deviation,
                "device_hash_collision": dev_collision,
                "payment_hash_collision": pay_collision,
                "invite_burst": 0.0,
            },
        )

    # ---------------------------- referrals -------------------------- #
    def score_referral(
        self,
        *,
        referral_id: str,
        inviter_user_id: str,
        at: str,
        inviter_device_hash: str,
        invitee_device_hash: str,
        inviter_payment_hash: str,
        invitee_payment_hash: str,
    ) -> FraudScore:
        now = _parse(at)
        recent = [t for t in self._user_invite_ts[inviter_user_id] if now - t <= timedelta(days=1)]
        burst = min(len(recent) / 5.0, 1.0)
        self._user_invite_ts[inviter_user_id].append(now)

        dev_collision = 1.0 if inviter_device_hash == invitee_device_hash else 0.0
        pay_collision = 1.0 if inviter_payment_hash == invitee_payment_hash else 0.0

        return self._score(
            entity_type="referral",
            entity_id=referral_id,
            user_id=inviter_user_id,
            at=at,
            features={
                "receipt_velocity": 0.0,
                "archetype_deviation": 0.0,
                "device_hash_collision": dev_collision,
                "payment_hash_collision": pay_collision,
                "invite_burst": burst,
            },
        )

    # ------------------------- review auto-resolve ------------------- #
    def tick(self, now_ts: str) -> list[FraudScore]:
        """Авто-разрешение полосы «на ревью» по истечении REVIEW_HOLD.

        Детерминированное правило: «пропустить», если за время удержания у того же
        пользователя не накопилось нового сигнала риска (score >= review); иначе
        «заблокировать» (edge case из spec).
        """
        now = _parse(now_ts)
        resolved: list[FraudScore] = []
        still: list[FraudScore] = []
        for fs in self._pending_review:
            if now - _parse(fs.at) < timedelta(hours=config.REVIEW_HOLD_HOURS):
                still.append(fs)
                continue
            new_signal = any(
                other.user_id == fs.user_id
                and other.entity_id != fs.entity_id
                and _parse(fs.at) < _parse(other.at) <= now
                and other.score >= config.FRAUD_THRESHOLDS["review"] - 1e-9
                for other in self._scores
            )
            fs.review_outcome = "block" if new_signal else "pass"
            fs.review_resolved_at = now_ts
            resolved.append(fs)
        self._pending_review = still
        return resolved

    # ------------------------------ queries ------------------------- #
    def effective_decision(self, entity_id: str) -> str:
        fs = self._by_entity.get(entity_id)
        if fs is None:
            return "pass"
        if fs.decision == "review":
            return fs.review_outcome or "review"
        return fs.decision

    def scores(self) -> list[FraudScore]:
        return list(self._scores)

    def counters(self) -> dict[str, int]:
        return {
            "blocked": sum(1 for s in self._scores if s.decision == "block"),
            "review": sum(1 for s in self._scores if s.decision == "review"),
            "review_auto_resolved": sum(
                1 for s in self._scores if s.review_resolved_at is not None
            ),
        }


def precision_recall_on_labeled(
    predictions: list[tuple[bool, str]],
) -> tuple[float, float]:
    """predictions: список (is_fraud_truth, decision). Фрод-класс = decision != 'pass'.

    Возвращает (precision, recall) на фрод-классе.
    """
    tp = sum(1 for truth, d in predictions if truth and d != "pass")
    fp = sum(1 for truth, d in predictions if not truth and d != "pass")
    fn = sum(1 for truth, d in predictions if truth and d == "pass")
    precision = tp / (tp + fp) if (tp + fp) else 1.0
    recall = tp / (tp + fn) if (tp + fn) else 1.0
    return precision, recall
