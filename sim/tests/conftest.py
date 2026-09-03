"""Добавляем корень репозитория в sys.path, чтобы тесты паритета могли
импортировать пакет ``fixtures`` (демо-сценарий) наравне с ``gaming_sim``.
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
