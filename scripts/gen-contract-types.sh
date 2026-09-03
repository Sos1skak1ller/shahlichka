#!/usr/bin/env bash
# T006 — распространение контракта из specs/001-gaming-layer/contracts/*.schema.json.
#
# В окружении нет генератора JSON Schema → pydantic/TS, поэтому модели ведутся вручную:
#   - Python:  engine/src/gaming_engine/contracts.py
#   - TS/zod:  web/src/contract/types.ts
# Синхронность гарантируется round-trip тестом engine/tests/contract/test_schema_roundtrip.py
# и web/tests/client.test.ts (zod-валидация фикстур против скопированных схем).
#
# Этот скрипт: (1) валидирует сами схемы, (2) копирует их туда, где их читают рантайм-тесты.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/specs/001-gaming-layer/contracts"
WEB_DST="$ROOT/web/src/contract/schemas"
FIX_DST="$ROOT/fixtures/schema"

mkdir -p "$WEB_DST" "$FIX_DST"

python3 - "$SRC" <<'PY'
import json, sys, pathlib
src = pathlib.Path(sys.argv[1])
n = 0
for f in sorted(src.glob("*.schema.json")):
    json.loads(f.read_text())  # bare parse; full Draft check done by jsonschema in tests
    n += 1
    print(f"  ok  {f.name}")
print(f"validated {n} schema file(s)")
PY

cp "$SRC"/*.schema.json "$WEB_DST"/
cp "$SRC"/*.schema.json "$FIX_DST"/
echo "copied schemas -> web/src/contract/schemas/ and fixtures/schema/"
