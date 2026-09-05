"""Артефакт: побитовая воспроизводимость записи и корректный round-trip."""

from __future__ import annotations

import numpy as np

from recsys.artifacts import ARTIFACT_VERSION, Artifact, load, save


def _artifact() -> Artifact:
    rng = np.random.default_rng(0)
    return Artifact(
        version=ARTIFACT_VERSION,
        source="sim",
        trained_at="2026-09-05",
        params={"k": 3, "lambda": 0.1, "alpha": 20.0, "iters": 5, "seed": 0, "dtype": "float32"},
        categories=["dairy", "groceries", "snacks"],
        Y=rng.normal(size=(3, 3)).astype(np.float32),
        skus=["s1", "s2"],
        Z=rng.normal(size=(2, 3)).astype(np.float32),
        pop=np.asarray([0.4, 0.1], dtype=np.float32),
        sku_category={"s1": "dairy", "s2": "snacks"},
        category_popularity=np.asarray([0.9, 0.5, 0.2], dtype=np.float32),
    )


def test_npz_bytes_are_identical_across_saves(tmp_path) -> None:
    """np.savez кладёт в zip текущее время — тогда два прогона различались бы
    в байтах метки. Запись обязана зависеть только от массивов."""
    art = _artifact()
    _, a = save(art, tmp_path / "one")
    _, b = save(art, tmp_path / "two")
    assert a.read_bytes() == b.read_bytes()


def test_meta_is_stable_across_saves(tmp_path) -> None:
    art = _artifact()
    m1, _ = save(art, tmp_path / "one")
    m2, _ = save(art, tmp_path / "two")
    assert m1.read_text(encoding="utf-8") == m2.read_text(encoding="utf-8")


def test_round_trip_preserves_everything(tmp_path) -> None:
    art = _artifact()
    save(art, tmp_path / "a")
    got = load(tmp_path / "a")

    assert got.version == art.version
    assert got.source == art.source
    assert got.categories == art.categories
    assert got.skus == art.skus
    assert got.sku_category == art.sku_category
    assert got.params["k"] == art.params["k"]
    assert np.array_equal(got.Y, art.Y)
    assert np.array_equal(got.Z, art.Z)
    assert np.array_equal(got.pop, art.pop)
    assert np.array_equal(got.category_popularity, art.category_popularity)
    assert got.model_version() == f"{ARTIFACT_VERSION}/sim"


def test_categories_only_artifact_round_trips(tmp_path) -> None:
    """Модель B необязательна: --model categories не должен ломать чтение."""
    art = _artifact()
    art.Z = None
    art.pop = None
    art.skus = []
    save(art, tmp_path / "a")
    got = load(tmp_path / "a")
    assert got.Z is None
    assert got.pop is None
    assert got.skus == []
