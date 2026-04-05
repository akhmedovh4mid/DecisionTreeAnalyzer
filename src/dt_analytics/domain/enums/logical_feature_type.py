"""Перечисление логических типов признаков."""

from __future__ import annotations

from enum import StrEnum


class LogicalFeatureType(StrEnum):
    """Логические типы, используемые внутри доменной модели."""

    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    TEXT = "text"
    UNKNOWN = "unknown"
