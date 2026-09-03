"""T014 — модели gaming_engine.contracts синхронны с JSON Schema контракта.

Для каждой схемы: строим пример → валидируем JSON Schema (Draft 2020-12) →
парсим pydantic-моделью → дампим → снова валидируем схемой.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from gaming_engine import contracts as c

CONTRACTS_DIR = (
    Path(__file__).resolve().parents[3] / "specs" / "001-gaming-layer" / "contracts"
)


def _schema(name: str) -> dict:
    return json.loads((CONTRACTS_DIR / name).read_text(encoding="utf-8"))


SAMPLES: dict[str, tuple[str, type, dict]] = {
    "purchase-event": (
        "purchase-event.schema.json",
        c.PurchaseEvent,
        {
            "receipt_id": "r1",
            "user_id": "u1",
            "store_code": "s1",
            "chain_code": "TS5",
            "district_code": "d1",
            "timestamp": "2026-03-02T10:00:00Z",
            "sku_list": ["a"],
            "category_list": ["baby_food"],
            "total_sum": 1000.0,
            "saved_amount": 120.0,
            "device_id_hash": "dev",
            "payment_instrument_hash": "pay",
            "corrects_receipt_id": None,
        },
    ),
    "profile-screen": (
        "profile-screen.schema.json",
        c.ProfileScreenView,
        {
            "user_id": "u1",
            "display_name": None,
            "avatar": {
                "level": 1,
                "visual_stage": 2,
                "state": "progressing",
                "unlocked_customizations": ["starter_skin", "bronze_badge"],
                "last_transition_at": "2026-03-02T10:00:00Z",
            },
            "savings": {
                "total_saved_amount": 600.0,
                "current_threshold": 500.0,
                "next_threshold": 1500.0,
                "progress_ratio": 0.1,
            },
            "streak": {"streak_count": 1, "last_active_week": "2026-W10"},
        },
    ),
    "challenge-screen": (
        "challenge-screen.schema.json",
        c.ChallengeScreenView,
        {
            "user_id": "u1",
            "iso_week": "2026-W10",
            "challenge": {
                "challenge_id": "c1",
                "text": "Купите 3 раза детское питание до 16 марта",
                "mechanic_type": "category_repeat",
                "generated_by": "ml_ranker",
                "params": {"category": "baby_food", "n": 3, "deadline": "2026-03-16T00:00:00Z"},
                "progress": 1,
                "target": 3,
                "status": "active",
                "valid_to": "2026-03-16T00:00:00Z",
                "reward_amount": 30.0,
                "within_budget": True,
            },
            "notes": [],
        },
    ),
    "referral-screen": (
        "referral-screen.schema.json",
        c.ReferralScreenView,
        {
            "user_id": "u1",
            "invite_link": "https://x5.local/i/abc",
            "released_reward_total": 80.0,
            "budget_remaining_this_week": 10.0,
            "referrals": [
                {
                    "referral_id": "ref1",
                    "invitee_alias": "friend-1",
                    "status": "reward_released",
                    "invited_at": "2026-03-01T00:00:00Z",
                    "window_deadline": "2026-03-31T00:00:00Z",
                    "reward_amount": 40.0,
                    "block_reason": None,
                }
            ],
        },
    ),
    "simulation-report": (
        "simulation-report.schema.json",
        c.SimulationReport,
        {
            "run_id": "run-1",
            "population_size": 1000,
            "weeks": 4,
            "seed": 42,
            "engine_version": "0.1.0",
            "ranker_version": "rule-v0",
            "chain_mix": {"TS5": 0.4, "TSX": 0.35, "TSC": 0.25},
            "metrics": [
                {
                    "name": "d7_return_no_push",
                    "kind": "primary",
                    "treatment": 0.44,
                    "control": 0.40,
                    "delta": 0.04,
                    "period": "W1-W4",
                }
            ],
            "economy": {
                "total_reward_cost": 1000.0,
                "margin_uplift": 4000.0,
                "roi": 3000.0,
                "invariant_holds": True,
                "budget_rejections": 2,
            },
            "antifraud": {
                "fraud_class_precision": 0.93,
                "fraud_class_recall": 0.70,
                "labeled_set_size": 120,
                "review_auto_resolved": 5,
            },
            "pilot_plan": {
                "hypothesis": "H1",
                "primary_metrics": ["d7_return_no_push"],
                "guardrail_metrics": ["retention"],
                "roi_formula": "Δmargin − Σreward_cost",
            },
        },
    ),
}


@pytest.mark.parametrize("key", list(SAMPLES))
def test_sample_valid_against_schema(key: str) -> None:
    schema_file, _, sample = SAMPLES[key]
    Draft202012Validator.check_schema(_schema(schema_file))
    Draft202012Validator(_schema(schema_file)).validate(sample)


@pytest.mark.parametrize("key", list(SAMPLES))
def test_pydantic_roundtrip_matches_schema(key: str) -> None:
    schema_file, model, sample = SAMPLES[key]
    obj = model.model_validate(sample)
    dumped = json.loads(obj.model_dump_json())
    Draft202012Validator(_schema(schema_file)).validate(dumped)


def test_all_schema_files_have_a_sample() -> None:
    on_disk = {p.name for p in CONTRACTS_DIR.glob("*.schema.json")}
    covered = {sf for sf, _, _ in SAMPLES.values()}
    assert on_disk == covered
