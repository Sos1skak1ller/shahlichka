"""Retrieval категорий: стадия 1 из §5 спеки.

Здесь именно retrieval — чистый dot product и отсечение исключённых. Вторая стадия
(линейная смесь с recency, маржой и новизной) живёт на стороне engine, потому что
маржа и бюджет — не забота рекомендателя.
"""

from __future__ import annotations

import numpy as np

from recsys.als import fold_in, gramian
from recsys.artifacts import Artifact
from recsys.types import CategoryScore

DEFAULT_TOP_K = 20


def user_vector(
    artifact: Artifact,
    weights: dict[str, float],
    *,
    lam: float,
    alpha: float,
) -> np.ndarray:
    """Вектор пользователя через fold-in по его затухающим весам категорий.

    Категории, которых не было в обучении, игнорируются: у них нет фактора, и
    подставить его неоткуда.
    """
    index = {c: i for i, c in enumerate(artifact.categories)}
    pairs = sorted((index[c], w) for c, w in weights.items() if c in index and w > 0)
    if not pairs:
        return np.zeros(artifact.Y.shape[1], dtype=artifact.Y.dtype)

    idx = np.asarray([i for i, _ in pairs], dtype=np.int64)
    conf = np.asarray([1.0 + alpha * w for _, w in pairs], dtype=np.float64)
    return fold_in(artifact.Y, gramian(artifact.Y), idx, conf, lam)


def rank(
    artifact: Artifact,
    weights: dict[str, float],
    *,
    exclude: set[str],
    k: int = DEFAULT_TOP_K,
    lam: float = 0.1,
    alpha: float = 20.0,
) -> list[CategoryScore]:
    """Топ-k категорий. Пустая история → популярные категории с `is_fallback=True`."""
    u = user_vector(artifact, weights, lam=lam, alpha=alpha)

    # Вырожденный вектор = нет истории, которую модель знает. Скор был бы нулевым
    # для всех категорий, и порядок определился бы шумом сортировки.
    if not np.any(u):
        return _popularity_fallback(artifact, exclude=exclude, k=k)

    scores = (artifact.Y @ u).astype(np.float64)
    return _take_top(artifact.categories, scores, exclude=exclude, k=k, is_fallback=False)


def _popularity_fallback(
    artifact: Artifact, *, exclude: set[str], k: int
) -> list[CategoryScore]:
    if artifact.category_popularity is not None:
        scores = artifact.category_popularity.astype(np.float64)
    else:
        # Популярности в артефакте нет — отдаём стабильный алфавитный порядок,
        # но выдача всё равно непустая (критерий приёмки №5).
        scores = np.zeros(len(artifact.categories), dtype=np.float64)
    return _take_top(artifact.categories, scores, exclude=exclude, k=k, is_fallback=True)


def _take_top(
    categories: list[str],
    scores: np.ndarray,
    *,
    exclude: set[str],
    k: int,
    is_fallback: bool,
) -> list[CategoryScore]:
    """Отсечь исключённые и взять k лучших с детерминированным тай-брейком.

    Исключённые не «штрафуются», а выбрасываются: критерий приёмки №4 требует, чтобы
    они не появлялись в выдаче никогда, в том числе когда кандидатов меньше k.
    """
    rows = [
        (float(scores[i]), c)
        for i, c in enumerate(categories)
        if c not in exclude
    ]
    rows.sort(key=lambda t: (-t[0], t[1]))  # тай-брейк по имени — воспроизводимо
    return [CategoryScore(category=c, score=s, is_fallback=is_fallback) for s, c in rows[:k]]
