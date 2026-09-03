"""Жизненный цикл челленджа: не более одного активного на пользователя, недельный
цикл, прогресс по подтверждающим чекам, завершение → начисление через RewardLedger
(data-model §6, FR-008/FR-011/FR-012/FR-013/FR-014, research.md R5).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime

from gaming_engine import config
from gaming_engine.challenge import assemble as _assemble
from gaming_engine.challenge import features as _features
from gaming_engine.challenge.candidates import eligible_candidates
from gaming_engine.challenge.ranker import RANKER_VERSION, choose
from gaming_engine.challenge.templates import load_registry
from gaming_engine.contracts import PurchaseEvent
from gaming_engine.timing import anti_fatigue_triggered
from gaming_engine.weekcal import iso_week, weeks_between

# precheck(mechanic, reward_cost, iso_week, archetype) -> (ok: bool, reason: str)
PreCheckFn = Callable[[str, float, str, str], tuple[bool, str]]
# accrue(mechanic, reward_cost, iso_week, archetype, at) -> None
AccrueFn = Callable[[str, float, str, str, str], None]


@dataclass
class ChallengeRecord:
    challenge_id: str
    user_id: str
    iso_week: str
    template_id: str
    mechanic_type: str
    generated_by: str
    category: str
    target: int
    deadline_iso: str
    valid_from: str
    text: str
    reward_amount: float
    status: str = "active"  # active | completed | expired | rejected_economy
    progress: int = 0
    within_budget: bool = True
    notes: list[str] = field(default_factory=list)


def _parse(ts: str) -> datetime:
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


@dataclass
class ChallengeService:
    _by_user: dict[str, list[ChallengeRecord]] = field(default_factory=dict)
    _counter: int = 0

    # ----------------------------- helpers -------------------------------- #
    def _records(self, user_id: str) -> list[ChallengeRecord]:
        return self._by_user.setdefault(user_id, [])

    def active(self, user_id: str) -> ChallengeRecord | None:
        for rec in self._records(user_id):
            if rec.status == "active":
                return rec
        return None

    def _consecutive_ignored(self, user_id: str) -> int:
        count = 0
        for rec in reversed(self._records(user_id)):
            if rec.status in ("completed", "expired") and rec.progress == 0:
                count += 1
            elif rec.status == "completed" and rec.progress > 0:
                break
            elif rec.status == "active":
                continue
            else:
                break
        return count

    def _recent_template_ids(self, user_id: str, as_of_week: str) -> set[str]:
        out: set[str] = set()
        for rec in self._records(user_id):
            if 0 <= weeks_between(rec.iso_week, as_of_week) < config.CHALLENGE_TEMPLATE_COOLDOWN_WEEKS:
                out.add(rec.template_id)
        return out

    # ----------------------------- generate ------------------------------ #
    def generate(
        self,
        user_id: str,
        *,
        user_events: list[PurchaseEvent],
        segment: str,
        archetype: str,
        avatar_level: int,
        as_of_ts: str,
        remaining_budget: float,
        precheck: PreCheckFn,
    ) -> ChallengeRecord:
        wk = iso_week(as_of_ts)

        existing = self.active(user_id)
        if existing is not None:
            # FR-008: один активный челлендж; новый на новой неделе не выдаётся,
            # пока текущий не завершён/не истёк.
            return existing

        feats = _features.build(
            user_events, archetype=archetype, avatar_level=avatar_level, as_of_week=wk
        )

        notes: list[str] = []
        exclude_mechanic: str | None = None
        if anti_fatigue_triggered(self._consecutive_ignored(user_id)):
            last = self._records(user_id)[-1] if self._records(user_id) else None
            exclude_mechanic = last.mechanic_type if last else None
            notes.append("anti_fatigue_switch")

        pool = eligible_candidates(
            feats,
            segment=segment,
            remaining_budget=remaining_budget,
            recent_template_ids=self._recent_template_ids(user_id, wk),
            exclude_mechanic=exclude_mechanic,
        )
        if pool.pool_exhausted:
            notes.append("template_pool_exhausted")

        pick = choose(feats, pool.templates, budget=remaining_budget)
        if pick.generated_by == "fallback" and not feats.has_history:
            notes.append("cold_start_fallback")

        asm = _assemble.assemble(
            pick.template, category=pick.category, n=pick.n, from_ts=as_of_ts
        )

        mechanic = "challenge"
        ok, _reason = precheck(mechanic, asm.reward_amount, wk, archetype)

        self._counter += 1
        rec = ChallengeRecord(
            challenge_id=f"ch-{user_id}-{self._counter:04d}",
            user_id=user_id,
            iso_week=wk,
            template_id=pick.template.template_id,
            mechanic_type=pick.template.mechanic_type,
            generated_by=pick.generated_by,
            category=asm.category,
            target=asm.n,
            deadline_iso=asm.deadline_iso,
            valid_from=as_of_ts,
            text=asm.text,
            reward_amount=asm.reward_amount,
            within_budget=ok,
            notes=notes,
        )
        if not ok:
            # US3 сценарий 5 / FR-019: не показываем пользователю
            rec.status = "rejected_economy"
        self._records(user_id).append(rec)
        return rec

    # ------------------------- progress / lifecycle ---------------------- #
    def on_purchase(
        self,
        user_id: str,
        event: PurchaseEvent,
        *,
        archetype: str,
        accrue: AccrueFn,
    ) -> None:
        rec = self.active(user_id)
        if rec is None or event.kind != "purchase" or event.saved_amount <= 0:
            return
        if _parse(event.timestamp) > _parse(rec.deadline_iso):
            rec.status = "expired"
            return
        if rec.category in event.category_list:
            rec.progress += 1
            if rec.progress >= rec.target:
                rec.status = "completed"
                accrue("challenge", rec.reward_amount, rec.iso_week, archetype, event.timestamp)

    def expire_stale(self, user_id: str, as_of_ts: str) -> None:
        rec = self.active(user_id)
        if rec is not None and _parse(as_of_ts) > _parse(rec.deadline_iso):
            rec.status = "expired"

    # ------------------------------ view -------------------------------- #
    def latest_visible(self, user_id: str) -> ChallengeRecord | None:
        for rec in reversed(self._records(user_id)):
            if rec.status in ("active", "completed", "expired"):
                return rec
        return None

    def week_notes(self, user_id: str) -> list[str]:
        rec = self.latest_visible(user_id) or (
            self._records(user_id)[-1] if self._records(user_id) else None
        )
        return list(rec.notes) if rec else []


def registry_version() -> str:
    load_registry()  # прогрев кэша
    return RANKER_VERSION
