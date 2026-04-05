"""Сценарий запуска эксперимента с деревом решений."""

from __future__ import annotations

from dt_analytics.application.dto.experiment_dto import (
    ExperimentDto,
    ExperimentRunResultDto,
    RunExperimentRequest,
)
from dt_analytics.application.dto.ml_experiment_dto import (
    EvaluationResultDto,
    ModelConfigDto,
    PreprocessingConfigDto,
    TrainingResultDto,
)
from dt_analytics.application.mappers import (
    to_domain_experiment_execution_input,
    to_ml_experiment_result_dto,
)
from dt_analytics.domain import ExperimentId, ProjectId
from dt_analytics.domain.repositories import (
    ArtifactRepository,
    DatasetRepository,
    ExperimentRepository,
    ProjectRepository,
)
from dt_analytics.domain.services import MlExperimentService
from dt_analytics.shared import Result


class RunDecisionTreeExperimentUseCase:
    """Запуск существующего эксперимента и сохранение результатов."""

    def __init__(
        self,
        project_repository: ProjectRepository,
        dataset_repository: DatasetRepository,
        experiment_repository: ExperimentRepository,
        artifact_repository: ArtifactRepository,
        ml_experiment_service: MlExperimentService,
    ) -> None:
        self._project_repository = project_repository
        self._dataset_repository = dataset_repository
        self._experiment_repository = experiment_repository
        self._artifact_repository = artifact_repository
        self._ml_experiment_service = ml_experiment_service

    def execute(self, request: RunExperimentRequest) -> Result[ExperimentRunResultDto]:
        """Запустить сконфигурированный эксперимент и сохранить получившееся состояние."""
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

        experiment = experiment_result.unwrap()

        dataset_result = self._dataset_repository.get_by_id(
            project_id=project_id,
            dataset_id=experiment.dataset_id,
        )
        if dataset_result.is_failure:
            return Result.fail(
                code=dataset_result.error.code if dataset_result.error else "dataset_not_found",
                message=dataset_result.error.message
                if dataset_result.error
                else "Эксперимент не найден.",
                details=dataset_result.error.details if dataset_result.error else None,
                warnings=list(dataset_result.warnings),
            )

        dataset = dataset_result.unwrap()

        try:
            experiment.start()
        except ValueError as exc:
            return Result.fail(
                code="experiment_invalid_state",
                message="Эксперимент не может быть запущен в текущем состоянии.",
                details=str(exc),
            )

        running_save_result = self._experiment_repository.save(
            project_id=project_id,
            experiment=experiment,
        )
        if running_save_result.is_failure:
            return Result.fail(
                code=running_save_result.error.code
                if running_save_result.error
                else "experiment_save_failed",
                message=running_save_result.error.message
                if running_save_result.error
                else "Не удалось сохранить состояние запущенного эксперимента.",
                details=running_save_result.error.details if running_save_result.error else None,
                warnings=list(running_save_result.warnings),
            )

        data_ref = request.data_ref_override or str(dataset.local_copy_file.path)

        ml_request = self._to_ml_request(
            project_id=request.project_id,
            data_ref=data_ref,
            runtime_metadata=request.runtime_metadata,
            experiment=experiment,
        )

        execution_input = to_domain_experiment_execution_input(ml_request)
        execution_result = self._ml_experiment_service.run(execution_input)

        if execution_result.is_failure:
            experiment.mark_failed(
                execution_result.error.message
                if execution_result.error
                else "Неизвестная ошибка выполнения эксперимента."
            )
            failed_save_result = self._experiment_repository.save(
                project_id=project_id,
                experiment=experiment,
            )
            if failed_save_result.is_failure:
                return Result.fail(
                    code=failed_save_result.error.code
                    if failed_save_result.error
                    else "experiment_fail_save_failed",
                    message=failed_save_result.error.message
                    if failed_save_result.error
                    else "Не удалось сохранить состояние завершившегося с ошибкой эксперимента.",
                    details=failed_save_result.error.details if failed_save_result.error else None,
                    warnings=list(execution_result.warnings) + list(failed_save_result.warnings),
                )

            return Result.fail(
                code=execution_result.error.code
                if execution_result.error
                else "experiment_execution_failed",
                message=execution_result.error.message
                if execution_result.error
                else "Выполнение эксперимента завершилось с ошибкой.",
                details=execution_result.error.details if execution_result.error else None,
                warnings=list(execution_result.warnings),
            )

        execution_output = execution_result.unwrap()

        try:
            experiment.mark_trained(execution_output.training_result)
            experiment.mark_evaluated(execution_output.evaluation_result)
            for artifact in execution_output.artifacts:
                experiment.add_artifact(artifact)
        except ValueError as exc:
            experiment.mark_failed(str(exc))
            self._experiment_repository.save(project_id=project_id, experiment=experiment)
            return Result.fail(
                code="experiment_state_update_failed",
                message="Не удалось обновить состояние эксперимента после выполнения ML.",
                details=str(exc),
            )

        experiment_save_result = self._experiment_repository.save(
            project_id=project_id,
            experiment=experiment,
        )
        if experiment_save_result.is_failure:
            return Result.fail(
                code=experiment_save_result.error.code
                if experiment_save_result.error
                else "experiment_save_failed",
                message=experiment_save_result.error.message
                if experiment_save_result.error
                else "Не удалось сохранить результаты эксперимента.",
                details=experiment_save_result.error.details
                if experiment_save_result.error
                else None,
                warnings=list(experiment_save_result.warnings),
            )

        for artifact in execution_output.artifacts:
            artifact_save_result = self._artifact_repository.add(
                project_id=project_id,
                experiment_id=experiment.id,
                artifact=artifact,
            )
            if artifact_save_result.is_failure:
                return Result.fail(
                    code=artifact_save_result.error.code
                    if artifact_save_result.error
                    else "artifact_save_failed",
                    message=artifact_save_result.error.message
                    if artifact_save_result.error
                    else "Не удалось сохранить артефакт эксперимента.",
                    details=artifact_save_result.error.details
                    if artifact_save_result.error
                    else None,
                    warnings=list(artifact_save_result.warnings),
                )

        execution_dto = to_ml_experiment_result_dto(execution_output)
        experiment_dto = self._to_experiment_dto(
            project_id=request.project_id,
            experiment=experiment,
        )

        return Result.ok(
            ExperimentRunResultDto(
                experiment=experiment_dto,
                execution=execution_dto,
            ),
            warnings=list(execution_result.warnings),
        )

    @staticmethod
    def _to_ml_request(
        *,
        project_id: str,
        data_ref: str,
        runtime_metadata: dict[str, object],
        experiment,
    ):
        from dt_analytics.application.dto.ml_experiment_dto import RunMlExperimentRequest

        return RunMlExperimentRequest(
            project_id=project_id,
            dataset_id=experiment.dataset_id.value,
            experiment_name=experiment.name,
            task_type=experiment.model_config.task_type.value,
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
            data_ref=data_ref,
            notes=experiment.notes,
            runtime_metadata=runtime_metadata,  # pyright: ignore[reportArgumentType]
        )

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
