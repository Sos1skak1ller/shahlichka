"""Критерий приёмки №2: обучение воспроизводимо бит в бит."""

from __future__ import annotations

import numpy as np
import pytest
from scipy.sparse import csr_matrix

from recsys.als import ALSParams, fit, fold_in, gramian, loss, solve_vector
from recsys.matrix import build_category_matrix
from recsys.sources.sim_events import SimSource

PARAMS = ALSParams(k=4, lam=0.1, alpha=20.0, iters=5, seed=0)


@pytest.fixture(scope="module")
def matrix(small_events) -> csr_matrix:
    return build_category_matrix(SimSource(small_events).stream()).matrix


def test_two_runs_same_seed_are_bitwise_equal(matrix) -> None:
    x1, y1 = fit(matrix, PARAMS)
    x2, y2 = fit(matrix, PARAMS)
    assert np.array_equal(x1, x2)
    assert np.array_equal(y1, y2)


def test_different_seed_changes_factors(matrix) -> None:
    """Иначе тест на равенство выше был бы бессмысленным."""
    _, y0 = fit(matrix, PARAMS)
    _, y1 = fit(matrix, ALSParams(k=4, lam=0.1, alpha=20.0, iters=5, seed=1))
    assert not np.array_equal(y0, y1)


def test_factors_are_float32(matrix) -> None:
    x, y = fit(matrix, PARAMS)
    assert x.dtype == np.float32
    assert y.dtype == np.float32


def test_loss_decreases(matrix) -> None:
    seen: list[float] = []
    fit(matrix, PARAMS, on_iter=lambda i, ls: seen.append(ls))
    assert seen[-1] < seen[0], f"loss не убывает: {seen}"


def test_empty_row_folds_into_zero_vector(matrix) -> None:
    _, Y = fit(matrix, PARAMS)
    v = fold_in(Y, gramian(Y), np.asarray([], dtype=np.int64), np.asarray([]), 0.1)
    assert not np.any(v)


def test_fold_in_reproduces_training_vector(matrix) -> None:
    """Fold-in — это тот же шаг ALS, поэтому для строки из обучения он обязан
    воспроизвести её фактор при той же Y."""
    X, Y = fit(matrix, PARAMS)
    YtY = gramian(Y)
    row = 0
    lo, hi = matrix.indptr[row], matrix.indptr[row + 1]
    idx = matrix.indices[lo:hi]
    conf = 1.0 + PARAMS.alpha * matrix.data[lo:hi]
    # X был посчитан при предыдущей Y, поэтому сравниваем с явным пересчётом.
    expected = solve_vector(Y, YtY, idx, conf, PARAMS.lam)
    got = fold_in(Y, YtY, idx, conf, PARAMS.lam)
    assert np.array_equal(expected, got)
    assert X.shape[1] == Y.shape[1]


def test_loss_is_finite(matrix) -> None:
    X, Y = fit(matrix, PARAMS)
    assert np.isfinite(loss(matrix, X, Y, PARAMS.lam, PARAMS.alpha))
