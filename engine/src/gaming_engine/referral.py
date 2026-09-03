"""Реферальная программа с отложенной наградой (data-model §8, FR-017/FR-021..FR-024).

Награда обеим сторонам выдаётся ТОЛЬКО после подтверждённой чеком первой покупки
приглашённого и прохождения антифрода; списывается из недельного потолка инвайтера.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from gaming_engine import config

# score_referral(referral_id, inviter_user_id, at, hashes...) -> decision str
ScoreRefFn = Callable[..., str]
# accrue(user_id, mechanic, reward_cost, iso_week, at) -> bool  (ok?)
AccrueRefFn = Callable[[str, str, float, str, str], bool]


def _parse(ts: str) -> datetime:
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


@dataclass
class Referral:
    referral_id: str
    inviter_user_id: str
    invitee_token: str
    status: str = "invited"  # invited|registered|purchase_confirmed|reward_released|blocked|expired
    invitee_user_id: str | None = None
    status_timestamps: dict[str, str] = field(default_factory=dict)
    reward_amount: float = 0.0
    block_reason: str | None = None
    window_deadline: str | None = None
    fraud_decision: str | None = None

    def _set(self, status: str, at: str) -> None:
        self.status = status
        self.status_timestamps[status] = at


@dataclass
class ReferralService:
    _by_id: dict[str, Referral] = field(default_factory=dict)
    _by_token: dict[str, Referral] = field(default_factory=dict)
    _by_invitee: dict[str, Referral] = field(default_factory=dict)
    _counter: int = 0

    # ------------------------------------------------------------------ #
    def invite(self, inviter_user_id: str, at: str, *, token: str | None = None) -> Referral:
        self._counter += 1
        tok = token or f"inv-{inviter_user_id}-{self._counter:04d}"
        r = Referral(
            referral_id=f"ref-{self._counter:04d}",
            inviter_user_id=inviter_user_id,
            invitee_token=tok,
        )
        r._set("invited", at)
        self._by_id[r.referral_id] = r
        self._by_token[tok] = r
        return r

    def register(
        self,
        token: str,
        invitee_user_id: str,
        at: str,
        *,
        inviter_device_hash: str,
        invitee_device_hash: str,
        inviter_payment_hash: str,
        invitee_payment_hash: str,
    ) -> Referral:
        r = self._by_token[token]
        if r.status != "invited":
            return r
        # FR-017: self-referral — совпадение хэша устройства/платёжного инструмента
        if (
            invitee_device_hash == inviter_device_hash
            or invitee_payment_hash == inviter_payment_hash
        ):
            r._set("blocked", at)
            r.block_reason = "self_referral"
            return r
        r.invitee_user_id = invitee_user_id
        r._set("registered", at)
        r.window_deadline = (
            _parse(at) + timedelta(days=config.REFERRAL_WINDOW_DAYS)
        ).isoformat().replace("+00:00", "Z")
        self._by_invitee[invitee_user_id] = r
        return r

    # ------------------------------------------------------------------ #
    def on_invitee_purchase(
        self,
        invitee_user_id: str,
        at: str,
        *,
        score_ref: ScoreRefFn,
        accrue: AccrueRefFn,
        inviter_device_hash: str,
        inviter_payment_hash: str,
        invitee_device_hash: str,
        invitee_payment_hash: str,
        iso_week_of: Callable[[str], str],
    ) -> None:
        r = self._by_invitee.get(invitee_user_id)
        if r is None or r.status != "registered":
            return
        if r.window_deadline and _parse(at) > _parse(r.window_deadline):
            r._set("expired", at)  # FR-024
            return
        r._set("purchase_confirmed", at)
        decision = score_ref(
            referral_id=r.referral_id,
            inviter_user_id=r.inviter_user_id,
            at=at,
            inviter_device_hash=inviter_device_hash,
            invitee_device_hash=invitee_device_hash,
            inviter_payment_hash=inviter_payment_hash,
            invitee_payment_hash=invitee_payment_hash,
        )
        r.fraud_decision = decision
        if decision == "pass":
            self._release(r, at, accrue=accrue, iso_week_of=iso_week_of)
        elif decision == "block":
            r._set("blocked", at)
            r.block_reason = "antifraud_block"
        # decision == "review" → остаётся purchase_confirmed, разрешится в resolve_reviews

    def _release(
        self,
        r: Referral,
        at: str,
        *,
        accrue: AccrueRefFn,
        iso_week_of: Callable[[str], str],
    ) -> None:
        reward = config.REFERRAL_REWARD_PER_SIDE
        wk = iso_week_of(at)
        ok = accrue(r.inviter_user_id, "referral", reward, wk, at)  # FR-023
        if not ok:
            return  # бюджетный потолок инвайтера исчерпан — награда не выдаётся
        r.reward_amount = reward
        r._set("reward_released", at)

    def resolve_reviews(
        self,
        at: str,
        *,
        effective_decision: Callable[[str], str],
        accrue: AccrueRefFn,
        iso_week_of: Callable[[str], str],
    ) -> None:
        for r in self._by_id.values():
            if r.status != "purchase_confirmed":
                continue
            dec = effective_decision(r.referral_id)
            if dec == "pass":
                self._release(r, at, accrue=accrue, iso_week_of=iso_week_of)
            elif dec == "block":
                r._set("blocked", at)
                r.block_reason = "antifraud_block"

    def expire_stale(self, at: str) -> None:
        for r in self._by_id.values():
            if r.status == "registered" and r.window_deadline and _parse(at) > _parse(r.window_deadline):
                r._set("expired", at)

    # ------------------------------------------------------------------ #
    def for_inviter(self, inviter_user_id: str) -> list[Referral]:
        return [r for r in self._by_id.values() if r.inviter_user_id == inviter_user_id]

    def released_total(self, inviter_user_id: str) -> float:
        return sum(
            r.reward_amount for r in self.for_inviter(inviter_user_id) if r.status == "reward_released"
        )
