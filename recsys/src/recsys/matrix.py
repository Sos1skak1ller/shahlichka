"""Сборка разреженных матриц из потока взаимодействий.

Модуль знает про веса и ничего про ALS. Две матрицы строятся независимо, потому
что это две разные модели (§3 спеки):

* модель A — `user × category`, вес чека затухает экспоненциально;
* модель B — `receipt × sku`, бинарная.

Порядок строк и столбцов — лексикографический. Это не косметика: детерминизм
артефакта (критерий приёмки №2) требует фиксированного порядка обхода, а порядок
первого появления зависит от того, как источник отдал поток.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date

import numpy as np
from scipy.sparse import coo_matrix, csr_matrix

from recsys.types import Interaction

HALF_LIFE_WEEKS = 8.0
DTYPE = np.float32


@dataclass
class MatrixBundle:
    """Матрица взаимодействий вместе с подписями осей."""

    matrix: csr_matrix
    rows: list[str]
    cols: list[str]

    @property
    def sparsity(self) -> float:
        total = self.matrix.shape[0] * self.matrix.shape[1]
        return 1.0 - (self.matrix.nnz / total if total else 0.0)


def week_index(ts_week: str) -> int:
    """"2026-W14" -> порядковый номер недели, пригодный для вычитания."""
    year_s, week_s = ts_week.split("-W")
    monday = date.fromisocalendar(int(year_s), int(week_s), 1)
    return monday.toordinal() // 7


def decay_weight(age_weeks: float, half_life: float = HALF_LIFE_WEEKS) -> float:
    """0.5 ** (age / half_life). Свежая покупка весит 1.0, восьминедельная — 0.5.

    Отрицательный возраст (взаимодействие «из будущего» относительно as_of)
    прижимается к нулю, иначе одна опечатка в дате даёт вес больше единицы.
    """
    return float(0.5 ** (max(age_weeks, 0.0) / half_life))


def build_category_matrix(
    interactions: Iterable[Interaction],
    *,
    as_of_week: str | None = None,
    half_life: float = HALF_LIFE_WEEKS,
) -> MatrixBundle:
    """Модель A: `user × category`, вес — сумма затухающих вкладов ЧЕКОВ.

    Считаются именно чеки, а не товарные строки: иначе корзина из десяти йогуртов
    весила бы как десять походов за молочкой, и модель уехала бы в категории с
    длинными чеками вместо интересных.

    Сумма чека в вес не кладётся сознательно (§3): иначе вкус подменяется дороговизной.
    """
    # (user, category) -> {receipt_id: week} — дедупликация товарных строк по чеку.
    seen: dict[tuple[str, str], dict[str, int]] = {}
    for it in interactions:
        key = (it.user_id, it.category)
        seen.setdefault(key, {})[it.receipt_id] = week_index(it.ts_week)

    if not seen:
        return MatrixBundle(csr_matrix((0, 0), dtype=DTYPE), [], [])

    users = sorted({u for u, _ in seen})
    cats = sorted({c for _, c in seen})
    u_ix = {u: i for i, u in enumerate(users)}
    c_ix = {c: i for i, c in enumerate(cats)}

    last_week = max(w for receipts in seen.values() for w in receipts.values())
    as_of = week_index(as_of_week) if as_of_week else last_week

    rows: list[int] = []
    cols: list[int] = []
    vals: list[float] = []
    for (user, cat), receipts in seen.items():
        weight = sum(decay_weight(as_of - w, half_life) for w in receipts.values())
        if weight <= 0.0:
            continue
        rows.append(u_ix[user])
        cols.append(c_ix[cat])
        vals.append(weight)

    m = coo_matrix(
        (np.asarray(vals, dtype=DTYPE), (np.asarray(rows), np.asarray(cols))),
        shape=(len(users), len(cats)),
        dtype=DTYPE,
    ).tocsr()
    m.sum_duplicates()
    return MatrixBundle(m, users, cats)


def user_category_weights(
    interactions: Iterable[Interaction],
    *,
    as_of_week: str | None = None,
    half_life: float = HALF_LIFE_WEEKS,
) -> dict[str, float]:
    """Затухающие веса категорий для ОДНОГО пользователя — вход fold-in.

    Намеренно та же арифметика, что в `build_category_matrix`: если обучение и
    инференс посчитают вес по-разному, вектор пользователя окажется в другом
    масштабе, чем факторы, на которых училась модель.
    """
    per_cat: dict[str, dict[str, int]] = {}
    for it in interactions:
        per_cat.setdefault(it.category, {})[it.receipt_id] = week_index(it.ts_week)

    if not per_cat:
        return {}

    last_week = max(w for receipts in per_cat.values() for w in receipts.values())
    as_of = week_index(as_of_week) if as_of_week else last_week
    return {
        cat: sum(decay_weight(as_of - w, half_life) for w in receipts.values())
        for cat, receipts in per_cat.items()
    }


def category_popularity(bundle: MatrixBundle) -> np.ndarray:
    """Доля пользователей, у которых категория встречается. Основа cold-start-выдачи."""
    n_users = bundle.matrix.shape[0] or 1
    counts = np.asarray((bundle.matrix > 0).sum(axis=0)).ravel()
    return (counts / n_users).astype(DTYPE)


def build_receipt_sku_matrix(interactions: Iterable[Interaction]) -> MatrixBundle:
    """Модель B: `receipt × sku`, бинарная.

    «Пользователь» здесь — чек: что берут вместе, это свойство корзины, а не
    человека. По `user × sku` получилось бы «что человек покупает вообще».
    """
    pairs: set[tuple[str, str]] = set()
    for it in interactions:
        if it.sku is None:
            continue
        pairs.add((it.receipt_id, it.sku))

    if not pairs:
        return MatrixBundle(csr_matrix((0, 0), dtype=DTYPE), [], [])

    receipts = sorted({r for r, _ in pairs})
    skus = sorted({s for _, s in pairs})
    r_ix = {r: i for i, r in enumerate(receipts)}
    s_ix = {s: i for i, s in enumerate(skus)}

    rows = np.fromiter((r_ix[r] for r, _ in sorted(pairs)), dtype=np.int32, count=len(pairs))
    cols = np.fromiter((s_ix[s] for _, s in sorted(pairs)), dtype=np.int32, count=len(pairs))
    vals = np.ones(len(pairs), dtype=DTYPE)

    m = coo_matrix((vals, (rows, cols)), shape=(len(receipts), len(skus)), dtype=DTYPE).tocsr()
    m.sum_duplicates()
    return MatrixBundle(m, receipts, skus)


def sku_popularity(bundle: MatrixBundle) -> np.ndarray:
    """Доля чеков, содержащих товар. Используется как штраф за популярность."""
    n_receipts = bundle.matrix.shape[0] or 1
    counts = np.asarray((bundle.matrix > 0).sum(axis=0)).ravel()
    return (counts / n_receipts).astype(DTYPE)


def sku_to_category(interactions: Iterable[Interaction]) -> dict[str, str]:
    """Справочник sku -> категория (первая встреченная, порядок детерминирован сортировкой)."""
    out: dict[str, str] = {}
    for it in interactions:
        if it.sku is not None and it.sku not in out:
            out[it.sku] = it.category
    return out
