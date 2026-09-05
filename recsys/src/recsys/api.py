"""Публичная точка входа. Всё, что видит engine, — эти три функции и два dataclass'а.

Обучение отсюда недоступно принципиально: `api` умеет только читать артефакт
(критерий приёмки №6).
"""

from __future__ import annotations

import os
from collections.abc import Iterable
from pathlib import Path

from recsys import categories as _categories
from recsys import companions as _companions
from recsys.artifacts import Artifact, load_cached
from recsys.matrix import user_category_weights
from recsys.sources.sim_events import SimSource
from recsys.types import CategoryScore, ItemScore

_DEFAULT_PREFIX = Path(__file__).resolve().parents[2] / "artifacts" / "als_v0"
_ENV_VAR = "RECSYS_ARTIFACT"


def artifact_prefix() -> str:
    """Путь к артефакту: переменная окружения либо `recsys/artifacts/als_v0`."""
    return os.environ.get(_ENV_VAR) or str(_DEFAULT_PREFIX)


def _artifact() -> Artifact:
    return load_cached(artifact_prefix())


def recommend_categories(
    events: Iterable[dict],
    *,
    exclude: set[str],
    k: int = 5,
    as_of_week: str,
) -> list[CategoryScore]:
    """Топ-k интересных пользователю категорий, кроме исключённых.

    `events` — PurchaseEvent-подобные словари (`category_list`, `sku_list`,
    `timestamp`, `receipt_id`, `user_id`). История одного пользователя.
    """
    art = _artifact()
    interactions = list(SimSource(events).stream())
    weights = user_category_weights(interactions, as_of_week=as_of_week)
    params = art.params
    return _categories.rank(
        art,
        weights,
        exclude=set(exclude),
        k=k,
        lam=float(params.get("lambda", 0.1)),
        alpha=float(params.get("alpha", 20.0)),
    )


def recommend_companions(
    basket_skus: list[str],
    *,
    exclude_skus: frozenset[str] = frozenset(),
    k: int = 5,
) -> list[ItemScore]:
    """Товары, идущие в комплекте к корзине. Не персонально — свойство товара."""
    return _companions.rank(_artifact(), basket_skus, exclude_skus=exclude_skus, k=k)


def model_version() -> str:
    """Например, "als-v0/sim"."""
    return _artifact().model_version()
