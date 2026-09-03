"""Ранжирование кандидатов (research.md R3, шаг 3).

Лёгкая объяснимая модель: LogisticRegression, обученная ОДИН РАЗ при импорте на
фиксированном синтетическом наборе (детерминированный solver 'liblinear',
random_state=0). Никакого LLM, вывод воспроизводим.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.linear_model import LogisticRegression

from gaming_engine.challenge.features import UserFeatures
from gaming_engine.challenge.templates import ChallengeTemplate, load_registry

RANKER_VERSION = "logreg-v0"

# Признаки: [affinity, recency, level_fit, monetary_norm]
# Синтетическая обучающая выборка: высокие affinity/recency/fit → отклик.
_X_TRAIN = np.array(
    [
        [0.9, 0.9, 0.9, 0.8, 1.0],
        [0.8, 0.7, 0.8, 0.6, 1.0],
        [0.7, 0.8, 0.6, 0.5, 1.0],
        [0.6, 0.6, 0.7, 0.4, 1.0],
        [0.5, 0.5, 0.6, 0.5, 1.0],
        [0.2, 0.3, 0.4, 0.2, 0.0],
        [0.1, 0.2, 0.3, 0.1, 0.0],
        [0.3, 0.1, 0.2, 0.2, 0.0],
        [0.15, 0.4, 0.35, 0.1, 0.0],
        [0.05, 0.05, 0.1, 0.05, 0.0],
    ]
)
_MODEL = LogisticRegression(solver="liblinear", random_state=0)
_MODEL.fit(_X_TRAIN[:, :4], _X_TRAIN[:, 4].astype(int))


@dataclass
class RankedChoice:
    template: ChallengeTemplate
    category: str
    n: int
    score: float
    generated_by: str  # "ml_ranker" | "fallback"


def _feature_row(template: ChallengeTemplate, category: str, feats: UserFeatures) -> list[float]:
    rfm = feats.by_category.get(category)
    max_freq = max((r.frequency for r in feats.by_category.values()), default=1) or 1
    max_mon = max((r.monetary for r in feats.by_category.values()), default=1.0) or 1.0
    affinity = (rfm.frequency / max_freq) if rfm else 0.0
    recency = 1.0 / (1.0 + (rfm.recency_weeks if rfm else 12))
    mid = (template.min_level + template.max_level) / 2.0
    level_fit = max(0.0, 1.0 - abs(feats.avatar_level - mid) / 4.0)
    monetary = (rfm.monetary / max_mon) if rfm else 0.0
    return [affinity, recency, level_fit, monetary]


def _target_category(template: ChallengeTemplate, feats: UserFeatures) -> str:
    tops = feats.top_categories(3)
    return tops[0] if tops else load_registry().fallback_category_by_segment.get("parents_0_3", "baby_food")


def _n_for(template: ChallengeTemplate, feats: UserFeatures, budget: float) -> int:
    """Детерминированный выбор N: масштаб от частоты покупок в целевой категории,
    но не выходя за остаток бюджета."""
    cat = _target_category(template, feats)
    rfm = feats.by_category.get(cat)
    freq = rfm.frequency if rfm else 0
    opts = sorted(template.n_options)
    prefer = opts[min(freq // 2, len(opts) - 1)]
    return template.best_n_within(budget, prefer)


def rank(
    feats: UserFeatures, candidates: list[ChallengeTemplate], budget: float
) -> list[RankedChoice]:
    scored: list[RankedChoice] = []
    for t in candidates:
        cat = _target_category(t, feats)
        row = _feature_row(t, cat, feats)
        prob = float(_MODEL.predict_proba(np.array([row]))[0, 1])
        scored.append(
            RankedChoice(
                template=t,
                category=cat,
                n=_n_for(t, feats, budget),
                score=prob,
                generated_by="ml_ranker",
            )
        )
    scored.sort(key=lambda c: (-c.score, c.template.template_id))
    return scored


def choose(
    feats: UserFeatures, candidates: list[ChallengeTemplate], budget: float = 1e9
) -> RankedChoice:
    reg = load_registry()
    if not feats.has_history or not candidates:
        fb = reg.fallback()
        cat = reg.fallback_category_by_segment.get("parents_0_3", "baby_food")
        return RankedChoice(
            template=fb,
            category=cat,
            n=fb.best_n_within(budget, sorted(fb.n_options)[0]),
            score=0.0,
            generated_by="fallback",
        )
    return rank(feats, candidates, budget)[0]
