"""Веса матрицы: затухание, счёт по чекам, а не по товарным строкам."""

from __future__ import annotations

import pytest

from recsys.matrix import (
    HALF_LIFE_WEEKS,
    build_category_matrix,
    build_receipt_sku_matrix,
    decay_weight,
    user_category_weights,
    week_index,
)
from recsys.types import Interaction


def _it(user: str, receipt: str, cat: str, week: str, sku: str | None = "s1") -> Interaction:
    return Interaction(user, receipt, cat, sku, week, 100.0)


def test_decay_halves_at_half_life() -> None:
    assert decay_weight(0.0) == pytest.approx(1.0)
    assert decay_weight(HALF_LIFE_WEEKS) == pytest.approx(0.5)
    assert decay_weight(2 * HALF_LIFE_WEEKS) == pytest.approx(0.25)


def test_future_interaction_does_not_outweigh_present() -> None:
    """Отрицательный возраст прижимается к нулю, вес не превышает 1."""
    assert decay_weight(-5.0) == pytest.approx(1.0)


def test_week_index_is_monotonic_across_year_boundary() -> None:
    assert week_index("2027-W01") > week_index("2026-W52")


def test_receipt_counted_once_regardless_of_line_count() -> None:
    """Десять йогуртов в одном чеке — это один поход за молочкой, а не десять."""
    many_lines = [_it("u1", "r1", "dairy", "2026-W10", sku=f"s{i}") for i in range(10)]
    one_line = [_it("u1", "r1", "dairy", "2026-W10")]
    a = build_category_matrix(many_lines, as_of_week="2026-W10")
    b = build_category_matrix(one_line, as_of_week="2026-W10")
    assert a.matrix.toarray() == pytest.approx(b.matrix.toarray())


def test_two_receipts_sum_their_weights() -> None:
    rows = [_it("u1", "r1", "dairy", "2026-W10"), _it("u1", "r2", "dairy", "2026-W10")]
    m = build_category_matrix(rows, as_of_week="2026-W10")
    assert float(m.matrix.toarray()[0, 0]) == pytest.approx(2.0)


def test_older_receipt_weighs_less() -> None:
    fresh = build_category_matrix([_it("u", "r", "dairy", "2026-W18")], as_of_week="2026-W18")
    old = build_category_matrix([_it("u", "r", "dairy", "2026-W10")], as_of_week="2026-W18")
    assert float(old.matrix.toarray()[0, 0]) < float(fresh.matrix.toarray()[0, 0])


def test_axes_are_sorted_for_determinism() -> None:
    rows = [
        _it("u2", "r1", "snacks", "2026-W10"),
        _it("u1", "r2", "dairy", "2026-W10"),
    ]
    m = build_category_matrix(rows, as_of_week="2026-W10")
    assert m.rows == ["u1", "u2"]
    assert m.cols == ["dairy", "snacks"]


def test_user_weights_match_matrix_row() -> None:
    """Инференс и обучение обязаны считать вес одной формулой."""
    rows = [_it("u1", "r1", "dairy", "2026-W10"), _it("u1", "r2", "snacks", "2026-W12")]
    m = build_category_matrix(rows, as_of_week="2026-W14")
    weights = user_category_weights(rows, as_of_week="2026-W14")
    dense = m.matrix.toarray()[0]
    for j, cat in enumerate(m.cols):
        assert weights[cat] == pytest.approx(float(dense[j]), rel=1e-6)


def test_receipt_sku_matrix_is_binary() -> None:
    rows = [_it("u1", "r1", "dairy", "2026-W10", sku="s1")] * 3
    m = build_receipt_sku_matrix(rows)
    assert m.matrix.toarray().max() == pytest.approx(1.0)


def test_empty_stream_yields_empty_bundle() -> None:
    m = build_category_matrix([])
    assert m.matrix.shape == (0, 0)
    assert m.cols == []
