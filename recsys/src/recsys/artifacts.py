"""Сохранение и чтение артефакта модели: `<name>.meta.json` + `<name>.npz`.

Инференс читает артефакт один раз (`lru_cache`); обучение в рантайме запрещено
(критерий приёмки №6).

Про детерминизм записи. `np.savez` кладёт каждый массив в zip-запись, а zip хранит
время модификации — два прогона с одним сидом дали бы файлы, различающиеся в байтах
меток времени, и критерий приёмки №2 («побитово идентичные .npz») провалился бы на
ровном месте. Поэтому архив собирается вручную с фиксированной датой и без сжатия:
содержимое zip тогда зависит только от самих массивов.
"""

from __future__ import annotations

import io
import json
import zipfile
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import numpy as np

ARTIFACT_VERSION = "als-v0"
_FIXED_ZIP_DATE = (1980, 1, 1, 0, 0, 0)  # минимальная дата, допустимая в zip


@dataclass
class Artifact:
    """Обученные модели вместе с подписями осей."""

    version: str
    source: str
    trained_at: str
    params: dict
    categories: list[str]
    Y: np.ndarray  # (n_categories, k) — модель A
    skus: list[str] = field(default_factory=list)
    Z: np.ndarray | None = None  # (n_skus, k) — модель B
    pop: np.ndarray | None = None  # (n_skus,) — доля чеков с товаром
    sku_category: dict[str, str] = field(default_factory=dict)
    category_popularity: np.ndarray | None = None  # (n_categories,) — для cold start

    def model_version(self) -> str:
        return f"{self.version}/{self.source}"


def _write_deterministic_npz(path: Path, arrays: dict[str, np.ndarray]) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as zf:
        for name in sorted(arrays):  # фиксированный порядок записей
            buf = io.BytesIO()
            np.lib.format.write_array(buf, np.ascontiguousarray(arrays[name]), allow_pickle=False)
            info = zipfile.ZipInfo(filename=f"{name}.npy", date_time=_FIXED_ZIP_DATE)
            info.compress_type = zipfile.ZIP_STORED
            zf.writestr(info, buf.getvalue())


def save(artifact: Artifact, out_prefix: str | Path) -> tuple[Path, Path]:
    prefix = Path(out_prefix)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    npz_path = prefix.with_suffix(".npz")
    meta_path = prefix.with_suffix(".meta.json")

    arrays: dict[str, np.ndarray] = {"Y": artifact.Y}
    if artifact.Z is not None:
        arrays["Z"] = artifact.Z
    if artifact.pop is not None:
        arrays["pop"] = artifact.pop
    if artifact.category_popularity is not None:
        arrays["category_popularity"] = artifact.category_popularity
    _write_deterministic_npz(npz_path, arrays)

    meta = {
        "version": artifact.version,
        "source": artifact.source,
        "trained_at": artifact.trained_at,
        **artifact.params,
        "categories": artifact.categories,
        "skus": artifact.skus,
        "sku_category": artifact.sku_category,
    }
    meta_path.write_text(
        json.dumps(meta, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return meta_path, npz_path


def load(prefix: str | Path) -> Artifact:
    p = Path(prefix)
    meta = json.loads(p.with_suffix(".meta.json").read_text(encoding="utf-8"))
    with np.load(p.with_suffix(".npz")) as npz:
        Y = npz["Y"]
        Z = npz["Z"] if "Z" in npz.files else None
        pop = npz["pop"] if "pop" in npz.files else None
        cat_pop = npz["category_popularity"] if "category_popularity" in npz.files else None

    known = {"version", "source", "trained_at", "categories", "skus", "sku_category"}
    return Artifact(
        version=meta["version"],
        source=meta["source"],
        trained_at=meta["trained_at"],
        params={k: v for k, v in meta.items() if k not in known},
        categories=list(meta["categories"]),
        Y=Y,
        skus=list(meta.get("skus", [])),
        Z=Z,
        pop=pop,
        sku_category=dict(meta.get("sku_category", {})),
        category_popularity=cat_pop,
    )


@lru_cache(maxsize=4)
def load_cached(prefix: str) -> Artifact:
    """Артефакт читается с диска один раз на процесс."""
    return load(prefix)
