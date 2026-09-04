"""Временный пул Promo Studio явно отделён от одобренных маркетингом промо."""

from __future__ import annotations

import json
from pathlib import Path

from gaming_engine.promo import load_promos


ROOT = Path(__file__).resolve().parents[3]
PROMO_POOL = ROOT / "fixtures" / "data" / "promo_pool.json"


def test_demo_promos_are_explicitly_marked_pending_review() -> None:
    payload = json.loads(PROMO_POOL.read_text(encoding="utf-8"))

    assert payload["dataset_kind"] == "demo_seed"
    assert payload["approval_status"] == "pending_marketing_review"
    assert payload["demo_only"] is True
    assert payload["replace_before_pilot"] is True
    assert payload["promos"]

    ids = [promo["promo_id"] for promo in payload["promos"]]
    assert len(ids) == len(set(ids))

    for promo in payload["promos"]:
        assert promo["promo_id"].startswith("demo_")
        assert promo["title"]
        assert promo["description"]
        assert promo["approval_status"] == "pending_marketing_review"
        assert promo["demo_only"] is True
        assert promo["discount_type"] in {"percent", "fixed"}
        assert promo["discount_value"] > 0
        assert promo["margin_impact"] >= 0
        assert promo["objective"] in {
            "retain_category",
            "expand_categories",
            "trade_up",
            "basket_completion",
        }
        assert promo["shopping_missions"]
        assert promo["channels"]
        assert promo["target_metric"]


def test_demo_promos_remain_compatible_with_recommendation_engine() -> None:
    load_promos.cache_clear()
    loaded = load_promos()

    assert loaded
    assert all(promo.promo_id.startswith("demo_") for promo in loaded)
