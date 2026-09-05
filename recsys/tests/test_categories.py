"""Retrieval категорий: критерии приёмки №3, №4, №5."""

from __future__ import annotations

from tests.conftest import TASTE_GROUPS, make_events

from recsys import categories as cats
from recsys.matrix import user_category_weights
from recsys.sources.sim_events import SimSource
from recsys.types import CategoryScore

AS_OF = "2026-W16"


def _weights(events: list[dict], user_id: str) -> dict[str, float]:
    mine = [e for e in events if e["user_id"] == user_id]
    return user_category_weights(SimSource(mine).stream(), as_of_week=AS_OF)


def test_excluded_categories_never_appear(artifact, events) -> None:
    """Критерий №4: исключённые не в выдаче никогда, даже если кандидатов мало."""
    art, _ = artifact
    exclude = {"dairy", "groceries"}
    for user in ("u0000", "u0001", "u0002"):
        out = cats.rank(art, _weights(events, user), exclude=exclude, k=20)
        assert out, "выдача не должна быть пустой"
        assert not ({c.category for c in out} & exclude)


def test_excluding_everything_returns_empty_without_error(artifact, events) -> None:
    art, _ = artifact
    out = cats.rank(art, _weights(events, "u0000"), exclude=set(art.categories), k=5)
    assert out == []


def test_cold_start_is_non_empty_and_flagged(artifact) -> None:
    """Критерий №5: профиль без истории — непустой результат с is_fallback."""
    art, _ = artifact
    out = cats.rank(art, {}, exclude=set(), k=5)
    assert out
    assert all(c.is_fallback for c in out)


def test_cold_start_respects_exclude(artifact) -> None:
    art, _ = artifact
    out = cats.rank(art, {}, exclude={"dairy"}, k=5)
    assert "dairy" not in {c.category for c in out}


def test_unknown_categories_are_ignored_not_crashing(artifact) -> None:
    art, _ = artifact
    out = cats.rank(art, {"нет-такой-категории": 3.0}, exclude=set(), k=5)
    assert out
    assert all(c.is_fallback for c in out), "неизвестные веса = пустой вектор = fallback"


def test_ranking_is_deterministic(artifact, events) -> None:
    art, _ = artifact
    w = _weights(events, "u0000")
    a = cats.rank(art, w, exclude=set(), k=10)
    b = cats.rank(art, w, exclude=set(), k=10)
    assert a == b


def test_result_is_sorted_by_score_desc(artifact, events) -> None:
    art, _ = artifact
    out = cats.rank(art, _weights(events, "u0000"), exclude=set(), k=10)
    assert [c.score for c in out] == sorted((c.score for c in out), reverse=True)
    assert all(isinstance(c, CategoryScore) for c in out)


def test_recall_at_5_on_leave_last_week_out(artifact, events) -> None:
    """Критерий №3: спрятать последнюю неделю, проверить попадание в топ-5.

    Считается только по пользователям, у которых спрятанная категория не входит в
    exclude, — как и описано в спеке.
    """
    art, _ = artifact
    last_week = max(e["timestamp"] for e in events)[:10]

    hits = total = 0
    for user in sorted({e["user_id"] for e in events}):
        mine = [e for e in events if e["user_id"] == user]
        history = [e for e in mine if e["timestamp"][:10] < last_week]
        held_out = {c for e in mine if e["timestamp"][:10] >= last_week for c in e["category_list"]}
        if not history or not held_out:
            continue
        seen = {c for e in history for c in e["category_list"]}
        # exclude — то, что пользователь и так берёт; проверяем только новое
        target = held_out - seen
        if not target:
            continue
        w = user_category_weights(SimSource(history).stream(), as_of_week=AS_OF)
        out = cats.rank(art, w, exclude=seen, k=5)
        got = {c.category for c in out}
        total += 1
        hits += int(bool(target & got))

    if total == 0:
        # На таком маленьком батче «новых» категорий может не оказаться вовсе —
        # тогда метрика неинформативна, и молча зеленеть ей нельзя.
        import pytest

        pytest.skip("нет пользователей с новой категорией в последней неделе")
    recall = hits / total
    assert recall >= 0.6, f"recall@5 = {recall:.2f} на {total} профилях"


def test_make_events_is_deterministic() -> None:
    assert make_events(n_users=4, weeks=2, seed=3) == make_events(n_users=4, weeks=2, seed=3)
    assert set(TASTE_GROUPS) == {"baby", "home", "snack"}
