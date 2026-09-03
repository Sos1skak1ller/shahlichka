"""Детерминированные фикстуры для тестов движка (T013).

Ничего случайного и никаких системных часов: все метки времени задаются явно.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

HISTORIES_DIR = Path(__file__).parent / "integration" / "_histories"


def make_event(
    receipt_id: str,
    user_id: str = "u1",
    *,
    timestamp: str,
    saved_amount: float,
    total_sum: float | None = None,
    categories: list[str] | None = None,
    skus: list[str] | None = None,
    chain_code: str = "TS5",
    store_code: str = "s001",
    district_code: str = "d001",
    device_id_hash: str = "dev-a",
    payment_instrument_hash: str = "pay-a",
    corrects_receipt_id: str | None = None,
) -> dict:
    """Собрать словарь события покупки, валидный по purchase-event.schema.json."""
    cats = categories or ["baby_food"]
    return {
        "receipt_id": receipt_id,
        "user_id": user_id,
        "store_code": store_code,
        "chain_code": chain_code,
        "district_code": district_code,
        "timestamp": timestamp,
        "sku_list": skus or [f"sku-{receipt_id}"],
        "category_list": cats,
        "total_sum": total_sum if total_sum is not None else max(saved_amount, 0.0) * 10,
        "saved_amount": saved_amount,
        "device_id_hash": device_id_hash,
        "payment_instrument_hash": payment_instrument_hash,
        "corrects_receipt_id": corrects_receipt_id,
    }


@pytest.fixture
def event_factory():
    return make_event


def load_histories() -> list[tuple[str, dict]]:
    out: list[tuple[str, dict]] = []
    for f in sorted(HISTORIES_DIR.glob("*.json")):
        out.append((f.stem, json.loads(f.read_text(encoding="utf-8"))))
    return out
