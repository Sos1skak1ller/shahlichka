"""Инвариант паритета demo ↔ sim (SC-006, FR-031): один и тот же скриптовый
сценарий даёт совпадающие ключевые числа в демо-фикстурах и при прогоне через
gaming_sim (тот же gaming_engine).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from fixtures.scenario import build_scenario, key_numbers


def parity_numbers() -> dict:
    return key_numbers(build_scenario())


def check_against_fixtures(fixtures_dir: Path) -> tuple[bool, dict, dict]:
    engine_numbers = parity_numbers()
    profile = json.loads((fixtures_dir / "profile-screen.json").read_text(encoding="utf-8"))
    fixture_numbers = {
        "total_saved_amount": profile["savings"]["total_saved_amount"],
        "avatar_level": profile["avatar"]["level"],
        "streak_count": profile["streak"]["streak_count"],
    }
    return engine_numbers == fixture_numbers, engine_numbers, fixture_numbers


def _main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixtures", type=Path, default=Path("fixtures/out"))
    args = ap.parse_args()
    ok, a, b = check_against_fixtures(args.fixtures)
    print("sim  :", a)
    print("fixt :", b)
    if not ok:
        print("PARITY MISMATCH", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    _main()
