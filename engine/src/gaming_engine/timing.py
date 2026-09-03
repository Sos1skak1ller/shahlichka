"""Rule-based тайминг механик + anti-fatigue (research.md R3, шаг 5; FR-014)."""

from __future__ import annotations

from gaming_engine import config


def anti_fatigue_triggered(consecutive_ignored: int, n: int | None = None) -> bool:
    """N последовательных циклов без отклика → пора менять тип механики."""
    threshold = config.ANTI_FATIGUE_N if n is None else n
    return consecutive_ignored >= threshold


def should_generate_challenge(has_active_challenge: bool) -> bool:
    return not has_active_challenge
