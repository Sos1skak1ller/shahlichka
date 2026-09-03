"""Когортный прогон: treatment (слой включён) и control (выключен) из одного
микса популяции (FR-032a). Тот же ``gaming_engine``, что и в демо (FR-031).
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path

import numpy as np
from gaming_engine import Engine, config
from gaming_engine.antifraud import precision_recall_on_labeled

from gaming_sim.generator import generate_week, iso, week_start
from gaming_sim.metrics import CohortAccumulator
from gaming_sim.population import (
    SyntheticUserProfile,
    observed_chain_mix,
    observed_segment_mix,
    sample_population,
)

FRAUD_EVERY = 50  # каждый 50-й профиль — синтетический фрод (≈2%)
ILLUSTRATIVE_MARGIN_PER_RECEIPT = 45.0  # ₽, иллюстративно (кейс не даёт — ТЗ 12)


@dataclass
class SimulationResult:
    run_id: str
    population_size: int
    weeks: int
    seed: int
    profiles: list[SyntheticUserProfile]
    cohort_metrics: dict[str, dict[str, float]]
    economy: dict[str, float | bool | int]
    antifraud: dict[str, float | int]
    engine_version: str = config.ENGINE_VERSION
    ranker_version: str = "logreg-v0"
    fraud_user_ids: set[str] = field(default_factory=set)

    def chain_mix(self) -> dict[str, float]:
        return observed_chain_mix(self.profiles)

    def segment_mix(self) -> dict[str, float]:
        return observed_segment_mix(self.profiles)


_ref_seq = 0


def _spawn_referral(eng: Engine, profile, week: int, rng, *, treatment: bool) -> None:
    """Синтетический реферал: приглашение → регистрация → (часто) покупка в окне.

    Ведёт полный путь через ReferralService, поэтому реферальные награды попадают
    в RewardLedger и учитываются в экономике отчёта (FR-023).
    """
    global _ref_seq
    _ref_seq += 1
    friend = f"{profile.user_id}-f{_ref_seq}"
    ws = week_start(week)
    r = eng.create_invite(profile.user_id, iso(ws + timedelta(days=1)))
    eng.register_referral(
        r.invitee_token,
        friend,
        iso(ws + timedelta(days=2)),
        invitee_device_hash=f"dev-{friend}",
        invitee_payment_hash=f"pay-{friend}",
    )
    if rng.random() < (0.65 if treatment else 0.5):
        eng.ingest(
            {
                "receipt_id": f"{friend}-r0",
                "user_id": friend,
                "store_code": "s-ref-001",
                "chain_code": profile.chain_code,
                "district_code": "d-000",
                "timestamp": iso(ws + timedelta(days=4)),
                "sku_list": ["sku-ref"],
                "category_list": ["baby_food"],
                "total_sum": 900.0,
                "saved_amount": 150.0,
                "device_id_hash": f"dev-{friend}",
                "payment_instrument_hash": f"pay-{friend}",
                "corrects_receipt_id": None,
            }
        )


def _engagement(eng: Engine, user_id: str) -> float:
    lvl = eng.avatar_state(user_id).level
    active = eng.challenges.active(user_id) is not None
    return min(1.0, lvl / 4.0 + (0.3 if active else 0.0))


def _run_cohort(
    profiles: list[SyntheticUserProfile],
    fraud_ids: set[str],
    weeks: int,
    seed: int,
    *,
    treatment: bool,
) -> tuple[CohortAccumulator, Engine]:
    rng = np.random.default_rng([seed, 1 if treatment else 0])
    eng = Engine(gaming_layer_enabled=treatment)
    for p in profiles:
        eng.register_user(
            p.user_id, archetype=p.archetype, segment=p.segment, chain_code=p.chain_code
        )

    acc = CohortAccumulator(weeks=weeks, n_users=len(profiles))
    last_week_start = week_start(weeks - 1)
    two_weeks_start = week_start(max(0, weeks - 2))

    for w in range(weeks):
        ws = week_start(w)
        for p in profiles:
            if treatment:
                eng.generate_challenge(p.user_id, iso(ws))
            engagement = _engagement(eng, p.user_id) if treatment else 0.0
            acc.observe_engagement(engagement)

            out = generate_week(
                p, w, rng,
                engagement=engagement,
                treatment=treatment,
                is_fraud=p.user_id in fraud_ids,
            )

            # US6: релевантная персональная акция слегка поднимает чек и корзину
            promo_cat: str | None = None
            if treatment and out.events:
                ranked = eng.rank_promos(p.user_id, out.events[0]["timestamp"])
                promo_cat = ranked[0].category if ranked else None

            for ev in out.events:
                if promo_cat and promo_cat in ev["category_list"]:
                    ev["total_sum"] = round(ev["total_sum"] * 1.08, 2)
                    ev["sku_list"] = ev["sku_list"] + [f"sku-promo-{promo_cat}"]
                eng.ingest(ev)
                ts = ev["timestamp"]
                acc.observe_receipt(
                    p.user_id,
                    check_sum=ev["total_sum"],
                    basket_items=len(ev["sku_list"]),
                    in_last_7d=ts >= iso(last_week_start),
                    in_last_2w=ts >= iso(two_weeks_start),
                )
            if out.referral_created:
                acc.referral_new_users += 1
                _spawn_referral(eng, p, w, rng, treatment=treatment)
        eng.tick(iso(ws + timedelta(days=7)))

    return acc, eng


def run_simulation(population_size: int, weeks: int = 4, seed: int = 42) -> SimulationResult:
    if not (1000 <= population_size <= 10000):
        raise ValueError("population_size вне диапазона 1–10 тыс. (US4)")
    global _ref_seq
    _ref_seq = 0
    rng = np.random.default_rng(seed)
    profiles = sample_population(population_size, rng)
    fraud_ids = {p.user_id for i, p in enumerate(profiles) if i % FRAUD_EVERY == 0}

    t_acc, t_eng = _run_cohort(profiles, fraud_ids, weeks, seed, treatment=True)
    c_acc, _c_eng = _run_cohort(profiles, fraud_ids, weeks, seed, treatment=False)

    t_metrics = t_acc.as_metrics()
    c_metrics = c_acc.as_metrics()

    summary = t_eng.run_summary()
    extra_receipts = t_acc.receipts - c_acc.receipts
    margin_uplift = extra_receipts * ILLUSTRATIVE_MARGIN_PER_RECEIPT
    reward_cost = float(summary["total_reward_cost"])
    roi = margin_uplift - reward_cost
    invariant_holds = bool(summary["economy_invariant_holds"]) and reward_cost <= max(margin_uplift, 0.0) + 1e-6

    labeled = [
        (fs.user_id in fraud_ids, fs.decision)
        for fs in t_eng.fraud_scores()
        if fs.entity_type == "receipt"
    ]
    precision, recall = precision_recall_on_labeled(labeled) if labeled else (1.0, 1.0)

    return SimulationResult(
        run_id=f"run-{population_size}-{weeks}w-s{seed}",
        population_size=population_size,
        weeks=weeks,
        seed=seed,
        profiles=profiles,
        cohort_metrics={"treatment": t_metrics, "control": c_metrics},
        economy={
            "total_reward_cost": round(reward_cost, 2),
            "margin_uplift": round(margin_uplift, 2),
            "roi": round(roi, 2),
            "invariant_holds": invariant_holds,
            "budget_rejections": int(summary["budget_rejections"]),
        },
        antifraud={
            "fraud_class_precision": round(precision, 4),
            "fraud_class_recall": round(recall, 4),
            "labeled_set_size": len(labeled),
            "review_auto_resolved": int(summary["antifraud_review_auto_resolved"]),
        },
        fraud_user_ids=fraud_ids,
    )


def _main() -> None:
    ap = argparse.ArgumentParser(description="Когортная симуляция игрового слоя Х5 Клуб")
    ap.add_argument("--population", type=int, required=True)
    ap.add_argument("--weeks", type=int, default=4)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    from gaming_sim.report import build_report  # локальный импорт: избегаем цикла

    result = run_simulation(args.population, args.weeks, args.seed)
    report = build_report(result)
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(text)


if __name__ == "__main__":
    _main()
