"""Критерий приёмки №1: пакет не зависит от gaming_engine.

Проверяется обходом AST, а не попыткой импорта: импорт бы прошёл, если пакет
установлен в то же окружение, и нарушение осталось бы незамеченным.
"""

from __future__ import annotations

import ast
from pathlib import Path

FORBIDDEN = ("gaming_engine", "gaming_sim")
SRC = Path(__file__).resolve().parents[1] / "src" / "recsys"


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module)
    return found


def test_package_does_not_import_engine() -> None:
    offenders: dict[str, set[str]] = {}
    for py in sorted(SRC.rglob("*.py")):
        bad = {
            m
            for m in _imported_modules(py)
            if any(m == f or m.startswith(f + ".") for f in FORBIDDEN)
        }
        if bad:
            offenders[str(py.relative_to(SRC))] = bad
    assert not offenders, f"recsys не должен зависеть от движка: {offenders}"


def test_src_tree_is_not_empty() -> None:
    # Страховка от «зелёного» теста при опечатке в пути.
    assert list(SRC.rglob("*.py")), f"не найдено ни одного модуля в {SRC}"
