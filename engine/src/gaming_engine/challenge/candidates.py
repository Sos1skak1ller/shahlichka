"""Генерация кандидатов: фильтр шаблонов по применимости (research.md R3, шаг 2)."""

from __future__ import annotations

from dataclasses import dataclass

from gaming_engine.challenge.features import UserFeatures
from gaming_engine.challenge.templates import ChallengeTemplate, load_registry


@dataclass
class CandidatePool:
    templates: list[ChallengeTemplate]
    pool_exhausted: bool  # после кулдауна не осталось ни одного шаблона


def eligible_candidates(
    feats: UserFeatures,
    *,
    segment: str,
    remaining_budget: float,
    recent_template_ids: set[str],
    exclude_mechanic: str | None = None,
) -> CandidatePool:
    reg = load_registry()
    base = [
        t
        for t in reg.templates
        if t.eligible_for(segment=segment, avatar_level=feats.avatar_level)
        and t.min_reward() <= remaining_budget + 1e-9
        and (exclude_mechanic is None or t.mechanic_type != exclude_mechanic)
    ]
    after_cooldown = [t for t in base if t.template_id not in recent_template_ids]
    if after_cooldown:
        return CandidatePool(after_cooldown, pool_exhausted=False)
    # пул исчерпан кулдауном — сигналим наверх, но отдаём base как запасной вариант
    return CandidatePool(base, pool_exhausted=True)
