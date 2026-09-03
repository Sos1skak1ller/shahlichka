"""Pydantic-модели контракта — ручная реализация JSON Schema из
``specs/001-gaming-layer/contracts/*.schema.json`` (research.md R7).

Синхронность со схемами проверяет ``engine/tests/contract/test_schema_roundtrip.py``.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ChainCode = Literal["TS5", "TSX", "TSC"]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --------------------------------------------------------------------------- #
# purchase-event.schema.json
# --------------------------------------------------------------------------- #
class PurchaseEvent(_Strict):
    receipt_id: str = Field(min_length=1)
    user_id: str = Field(min_length=1)
    store_code: str
    chain_code: ChainCode
    district_code: str
    timestamp: str  # ISO-8601 date-time; движок не парсит его в datetime без нужды
    sku_list: list[str] = Field(default_factory=list)
    category_list: list[str] = Field(default_factory=list)
    total_sum: float = Field(ge=0)
    saved_amount: float
    device_id_hash: str
    payment_instrument_hash: str
    corrects_receipt_id: str | None = None

    @property
    def kind(self) -> Literal["purchase", "correction"]:
        return "correction" if self.corrects_receipt_id else "purchase"


# --------------------------------------------------------------------------- #
# profile-screen.schema.json
# --------------------------------------------------------------------------- #
class AvatarView(_Strict):
    level: int = Field(ge=0)
    visual_stage: int = Field(ge=1)
    state: Literal["progressing", "level_up_pending", "max_level"]
    unlocked_customizations: list[str] = Field(default_factory=list)
    last_transition_at: str | None = None


class SavingsView(_Strict):
    total_saved_amount: float = Field(ge=0)
    current_threshold: float = Field(ge=0)
    next_threshold: float | None
    progress_ratio: float = Field(ge=0, le=1)


class StreakView(_Strict):
    streak_count: int = Field(ge=0)
    last_active_week: str | None = Field(default=None, pattern=r"^\d{4}-W\d{2}$")


class ProfileScreenView(_Strict):
    user_id: str
    display_name: str | None = None
    avatar: AvatarView
    savings: SavingsView
    streak: StreakView


# --------------------------------------------------------------------------- #
# challenge-screen.schema.json
# --------------------------------------------------------------------------- #
MechanicType = Literal["category_repeat", "basket_growth", "streak_keep", "cross_chain"]
GeneratedBy = Literal["ml_ranker", "rule", "fallback"]


class ChallengeParams(_Strict):
    category: str
    n: int = Field(ge=1)
    deadline: str


class ChallengeView(_Strict):
    challenge_id: str
    text: str = Field(min_length=1)
    mechanic_type: MechanicType
    generated_by: GeneratedBy
    params: ChallengeParams
    progress: int = Field(ge=0)
    target: int = Field(ge=1)
    status: Literal["active", "completed", "expired"]
    valid_to: str
    reward_amount: float = Field(ge=0)
    within_budget: bool | None = None


class ChallengeScreenView(_Strict):
    user_id: str
    iso_week: str = Field(pattern=r"^\d{4}-W\d{2}$")
    challenge: ChallengeView | None
    notes: list[
        Literal["cold_start_fallback", "template_pool_exhausted", "anti_fatigue_switch"]
    ] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# referral-screen.schema.json
# --------------------------------------------------------------------------- #
ReferralStatus = Literal[
    "invited", "registered", "purchase_confirmed", "reward_released", "blocked", "expired"
]


class ReferralItem(_Strict):
    referral_id: str
    invitee_alias: str | None = None
    status: ReferralStatus
    invited_at: str
    window_deadline: str | None = None
    reward_amount: float = Field(default=0, ge=0)
    block_reason: Literal["self_referral", "antifraud_block", "window_expired"] | None = None


class ReferralScreenView(_Strict):
    user_id: str
    invite_link: str
    released_reward_total: float = Field(ge=0)
    budget_remaining_this_week: float | None = Field(default=None, ge=0)
    referrals: list[ReferralItem] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# simulation-report.schema.json
# --------------------------------------------------------------------------- #
MetricName = Literal[
    "d7_return_no_push",
    "purchase_frequency",
    "avg_check",
    "retention",
    "referral_new_users",
    "basket_items",
    "session_length",
]


class MetricRow(_Strict):
    name: MetricName
    kind: Literal["primary", "guardrail"]
    treatment: float
    control: float
    delta: float
    period: str | None = None


class EconomyBlock(_Strict):
    total_reward_cost: float = Field(ge=0)
    margin_uplift: float
    roi: float
    invariant_holds: bool
    budget_rejections: int = Field(default=0, ge=0)


class AntifraudBlock(_Strict):
    fraud_class_precision: float = Field(ge=0, le=1)
    fraud_class_recall: float = Field(ge=0, le=1)
    labeled_set_size: int = Field(ge=1)
    review_auto_resolved: int = Field(default=0, ge=0)


class PilotPlan(_Strict):
    hypothesis: str | None = None
    primary_metrics: list[str] = Field(default_factory=list)
    guardrail_metrics: list[str] = Field(default_factory=list)
    roi_formula: str | None = None


class SimulationReport(_Strict):
    run_id: str
    population_size: int = Field(ge=1000, le=10000)
    weeks: int = Field(ge=1)
    seed: int
    engine_version: str
    ranker_version: str | None = None
    chain_mix: dict[str, float]
    metrics: list[MetricRow] = Field(min_length=1)
    economy: EconomyBlock
    antifraud: AntifraudBlock
    pilot_plan: PilotPlan | None = None
