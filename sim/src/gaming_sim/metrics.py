"""Primary и guardrail метрики по когорте (data-model §14, FR-033)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CohortAccumulator:
    weeks: int
    n_users: int
    receipts: int = 0
    total_check_sum: float = 0.0
    total_basket_items: int = 0
    referral_new_users: int = 0
    users_active_last_7d: set[str] = field(default_factory=set)
    users_active_last_2w: set[str] = field(default_factory=set)
    users_ever_active: set[str] = field(default_factory=set)
    engagement_sum: float = 0.0
    engagement_obs: int = 0

    def observe_receipt(
        self,
        user_id: str,
        check_sum: float,
        basket_items: int,
        in_last_7d: bool,
        in_last_2w: bool,
    ) -> None:
        self.receipts += 1
        self.total_check_sum += check_sum
        self.total_basket_items += basket_items
        self.users_ever_active.add(user_id)
        if in_last_7d:
            self.users_active_last_7d.add(user_id)
        if in_last_2w:
            self.users_active_last_2w.add(user_id)

    def observe_engagement(self, value: float) -> None:
        self.engagement_sum += value
        self.engagement_obs += 1

    def as_metrics(self) -> dict[str, float]:
        nu = self.n_users or 1
        rc = self.receipts or 1
        avg_engage = self.engagement_sum / (self.engagement_obs or 1)
        return {
            "d7_return_no_push": round(len(self.users_active_last_7d) / nu, 4),
            "purchase_frequency": round(self.receipts / nu / (self.weeks or 1), 4),
            "avg_check": round(self.total_check_sum / rc, 2),
            "retention": round(len(self.users_active_last_2w) / nu, 4),
            "referral_new_users": float(self.referral_new_users),
            "basket_items": round(self.total_basket_items / rc, 3),
            # синтетический прокси: длина сессии слабо растёт с вовлечённостью
            "session_length": round(180.0 + 40.0 * avg_engage, 2),
        }


METRIC_KIND: dict[str, str] = {
    "d7_return_no_push": "primary",
    "purchase_frequency": "primary",
    "avg_check": "primary",
    "retention": "guardrail",
    "referral_new_users": "guardrail",
    "basket_items": "guardrail",
    "session_length": "guardrail",
}
