"""T050 / US4 сценарий 1 — сгенерированная популяция воспроизводит заданный микс
сегментов и сетей из §3.1 в пределах допустимого отклонения.
"""

from __future__ import annotations

import numpy as np
import pytest

from gaming_sim.population import (
    load_mix,
    observed_chain_mix,
    observed_segment_mix,
    sample_population,
)

TOLERANCE = 0.05


@pytest.mark.parametrize("n", [1000, 10000])
def test_chain_mix_matches_target(n: int) -> None:
    mix = load_mix()
    rng = np.random.default_rng(123)
    profiles = sample_population(n, rng, mix=mix)
    observed = observed_chain_mix(profiles)
    for chain, target in mix["chain_weights"].items():
        assert abs(observed.get(chain, 0.0) - target) <= TOLERANCE, (chain, observed)


def test_segment_mix_within_convex_hull_of_chains() -> None:
    mix = load_mix()
    rng = np.random.default_rng(7)
    profiles = sample_population(10000, rng, mix=mix)
    observed = observed_segment_mix(profiles)
    for seg in mix["segments"]:
        lo = min(mix["by_chain"][c][seg] for c in mix["by_chain"])
        hi = max(mix["by_chain"][c][seg] for c in mix["by_chain"])
        assert lo - TOLERANCE <= observed.get(seg, 0.0) <= hi + TOLERANCE, (seg, observed.get(seg))


def test_parents_segment_is_well_represented() -> None:
    rng = np.random.default_rng(1)
    profiles = sample_population(5000, rng)
    share = observed_segment_mix(profiles).get("parents_0_3", 0.0)
    # целевой сегмент должен быть заметной долей (§3.1: ~26–28% среди МП)
    assert share >= 0.18


def test_deterministic_for_same_seed() -> None:
    a = sample_population(2000, np.random.default_rng(42))
    b = sample_population(2000, np.random.default_rng(42))
    assert [p.user_id + p.segment + p.archetype for p in a] == [
        p.user_id + p.segment + p.archetype for p in b
    ]
