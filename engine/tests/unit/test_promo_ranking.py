"""T069 / FR-025/FR-026/FR-027 — персональное ранжирование пула акций."""

from __future__ import annotations

from gaming_engine import Engine
from gaming_engine.challenge.features import UserFeatures
from gaming_engine.challenge.features import build as build_feats
from gaming_engine.contracts import PurchaseEvent
from gaming_engine.promo import rank_promos

from tests.conftest import make_event


def _feats(cats_by_week: list[tuple[str, list[str]]]) -> UserFeatures:
    evs = [
        PurchaseEvent.model_validate(
            make_event(f"r{i}", "u", timestamp=ts, saved_amount=150.0, categories=cats)
        )
        for i, (ts, cats) in enumerate(cats_by_week)
    ]
    return build_feats(evs, archetype="loyalist", avatar_level=1, as_of_week="2026-W12")


def test_recent_category_ranks_above_unseen() -> None:
    feats = _feats(
        [
            ("2026-03-09T10:00:00Z", ["hygiene"]),
            ("2026-03-11T10:00:00Z", ["hygiene"]),
            ("2026-03-16T10:00:00Z", ["hygiene"]),
        ]
    )
    ranked = rank_promos(feats, segment="parents_0_3")
    top = ranked[0]
    assert top.category == "hygiene"
    unseen_positions = [i for i, r in enumerate(ranked) if r.category not in {"hygiene"}]
    assert min(unseen_positions) > 0  # все незнакомые категории — ниже топа


def test_margin_breaks_ties_for_equal_relevance() -> None:
    # пустая история → cat_match и recency одинаковы у всех → решает маржинальность
    feats = _feats([])
    ranked = rank_promos(feats, segment="mature")
    margins = [r.margin_impact for r in ranked]
    assert margins == sorted(margins, reverse=True)


def test_empty_history_is_neutral_and_no_error() -> None:
    feats = _feats([])
    ranked = rank_promos(feats, segment="mature")
    assert ranked  # не пусто, без исключений
    scores = [r.rank_score for r in ranked]
    assert scores == sorted(scores, reverse=True)


def test_engine_rank_promos_end_to_end() -> None:
    eng = Engine()
    eng.register_user("u", archetype="loyalist", segment="parents_0_3")
    for i, ts in enumerate(["2026-03-02T10:00:00Z", "2026-03-05T10:00:00Z", "2026-03-09T10:00:00Z"]):
        eng.ingest(make_event(f"r{i}", "u", timestamp=ts, saved_amount=200.0, categories=["diapers"]))
    ranked = eng.rank_promos("u", "2026-03-12T00:00:00Z")
    assert ranked[0].category == "diapers"


def test_deterministic() -> None:
    feats = _feats([("2026-03-09T10:00:00Z", ["dairy"]), ("2026-03-11T10:00:00Z", ["dairy"])])
    assert [r.promo_id for r in rank_promos(feats, segment="parents_0_3")] == [
        r.promo_id for r in rank_promos(feats, segment="parents_0_3")
    ]
