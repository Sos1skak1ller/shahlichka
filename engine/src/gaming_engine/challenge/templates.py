"""Реестр шаблонов челленджей (data-model §5)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

_DATA = (
    Path(__file__).resolve().parents[4]
    / "fixtures"
    / "data"
    / "challenge_templates.json"
)


@dataclass(frozen=True)
class ChallengeTemplate:
    template_id: str
    mechanic_type: str
    condition_pattern: str
    reward_formula: str
    min_level: int
    max_level: int
    segments: tuple[str, ...]
    n_options: tuple[int, ...]
    deadline_offset_days: int

    def eligible_for(self, *, segment: str, avatar_level: int) -> bool:
        return (
            segment in self.segments
            and self.min_level <= avatar_level <= self.max_level
        )

    def reward_for(self, n: int) -> float:
        return _safe_eval(self.reward_formula, n)

    def max_reward(self) -> float:
        return max(self.reward_for(n) for n in self.n_options)

    def min_reward(self) -> float:
        return min(self.reward_for(n) for n in self.n_options)

    def best_n_within(self, budget: float, prefer: int) -> int:
        """Наибольшее n из n_options, укладывающееся в бюджет, но не больше prefer.

        Если даже минимальное n не влезает — вернуть минимальное (экономику
        поймает pre_check и пометит rejected_economy).
        """
        opts = sorted(self.n_options)
        affordable = [n for n in opts if self.reward_for(n) <= budget + 1e-9 and n <= prefer]
        if affordable:
            return affordable[-1]
        within = [n for n in opts if self.reward_for(n) <= budget + 1e-9]
        return within[-1] if within else opts[0]


@dataclass(frozen=True)
class TemplateRegistry:
    templates: tuple[ChallengeTemplate, ...]
    fallback_template_id: str
    fallback_category_by_segment: dict[str, str]

    def by_id(self, template_id: str) -> ChallengeTemplate:
        for t in self.templates:
            if t.template_id == template_id:
                return t
        raise KeyError(template_id)

    def fallback(self) -> ChallengeTemplate:
        return self.by_id(self.fallback_template_id)


def _safe_eval(formula: str, n: int) -> float:
    """Мини-вычислитель reward_formula: допускаются только 'n', числа и + - * / ( )."""
    allowed = set("0123456789 nN+-*/(). ")
    if not set(formula) <= allowed:
        raise ValueError(f"unsafe reward_formula: {formula!r}")
    return float(eval(formula, {"__builtins__": {}}, {"n": n, "N": n}))  # noqa: S307


@lru_cache(maxsize=1)
def load_registry() -> TemplateRegistry:
    raw = json.loads(_DATA.read_text(encoding="utf-8"))
    templates = tuple(
        ChallengeTemplate(
            template_id=t["template_id"],
            mechanic_type=t["mechanic_type"],
            condition_pattern=t["condition_pattern"],
            reward_formula=str(t["reward_formula"]),
            min_level=int(t["eligibility_rules"].get("min_level", 0)),
            max_level=int(t["eligibility_rules"].get("max_level", 4)),
            segments=tuple(t["eligibility_rules"].get("segments", [])),
            n_options=tuple(t["param_space"].get("n", [1])),
            deadline_offset_days=int(t["param_space"].get("deadline_offset_days", 7)),
        )
        for t in raw["templates"]
    )
    return TemplateRegistry(
        templates=templates,
        fallback_template_id=raw["fallback_template_id"],
        fallback_category_by_segment=dict(raw["fallback_category_by_segment"]),
    )
