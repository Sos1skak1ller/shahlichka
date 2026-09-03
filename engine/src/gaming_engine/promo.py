"""Персональное ранжирование пула акций «от маркетинга» (data-model §9,
FR-025/FR-026/FR-027). Эвристика: совпадение категории с историей + свежесть +
маржинальность акции. Без нового экрана — потребляется внутри существующих (FR-007).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from gaming_engine import config
from gaming_engine.challenge.features import UserFeatures

_DATA = (
    Path(__file__).resolve().parents[3] / "fixtures" / "data" / "promo_pool.json"
)


@dataclass(frozen=True)
class Promo:
    promo_id: str
    category: str
    discount_type: str
    discount_value: float
    margin_impact: float
    segments: tuple[str, ...]

    def eligible_for(self, segment: str) -> bool:
        return not self.segments or segment in self.segments


@dataclass
class RankedPromo:
    promo_id: str
    category: str
    rank_score: float
    margin_impact: float


@lru_cache(maxsize=1)
def load_promos() -> tuple[Promo, ...]:
    raw = json.loads(_DATA.read_text(encoding="utf-8"))
    return tuple(
        Promo(
            promo_id=p["promo_id"],
            category=p["category"],
            discount_type=p["discount_type"],
            discount_value=float(p["discount_value"]),
            margin_impact=float(p["margin_impact"]),
            segments=tuple(p.get("eligibility_rules", {}).get("segments", [])),
        )
        for p in raw["promos"]
    )


def rank_promos(feats: UserFeatures, *, segment: str) -> list[RankedPromo]:
    promos = [p for p in load_promos() if p.eligible_for(segment)]
    if not promos:
        return []

    max_freq = max((r.frequency for r in feats.by_category.values()), default=1) or 1
    max_margin = max((p.margin_impact for p in promos), default=1.0) or 1.0
    w = config.PROMO_RANK_WEIGHTS

    ranked: list[RankedPromo] = []
    for p in promos:
        rfm = feats.by_category.get(p.category)
        cat_match = (rfm.frequency / max_freq) if rfm else 0.0
        recency = 1.0 / (1.0 + (rfm.recency_weeks if rfm else 12))
        margin = p.margin_impact / max_margin
        score = (
            w["category_match"] * cat_match
            + w["recency"] * recency
            + w["margin"] * margin
        )
        ranked.append(
            RankedPromo(
                promo_id=p.promo_id,
                category=p.category,
                rank_score=round(score, 6),
                margin_impact=p.margin_impact,
            )
        )

    # tie-break: сначала маржинальность (FR-026), затем id — для детерминизма
    ranked.sort(key=lambda r: (-r.rank_score, -r.margin_impact, r.promo_id))
    return ranked
