"""Перечисление статусов эксперимента."""

from __future__ import annotations

from enum import StrEnum


class ExperimentStatus(StrEnum):
    """Стадии жизненного цикла эксперимента."""

    DRAFT = "draft"
    CONFIGURED = "configured"
    RUNNING = "running"
    TRAINED = "trained"
    EVALUATED = "evaluated"
    FAILED = "failed"
    ARCHIVED = "archived"
