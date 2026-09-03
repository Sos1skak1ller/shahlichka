"""Событийный лог покупок: идемпотентный приём, разрешение корректировок,
стабильный порядок (data-model §3, FR-030/FR-030a).

Индексы по пользователю ведутся инкрементально — приём одного события O(1)
амортизированно (важно для симуляции на сотни тысяч чеков).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from gaming_engine.contracts import PurchaseEvent


@dataclass
class IngestResult:
    accepted: bool
    reason: str = ""
    event: PurchaseEvent | None = None
    effective_saved_amount: float = 0.0


@dataclass
class EventLog:
    _events: list[PurchaseEvent] = field(default_factory=list)
    _seen: set[str] = field(default_factory=set)
    _by_user: dict[str, list[PurchaseEvent]] = field(default_factory=dict)
    _saved_by_user: dict[str, float] = field(default_factory=dict)

    @property
    def events(self) -> list[PurchaseEvent]:
        return sorted(self._events, key=lambda e: (e.timestamp, e.receipt_id))

    def ingest(self, event: PurchaseEvent | dict) -> IngestResult:
        ev = event if isinstance(event, PurchaseEvent) else PurchaseEvent.model_validate(event)

        if ev.receipt_id in self._seen:  # FR-030a
            return IngestResult(False, "duplicate_receipt", ev)

        if ev.kind == "correction" and ev.corrects_receipt_id not in self._seen:
            return IngestResult(False, "orphan_correction", ev)

        self._events.append(ev)
        self._seen.add(ev.receipt_id)
        bucket = self._by_user.setdefault(ev.user_id, [])
        # держим per-user список в стабильном порядке (обычно приходит уже по времени)
        if bucket and (ev.timestamp, ev.receipt_id) < (bucket[-1].timestamp, bucket[-1].receipt_id):
            bucket.append(ev)
            bucket.sort(key=lambda e: (e.timestamp, e.receipt_id))
        else:
            bucket.append(ev)
        self._saved_by_user[ev.user_id] = self._saved_by_user.get(ev.user_id, 0.0) + ev.saved_amount
        return IngestResult(True, "", ev, effective_saved_amount=ev.saved_amount)

    def user_events(self, user_id: str) -> list[PurchaseEvent]:
        return self._by_user.get(user_id, [])

    def total_saved(self, user_id: str) -> float:
        return self._saved_by_user.get(user_id, 0.0)

    def confirmed_purchases(self, user_id: str) -> list[PurchaseEvent]:
        return [
            e for e in self.user_events(user_id) if e.kind == "purchase" and e.saved_amount > 0
        ]
