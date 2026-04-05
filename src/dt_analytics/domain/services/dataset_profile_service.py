"""Контракт сервиса профилирования наборов данных."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from dt_analytics.domain.entities import DatasetProfile, FeatureDefinition
from dt_analytics.domain.enums import LogicalFeatureType
from dt_analytics.shared import Result


@dataclass(frozen=True, slots=True)
class FeatureSnapshot:
    """
    Снимок метаданных признака, используемый как входные данные для логики профилирования.

    Эта структура намеренно приближена к доменной модели и отвязана от pandas.
    """

    name: str
    physical_dtype: str
    logical_type: LogicalFeatureType
    nullable: bool
    missing_count: int = 0
    unique_count: int | None = None
    ordinal_position: int = 0


@dataclass(frozen=True, slots=True)
class DatasetStructureSnapshot:
    """
    Снимок структуры набора данных, используемый как входные данные для сервиса профилирования.
    """

    row_count: int
    column_count: int
    missing_total: int = 0
    duplicate_count: int = 0
    memory_usage_bytes: int | None = None
    features: tuple[FeatureSnapshot, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class DatasetProfileResult:
    """
    Структурированный результат профилирования,
    возвращаемый сервисом профилирования набора данных.
    """

    features: tuple[FeatureDefinition, ...]
    profile: DatasetProfile


class DatasetProfileService(Protocol):
    """
    Контракт для построения доменных объектов профилированияs
    из «сырых» метаданных набора данных.
    """

    def profile(self, snapshot: DatasetStructureSnapshot) -> Result[DatasetProfileResult]:
        """Создать определения признаков и профиль набора данных из снимка структуры."""
        ...
