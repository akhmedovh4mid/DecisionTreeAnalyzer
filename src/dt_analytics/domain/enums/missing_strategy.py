"""Перечисление стратегии обработки пропущенных значений."""

from __future__ import annotations

from enum import StrEnum


class MissingStrategy(StrEnum):
    """Поддерживаемые стратегии обработки пропущенных значений."""

    DROP_ROWS = "drop_rows"
    MEDIAN_MODE = "median_mode"
    CONSTANT = "constant"
