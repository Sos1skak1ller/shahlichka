"""Единый интерфейс источника данных.

Стриминг выбран, чтобы 45,8 млн строк RetailHero и 10 тыс. синтетических профилей
шли ровно одним путём: `matrix.build()` не знает, откуда пришли взаимодействия.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Protocol, runtime_checkable

from recsys.types import Interaction


@runtime_checkable
class Source(Protocol):
    def stream(self) -> Iterator[Interaction]: ...
