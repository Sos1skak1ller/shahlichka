"""T053 / SC-007 — отчёт симуляции валиден по contracts/simulation-report.schema.json
и содержит блоки economy (roi, invariant_holds) и antifraud (precision/recall).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from gaming_sim import run_simulation
from gaming_sim.report import build_report

SCHEMA = (
    Path(__file__).resolve().parents[2]
    / "specs" / "001-gaming-layer" / "contracts" / "simulation-report.schema.json"
)


@pytest.fixture(scope="module")
def report() -> dict:
    return build_report(run_simulation(1000, weeks=4, seed=99), validate=False)


def test_report_validates_against_schema(report: dict) -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(report)


def test_report_has_economy_and_antifraud_blocks(report: dict) -> None:
    econ = report["economy"]
    assert set(econ) >= {"total_reward_cost", "margin_uplift", "roi", "invariant_holds"}
    assert econ["roi"] == round(econ["margin_uplift"] - econ["total_reward_cost"], 2)

    af = report["antifraud"]
    assert 0.0 <= af["fraud_class_precision"] <= 1.0
    assert 0.0 <= af["fraud_class_recall"] <= 1.0
    assert af["labeled_set_size"] >= 1


def test_precision_meets_sc004_target(report: dict) -> None:
    from gaming_engine import config

    assert report["antifraud"]["fraud_class_precision"] >= config.PRECISION_TARGET


def test_economy_invariant_holds_sc003(report: dict) -> None:
    assert report["economy"]["invariant_holds"] is True
    assert report["economy"]["total_reward_cost"] <= max(report["economy"]["margin_uplift"], 0.0) + 1e-6


def test_pilot_plan_lists_hypotheses_and_metrics(report: dict) -> None:
    pp = report["pilot_plan"]
    assert "H1" in pp["hypothesis"]
    assert "d7_return_no_push" in pp["primary_metrics"]
    assert "retention" in pp["guardrail_metrics"]
    assert "ROI" in pp["roi_formula"]


@pytest.mark.slow
def test_10k_population_runs_and_reports() -> None:
    report = build_report(run_simulation(10000, weeks=4, seed=1))
    assert report["population_size"] == 10000
    assert len(report["metrics"]) == 7
