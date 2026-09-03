"""4–5 архетипов покупателя с вероятностными профилями чеков (research.md R6, ТЗ 10.5).

Осознанный компромисс ради скорости: не полноценная agent-based модель, а
когортное сэмплирование отклика из распределения, привязанного к архетипу.
"""

from __future__ import annotations

from dataclasses import dataclass

BABY_CATEGORIES = ("baby_food", "diapers", "hygiene", "dairy")
GENERAL_CATEGORIES = ("groceries", "household", "snacks", "dairy")


@dataclass(frozen=True)
class Archetype:
    name: str
    weekly_lambda: float  # среднее число чеков в неделю
    saved_mean: float  # средняя экономия на чек, ₽
    saved_sd: float
    categories: tuple[tuple[str, float], ...]  # (категория, вес)
    referral_prob_per_week: float
    engagement_sensitivity: float  # насколько отклик растёт от вовлечённости (treatment)


def _cats(weights: dict[str, float]) -> tuple[tuple[str, float], ...]:
    return tuple(weights.items())


ARCHETYPES: dict[str, Archetype] = {
    "bargain_hunter": Archetype(
        "bargain_hunter", 2.6, 190.0, 70.0,
        _cats({"baby_food": 0.35, "diapers": 0.25, "snacks": 0.2, "household": 0.2}),
        0.010, 0.28,
    ),
    "loyalist": Archetype(
        "loyalist", 2.1, 150.0, 55.0,
        _cats({"baby_food": 0.4, "dairy": 0.25, "diapers": 0.2, "hygiene": 0.15}),
        0.014, 0.34,
    ),
    "sleeper": Archetype(
        "sleeper", 0.8, 110.0, 45.0,
        _cats({"groceries": 0.4, "baby_food": 0.3, "household": 0.3}),
        0.004, 0.22,
    ),
    "cross_shopper": Archetype(
        "cross_shopper", 2.9, 210.0, 80.0,
        _cats({"baby_food": 0.3, "diapers": 0.2, "dairy": 0.2, "household": 0.15, "snacks": 0.15}),
        0.018, 0.40,
    ),
    "mixed": Archetype(
        "mixed", 1.7, 160.0, 60.0,
        _cats({"baby_food": 0.3, "groceries": 0.25, "dairy": 0.25, "hygiene": 0.2}),
        0.010, 0.30,
    ),
}

# Распределение архетипов, условное по сегменту (иллюстративно).
ARCHETYPE_BY_SEGMENT: dict[str, dict[str, float]] = {
    "parents_0_3": {"loyalist": 0.34, "cross_shopper": 0.30, "bargain_hunter": 0.22, "mixed": 0.10, "sleeper": 0.04},
    "mature": {"loyalist": 0.34, "mixed": 0.30, "bargain_hunter": 0.18, "sleeper": 0.12, "cross_shopper": 0.06},
    "youth": {"bargain_hunter": 0.36, "mixed": 0.30, "cross_shopper": 0.20, "sleeper": 0.10, "loyalist": 0.04},
    "senior": {"sleeper": 0.40, "loyalist": 0.28, "mixed": 0.24, "bargain_hunter": 0.08, "cross_shopper": 0.0},
    "bad_habits": {"mixed": 0.4, "bargain_hunter": 0.3, "sleeper": 0.2, "loyalist": 0.1, "cross_shopper": 0.0},
}
