"""Источник поверх синтетических событий `gaming_sim.generator`.

Импорта `gaming_sim` здесь нет: на вход приходят обычные словари, поэтому пакет
остаётся самостоятельным (критерий приёмки №1).

Гранулярность `Interaction` — одна товарная строка чека, как в RetailHero, где
каждая строка `purchases.csv` — это товар в транзакции. Синтетическое событие
устроено иначе: `category_list` и `sku_list` не связаны попарно, поэтому категории
раскладываются по товарам циклически, а категории, которым товара не хватило,
отдаются отдельной строкой с `sku=None`. Так ни одна категория чека не теряется.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from datetime import datetime

from recsys.types import Interaction


def iso_week(timestamp: str) -> str:
    """"2026-03-31T19:00:00Z" -> "2026-W14". Свой, чтобы не тянуть gaming_engine."""
    ts = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    year, week, _ = ts.isocalendar()
    return f"{year}-W{week:02d}"


class SimSource:
    """Взаимодействия из списка PurchaseEvent-подобных словарей. Без I/O."""

    def __init__(self, events: Iterable[dict]) -> None:
        self._events = list(events)

    def stream(self) -> Iterator[Interaction]:
        for ev in self._events:
            # Корректировки — это сторно, а не покупка: в матрицу вкуса они не идут.
            if ev.get("corrects_receipt_id"):
                continue
            cats: list[str] = list(ev.get("category_list") or [])
            if not cats:
                continue
            skus: list[str] = list(ev.get("sku_list") or [])
            week = iso_week(ev["timestamp"])
            total = float(ev.get("total_sum") or 0.0)
            per_line = total / len(skus) if skus else total

            covered: set[str] = set()
            for i, sku in enumerate(skus):
                cat = cats[i % len(cats)]
                covered.add(cat)
                yield Interaction(
                    user_id=str(ev["user_id"]),
                    receipt_id=str(ev["receipt_id"]),
                    category=cat,
                    sku=str(sku),
                    ts_week=week,
                    amount=per_line,
                )
            for cat in cats:
                if cat not in covered:
                    yield Interaction(
                        user_id=str(ev["user_id"]),
                        receipt_id=str(ev["receipt_id"]),
                        category=cat,
                        sku=None,
                        ts_week=week,
                        amount=0.0,
                    )
