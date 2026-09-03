"""Сборка отчёта симуляции по contracts/simulation-report.schema.json (FR-033).

Метрики приводятся по обеим когортам с delta = treatment − control; блок economy
содержит формулу ROI, блок antifraud — precision/recall на фрод-классе.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from jsonschema import Draft202012Validator

from gaming_sim.metrics import METRIC_KIND

if TYPE_CHECKING:
    from gaming_sim.runner import SimulationResult

_SCHEMA = (
    Path(__file__).resolve().parents[3]
    / "specs"
    / "001-gaming-layer"
    / "contracts"
    / "simulation-report.schema.json"
)


def build_report(result: SimulationResult, *, validate: bool = True) -> dict:
    t = result.cohort_metrics["treatment"]
    c = result.cohort_metrics["control"]

    metrics = []
    for name, kind in METRIC_KIND.items():
        tv, cv = float(t[name]), float(c[name])
        metrics.append(
            {
                "name": name,
                "kind": kind,
                "treatment": tv,
                "control": cv,
                "delta": round(tv - cv, 4),
                "period": f"W1-W{result.weeks}",
            }
        )

    report = {
        "run_id": result.run_id,
        "population_size": result.population_size,
        "weeks": result.weeks,
        "seed": result.seed,
        "engine_version": result.engine_version,
        "ranker_version": result.ranker_version,
        "chain_mix": result.chain_mix(),
        "metrics": metrics,
        "economy": {
            "total_reward_cost": float(result.economy["total_reward_cost"]),
            "margin_uplift": float(result.economy["margin_uplift"]),
            "roi": float(result.economy["roi"]),
            "invariant_holds": bool(result.economy["invariant_holds"]),
            "budget_rejections": int(result.economy["budget_rejections"]),
        },
        "antifraud": {
            "fraud_class_precision": float(result.antifraud["fraud_class_precision"]),
            "fraud_class_recall": float(result.antifraud["fraud_class_recall"]),
            "labeled_set_size": int(result.antifraud["labeled_set_size"]),
            "review_auto_resolved": int(result.antifraud["review_auto_resolved"]),
        },
        "pilot_plan": {
            "hypothesis": (
                "Персональный игровой слой на сегменте «родители с детьми до 3 лет» "
                "повышает частоту покупок и возврат без дополнительных push-скидок (H1–H3)."
            ),
            "primary_metrics": [n for n, k in METRIC_KIND.items() if k == "primary"],
            "guardrail_metrics": [n for n, k in METRIC_KIND.items() if k == "guardrail"],
            "roi_formula": "ROI = Δmargin(treatment − control) − Σ стоимость выданных наград",
        },
    }

    if validate:
        schema = json.loads(_SCHEMA.read_text(encoding="utf-8"))
        Draft202012Validator(schema).validate(report)
    return report
