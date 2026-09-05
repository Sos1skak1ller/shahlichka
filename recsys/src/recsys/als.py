"""ALS для implicit feedback (Hu, Koren, Volinsky 2008). Чистый numpy + scipy.

Модуль не знает слова «категория» — только матрица, факторы и линал.

Детерминизм здесь не пожелание, а критерий приёмки №2. Он держится на трёх вещах:
фиксированный сид инициализации, фиксированный порядок обхода строк и прямой
солвер `np.linalg.solve` вместо итеративного. Четвёртое условие — однопоточный
BLAS — задаётся снаружи, в `train.py`, до импорта numpy.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.sparse import csr_matrix

DTYPE = np.float32
ACC_DTYPE = np.float64  # накопление YtY и решение системы — в двойной точности


@dataclass(frozen=True)
class ALSParams:
    k: int = 32
    lam: float = 0.1
    alpha: float = 20.0
    iters: int = 12
    seed: int = 0


def _init_factors(n: int, k: int, rng: np.random.Generator) -> np.ndarray:
    return rng.normal(0.0, 0.01, size=(n, k)).astype(DTYPE)


def gramian(Y: np.ndarray) -> np.ndarray:
    """YᵀY в float64: суммирование идёт по всем строкам, точность там важна."""
    Yd = Y.astype(ACC_DTYPE, copy=False)
    return Yd.T @ Yd


def solve_vector(
    Y: np.ndarray,
    YtY: np.ndarray,
    idx: np.ndarray,
    conf: np.ndarray,
    lam: float,
) -> np.ndarray:
    """Один шаг ALS: вектор строки при фиксированной Y.

    `idx` — ненулевые позиции строки, `conf` — их confidence (1 + alpha·value).
    Предпочтение p на ненулевых равно 1, поэтому b = Yiᵀ·conf.

    Эта же функция — инференс: fold-in нового пользователя есть ровно один её вызов,
    отдельного кода для предсказания не существует.
    """
    k = Y.shape[1]
    if idx.size == 0:
        # Нет истории — система вырождается в λ·I·x = 0, то есть нулевой вектор.
        return np.zeros(k, dtype=DTYPE)
    Yi = Y[idx].astype(ACC_DTYPE, copy=False)
    c = conf.astype(ACC_DTYPE, copy=False)
    A = YtY + Yi.T @ ((c - 1.0)[:, None] * Yi) + lam * np.eye(k, dtype=ACC_DTYPE)
    b = Yi.T @ c
    return np.linalg.solve(A, b).astype(DTYPE)


def fold_in(
    Y: np.ndarray,
    YtY: np.ndarray,
    idx: np.ndarray,
    conf: np.ndarray,
    lam: float,
) -> np.ndarray:
    """Вектор пользователя, которого не было в обучении. Тот же solve_vector."""
    return solve_vector(Y, YtY, idx, conf, lam)


def _solve_all_rows(
    M: csr_matrix,
    Y: np.ndarray,
    lam: float,
    alpha: float,
) -> np.ndarray:
    """Пересчитать факторы всех строк при фиксированной Y.

    Строки независимы друг от друга, поэтому порядок обхода на результат не влияет —
    но он всё равно фиксирован (0..n-1), чтобы прогон был воспроизводим построчно.
    """
    YtY = gramian(Y)
    n_rows = M.shape[0]
    out = np.zeros((n_rows, Y.shape[1]), dtype=DTYPE)
    indptr, indices, data = M.indptr, M.indices, M.data
    for r in range(n_rows):
        lo, hi = indptr[r], indptr[r + 1]
        idx = indices[lo:hi]
        conf = 1.0 + alpha * data[lo:hi]
        out[r] = solve_vector(Y, YtY, idx, conf, lam)
    return out


def loss(M: csr_matrix, X: np.ndarray, Y: np.ndarray, lam: float, alpha: float) -> float:
    """Целевая функция HKV.

    Наивно она суммируется по всем парам (u, i) — это O(n·m) и на реальных размерах
    неприемлемо. Используем тождество:
        Σ_all c·(p − xy)²  =  Σ_nnz [c·(p − xy)² − (xy)²]  +  trace(XᵀX · YᵀY)
    второе слагаемое покрывает нули, где c = 1 и p = 0.
    """
    XtX = gramian(X)
    YtY = gramian(Y)
    total = float(np.sum(XtX * YtY))  # trace(XtX @ YtY) без материализации произведения

    indptr, indices, data = M.indptr, M.indices, M.data
    Xd = X.astype(ACC_DTYPE, copy=False)
    Yd = Y.astype(ACC_DTYPE, copy=False)
    for r in range(M.shape[0]):
        lo, hi = indptr[r], indptr[r + 1]
        if lo == hi:
            continue
        idx = indices[lo:hi]
        conf = 1.0 + alpha * data[lo:hi].astype(ACC_DTYPE)
        pred = Yd[idx] @ Xd[r]
        total += float(np.sum(conf * (1.0 - pred) ** 2 - pred**2))

    reg = lam * (float(np.sum(Xd**2)) + float(np.sum(Yd**2)))
    return total + reg


def fit(
    M: csr_matrix,
    params: ALSParams,
    *,
    on_iter: callable | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Обучить факторы строк и столбцов. Возвращает (X, Y).

    `on_iter(i, loss)` — необязательный колбэк для печати прогресса; сам loss
    считается только если колбэк передан, потому что он дороже самой итерации.
    """
    n_rows, n_cols = M.shape
    rng = np.random.default_rng(params.seed)
    # Порядок инициализации фиксирован: сначала X, потом Y — менять нельзя,
    # иначе тот же сид даст другие факторы.
    X = _init_factors(n_rows, params.k, rng)
    Y = _init_factors(n_cols, params.k, rng)

    Mt = M.T.tocsr()
    for it in range(params.iters):
        X = _solve_all_rows(M, Y, params.lam, params.alpha)
        Y = _solve_all_rows(Mt, X, params.lam, params.alpha)
        if on_iter is not None:
            on_iter(it, loss(M, X, Y, params.lam, params.alpha))
    return X, Y
