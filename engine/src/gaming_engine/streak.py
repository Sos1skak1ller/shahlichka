"""Недельный стрик покупок (data-model §4, FR-006).

Стрик = число подряд идущих ISO-недель, в каждой из которых нетто-экономия по
подтверждённым чекам положительна. Открытия приложения не учитываются. Первая
неделя без подтверждённой покупки сбрасывает стрик в 0.

Считается заново из событийного лога при каждом обращении — детерминированно и
корректно при корректировках (research.md R2).
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from gaming_engine.contracts import PurchaseEvent
from gaming_engine.weekcal import is_next_week, iso_week, weeks_between


@dataclass
class StreakState:
    streak_count: int = 0
    last_active_week: str | None = None


def _event_week(ev: PurchaseEvent, by_id: dict[str, PurchaseEvent]) -> str:
    """Корректировка относится к неделе ИСХОДНОГО чека, не к своей метке времени."""
    if ev.kind == "correction" and ev.corrects_receipt_id in by_id:
        return iso_week(by_id[ev.corrects_receipt_id].timestamp)
    return iso_week(ev.timestamp)


def compute(
    user_events: list[PurchaseEvent], as_of_week: str | None = None
) -> StreakState:
    if not user_events:
        return StreakState()

    by_id = {e.receipt_id: e for e in user_events}
    net_by_week: dict[str, float] = defaultdict(float)
    for e in user_events:
        net_by_week[_event_week(e, by_id)] += e.saved_amount

    active_weeks = sorted(w for w, v in net_by_week.items() if v > 1e-9)
    if not active_weeks:
        return StreakState()

    last = active_weeks[-1]

    # FR-006: если между последней активной неделей и «сейчас» есть пропущенная
    # календарная неделя — серия прервана (стрик 0), но неделю активности помним.
    if as_of_week is not None and weeks_between(last, as_of_week) >= 2:
        return StreakState(streak_count=0, last_active_week=last)

    count = 1
    for i in range(len(active_weeks) - 1, 0, -1):
        if is_next_week(active_weeks[i - 1], active_weeks[i]):
            count += 1
        else:
            break
    return StreakState(streak_count=count, last_active_week=last)
