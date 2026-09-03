"""Генерация недельного потока чеков и реферальных рёбер для одного профиля
(research.md R6). Детерминизм: единственный источник случайности — переданный
``numpy`` Generator с явным сидом.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import numpy as np

from gaming_sim.archetypes import ARCHETYPES
from gaming_sim.population import SyntheticUserProfile

BASE_DATE = datetime(2026, 1, 5, tzinfo=UTC)  # понедельник ISO-недели 2


def week_start(week_index: int) -> datetime:
    return BASE_DATE + timedelta(weeks=week_index)


def iso(ts: datetime) -> str:
    return ts.isoformat().replace("+00:00", "Z")


@dataclass
class WeekOutput:
    events: list[dict]
    referral_created: bool


def _sample_category(rng: np.random.Generator, cats: tuple[tuple[str, float], ...]) -> str:
    names = [c for c, _ in cats]
    w = np.array([wt for _, wt in cats], dtype=float)
    w /= w.sum()
    return names[int(rng.choice(len(names), p=w))]


def generate_week(
    profile: SyntheticUserProfile,
    week_index: int,
    rng: np.random.Generator,
    *,
    engagement: float,
    treatment: bool,
    is_fraud: bool,
) -> WeekOutput:
    arch = ARCHETYPES[profile.archetype]
    ws = week_start(week_index)

    lam = arch.weekly_lambda
    if treatment:
        lam *= 1.0 + arch.engagement_sensitivity * engagement
    k = int(rng.poisson(lam))

    events: list[dict] = []
    for j in range(k):
        day = int(rng.integers(0, 7))
        hour = int(rng.integers(7, 22))
        ts = ws + timedelta(days=day, hours=hour, minutes=int(rng.integers(0, 60)))
        saved = float(max(0.0, rng.normal(arch.saved_mean, arch.saved_sd)))
        n_items = int(max(1, rng.poisson(4)))
        cat = _sample_category(rng, arch.categories)

        dev = "dev-fraudring" if is_fraud else f"dev-{profile.user_id}"
        pay = "pay-fraudring" if is_fraud else f"pay-{profile.user_id}"

        events.append(
            {
                "receipt_id": f"{profile.user_id}-w{week_index}-{j}",
                "user_id": profile.user_id,
                "store_code": f"s-{profile.chain_code}-{int(rng.integers(1, 40)):03d}",
                "chain_code": profile.chain_code,
                "district_code": f"d-{int(rng.integers(1, 80)):03d}",
                "timestamp": iso(ts),
                "sku_list": [f"sku-{int(rng.integers(1, 9999))}" for _ in range(n_items)],
                "category_list": [cat],
                "total_sum": round(saved * 9.0 + rng.normal(200, 60), 2),
                "saved_amount": round(saved * (6.0 if is_fraud else 1.0), 2),
                "device_id_hash": dev,
                "payment_instrument_hash": pay,
                "corrects_receipt_id": None,
            }
        )

    ref_prob = arch.referral_prob_per_week * (1.4 if treatment else 1.0)
    referral_created = bool(rng.random() < ref_prob)
    return WeekOutput(events=events, referral_created=referral_created)
