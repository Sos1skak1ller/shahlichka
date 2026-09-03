"""RewardLedger — недельный бюджетный потолок и инвариант экономики
(data-model §11, FR-018/FR-019, research.md R5).

Экономика считается ЗАРАНЕЕ: pre_check выполняется до начисления награды.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from gaming_engine import config


@dataclass
class Rejection:
    mechanic: str
    reason: str  # "budget_exceeded" | "economy_invariant_violation"
    at: str


@dataclass
class WeekLedger:
    user_id: str
    iso_week: str
    budget_cap: float
    accrued_reward: float = 0.0
    spent_to_date: float = 0.0
    rejections: list[Rejection] = field(default_factory=list)


@dataclass
class PreCheck:
    ok: bool
    reason: str = ""


def weekly_margin(archetype: str) -> float:
    return config.WEEKLY_MARGIN_BY_ARCHETYPE.get(
        archetype, config.WEEKLY_MARGIN_BY_ARCHETYPE["mixed"]
    )


def expected_margin_uplift(mechanic: str) -> float:
    return config.EXPECTED_MARGIN_UPLIFT_BY_MECHANIC.get(mechanic, 0.0)


@dataclass
class RewardLedger:
    _weeks: dict[tuple[str, str], WeekLedger] = field(default_factory=dict)

    def _get(self, user_id: str, iso_week: str, archetype: str) -> WeekLedger:
        key = (user_id, iso_week)
        wl = self._weeks.get(key)
        if wl is None:
            cap = config.BUDGET_CAP_PCT * weekly_margin(archetype)
            wl = WeekLedger(user_id=user_id, iso_week=iso_week, budget_cap=cap)
            self._weeks[key] = wl
        return wl

    def pre_check(
        self,
        user_id: str,
        iso_week: str,
        archetype: str,
        mechanic: str,
        reward_cost: float,
        at: str,
    ) -> PreCheck:
        wl = self._get(user_id, iso_week, archetype)
        # (1) недельный потолок
        if wl.spent_to_date + reward_cost > wl.budget_cap + 1e-9:
            wl.rejections.append(Rejection(mechanic, "budget_exceeded", at))
            return PreCheck(False, "budget_exceeded")
        # (2) инвариант кейса: стоимость награды ≤ ожидаемый прирост маржи
        if reward_cost > expected_margin_uplift(mechanic) + 1e-9:
            wl.rejections.append(Rejection(mechanic, "economy_invariant_violation", at))
            return PreCheck(False, "economy_invariant_violation")
        return PreCheck(True)

    def accrue(
        self,
        user_id: str,
        iso_week: str,
        archetype: str,
        mechanic: str,
        reward_cost: float,
        at: str,
    ) -> PreCheck:
        """pre_check + фактическое списание из потолка. Возвращает результат проверки."""
        pc = self.pre_check(user_id, iso_week, archetype, mechanic, reward_cost, at)
        if not pc.ok:
            return pc
        wl = self._get(user_id, iso_week, archetype)
        wl.accrued_reward += reward_cost
        wl.spent_to_date += reward_cost
        return pc

    def week(self, user_id: str, iso_week: str, archetype: str = "mixed") -> WeekLedger:
        return self._get(user_id, iso_week, archetype)

    def remaining(self, user_id: str, iso_week: str, archetype: str = "mixed") -> float:
        wl = self._get(user_id, iso_week, archetype)
        return max(0.0, wl.budget_cap - wl.spent_to_date)

    def total_rejections(self) -> int:
        return sum(len(w.rejections) for w in self._weeks.values())
