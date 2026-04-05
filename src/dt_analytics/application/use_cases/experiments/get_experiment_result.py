"""Сценарий получения результата эксперимента."""

from __future__ import annotations

from dt_analytics.application.dto.experiment_dto import (
    ExperimentDto,
    ExperimentResultDto,
    GetExperimentResultRequest,
)
from dt_analytics.application.dto.ml_experiment_dto import (
    ArtifactReferenceDto,
    EvaluationResultDto,
    ModelConfigDto,
    PreprocessingConfigDto,
    TrainingResultDto,
)
from dt_analytics.domain import ExperimentId, ProjectId
from dt_analytics.domain.repositories import (
    ArtifactRepository,
    ExperimentRepository,
    ProjectRepository,
)
from dt_analytics.shared import Result


class GetExperimentResultUseCase:
    """Загрузить результат эксперимента вместе с связанными артефактами."""

    def __init__(
        self,
        project_repository: ProjectRepository,
        experiment_repository: ExperimentRepository,
        artifact_repository: ArtifactRepository,
    ) -> None:
        self._project_repository = project_repository
        self._experiment_repository = experiment_repository
        self._artifact_repository = artifact_repository

    def execute(self, request: GetExperimentResultRequest) -> Result[ExperimentResultDto]:
        """Вернуть подробный DTO результата эксперимента."""
        project_id = ProjectId(request.project_id)
        experiment_id = ExperimentId(request.experiment_id)

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

        experiment_result = self._experiment_repository.get_by_id(
            project_id=project_id,
            experiment_id=experiment_id,
        )
        if experiment_result.is_failure:
            return Result.fail(
                code=experiment_result.error.code
                if experiment_result.error
                else "experiment_not_found",
                message=experiment_result.error.message
                if experiment_result.error
                else "Эксперимент не найден.",
                details=experiment_result.error.details if experiment_result.error else None,
                warnings=list(experiment_result.warnings),
            )

        artifacts_result = self._artifact_repository.list_by_experiment(
            project_id=project_id,
            experiment_id=experiment_id,
        )
        if artifacts_result.is_failure:
            return Result.fail(
                code=artifacts_result.error.code
                if artifacts_result.error
                else "artifact_load_failed",
                message=artifacts_result.error.message
                if artifacts_result.error
                else "Не удалось загрузить артефакты эксперимента.",
                details=artifacts_result.error.details if artifacts_result.error else None,
                warnings=list(artifacts_result.warnings),
            )

        experiment = experiment_result.unwrap()
        artifacts = artifacts_result.unwrap()

        dto = ExperimentResultDto(
            experiment=self._to_experiment_dto(
                project_id=request.project_id,
                experiment=experiment,
            ),
            artifacts=tuple(self._to_artifact_dto(artifact) for artifact in artifacts),
        )
        return Result.ok(dto)

    @staticmethod
    def _to_training_result_dto(training_result) -> TrainingResultDto:
        return TrainingResultDto(
            id=training_result.id.value,
            train_score=training_result.train_score,
            tree_depth=training_result.tree_depth,
            leaf_count=training_result.leaf_count,
            node_count=training_result.node_count,
            feature_importance=training_result.feature_importance,
            class_labels=tuple(training_result.class_labels),
            created_at=training_result.created_at.isoformat(),
        )

    @staticmethod
    def _to_evaluation_result_dto(evaluation_result) -> EvaluationResultDto:
        return EvaluationResultDto(
            id=evaluation_result.id.value,
            accuracy=evaluation_result.accuracy,
            precision_weighted=evaluation_result.precision_weighted,
            recall_weighted=evaluation_result.recall_weighted,
            f1_weighted=evaluation_result.f1_weighted,
            confusion_matrix=tuple(
                tuple(int(cell) for cell in row) for row in evaluation_result.confusion_matrix
            ),
            classification_report=evaluation_result.classification_report,
            created_at=evaluation_result.created_at.isoformat(),
        )

    @staticmethod
    def _to_artifact_dto(artifact) -> ArtifactReferenceDto:
        return ArtifactReferenceDto(
            id=artifact.id.value,
            artifact_type=artifact.artifact_type.value,
            file_path=artifact.file.path,
            metadata=artifact.metadata,
            created_at=artifact.created_at.isoformat(),
        )

    @classmethod
    def _to_experiment_dto(cls, project_id: str, experiment) -> ExperimentDto:
        training_result = (
            cls._to_training_result_dto(experiment.training_result)
            if experiment.training_result is not None
            else None
        )
        evaluation_result = (
            cls._to_evaluation_result_dto(experiment.evaluation_result)
            if experiment.evaluation_result is not None
            else None
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
            preprocessing_config=PreprocessingConfigDto(
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
            ),
            model_config=ModelConfigDto(
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
            ),
            training_result=training_result,
            evaluation_result=evaluation_result,
            artifact_count=len(experiment.artifacts),
        )
