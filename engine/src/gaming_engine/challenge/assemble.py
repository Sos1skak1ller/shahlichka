"""Сборка текста челленджа из шаблонной строки (FR-010) — без свободной генерации."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from gaming_engine.challenge.templates import ChallengeTemplate

_RU_MONTHS = [
    "", "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря",
]


def _parse(ts: str) -> datetime:
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def _human_date(dt: datetime) -> str:
    return f"{dt.day} {_RU_MONTHS[dt.month]}"


@dataclass
class AssembledChallenge:
    text: str
    category: str
    n: int
    deadline_iso: str
    reward_amount: float


def assemble(
    template: ChallengeTemplate,
    *,
    category: str,
    n: int,
    from_ts: str,
) -> AssembledChallenge:
    deadline = _parse(from_ts) + timedelta(days=template.deadline_offset_days)
    text = template.condition_pattern.format(
        n=n, category=category, deadline=_human_date(deadline)
    )
    return AssembledChallenge(
        text=text,
        category=category,
        n=n,
        deadline_iso=deadline.isoformat().replace("+00:00", "Z"),
        reward_amount=round(template.reward_for(n), 2),
    )
