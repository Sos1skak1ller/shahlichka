#!/usr/bin/env bash
# T007 — инвариант FR-031 / SC-006: тот же сценарий даёт те же ключевые числа
# в демо-фикстурах (fixtures/out/) и в прогоне через gaming_sim.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "[1/2] rebuild demo fixtures via engine ..."
uv run python -m fixtures.build

echo "[2/2] replay same scenario via gaming_sim and diff ..."
uv run python -m gaming_sim.parity --fixtures fixtures/out
echo "parity OK"
