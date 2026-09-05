"""Engine — фасад расчётного ядра. Композирует событийный лог, проекции аватара и
стрика, реестр наград. Без I/O и системных часов (research.md R2, FR-031).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from gaming_engine import avatar, config, streak
from gaming_engine.antifraud import AntifraudService
from gaming_engine.challenge.service import ChallengeRecord, ChallengeService
from gaming_engine.contracts import (
    ActivityItem,
    AvatarView,
    CatalogItem,
    ChallengeHistoryItem,
    ChallengeParams,
    ChallengeScreenView,
    ChallengeView,
    ProfileScreenView,
    PurchaseEvent,
    ReferralItem,
    ReferralScreenView,
    SavingsView,
    StreakView,
)
from gaming_engine.event_log import EventLog, IngestResult
from gaming_engine.ledger import RewardLedger
from gaming_engine.referral import Referral, ReferralService
from gaming_engine.weekcal import iso_week


@dataclass
class UserMeta:
    user_id: str
    segment: str = config.SEGMENT
    archetype: str = "mixed"
    chain_code: str = "TS5"
    display_name: str | None = None


@dataclass
class Engine:
    gaming_layer_enabled: bool = True  # флаг когорты (control cohort → False), см. US4
    log: EventLog = field(default_factory=EventLog)
    ledger: RewardLedger = field(default_factory=RewardLedger)
    challenges: ChallengeService = field(default_factory=ChallengeService)
    antifraud: AntifraudService = field(default_factory=AntifraudService)
    referrals: ReferralService = field(default_factory=ReferralService)
    _users: dict[str, UserMeta] = field(default_factory=dict)
    _avatars: dict[str, avatar.AvatarState] = field(default_factory=dict)
    _hashes: dict[str, tuple[str, str]] = field(default_factory=dict)

    # ------------------------------------------------------------------ #
    # Регистрация синтетических пользователей
    # ------------------------------------------------------------------ #
    def register_user(
        self,
        user_id: str,
        *,
        archetype: str = "mixed",
        segment: str | None = None,
        chain_code: str = "TS5",
        display_name: str | None = None,
    ) -> UserMeta:
        meta = UserMeta(
            user_id=user_id,
            archetype=archetype,
            segment=segment or config.SEGMENT,
            chain_code=chain_code,
            display_name=display_name,
        )
        self._users[user_id] = meta
        return meta

    def meta(self, user_id: str) -> UserMeta:
        m = self._users.get(user_id)
        if m is None:
            m = self.register_user(user_id)
        return m

    # ------------------------------------------------------------------ #
    # Приём событий
    # ------------------------------------------------------------------ #
    def ingest(self, event: PurchaseEvent | dict) -> IngestResult:
        res = self.log.ingest(event)
        if not res.accepted or res.event is None:
            return res
        ev = res.event
        meta = self.meta(ev.user_id)
        if ev.kind == "purchase":
            self._hashes[ev.user_id] = (ev.device_id_hash, ev.payment_instrument_hash)
            # Антифрод скорит каждый чек до любого начисления (FR-015).
            self.antifraud.score_receipt(ev, archetype=meta.archetype)
        if self.gaming_layer_enabled:
            self._recompute_avatar(ev)
            self._advance_challenge(ev)
            self._advance_referral(ev)
        return res

    def _hash_of(self, user_id: str) -> tuple[str, str]:
        return self._hashes.get(user_id, (f"dev-{user_id}", f"pay-{user_id}"))

    def _accrue_ok(self, user_id: str, mechanic: str, cost: float, wk: str, at: str) -> bool:
        return self.ledger.accrue(
            user_id, wk, self.meta(user_id).archetype, mechanic, cost, at
        ).ok

    def _advance_referral(self, ev: PurchaseEvent) -> None:
        if ev.kind != "purchase" or ev.saved_amount <= 0:
            return
        inviter_hashes: dict[str, str] = {}
        ref = self.referrals._by_invitee.get(ev.user_id)  # noqa: SLF001
        if ref is None or ref.status != "registered":
            return
        idev, ipay = self._hash_of(ref.inviter_user_id)
        self.referrals.on_invitee_purchase(
            ev.user_id,
            ev.timestamp,
            score_ref=lambda **kw: self.antifraud.score_referral(**kw).decision,
            accrue=self._accrue_ok,
            inviter_device_hash=idev,
            inviter_payment_hash=ipay,
            invitee_device_hash=ev.device_id_hash,
            invitee_payment_hash=ev.payment_instrument_hash,
            iso_week_of=iso_week,
        )
        _ = inviter_hashes

    # -------------------------- referral API --------------------------- #
    def create_invite(self, inviter_user_id: str, at: str, token: str | None = None) -> Referral:
        self.meta(inviter_user_id)
        return self.referrals.invite(inviter_user_id, at, token=token)

    def register_referral(
        self,
        token: str,
        invitee_user_id: str,
        at: str,
        *,
        invitee_device_hash: str | None = None,
        invitee_payment_hash: str | None = None,
    ) -> Referral:
        self.meta(invitee_user_id)
        ref = self.referrals._by_token[token]  # noqa: SLF001
        idev, ipay = self._hash_of(ref.inviter_user_id)
        vdev = invitee_device_hash or f"dev-{invitee_user_id}"
        vpay = invitee_payment_hash or f"pay-{invitee_user_id}"
        self._hashes.setdefault(invitee_user_id, (vdev, vpay))
        return self.referrals.register(
            token,
            invitee_user_id,
            at,
            inviter_device_hash=idev,
            invitee_device_hash=vdev,
            inviter_payment_hash=ipay,
            invitee_payment_hash=vpay,
        )

    def _advance_challenge(self, ev: PurchaseEvent) -> None:
        meta = self.meta(ev.user_id)

        def accrue(mechanic: str, cost: float, wk: str, archetype: str, at: str) -> None:
            # Награда не начисляется, если завершающий чек не прошёл антифрод.
            if self.antifraud.effective_decision(ev.receipt_id) != "pass":
                return
            self.ledger.accrue(ev.user_id, wk, archetype, mechanic, cost, at)

        self.challenges.on_purchase(ev.user_id, ev, archetype=meta.archetype, accrue=accrue)

    def tick(self, now_ts: str) -> None:
        """Продвинуть модельное время: авто-разрешить полосу «на ревью» (FR-015a),
        закрыть просроченные рефералы, дозакрыть рефералы, вышедшие из ревью."""
        self.antifraud.tick(now_ts)
        self.referrals.expire_stale(now_ts)
        self.referrals.resolve_reviews(
            now_ts,
            effective_decision=self.antifraud.effective_decision,
            accrue=self._accrue_ok,
            iso_week_of=iso_week,
        )

    # ------------------------------------------------------------------ #
    # Ранжирование акций (US6) — без отдельного экрана (FR-007)
    # ------------------------------------------------------------------ #
    def rank_promos(
        self,
        user_id: str,
        as_of_ts: str | None = None,
        *,
        exclude_active: bool = True,
    ):
        """Персональное ранжирование пула акций.

        Если пакет `recsys` установлен и артефакт обучен, категории сначала отбирает
        рекомендатель (ALS), и промо фильтруются по его шортлисту. Без артефакта
        работает прежняя RFM-эвристика — движок не зависит от наличия модели.

        `exclude_active` выбрасывает из шортлиста категории, которые пользователь и
        так покупает регулярно: платить за покупку, которая случилась бы и без промо,
        — это каннибализация, а не рост.
        """
        from gaming_engine import reco_adapter
        from gaming_engine.challenge import features as _features
        from gaming_engine.promo import rank_promos as _rank

        meta = self.meta(user_id)
        at = as_of_ts or self._latest_ts(user_id) or "2026-01-05T00:00:00Z"
        events = self.log.user_events(user_id)
        feats = _features.build(
            events,
            archetype=meta.archetype,
            avatar_level=self.avatar_state(user_id).level,
            as_of_week=iso_week(at),
        )
        exclude = set(feats.by_category) if exclude_active else set()
        shortlist = reco_adapter.category_shortlist(
            events, exclude=exclude, as_of_week=iso_week(at)
        )
        return _rank(feats, segment=meta.segment, shortlist=shortlist)

    def get_referral_view(self, user_id: str) -> ReferralScreenView:
        meta = self.meta(user_id)
        items: list[ReferralItem] = []
        for r in self.referrals.for_inviter(user_id):
            items.append(
                ReferralItem(
                    referral_id=r.referral_id,
                    invitee_alias=(r.invitee_user_id[-6:] if r.invitee_user_id else None),
                    status=r.status,
                    invited_at=r.status_timestamps.get("invited", "2026-01-05T00:00:00Z"),
                    window_deadline=r.window_deadline,
                    reward_amount=r.reward_amount,
                    block_reason=r.block_reason,
                )
            )
        latest_week = iso_week(self._latest_ts(user_id) or "2026-01-05T00:00:00Z")
        return ReferralScreenView(
            user_id=user_id,
            invite_link=f"https://x5.local/i/{user_id}",
            released_reward_total=round(self.referrals.released_total(user_id), 2),
            budget_remaining_this_week=round(
                self.ledger.remaining(user_id, latest_week, meta.archetype), 2
            ),
            referrals=items,
        )

    def fraud_scores(self):
        return self.antifraud.scores()

    # ------------------------------------------------------------------ #
    # Сводка прогона (вход для отчёта симуляции, US4 / FR-033)
    # ------------------------------------------------------------------ #
    def run_summary(self) -> dict:
        af = self.antifraud.counters()
        total_reward = 0.0
        budget_rejections = 0
        invariant_ok = True
        for wl in self.ledger._weeks.values():  # noqa: SLF001 — внутренняя агрегация
            total_reward += wl.accrued_reward
            for r in wl.rejections:
                budget_rejections += 1
                if r.reason == "economy_invariant_violation":
                    invariant_ok = False
        return {
            "total_reward_cost": round(total_reward, 2),
            "budget_rejections": budget_rejections,
            "economy_invariant_holds": invariant_ok,
            "antifraud_blocked": af["blocked"],
            "antifraud_review": af["review"],
            "antifraud_review_auto_resolved": af["review_auto_resolved"],
        }

    def _recompute_avatar(self, ev: PurchaseEvent) -> None:
        total = self.total_saved(ev.user_id)
        prev = self._avatars.get(ev.user_id, avatar.AvatarState())
        self._avatars[ev.user_id] = avatar.recompute(
            prev,
            total,
            trigger_receipt_id=ev.receipt_id,
            at=ev.timestamp,
            is_correction=ev.kind == "correction",
        )

    # ------------------------------------------------------------------ #
    # Проекции
    # ------------------------------------------------------------------ #
    def total_saved(self, user_id: str) -> float:
        return max(0.0, self.log.total_saved(user_id))

    def avatar_state(self, user_id: str) -> avatar.AvatarState:
        return self._avatars.get(user_id, avatar.AvatarState())

    def streak_state(
        self, user_id: str, as_of_week: str | None = None
    ) -> streak.StreakState:
        return streak.compute(self.log.user_events(user_id), as_of_week)

    def get_profile_view(
        self, user_id: str, as_of_ts: str | None = None
    ) -> ProfileScreenView:
        av = self.avatar_state(user_id)
        total = self.total_saved(user_id)
        cur_thr = avatar.threshold_for_level(av.level)
        nxt = avatar.next_threshold(av.level)
        if nxt is None:
            ratio = 1.0
        else:
            span = nxt - cur_thr
            ratio = min(1.0, max(0.0, (total - cur_thr) / span)) if span > 0 else 0.0
        stk = self.streak_state(
            user_id, iso_week(as_of_ts) if as_of_ts is not None else None
        )
        meta = self.meta(user_id)
        return ProfileScreenView(
            user_id=user_id,
            display_name=meta.display_name,
            avatar=AvatarView(
                level=av.level,
                visual_stage=av.visual_stage,
                state=av.state,
                unlocked_customizations=av.unlocked_customizations,
                last_transition_at=av.last_transition_at,
            ),
            savings=SavingsView(
                total_saved_amount=round(total, 2),
                current_threshold=cur_thr,
                next_threshold=nxt,
                progress_ratio=round(ratio, 4),
            ),
            streak=StreakView(
                streak_count=stk.streak_count,
                last_active_week=stk.last_active_week,
            ),
            history=self._activity_feed(user_id),
        )

    def _activity_feed(self, user_id: str, limit: int = 15) -> list[ActivityItem]:
        items: list[ActivityItem] = []

        for ev in self.log.user_events(user_id):
            if ev.kind == "purchase" and ev.saved_amount > 0:
                items.append(
                    ActivityItem(
                        ts=ev.timestamp,
                        kind="purchase",
                        title="Покупка",
                        detail=", ".join(ev.category_list) or None,
                        amount=round(ev.saved_amount, 2),
                    )
                )

        for t in self.avatar_state(user_id).transition_history:
            if t.to_level > t.from_level:
                items.append(
                    ActivityItem(
                        ts=t.at,
                        kind="level_up",
                        title=f"Новый уровень: {t.to_level}",
                        detail="аватар подрос",
                    )
                )

        for rec in self.challenges.history(user_id):
            if rec.status == "completed":
                items.append(
                    ActivityItem(
                        ts=rec.completed_at or rec.valid_from,
                        kind="challenge_done",
                        title="Челлендж выполнен",
                        detail=rec.text,
                        amount=round(rec.reward_amount, 2),
                    )
                )

        for r in self.referrals.for_inviter(user_id):
            if r.status == "reward_released":
                items.append(
                    ActivityItem(
                        ts=r.status_timestamps.get("reward_released", r.status_timestamps.get("invited", "")),
                        kind="referral_reward",
                        title="Награда за друга",
                        detail=(r.invitee_user_id[-6:] if r.invitee_user_id else None),
                        amount=round(r.reward_amount, 2),
                    )
                )

        items = [i for i in items if i.ts]
        items.sort(key=lambda i: i.ts, reverse=True)
        return items[:limit]

    # ------------------------------------------------------------------ #
    # Челлендж (US2)
    # ------------------------------------------------------------------ #
    def _latest_ts(self, user_id: str) -> str | None:
        evs = self.log.user_events(user_id)
        return evs[-1].timestamp if evs else None

    def generate_challenge(self, user_id: str, as_of_ts: str | None = None) -> ChallengeRecord:
        meta = self.meta(user_id)
        at = as_of_ts or self._latest_ts(user_id) or "2026-01-05T00:00:00Z"
        wk = iso_week(at)

        def precheck(mechanic: str, cost: float, week: str, archetype: str) -> tuple[bool, str]:
            pc = self.ledger.pre_check(user_id, week, archetype, mechanic, cost, week)
            return pc.ok, pc.reason

        return self.challenges.generate(
            user_id,
            user_events=self.log.user_events(user_id),
            segment=meta.segment,
            archetype=meta.archetype,
            avatar_level=self.avatar_state(user_id).level,
            as_of_ts=at,
            remaining_budget=self.ledger.remaining(user_id, wk, meta.archetype),
            precheck=precheck,
        )

    def _challenge_catalog(self, user_id: str, as_of_ts: str) -> list[CatalogItem]:
        from gaming_engine.challenge import features as _features

        meta = self.meta(user_id)
        wk = iso_week(as_of_ts)
        feats = _features.build(
            self.log.user_events(user_id),
            archetype=meta.archetype,
            avatar_level=self.avatar_state(user_id).level,
            as_of_week=wk,
        )
        rows = self.challenges.catalog(
            feats=feats,
            segment=meta.segment,
            avatar_level=self.avatar_state(user_id).level,
            remaining_budget=self.ledger.remaining(user_id, wk, meta.archetype),
        )
        return [CatalogItem(**r) for r in rows]

    def _challenge_history(self, user_id: str) -> list[ChallengeHistoryItem]:
        out: list[ChallengeHistoryItem] = []
        for rec in self.challenges.history(user_id):
            out.append(
                ChallengeHistoryItem(
                    challenge_id=rec.challenge_id,
                    text=rec.text,
                    status=rec.status if rec.status in ("completed", "expired", "rejected_economy") else "expired",
                    reward_amount=rec.reward_amount if rec.status == "completed" else 0.0,
                    iso_week=rec.iso_week,
                )
            )
        return out

    def get_challenge_view(
        self, user_id: str, as_of_ts: str | None = None
    ) -> ChallengeScreenView:
        at = as_of_ts or self._latest_ts(user_id) or "2026-01-05T00:00:00Z"
        wk = iso_week(at)
        rec = self.challenges.latest_visible(user_id)
        notes = self.challenges.week_notes(user_id)
        catalog = self._challenge_catalog(user_id, at)
        history = self._challenge_history(user_id)
        if rec is None:
            return ChallengeScreenView(
                user_id=user_id, iso_week=wk, challenge=None, notes=notes,
                catalog=catalog, history=history,
            )
        cv = ChallengeView(
            challenge_id=rec.challenge_id,
            text=rec.text,
            mechanic_type=rec.mechanic_type,
            generated_by=rec.generated_by,
            params=ChallengeParams(
                category=rec.category, n=rec.target, deadline=rec.deadline_iso
            ),
            progress=rec.progress,
            target=rec.target,
            status=rec.status if rec.status in ("active", "completed", "expired") else "active",
            valid_to=rec.deadline_iso,
            reward_amount=rec.reward_amount,
            within_budget=rec.within_budget,
        )
        return ChallengeScreenView(
            user_id=user_id, iso_week=rec.iso_week, challenge=cv, notes=notes,
            catalog=catalog, history=history,
        )
