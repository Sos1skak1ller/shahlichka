"""ISO-неделя как единственная единица «времени» движка (research.md R2).

Никаких обращений к системным часам: всё выводится из ``timestamp`` события.
"""

from __future__ import annotations

from datetime import UTC, datetime


def _parse(ts: str) -> datetime:
    """Разбор ISO-8601. 'Z' → +00:00. Наивный timestamp считается UTC."""
    s = ts.replace("Z", "+00:00")
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt


def iso_week(ts: str) -> str:
    """'2026-03-05T12:00:00Z' -> '2026-W10' (формат контракта: YYYY-Www)."""
    dt = _parse(ts)
    year, week, _ = dt.isocalendar()
    return f"{year:04d}-W{week:02d}"


def week_ordinal(iso_wk: str) -> int:
    """Монотонный порядковый номер недели для сравнения и разности.

    Используем ISO-номер года * 53 + номер недели — достаточно для upper-bound
    'соседних' недель, не претендует на точный календарный подсчёт дней.
    """
    year_s, wk_s = iso_wk.split("-W")
    return int(year_s) * 53 + int(wk_s)


def weeks_between(a: str, b: str) -> int:
    """Число недель от a до b (b позже a → положительное)."""
    return week_ordinal(b) - week_ordinal(a)


def is_next_week(prev: str, cur: str) -> bool:
    return weeks_between(prev, cur) == 1


def is_same_week(a: str, b: str) -> bool:
    return a == b
