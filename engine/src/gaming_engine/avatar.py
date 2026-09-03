"""Аватар: state-machine, где уровень определяется ТОЛЬКО накопленной суммой
экономии (data-model §2, FR-003/FR-004/FR-005).

Принцип I конституции: прогресс идёт от денег к награде, никогда наоборот. В этом
модуле нет ни одного входа, связанного с активностью в приложении.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from gaming_engine import config

_THRESHOLDS = config.AVATAR_LEVEL_THRESHOLDS
_MAX_LEVEL = len(_THRESHOLDS) - 1


@dataclass
class Transition:
    from_level: int
    to_level: int
    trigger_receipt_id: str
    at: str
    reason: str  # "accrual" | "correction"


@dataclass
class AvatarState:
    level: int = 0
    visual_stage: int = 1
    state: str = "progressing"  # progressing | level_up_pending | max_level
    last_transition_at: str | None = None
    unlocked_customizations: list[str] = field(
        default_factory=lambda: [config.AVATAR_CUSTOMIZATIONS[0]]
    )
    transition_history: list[Transition] = field(default_factory=list)


def level_for_amount(total_saved: float) -> int:
    """Наибольший L, для которого total_saved >= threshold[L]."""
    lvl = 0
    for i, thr in enumerate(_THRESHOLDS):
        if total_saved + 1e-9 >= thr:
            lvl = i
    return lvl


def threshold_for_level(level: int) -> float:
    return _THRESHOLDS[min(max(level, 0), _MAX_LEVEL)]


def next_threshold(level: int) -> float | None:
    return _THRESHOLDS[level + 1] if level < _MAX_LEVEL else None


def recompute(
    prev: AvatarState,
    total_saved: float,
    trigger_receipt_id: str,
    at: str,
    is_correction: bool,
) -> AvatarState:
    """Пересчёт состояния аватара после изменения накопленной экономии.

    Уровень может как вырасти (накопление), так и снизиться (корректировка, FR-005).
    Разблокированные кастомизации при понижении НЕ отбираются (data-model §2).
    """
    new_level = level_for_amount(total_saved)
    st = AvatarState(
        level=new_level,
        visual_stage=new_level + 1,
        state=prev.state,
        last_transition_at=prev.last_transition_at,
        unlocked_customizations=list(prev.unlocked_customizations),
        transition_history=list(prev.transition_history),
    )

    if new_level != prev.level:
        st.transition_history.append(
            Transition(
                from_level=prev.level,
                to_level=new_level,
                trigger_receipt_id=trigger_receipt_id,
                at=at,
                reason="correction" if is_correction else "accrual",
            )
        )
        st.last_transition_at = at
        # разблокировать кастомизации по всем уровням до new_level включительно
        for lvl in range(new_level + 1):
            cust = config.AVATAR_CUSTOMIZATIONS[lvl]
            if cust not in st.unlocked_customizations:
                st.unlocked_customizations.append(cust)

    st.state = "max_level" if new_level >= _MAX_LEVEL else "progressing"
    return st
