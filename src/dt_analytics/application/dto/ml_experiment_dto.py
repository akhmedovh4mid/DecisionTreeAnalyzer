"""DTO‑модели для рабочего процесса ML‑экспериментов."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from dt_analytics.domain.enums import TaskType
from dt_analytics.shared.types import JsonDict


@dataclass(frozen=True, slots=True)
class PreprocessingConfigDto:
    """Конфигурация предобработки на уровне приложения."""

    id: str | None
    target_column: str
    feature_columns: tuple[str, ...]
    excluded_columns: tuple[str, ...] = ()
    missing_strategy: str = "median_mode"
    categorical_encoding_strategy: str = "one_hot"
    drop_duplicates: bool = False
    test_size: float = 0.2
    random_state: int = 42
    stratify_enabled: bool = True


@dataclass(frozen=True, slots=True)
class ModelConfigDto:
    """Конфигурация дерева решений на уровне приложения."""

    id: str | None
    task_type: str
    algorithm_code: str
    criterion: str = "gini"
    max_depth: int | None = None
    min_samples_split: int = 2
    min_samples_leaf: int = 1
    max_features: str | None = None
    splitter: str = "best"
    class_weight: str | None = None
    random_state: int = 42
    additional_params: JsonDict = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RunMlExperimentRequest:
    """
    DTO запроса на запуск ML‑эксперимента.

    `data_ref` — инфраструктурная ссылка на подготовленные данные.
    В MVP это может быть путь к файлу или любой другой непрозрачный идентификатор.
    """

    project_id: str
    dataset_id: str
    experiment_name: str
    task_type: str
    preprocessing_config: PreprocessingConfigDto
    model_config: ModelConfigDto
    data_ref: str
    notes: str | None = None
    runtime_metadata: JsonDict = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class PreparedDatasetSummaryDto:
    """Сводка по подготовленному набору данных после предобработки и разбиения."""

    dataset_id: str
    row_count: int
    column_count: int
    target_column: str
    feature_columns: tuple[str, ...]
    train_row_count: int
    test_row_count: int


@dataclass(frozen=True, slots=True)
class TrainingResultDto:
    """Результат обучения модели на уровне приложения."""

    id: str
    train_score: float | None
    tree_depth: int
    leaf_count: int
    node_count: int
    feature_importance: JsonDict = field(default_factory=dict)
    class_labels: tuple[str, ...] = ()
    created_at: str = ""


@dataclass(frozen=True, slots=True)
class EvaluationResultDto:
    """Результат оценки модели на уровне приложения."""

    id: str
    accuracy: float | None
    precision_weighted: float | None
    recall_weighted: float | None
    f1_weighted: float | None
    confusion_matrix: tuple[tuple[int, ...], ...] = ()
    classification_report: JsonDict = field(default_factory=dict)
    created_at: str = ""


@dataclass(frozen=True, slots=True)
class ArtifactReferenceDto:
    """Ссылка на артефакт на уровне приложения."""

    id: str
    artifact_type: str
    file_path: Path
    metadata: JsonDict = field(default_factory=dict)
    created_at: str = ""


@dataclass(frozen=True, slots=True)
class MlExperimentResultDto:
    """Итоговый DTO результата ML‑эксперимента для внешнего/API‑уровня."""

    prepared_dataset: PreparedDatasetSummaryDto
    training_result: TrainingResultDto
    evaluation_result: EvaluationResultDto
    artifacts: tuple[ArtifactReferenceDto, ...] = ()
    warnings: tuple[str, ...] = ()
    runtime_metadata: JsonDict = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ExperimentSummaryDto:
    """Компактный DTO‑сводка эксперимента для списков и обзорных виджетов."""

    project_id: str
    dataset_id: str
    experiment_name: str
    task_type: str
    algorithm_code: str
    target_column: str
    feature_count: int


def normalize_task_type(value: str) -> TaskType:
    """Преобразовать строковое значение в доменный тип TaskType."""
    return TaskType(value)
