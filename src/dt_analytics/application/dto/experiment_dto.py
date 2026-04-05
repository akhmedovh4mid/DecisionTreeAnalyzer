"""DTO, связанные с экспериментами приложения."""

from __future__ import annotations

from dataclasses import dataclass, field

from dt_analytics.application.dto.ml_experiment_dto import (
    ArtifactReferenceDto,
    EvaluationResultDto,
    MlExperimentResultDto,
    ModelConfigDto,
    PreprocessingConfigDto,
    TrainingResultDto,
)


@dataclass(frozen=True, slots=True)
class CreateExperimentRequest:
    """DTO запроса на создание нового эксперимента."""

    project_id: str
    dataset_id: str
    name: str
    preprocessing_config: PreprocessingConfigDto
    model_config: ModelConfigDto
    notes: str | None = None


@dataclass(frozen=True, slots=True)
class RunExperimentRequest:
    """DTO запроса на запуск существующего эксперимента."""

    project_id: str
    experiment_id: str
    data_ref_override: str | None = None
    runtime_metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class GetExperimentResultRequest:
    """DTO запроса на получение результатов эксперимента."""

    project_id: str
    experiment_id: str


@dataclass(frozen=True, slots=True)
class ExperimentDto:
    """DTO эксперимента для внешнего API / UI."""

    id: str
    project_id: str
    dataset_id: str
    name: str
    status: str
    notes: str | None
    started_at: str | None
    finished_at: str | None
    error_message: str | None
    preprocessing_config: PreprocessingConfigDto
    model_config: ModelConfigDto
    training_result: TrainingResultDto | None = None
    evaluation_result: EvaluationResultDto | None = None
    artifact_count: int = 0


@dataclass(frozen=True, slots=True)
class ExperimentRunResultDto:
    """DTO результата успешного запуска эксперимента."""

    experiment: ExperimentDto
    execution: MlExperimentResultDto


@dataclass(frozen=True, slots=True)
class ExperimentResultDto:
    """Подробный DTO, возвращаемый при чтении результата эксперимента."""

    experiment: ExperimentDto
    artifacts: tuple[ArtifactReferenceDto, ...] = ()
