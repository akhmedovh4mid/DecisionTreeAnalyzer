"""Перечисление типов задач."""

from __future__ import annotations

from enum import StrEnum


class TaskType(StrEnum):
    """Поддерживаемые типы задач машинного обучения."""

    CLASSIFICATION = "classification"
    REGRESSION = "regression"
