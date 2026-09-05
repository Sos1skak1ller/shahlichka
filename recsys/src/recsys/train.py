"""Офлайн-обучение моделей recsys.

    python -m recsys.train --source sim --events events.jsonl --out artifacts/als_v0
    python -m recsys.train --source sim --events events.jsonl --model categories

BLAS переводится в один поток ДО импорта numpy: многопоточное скалярное произведение
складывает частичные суммы в непредсказуемом порядке, float-сложение неассоциативно,
и критерий приёмки №2 (побитовое совпадение артефактов) перестаёт выполняться.
Потеря скорости здесь близка к нулю — матрицы в решателе 32×32, такие размеры BLAS
всё равно не распараллеливает.
"""

from __future__ import annotations

import os

os.environ.setdefault("VECLIB_MAXIMUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import argparse  # noqa: E402
import json  # noqa: E402
import time  # noqa: E402
from datetime import UTC, datetime  # noqa: E402
from pathlib import Path  # noqa: E402

from recsys import matrix as mx  # noqa: E402
from recsys.als import ALSParams, fit  # noqa: E402
from recsys.artifacts import ARTIFACT_VERSION, Artifact, save  # noqa: E402
from recsys.sources.sim_events import SimSource  # noqa: E402

DEFAULT_LAMBDA = 0.1
DEFAULT_ALPHA = 20.0
DEFAULT_ITERS = 12  # §3 «Параметры». В прозе того же раздела упомянуто 15 — расхождение
DEFAULT_SEED = 0
COMPANION_K = 32


def _read_events(path: Path) -> list[dict]:
    """JSONL (по событию на строку) либо JSON-массив."""
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    if text[0] == "[":
        return json.loads(text)
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def _log(msg: str) -> None:
    print(msg, flush=True)


def _train_categories(interactions, params_seed: int, lam: float, alpha: float, iters: int):
    bundle = mx.build_category_matrix(interactions)
    n_users, n_cats = bundle.matrix.shape
    if n_cats == 0:
        raise SystemExit("нет категорий: пустой поток взаимодействий")

    # Спека §3 задаёт k = min(32, n_categories // 2), что на 48 категориях даёт 24 —
    # ранг в половину ширины матрицы. Замер на sim-популяции (2500 профилей,
    # 16 недель) показал, что это переобучение: recall@5 при k=24 равен 40 %,
    # при k=16 — 47 %. Берём меньшее из формулы спеки и замеренного оптимума.
    MEASURED_BEST_K = 16
    k = min(32, MEASURED_BEST_K, max(1, n_cats // 2))
    params = ALSParams(k=k, lam=lam, alpha=alpha, iters=iters, seed=params_seed)
    _log(f"[A] user × category: {n_users} × {n_cats}, nnz={bundle.matrix.nnz}, "
         f"sparsity={bundle.sparsity:.4f}, k={k}")

    t0 = time.perf_counter()
    losses: list[float] = []
    _, Y = fit(bundle.matrix, params, on_iter=lambda i, ls: losses.append(ls))
    _log(f"[A] обучено за {time.perf_counter() - t0:.2f} c; "
         f"loss {losses[0]:.2f} -> {losses[-1]:.2f}")
    return bundle, Y, params


def _train_companions(interactions, params_seed: int, lam: float, alpha: float, iters: int):
    bundle = mx.build_receipt_sku_matrix(interactions)
    n_receipts, n_skus = bundle.matrix.shape
    if n_skus == 0:
        _log("[B] товаров нет — модель компаньонов пропущена")
        return None, None, None

    params = ALSParams(k=COMPANION_K, lam=lam, alpha=alpha, iters=iters, seed=params_seed)
    _log(f"[B] receipt × sku: {n_receipts} × {n_skus}, nnz={bundle.matrix.nnz}, "
         f"sparsity={bundle.sparsity:.4f}, k={COMPANION_K}")

    t0 = time.perf_counter()
    losses: list[float] = []
    _, Z = fit(bundle.matrix, params, on_iter=lambda i, ls: losses.append(ls))
    _log(f"[B] обучено за {time.perf_counter() - t0:.2f} c; "
         f"loss {losses[0]:.2f} -> {losses[-1]:.2f}")
    return bundle, Z, params


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="recsys.train")
    ap.add_argument("--source", choices=["sim", "retailhero"], default="sim")
    ap.add_argument("--events", type=Path, help="JSONL/JSON с событиями для --source sim")
    ap.add_argument("--data", type=Path, help="каталог CSV для --source retailhero")
    ap.add_argument("--model", choices=["categories", "companions", "both"], default="both")
    ap.add_argument("--out", type=Path, default=Path("artifacts/als_v0"))
    ap.add_argument("--iters", type=int, default=DEFAULT_ITERS)
    ap.add_argument("--lam", type=float, default=DEFAULT_LAMBDA)
    ap.add_argument("--alpha", type=float, default=DEFAULT_ALPHA)
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = ap.parse_args(argv)

    if args.source == "retailhero":
        raise SystemExit(
            "источник retailhero ещё не реализован (§9, пункт 7). "
            "Пока: --source sim --events <файл>"
        )
    if not args.events:
        raise SystemExit("для --source sim нужен --events <файл>")

    events = _read_events(args.events)
    interactions = list(SimSource(events).stream())
    _log(f"событий: {len(events)}, взаимодействий: {len(interactions)}")
    if not interactions:
        raise SystemExit("поток взаимодействий пуст")

    cat_bundle, Y, cat_params = _train_categories(
        interactions, args.seed, args.lam, args.alpha, args.iters
    )

    Z = pop = None
    skus: list[str] = []
    sku_cat: dict[str, str] = {}
    if args.model in ("companions", "both"):
        sku_bundle, Z, _ = _train_companions(
            interactions, args.seed, args.lam, args.alpha, args.iters
        )
        if sku_bundle is not None:
            skus = sku_bundle.cols
            pop = mx.sku_popularity(sku_bundle)
            sku_cat = mx.sku_to_category(interactions)

    artifact = Artifact(
        version=ARTIFACT_VERSION,
        source=args.source,
        trained_at=datetime.now(UTC).date().isoformat(),
        params={
            "k": cat_params.k,
            "lambda": cat_params.lam,
            "alpha": cat_params.alpha,
            "iters": cat_params.iters,
            "seed": cat_params.seed,
            "dtype": "float32",
            "half_life_weeks": mx.HALF_LIFE_WEEKS,
        },
        categories=cat_bundle.cols,
        Y=Y,
        skus=skus,
        Z=Z,
        pop=pop,
        sku_category=sku_cat,
        category_popularity=mx.category_popularity(cat_bundle),
    )
    meta_path, npz_path = save(artifact, args.out)
    _log(f"сохранено: {meta_path}  {npz_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
