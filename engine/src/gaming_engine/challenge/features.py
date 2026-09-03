"""Построение признаков пользователя для подбора челленджа (research.md R3, шаг 1).

RFM по категориям + архетип + уровень аватара. Всё выводится из событийного лога.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from gaming_engine.contracts import PurchaseEvent
from gaming_engine.weekcal import iso_week, weeks_between


@dataclass
class CategoryRFM:
    frequency: int = 0
    monetary: float = 0.0
    last_week: str | None = None
    recency_weeks: int = 999  # недель с последней покупки в категории (как есть → большое)


@dataclass
class UserFeatures:
    archetype: str
    avatar_level: int
    as_of_week: str
    total_events: int
    by_category: dict[str, CategoryRFM] = field(default_factory=dict)

    @property
    def has_history(self) -> bool:
        return bool(self.by_category)

    def top_categories(self, k: int = 3) -> list[str]:
        return [
            c
            for c, _ in sorted(
                self.by_category.items(),
                key=lambda kv: (kv[1].frequency, kv[1].monetary, kv[0]),
                reverse=True,
            )
        ][:k]


def build(
    user_events: list[PurchaseEvent],
    *,
    archetype: str,
    avatar_level: int,
    as_of_week: str,
) -> UserFeatures:
    by_cat: dict[str, CategoryRFM] = defaultdict(CategoryRFM)
    n = 0
    for ev in user_events:
        if ev.kind != "purchase" or ev.saved_amount <= 0:
            continue
        n += 1
        wk = iso_week(ev.timestamp)
        for cat in ev.category_list:
            r = by_cat[cat]
            r.frequency += 1
            r.monetary += ev.saved_amount
            if r.last_week is None or wk > r.last_week:
                r.last_week = wk

    for r in by_cat.values():
        if r.last_week is not None:
            r.recency_weeks = max(0, weeks_between(r.last_week, as_of_week))

    return UserFeatures(
        archetype=archetype,
        avatar_level=avatar_level,
        as_of_week=as_of_week,
        total_events=n,
        by_category=dict(by_cat),
    )
