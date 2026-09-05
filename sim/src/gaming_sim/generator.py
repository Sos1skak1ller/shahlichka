"""Генерация недельного потока чеков и реферальных рёбер для одного профиля
(research.md R6). Детерминизм: единственный источник случайности — переданный
``numpy`` Generator с явным сидом.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import numpy as np

from gaming_sim.archetypes import ARCHETYPES
from gaming_sim.catalog import sku_weights, skus_of
from gaming_sim.population import SyntheticUserProfile
from gaming_sim.taste import IMPULSE_PROB, taste_of

BASE_DATE = datetime(2026, 1, 5, tzinfo=UTC)  # понедельник ISO-недели 2


def week_start(week_index: int) -> datetime:
    return BASE_DATE + timedelta(weeks=week_index)


def iso(ts: datetime) -> str:
    return ts.isoformat().replace("+00:00", "Z")


@dataclass
class WeekOutput:
    events: list[dict]
    referral_created: bool


def _pick_skus(rng: np.random.Generator, categories: list[str], n_items: int) -> list[str]:
    """Позиции чека из справочника купленных категорий.

    Товар берётся из своей категории с перекошенным весом: так у «ходовых» позиций
    появляется устойчивое окружение, и модель сопутствующих товаров получает сигнал.
    """
    out: list[str] = []
    weights = np.asarray(sku_weights(), dtype=float)
    for i in range(max(1, n_items)):
        cat = categories[i % len(categories)]
        pool = skus_of(cat)
        if not pool:
            continue
        out.append(pool[int(rng.choice(len(pool), p=weights[: len(pool)] / weights[: len(pool)].sum()))])
    return out or [f"sku-{categories[0]}-01"]


def _week_categories(
    profile: SyntheticUserProfile,
    week_index: int,
    rng: np.random.Generator,
    n_receipts: int,
) -> list[list[str]]:
    """Разложить категории недели по чекам.

    Сначала те, которым пора по циклу, — они и создают предсказуемое окно возврата
    (H10) и обрыв привычки, когда пропущены (H13). Остаток добивается импульсными
    покупками из хвоста, иначе корзина была бы идеально метрономной.
    """
    taste = taste_of(profile.user_id, profile.segment)
    due = taste.due_categories(week_index, rng)
    core = list(taste.core_categories)

    baskets: list[list[str]] = [[] for _ in range(n_receipts)]
    for i, cat in enumerate(due):
        baskets[i % n_receipts].append(cat)

    for basket in baskets:
        if not basket:
            # Чек есть, а по циклу ничего не пришлось — берём что-то из ядра.
            basket.append(core[int(rng.integers(0, len(core)))])

        # Поход за продуктами — это не одна категория: берут то, что кончилось,
        # и попутно staples. Без этого чек остаётся однокатегорийным, и модель
        # сопутствующих товаров выучивает бесполезное «молочка идёт с молочкой».
        # Добиваем только staples: месячные категории от этого не должны
        # попадать в чек каждую неделю, иначе их цикл исчезает.
        staples = taste.staples or tuple(core)
        for _ in range(int(rng.integers(1, 4))):
            cat = staples[int(rng.integers(0, len(staples)))]
            if cat not in basket:
                basket.append(cat)

        if rng.random() < IMPULSE_PROB:
            impulse = taste.sample_impulse(rng)
            if impulse and impulse not in basket:
                basket.append(impulse)
    return baskets


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

    if k == 0:
        # Ноль чеков — это и есть пропуск недели: именно так в данных появляется
        # обрыв категорийной привычки, который ловит H13.
        ref_prob = arch.referral_prob_per_week * (1.4 if treatment else 1.0)
        return WeekOutput(events=[], referral_created=bool(rng.random() < ref_prob))

    baskets = _week_categories(profile, week_index, rng, k)

    events: list[dict] = []
    for j, cats in enumerate(baskets):
        day = int(rng.integers(0, 7))
        hour = int(rng.integers(7, 22))
        ts = ws + timedelta(days=day, hours=hour, minutes=int(rng.integers(0, 60)))
        saved = float(max(0.0, rng.normal(arch.saved_mean, arch.saved_sd)))
        n_items = int(max(len(cats), rng.poisson(4)))

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
                "sku_list": _pick_skus(rng, cats, n_items),
                "category_list": cats,
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
