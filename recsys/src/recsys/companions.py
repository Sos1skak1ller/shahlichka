"""Сопутствующие товары: item-item по факторам модели B.

Здесь cosine, а не dot — в отличие от retrieval категорий. Разница содержательная:
для «что вообще предложить» популярность полезный сигнал, а для «что идёт в комплект»
она шум. Без нормировки и штрафа компаньоном ко всему окажутся хлеб и молоко.
"""

from __future__ import annotations

import numpy as np

from recsys.artifacts import Artifact
from recsys.types import ItemScore

POPULARITY_BETA = 0.1
DEFAULT_TOP_K = 5


def _unit_rows(Z: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(Z, axis=1, keepdims=True)
    norms[norms == 0.0] = 1.0  # нулевой фактор оставляем нулевым, а не делим на 0
    return Z / norms


def rank(
    artifact: Artifact,
    basket_skus: list[str],
    *,
    exclude_skus: frozenset[str] = frozenset(),
    k: int = DEFAULT_TOP_K,
    beta: float = POPULARITY_BETA,
) -> list[ItemScore]:
    """Соседи корзины по косинусу минус штраф за популярность.

    Кандидаты — объединение соседей всех товаров корзины, минус сами эти товары и
    минус то, что пользователь берёт регулярно (`exclude_skus`).
    """
    if artifact.Z is None or not artifact.skus or not basket_skus:
        return []

    index = {s: i for i, s in enumerate(artifact.skus)}
    seed_idx = sorted({index[s] for s in basket_skus if s in index})
    if not seed_idx:
        return []

    unit = _unit_rows(artifact.Z.astype(np.float64))
    # Косинус каждого товара до центра корзины: суммирование по seed'ам эквивалентно
    # объединению соседей, но считается одним произведением.
    sims = unit @ unit[seed_idx].sum(axis=0)

    if artifact.pop is not None:
        sims = sims - beta * np.log1p(artifact.pop.astype(np.float64))

    dropped = set(basket_skus) | set(exclude_skus)
    rows = [
        (float(sims[i]), s)
        for i, s in enumerate(artifact.skus)
        if s not in dropped
    ]
    rows.sort(key=lambda t: (-t[0], t[1]))
    return [
        ItemScore(sku=s, category=artifact.sku_category.get(s), score=score)
        for score, s in rows[:k]
    ]
