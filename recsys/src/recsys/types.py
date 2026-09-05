"""Типы данных пакета. Ничего из `gaming_engine` здесь появиться не может —
`recsys` самостоятелен и знает только про взаимодействия, категории и товары.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class Interaction:
    """Одна строка «пользователь купил товар категории c в чеке r на неделе w»."""

    user_id: str
    receipt_id: str
    category: str
    sku: str | None
    ts_week: str  # ISO-неделя, "2026-W14"
    amount: float


@dataclass(frozen=True, slots=True)
class CategoryScore:
    category: str
    score: float
    is_fallback: bool = False


@dataclass(frozen=True, slots=True)
class ItemScore:
    sku: str
    category: str | None
    score: float


@dataclass(frozen=True, slots=True)
class Factors:
    """Обученные факторы одной ALS-модели.

    `rows` — подписи строк исходной матрицы (пользователи или чеки), они НЕ шиппятся
    в артефакт: новый пользователь получает вектор через fold-in. Поле нужно только
    внутри обучения и при замере качества.
    """

    X: np.ndarray | None  # (n_rows, k) — факторы строк, в артефакт не идут
    Y: np.ndarray  # (n_cols, k) — факторы столбцов, это и есть модель
    cols: list[str]  # подписи столбцов: категории или sku
    rows: list[str] | None = None
