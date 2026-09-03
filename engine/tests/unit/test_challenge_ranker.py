"""T027 — ранжирование/выбор челленджа: персональность, детерминизм, fallback,
cooldown пула, anti-fatigue.
"""

from __future__ import annotations

from gaming_engine import Engine

from tests.conftest import make_event


def _feed(eng: Engine, user: str, weeks: list[tuple[str, float, list[str]]]) -> None:
    for i, (ts, saved, cats) in enumerate(weeks):
        eng.ingest(make_event(f"{user}-r{i}", user, timestamp=ts, saved_amount=saved, categories=cats))


def test_different_history_yields_different_challenge() -> None:
    a = Engine()
    a.register_user("a", archetype="loyalist", segment="parents_0_3")
    _feed(a, "a", [("2026-03-02T10:00:00Z", 200.0, ["baby_food"]),
                   ("2026-03-04T10:00:00Z", 200.0, ["baby_food"]),
                   ("2026-03-06T10:00:00Z", 150.0, ["baby_food"])])

    b = Engine()
    b.register_user("b", archetype="loyalist", segment="parents_0_3")
    _feed(b, "b", [("2026-03-02T10:00:00Z", 200.0, ["diapers"]),
                   ("2026-03-04T10:00:00Z", 200.0, ["hygiene"]),
                   ("2026-03-06T10:00:00Z", 150.0, ["diapers"])])

    ca = a.generate_challenge("a", "2026-03-09T09:00:00Z")
    cb = b.generate_challenge("b", "2026-03-09T09:00:00Z")

    assert ca.generated_by == "ml_ranker"
    assert ca.category == "baby_food"
    assert cb.category in {"diapers", "hygiene"}
    assert ca.category != cb.category


def test_challenge_category_comes_from_user_history() -> None:
    eng = Engine()
    eng.register_user("u", archetype="cross_shopper", segment="parents_0_3")
    _feed(eng, "u", [("2026-03-02T10:00:00Z", 300.0, ["dairy"]),
                     ("2026-03-05T10:00:00Z", 300.0, ["dairy"])])
    ch = eng.generate_challenge("u", "2026-03-09T10:00:00Z")
    assert ch.category == "dairy"


def test_deterministic_repeat() -> None:
    def run() -> tuple[str, str, int]:
        eng = Engine()
        eng.register_user("u", archetype="loyalist", segment="parents_0_3")
        _feed(eng, "u", [("2026-03-02T10:00:00Z", 250.0, ["baby_food"]),
                         ("2026-03-05T10:00:00Z", 250.0, ["baby_food"])])
        c = eng.generate_challenge("u", "2026-03-09T10:00:00Z")
        return c.template_id, c.category, c.target

    assert run() == run()


def test_cold_start_fallback() -> None:
    eng = Engine()
    eng.register_user("u", archetype="sleeper", segment="parents_0_3")
    ch = eng.generate_challenge("u", "2026-03-02T10:00:00Z")
    assert ch.generated_by == "fallback"
    assert "cold_start_fallback" in ch.notes


def test_single_active_challenge_per_user() -> None:
    eng = Engine()
    eng.register_user("u", archetype="loyalist", segment="parents_0_3")
    _feed(eng, "u", [("2026-03-02T10:00:00Z", 250.0, ["baby_food"])])
    c1 = eng.generate_challenge("u", "2026-03-09T10:00:00Z")
    c2 = eng.generate_challenge("u", "2026-03-16T10:00:00Z")  # новая неделя
    assert c1.challenge_id == c2.challenge_id  # активный не заменяется


def test_anti_fatigue_switch_after_n_ignored() -> None:
    from gaming_engine import config

    eng = Engine()
    eng.register_user("u", archetype="loyalist", segment="parents_0_3")
    _feed(eng, "u", [("2026-03-02T10:00:00Z", 250.0, ["baby_food"]),
                     ("2026-03-05T10:00:00Z", 250.0, ["baby_food"])])

    week_ts = ["2026-03-09T10:00:00Z", "2026-03-16T10:00:00Z", "2026-03-23T10:00:00Z",
               "2026-03-30T10:00:00Z", "2026-04-06T10:00:00Z"]
    first = eng.generate_challenge("u", week_ts[0])
    first_mech = first.mechanic_type
    # «игнорируем» N челленджей: помечаем истёкшими с нулевым прогрессом
    for i in range(1, config.ANTI_FATIGUE_N + 1):
        eng.challenges.active("u").status = "expired"
        eng.generate_challenge("u", week_ts[i])
    switched = eng.challenges.latest_visible("u")
    assert "anti_fatigue_switch" in switched.notes
    assert switched.mechanic_type != first_mech
