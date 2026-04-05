"""Перечисление ролей признака."""

from __future__ import annotations

from enum import StrEnum


class FeatureRole(StrEnum):
    """Семантическая роль столбца в наборе данных."""

    FEATURE = "feature"
    TARGET = "target"
    EXCLUDED = "excluded"
    IDENTIFIER = "identifier"
