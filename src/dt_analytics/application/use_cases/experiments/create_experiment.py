"""Сценарий создания эксперимента."""

from __future__ import annotations

from dt_analytics.application.dto.experiment_dto import (
    CreateExperimentRequest,
    ExperimentDto,
)
from dt_analytics.application.dto.ml_experiment_dto import (
    ModelConfigDto,
    PreprocessingConfigDto,
)
from dt_analytics.application.mappers.ml_mapper import (
    to_domain_model_config,
    to_domain_preprocessing_config,
)
from dt_analytics.domain import DatasetId, Experiment, ProjectId
from dt_analytics.domain.repositories import (
    DatasetRepository,
    ExperimentRepository,
    ProjectRepository,
)
from dt_analytics.shared import Result


class CreateExperimentUseCase:
    """Создание нового эксперимента для существующего набора данных проекта."""

    def __init__(
        self,
        project_repository: ProjectRepository,
        dataset_repository: DatasetRepository,
        experiment_repository: ExperimentRepository,
    ) -> None:
        self._project_repository = project_repository
        self._dataset_repository = dataset_repository
        self._experiment_repository = experiment_repository

    def execute(self, request: CreateExperimentRequest) -> Result[ExperimentDto]:
        """Создать и сохранить сконфигурированный эксперимент."""
        project_id = ProjectId(request.project_id)
        dataset_id = DatasetId(request.dataset_id)

        project_result = self._project_repository.get_by_id(project_id)
        if project_result.is_failure:
            return Result.fail(
                code=project_result.error.code if project_result.error else "project_not_found",
                message=project_result.error.message
                if project_result.error
                else "Проект не найден.",
                details=project_result.error.details if project_result.error else None,
                warnings=list(project_result.warnings),
            )

        dataset_result = self._dataset_repository.get_by_id(
            project_id=project_id,
            dataset_id=dataset_id,
        )
        if dataset_result.is_failure:
            return Result.fail(
                code=dataset_result.error.code if dataset_result.error else "dataset_not_found",
                message=dataset_result.error.message
                if dataset_result.error
                else "Набор данных не найден.",
                details=dataset_result.error.details if dataset_result.error else None,
                warnings=list(dataset_result.warnings),
            )

        try:
            preprocessing_config = to_domain_preprocessing_config(request.preprocessing_config)
            model_config = to_domain_model_config(request.model_config)
            experiment = Experiment.create(
                dataset_id=dataset_id,
                preprocessing_config=preprocessing_config,
                model_config=model_config,
                name=request.name,
                notes=request.notes,
            )
        except ValueError as exc:
            return Result.fail(
                code="experiment_creation_failed",
                message="Не удалось построить конфигурацию эксперимента.",
                details=str(exc),
            )

        save_result = self._experiment_repository.add(
            project_id=project_id,
            experiment=experiment,
        )
        if save_result.is_failure:
            return Result.fail(
                code=save_result.error.code if save_result.error else "experiment_save_failed",
                message=save_result.error.message
                if save_result.error
                else "Не удалось сохранить эксперимент.",
                details=save_result.error.details if save_result.error else None,
                warnings=list(save_result.warnings),
            )

        saved_experiment = save_result.unwrap()
        return Result.ok(
            self._to_experiment_dto(
                project_id=request.project_id,
                experiment=saved_experiment,
            )
        )

    @staticmethod
    def _to_experiment_dto(project_id: str, experiment: Experiment) -> ExperimentDto:
        preprocessing_dto = PreprocessingConfigDto(
            id=experiment.preprocessing_config.id.value,
            target_column=experiment.preprocessing_config.target_column,
            feature_columns=tuple(experiment.preprocessing_config.feature_columns),
            excluded_columns=tuple(experiment.preprocessing_config.excluded_columns),
            missing_strategy=experiment.preprocessing_config.missing_strategy.value,
            categorical_encoding_strategy=(
                experiment.preprocessing_config.categorical_encoding_strategy.value
            ),
            drop_duplicates=experiment.preprocessing_config.drop_duplicates,
            test_size=experiment.preprocessing_config.test_size,
            random_state=experiment.preprocessing_config.random_state,
            stratify_enabled=experiment.preprocessing_config.stratify_enabled,
        )

        model_dto = ModelConfigDto(
            id=experiment.model_config.id.value,
            task_type=experiment.model_config.task_type.value,
            algorithm_code=experiment.model_config.algorithm_code,
            criterion=experiment.model_config.criterion,
            max_depth=experiment.model_config.max_depth,
            min_samples_split=experiment.model_config.min_samples_split,
            min_samples_leaf=experiment.model_config.min_samples_leaf,
            max_features=experiment.model_config.max_features,
            splitter=experiment.model_config.splitter,
            class_weight=experiment.model_config.class_weight,
            random_state=experiment.model_config.random_state,
            additional_params=experiment.model_config.additional_params,
        )

        return ExperimentDto(
            id=experiment.id.value,
            project_id=project_id,
            dataset_id=experiment.dataset_id.value,
            name=experiment.name,
            status=experiment.status.value,
            notes=experiment.notes,
            started_at=experiment.started_at.isoformat() if experiment.started_at else None,
            finished_at=experiment.finished_at.isoformat() if experiment.finished_at else None,
            error_message=experiment.error_message,
            preprocessing_config=preprocessing_dto,
            model_config=model_dto,
            training_result=None,
            evaluation_result=None,
            artifact_count=len(experiment.artifacts),
        )
