"""Перечисление стратегии кодирования категориальных признаков."""

from __future__ import annotations

from enum import StrEnum


class CategoricalEncodingStrategy(StrEnum):
    """Поддерживаемые стратегии кодирования категориальных признаков."""

    ONE_HOT = "one_hot"
    ORDINAL = "ordinal"
