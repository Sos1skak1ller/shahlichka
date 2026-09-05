"""Сопутствующие товары: cosine + штраф за популярность."""

from __future__ import annotations

import numpy as np

from recsys import companions
from recsys.artifacts import Artifact
from recsys.types import ItemScore


def _artifact_with(Z: np.ndarray, pop: np.ndarray, skus: list[str]) -> Artifact:
    return Artifact(
        version="als-v0",
        source="sim",
        trained_at="2026-09-05",
        params={},
        categories=["dairy"],
        Y=np.zeros((1, Z.shape[1]), dtype=np.float32),
        skus=skus,
        Z=Z.astype(np.float32),
        pop=pop.astype(np.float32),
        sku_category={s: "dairy" for s in skus},
    )


def test_basket_items_are_excluded(artifact) -> None:
    art, _ = artifact
    basket = art.skus[:2]
    out = companions.rank(art, basket, k=5)
    assert not ({i.sku for i in out} & set(basket))


def test_explicit_exclusions_are_respected(artifact) -> None:
    art, _ = artifact
    basket = [art.skus[0]]
    banned = frozenset(art.skus[1:3])
    out = companions.rank(art, basket, exclude_skus=banned, k=5)
    assert not ({i.sku for i in out} & banned)


def test_empty_basket_returns_empty(artifact) -> None:
    art, _ = artifact
    assert companions.rank(art, [], k=5) == []


def test_unknown_sku_returns_empty(artifact) -> None:
    art, _ = artifact
    assert companions.rank(art, ["нет-такого-товара"], k=5) == []


def test_popularity_penalty_demotes_bread_and_milk() -> None:
    """Без штрафа компаньоном ко всему оказывается самый популярный товар."""
    # b и c одинаково близки к a, но b встречается почти в каждом чеке.
    Z = np.asarray([[1.0, 0.0], [0.9, 0.1], [0.9, 0.1]])
    skus = ["a", "b_popular", "c_rare"]

    no_penalty = companions.rank(
        _artifact_with(Z, np.asarray([0.1, 0.95, 0.05]), skus), ["a"], k=2, beta=0.0
    )
    with_penalty = companions.rank(
        _artifact_with(Z, np.asarray([0.1, 0.95, 0.05]), skus), ["a"], k=2, beta=0.5
    )

    assert no_penalty[0].sku == "b_popular", "без штрафа побеждает популярный"
    assert with_penalty[0].sku == "c_rare", "штраф обязан его подвинуть"


def test_result_carries_category_and_is_sorted(artifact) -> None:
    art, _ = artifact
    out = companions.rank(art, art.skus[:1], k=4)
    assert all(isinstance(i, ItemScore) for i in out)
    assert [i.score for i in out] == sorted((i.score for i in out), reverse=True)
    assert all(i.category is not None for i in out)


def test_missing_model_b_returns_empty() -> None:
    art = _artifact_with(np.zeros((2, 2)), np.zeros(2), ["a", "b"])
    art.Z = None
    assert companions.rank(art, ["a"], k=3) == []
