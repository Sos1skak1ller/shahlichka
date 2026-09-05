"""Синтетические события для тестов — маленькие, детерминированные, без внешних зависимостей.

Намеренно не импортируем `gaming_sim`: он тянет `gaming_engine`, а пакет обязан
оставаться самостоятельным (критерий приёмки №1).
"""

from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta

import pytest

BASE = datetime(2026, 1, 5, 10, 0, tzinfo=UTC)  # понедельник ISO-недели 2

# Устойчивые «вкусы»: пользователь тянется к своей группе категорий, поэтому модели
# есть что выучить. Пересечение по dairy — чтобы группы не были ортогональны.
TASTE_GROUPS = {
    "baby": ["baby_food", "diapers", "hygiene", "dairy"],
    "home": ["groceries", "household", "dairy"],
    "snack": ["snacks", "groceries", "dairy"],
}


def _iso(ts: datetime) -> str:
    return ts.isoformat().replace("+00:00", "Z")


def make_events(
    n_users: int = 60,
    weeks: int = 12,
    seed: int = 0,
    receipts_per_week: int = 2,
) -> list[dict]:
    """Небольшой поток чеков: у каждого пользователя своя группа категорий."""
    rng = random.Random(seed)
    groups = list(TASTE_GROUPS)
    events: list[dict] = []
    for u in range(n_users):
        group = groups[u % len(groups)]
        cats = TASTE_GROUPS[group]
        user_id = f"u{u:04d}"
        for w in range(weeks):
            for j in range(receipts_per_week):
                # Изредка берём категорию не из своей группы — иначе матрица
                # распадается на непересекающиеся блоки и задача вырождается.
                pool = cats if rng.random() < 0.85 else list(TASTE_GROUPS["home"])
                cat = rng.choice(pool)
                ts = BASE + timedelta(weeks=w, days=rng.randint(0, 4), hours=rng.randint(0, 8))
                rid = f"{user_id}-w{w}-{j}"
                events.append(
                    {
                        "receipt_id": rid,
                        "user_id": user_id,
                        "timestamp": _iso(ts),
                        "category_list": [cat],
                        "sku_list": [f"sku-{cat}-{rng.randint(1, 4)}"],
                        "total_sum": 700.0,
                        "corrects_receipt_id": None,
                    }
                )
    return events


@pytest.fixture(scope="session")
def events() -> list[dict]:
    return make_events()


@pytest.fixture(scope="session")
def small_events() -> list[dict]:
    return make_events(n_users=12, weeks=6, seed=1)


@pytest.fixture(scope="session")
def artifact(events, tmp_path_factory):
    """Обученный на маленьком батче артефакт — общий для тестов инференса."""
    from recsys import matrix as mx
    from recsys.als import ALSParams, fit
    from recsys.artifacts import ARTIFACT_VERSION, Artifact, save
    from recsys.sources.sim_events import SimSource

    interactions = list(SimSource(events).stream())
    cat = mx.build_category_matrix(interactions)
    params = ALSParams(k=min(32, max(1, len(cat.cols) // 2)), lam=0.1, alpha=20.0, iters=12, seed=0)
    _, Y = fit(cat.matrix, params)

    sku = mx.build_receipt_sku_matrix(interactions)
    _, Z = fit(sku.matrix, ALSParams(k=8, lam=0.1, alpha=20.0, iters=12, seed=0))

    art = Artifact(
        version=ARTIFACT_VERSION,
        source="sim",
        trained_at="2026-09-05",
        params={"k": params.k, "lambda": params.lam, "alpha": params.alpha,
                "iters": params.iters, "seed": params.seed, "dtype": "float32"},
        categories=cat.cols,
        Y=Y,
        skus=sku.cols,
        Z=Z,
        pop=mx.sku_popularity(sku),
        sku_category=mx.sku_to_category(interactions),
        category_popularity=mx.category_popularity(cat),
    )
    prefix = tmp_path_factory.mktemp("artifacts") / "als_test"
    save(art, prefix)
    return art, str(prefix)
