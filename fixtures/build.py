"""Собрать экранные JSON-фикстуры из демо-сценария и провалидировать их против
JSON Schema контракта. Запуск: ``uv run python -m fixtures.build``.
"""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

from fixtures.scenario import build_scenario

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "fixtures" / "out"
SCHEMA = ROOT / "specs" / "001-gaming-layer" / "contracts"


def _validate(payload: dict, schema_name: str) -> None:
    schema = json.loads((SCHEMA / schema_name).read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(payload)


def build() -> list[str]:
    OUT.mkdir(parents=True, exist_ok=True)
    scn = build_scenario()
    written: list[str] = []

    # --- Экран 1: профиль / аватар (US1) --------------------------------- #
    profile = scn.engine.get_profile_view(scn.user_id).model_dump(mode="json")
    _validate(profile, "profile-screen.schema.json")
    (OUT / "profile-screen.json").write_text(
        json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    written.append("profile-screen.json")

    # --- Экран 2: челлендж (US2) ---------------------------------------- #
    challenge = scn.engine.get_challenge_view(scn.user_id).model_dump(mode="json")
    _validate(challenge, "challenge-screen.schema.json")
    (OUT / "challenge-screen.json").write_text(
        json.dumps(challenge, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    written.append("challenge-screen.json")

    # --- Экран 3: реферальная программа (US5) --------------------------- #
    referral = scn.engine.get_referral_view(scn.user_id).model_dump(mode="json")
    _validate(referral, "referral-screen.schema.json")
    (OUT / "referral-screen.json").write_text(
        json.dumps(referral, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    written.append("referral-screen.json")

    return written


if __name__ == "__main__":
    for name in build():
        print(f"wrote fixtures/out/{name}")
