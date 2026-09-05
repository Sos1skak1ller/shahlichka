"""Публичный API: критерии приёмки №5, №6, №7."""

from __future__ import annotations

import time

import pytest
from tests.conftest import make_events

from recsys import api
from recsys.artifacts import load_cached
from recsys.types import CategoryScore

AS_OF = "2026-W16"


@pytest.fixture(autouse=True)
def _point_api_at_test_artifact(artifact, monkeypatch):
    _, prefix = artifact
    monkeypatch.setenv("RECSYS_ARTIFACT", prefix)
    load_cached.cache_clear()
    yield
    load_cached.cache_clear()


def _user_events(user_id: str = "u0000") -> list[dict]:
    return [e for e in make_events() if e["user_id"] == user_id]


def test_recommend_categories_returns_scores() -> None:
    out = api.recommend_categories(_user_events(), exclude=set(), k=3, as_of_week=AS_OF)
    assert out and len(out) <= 3
    assert all(isinstance(c, CategoryScore) for c in out)


def test_recommend_categories_honours_exclude() -> None:
    out = api.recommend_categories(
        _user_events(), exclude={"dairy", "baby_food"}, k=5, as_of_week=AS_OF
    )
    assert not ({c.category for c in out} & {"dairy", "baby_food"})


def test_empty_history_falls_back_without_raising() -> None:
    """Критерий №5."""
    out = api.recommend_categories([], exclude=set(), k=5, as_of_week=AS_OF)
    assert out
    assert all(c.is_fallback for c in out)


def test_corrections_are_not_treated_as_purchases() -> None:
    events = _user_events()
    corrections = [{**e, "corrects_receipt_id": "r-orig"} for e in events]
    out = api.recommend_categories(corrections, exclude=set(), k=5, as_of_week=AS_OF)
    assert all(c.is_fallback for c in out), "сторно не должно формировать вкус"


def test_inference_never_trains(monkeypatch) -> None:
    """Критерий №6: обучение в рантайме запрещено."""

    def _boom(*args, **kwargs):
        raise AssertionError("als.fit вызван на инференсе")

    monkeypatch.setattr("recsys.als.fit", _boom)
    out = api.recommend_categories(_user_events(), exclude=set(), k=5, as_of_week=AS_OF)
    assert out


def test_inference_is_fast() -> None:
    """Критерий №7: < 5 мс на пользователя. Здесь артефакт крошечный, поэтому
    порог взят с большим запасом — тест ловит алгоритмическую регрессию
    (например, случайное переобучение внутри вызова), а не абсолютную скорость."""
    events = _user_events()
    api.recommend_categories(events, exclude=set(), k=5, as_of_week=AS_OF)  # прогрев кэша

    t0 = time.perf_counter()
    runs = 20
    for _ in range(runs):
        api.recommend_categories(events, exclude=set(), k=5, as_of_week=AS_OF)
    per_call_ms = (time.perf_counter() - t0) / runs * 1000
    assert per_call_ms < 50, f"{per_call_ms:.1f} мс на вызов"


def test_model_version_is_reported() -> None:
    assert api.model_version() == "als-v0/sim"


def test_artifact_is_read_once(monkeypatch) -> None:
    calls = {"n": 0}
    real = api.load_cached

    def counting(prefix):
        calls["n"] += 1
        return real(prefix)

    monkeypatch.setattr(api, "load_cached", counting)
    for _ in range(3):
        api.recommend_categories(_user_events(), exclude=set(), k=3, as_of_week=AS_OF)
    # load_cached зовётся каждый раз, но кэшируется внутри — проверяем, что чтения
    # с диска не происходит повторно.
    assert calls["n"] == 3
    assert real.cache_info().hits >= 2
