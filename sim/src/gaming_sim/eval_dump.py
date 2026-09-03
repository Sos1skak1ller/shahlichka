"""Выгрузка held-out профилей для экспертной разметки релевантности (SC-001/SC-002).

Прогоняет короткую симуляцию, затем для N случайных профилей выдаёт предложенный
челлендж / ранжирование акций в JSONL.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from gaming_engine import Engine

from gaming_sim.generator import generate_week, iso, week_start
from gaming_sim.population import sample_population


def _dump_challenges(n: int, seed: int, out: Path) -> int:
    rng = np.random.default_rng(seed)
    profiles = sample_population(max(1000, n * 25), rng)
    eng = Engine(gaming_layer_enabled=True)
    for p in profiles:
        eng.register_user(p.user_id, archetype=p.archetype, segment=p.segment, chain_code=p.chain_code)
    for w in range(3):
        for p in profiles:
            for ev in generate_week(p, w, rng, engagement=0.3, treatment=True, is_fraud=False).events:
                eng.ingest(ev)

    picks = rng.choice(len(profiles), size=min(n, len(profiles)), replace=False)
    lines = 0
    with out.open("w", encoding="utf-8") as fh:
        for idx in picks:
            p = profiles[int(idx)]
            ch = eng.generate_challenge(p.user_id, iso(week_start(3)))
            feats_top = eng.challenges  # noqa: F841 (только для контекста)
            rec = {
                "profile_id": p.user_id,
                "segment": p.segment,
                "archetype": p.archetype,
                "avatar_level": eng.avatar_state(p.user_id).level,
                "challenge_text": ch.text,
                "challenge_category": ch.category,
                "mechanic_type": ch.mechanic_type,
                "generated_by": ch.generated_by,
            }
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            lines += 1
    return lines


def _main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", choices=["challenge"], default="challenge")
    ap.add_argument("--n", type=int, default=40)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    written = _dump_challenges(args.n, args.seed, args.out)
    print(f"wrote {written} rows -> {args.out}")


if __name__ == "__main__":
    _main()
