"""T052 / SC-006, FR-031 — один и тот же скриптовый сценарий даёт совпадающие
ключевые числа в демо-фикстурах и при прогоне через gaming_sim (общий gaming_engine).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from gaming_sim.parity import check_against_fixtures, parity_numbers

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "fixtures" / "out"


def _rebuild_fixtures() -> None:
    subprocess.run(
        [sys.executable, "-m", "fixtures.build"], cwd=ROOT, check=True, capture_output=True
    )


def test_parity_key_numbers_match_fixtures() -> None:
    _rebuild_fixtures()
    ok, engine_numbers, fixture_numbers = check_against_fixtures(FIXTURES)
    assert ok, f"engine={engine_numbers} fixtures={fixture_numbers}"


def test_parity_numbers_are_stable() -> None:
    assert parity_numbers() == parity_numbers()


def test_fixture_files_present_and_valid_json() -> None:
    _rebuild_fixtures()
    for name in ("profile-screen.json", "challenge-screen.json"):
        json.loads((FIXTURES / name).read_text(encoding="utf-8"))
