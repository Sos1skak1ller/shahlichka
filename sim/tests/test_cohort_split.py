"""T051 / FR-032a — treatment и control берутся из одного и того же микса
популяции; различается только флаг gaming_layer_enabled. Отчёт валиден по схеме.
"""

from __future__ import annotations

from gaming_sim import run_simulation
from gaming_sim.report import build_report


def test_both_cohorts_reported_with_delta() -> None:
    result = run_simulation(1000, weeks=4, seed=42)
    assert set(result.cohort_metrics) == {"treatment", "control"}

    report = build_report(result)  # validate=True внутри → бросит при несоответствии схеме
    names = {m["name"] for m in report["metrics"]}
    assert {"d7_return_no_push", "purchase_frequency", "avg_check"} <= names
    assert {"retention", "referral_new_users", "basket_items", "session_length"} <= names
    for m in report["metrics"]:
        assert m["delta"] == round(m["treatment"] - m["control"], 4)


def test_treatment_shows_non_negative_primary_uplift() -> None:
    result = run_simulation(2000, weeks=4, seed=7)
    t = result.cohort_metrics["treatment"]
    c = result.cohort_metrics["control"]
    # игровой слой не должен снижать частоту покупок и возврат
    assert t["purchase_frequency"] >= c["purchase_frequency"]
    assert t["d7_return_no_push"] >= c["d7_return_no_push"] - 1e-9


def test_population_shared_between_cohorts() -> None:
    result = run_simulation(1500, weeks=3, seed=11)
    # один список профилей → один и тот же микс для обеих когорт
    assert result.population_size == 1500
    assert len(result.profiles) == 1500


def test_deterministic_run() -> None:
    a = build_report(run_simulation(1000, weeks=3, seed=5))
    b = build_report(run_simulation(1000, weeks=3, seed=5))
    assert a == b


def test_population_bounds_enforced() -> None:
    import pytest

    with pytest.raises(ValueError):
        run_simulation(999)
    with pytest.raises(ValueError):
        run_simulation(10001)
