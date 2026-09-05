"""Товарная таксономия: чтение `fixtures/data/categories.json` и веса для сэмплирования.

Категории — единый источник правды на весь проект, поэтому список не дублируется в
коде, а читается из данных. Вес категории для сегмента складывается из двух частей:

    вес = base_weight × segment_affinity.get(сегмент, 1.0)

`base_weight` — насколько категория популярна вообще, `segment_affinity` — насколько
она смещена к сегменту. Разделение нужно, чтобы «молочка» осталась массовой у всех, а
«подгузники» были массовыми только у родителей, и чтобы одно не приходилось выражать
через другое.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np

_DATA = Path(__file__).resolve().parents[3] / "fixtures" / "data" / "categories.json"

# Возрастные ограничения: этим сегментам 18+ не показываем и не генерируем.
_NO_RESTRICTED_SEGMENTS = frozenset({"parents_0_3"})


@dataclass(frozen=True)
class Category:
    id: str
    name: str
    group: str
    cadence: str
    base_weight: float
    margin_index: float
    age_restricted: bool
    segment_affinity: dict[str, float]

    def weight_for(self, segment: str) -> float:
        return self.base_weight * self.segment_affinity.get(segment, 1.0)


@lru_cache(maxsize=1)
def load_catalog() -> tuple[Category, ...]:
    raw = json.loads(_DATA.read_text(encoding="utf-8"))
    return tuple(
        Category(
            id=c["id"],
            name=c["name"],
            group=c["group"],
            cadence=c.get("cadence", "monthly"),
            base_weight=float(c["base_weight"]),
            margin_index=float(c.get("margin_index", 0.5)),
            age_restricted=bool(c.get("age_restricted", False)),
            segment_affinity=dict(c.get("segment_affinity", {})),
        )
        for c in raw["categories"]
    )


@lru_cache(maxsize=1)
def cadence_weeks() -> dict[str, int]:
    raw = json.loads(_DATA.read_text(encoding="utf-8"))
    return dict(raw["cadence_weeks"])


def category_ids() -> tuple[str, ...]:
    return tuple(c.id for c in load_catalog())


@lru_cache(maxsize=16)
def segment_weights(segment: str) -> tuple[tuple[str, float], ...]:
    """Категории и их веса для сегмента, отсортированные по id — детерминированно.

    18+ отсекается для сегментов из `_NO_RESTRICTED_SEGMENTS`: продукт не должен
    подсовывать алкоголь и табак родителям с детьми до трёх лет, даже на синтетике.
    """
    allow_restricted = segment not in _NO_RESTRICTED_SEGMENTS
    rows = [
        (c.id, c.weight_for(segment))
        for c in load_catalog()
        if allow_restricted or not c.age_restricted
    ]
    return tuple(sorted(rows))


def margin_index(category_id: str) -> float:
    for c in load_catalog():
        if c.id == category_id:
            return c.margin_index
    return 0.5


def cadence_of(category_id: str) -> int:
    """Типичный межпокупочный интервал категории в неделях."""
    weeks = cadence_weeks()
    for c in load_catalog():
        if c.id == category_id:
            return weeks.get(c.cadence, 4)
    return 4


# --- Справочник товаров ---------------------------------------------------- #
# SKU нужен стабильный и повторяющийся: на случайных идентификаторах модель
# «сопутствующих товаров» учиться не на чем — каждый товар встречается один раз,
# и матрица чек × товар вырождается в единичную.
SKUS_PER_CATEGORY = 14


@lru_cache(maxsize=1)
def sku_catalog() -> dict[str, tuple[str, ...]]:
    """`{категория: (sku, ...)}` — фиксированный справочник, одинаковый между прогонами."""
    return {
        c.id: tuple(f"sku-{c.id}-{i:02d}" for i in range(1, SKUS_PER_CATEGORY + 1))
        for c in load_catalog()
    }


@lru_cache(maxsize=1)
def sku_weights() -> tuple[float, ...]:
    """Веса позиций внутри категории: убывающие, как реальный спрос.

    Равномерный выбор дал бы полностью симметричную матрицу товаров, где ни у
    одного нет своего окружения. Перекос создаёт «ходовые» позиции и хвост.
    """
    w = [1.0 / (i + 1) ** 0.9 for i in range(SKUS_PER_CATEGORY)]
    total = sum(w)
    return tuple(x / total for x in w)


def skus_of(category_id: str) -> tuple[str, ...]:
    return sku_catalog().get(category_id, ())


# --- Родство категорий ------------------------------------------------------ #
# Нужно, чтобы освоение новой категории было предсказуемым событием. Если тянуть
# импульсную покупку равномерно из хвоста, «новая категория» становится
# случайностью, и recall@5 не поднимет никакая модель: предсказывать нечего.
# Родство выводится из самой таксономии, а не проставляется руками по 48×48.


_SEGMENTS = ("youth", "parents_0_3", "mature", "senior", "bad_habits")
_EMBED_NOISE_DIM = 6


@lru_cache(maxsize=1)
def category_embedding() -> dict[str, np.ndarray]:
    """Латентный вектор категории — низкоранговая структура вкуса.

    Первая версия считала родство как «общая группа + косинус по сегментам». Она
    не работала: бонус за группу доминировал, десятки категорий получали почти
    одинаковый балл, распределение выходило плоским, и потолок recall@5 упирался
    в 26 % независимо от резкости. Ничью нельзя разделить возведением в степень.

    Здесь вместо баллов — вектор из трёх частей: товарная группа, профиль по
    сегментам и детерминированный шум, дающий категориям индивидуальность внутри
    группы. Косинус между такими векторами меняется плавно, и у распределения
    появляется настоящая вариативность — та самая низкоранговая структура,
    которую ALS и рассчитан восстанавливать.
    """
    cats = load_catalog()
    groups = sorted({c.group for c in cats})
    g_ix = {g: i for i, g in enumerate(groups)}
    rng = np.random.default_rng(20260905)

    out: dict[str, np.ndarray] = {}
    for c in sorted(cats, key=lambda x: x.id):  # порядок фиксирован — детерминизм
        group_part = np.zeros(len(groups), dtype=np.float64)
        group_part[g_ix[c.group]] = 1.0
        seg_part = np.asarray(
            [c.segment_affinity.get(s, 1.0) for s in _SEGMENTS], dtype=np.float64
        )
        seg_part = seg_part / (np.linalg.norm(seg_part) or 1.0)
        noise = rng.normal(0.0, 1.0, size=_EMBED_NOISE_DIM)

        v = np.concatenate([group_part * 1.0, seg_part * 0.9, noise * 0.55])
        out[c.id] = v / (np.linalg.norm(v) or 1.0)
    return out


def user_vector(core: tuple[str, ...]) -> np.ndarray:
    """Вкус пользователя — центр его ядра в пространстве категорий."""
    emb = category_embedding()
    vecs = [emb[c] for c in core if c in emb]
    if not vecs:
        dim = len(next(iter(emb.values())))
        return np.zeros(dim)
    v = np.mean(vecs, axis=0)
    return v / (np.linalg.norm(v) or 1.0)


def affinity_to_core(candidate: str, core: tuple[str, ...]) -> float:
    """Косинус между категорией и центром ядра, сдвинутый в неотрицательную область."""
    emb = category_embedding()
    if candidate not in emb or not core:
        return 0.0
    return float((np.dot(emb[candidate], user_vector(core)) + 1.0) / 2.0)
