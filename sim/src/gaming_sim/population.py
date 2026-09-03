"""Сэмплирование популяции пропорционально долям сегментов по трём сетям
(§3.1 ТЗ, FR-032). Вес на «пользователей МП» уже заложен в segment_mix.json.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from gaming_sim.archetypes import ARCHETYPE_BY_SEGMENT

_MIX_PATH = (
    Path(__file__).resolve().parents[3] / "fixtures" / "data" / "segment_mix.json"
)


@dataclass(frozen=True)
class SyntheticUserProfile:
    user_id: str
    chain_code: str
    segment: str
    archetype: str


def _weighted_choice(rng: np.random.Generator, items: list[str], weights: list[float]) -> str:
    w = np.array(weights, dtype=float)
    w = w / w.sum()
    return items[int(rng.choice(len(items), p=w))]


def load_mix(path: Path | None = None) -> dict:
    return json.loads((path or _MIX_PATH).read_text(encoding="utf-8"))


def sample_population(
    n: int, rng: np.random.Generator, *, mix: dict | None = None
) -> list[SyntheticUserProfile]:
    mix = mix or load_mix()
    chains = list(mix["chain_weights"])
    chain_w = [mix["chain_weights"][c] for c in chains]

    profiles: list[SyntheticUserProfile] = []
    for i in range(n):
        chain = _weighted_choice(rng, chains, chain_w)
        seg_dist = mix["by_chain"][chain]
        segs = list(seg_dist)
        seg = _weighted_choice(rng, segs, [seg_dist[s] for s in segs])
        arch_dist = ARCHETYPE_BY_SEGMENT.get(seg, ARCHETYPE_BY_SEGMENT["mature"])
        archs = list(arch_dist)
        arch = _weighted_choice(rng, archs, [arch_dist[a] for a in archs])
        profiles.append(
            SyntheticUserProfile(
                user_id=f"sim-{i:06d}", chain_code=chain, segment=seg, archetype=arch
            )
        )
    return profiles


def observed_chain_mix(profiles: list[SyntheticUserProfile]) -> dict[str, float]:
    total = len(profiles) or 1
    out: dict[str, float] = {}
    for p in profiles:
        out[p.chain_code] = out.get(p.chain_code, 0.0) + 1.0 / total
    return {k: round(v, 4) for k, v in out.items()}


def observed_segment_mix(profiles: list[SyntheticUserProfile]) -> dict[str, float]:
    total = len(profiles) or 1
    out: dict[str, float] = {}
    for p in profiles:
        out[p.segment] = out.get(p.segment, 0.0) + 1.0 / total
    return {k: round(v, 4) for k, v in out.items()}
