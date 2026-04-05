"""Контракт сервиса ML‑экспериментов."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from dt_analytics.domain.entities import (
    ArtifactReference,
    EvaluationResult,
    ModelConfig,
    PreprocessingConfig,
    TrainingResult,
)
from dt_analytics.domain.enums import TaskType
from dt_analytics.domain.value_objects import DatasetId
from dt_analytics.shared import Result
from dt_analytics.shared.types import JsonDict


@dataclass(frozen=True, slots=True)
class PreparedDatasetSummary:
    """Краткое описание подготовленных данных, прошедших ML‑вход."""

    dataset_id: DatasetId
    row_count: int
    column_count: int
    target_column: str
    feature_columns: tuple[str, ...]
    train_row_count: int
    test_row_count: int


@dataclass(frozen=True, slots=True)
class ExperimentExecutionInput:
    """
    Контракт входных данных для выполнения ML‑эксперимента на уровне домена.

    Фактические данные представлены через `data_ref`.
    Конкретное значение `data_ref` определяется инфраструктурной реализацией
    и может ссылаться на путь к файлу, хэндл набора данных, ключ объекта в памяти и т.п.
    """

    dataset_id: DatasetId
    task_type: TaskType
    preprocessing_config: PreprocessingConfig
    model_config: ModelConfig
    data_ref: str
    runtime_metadata: JsonDict = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ExperimentExecutionOutput:
    """Структурированный результат выполнения ML‑эксперимента."""

    prepared_dataset: PreparedDatasetSummary
    training_result: TrainingResult
    evaluation_result: EvaluationResult
    artifacts: tuple[ArtifactReference, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)
    runtime_metadata: JsonDict = field(default_factory=dict)


class MlExperimentService(Protocol):
    """Контракт для выполнения эксперимента на основе дерева решений."""

    def run(self, request: ExperimentExecutionInput) -> Result[ExperimentExecutionOutput]:
        """Выполнить ML‑эксперимент и вернуть структурированные результаты."""
        ...
