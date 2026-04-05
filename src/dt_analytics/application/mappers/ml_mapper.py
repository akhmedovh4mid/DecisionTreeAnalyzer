"""Мапперы между прикладными ML‑DTO и доменными контрактами."""

from __future__ import annotations

from pathlib import Path

from dt_analytics.application.dto.ml_experiment_dto import (
    ArtifactReferenceDto,
    EvaluationResultDto,
    MlExperimentResultDto,
    ModelConfigDto,
    PreparedDatasetSummaryDto,
    PreprocessingConfigDto,
    RunMlExperimentRequest,
    TrainingResultDto,
)
from dt_analytics.domain import (
    ArtifactReference,
    ExperimentExecutionInput,
    ExperimentExecutionOutput,
    ModelConfig,
    PreprocessingConfig,
    TaskType,
)
from dt_analytics.domain.enums import (
    CategoricalEncodingStrategy,
    MissingStrategy,
)
from dt_analytics.shared.types import JsonDict


def to_domain_preprocessing_config(dto: PreprocessingConfigDto) -> PreprocessingConfig:
    """Преобразовать DTO предобработки на уровне приложения в доменную сущность."""
    if dto.id is None:
        return PreprocessingConfig.create(
            target_column=dto.target_column,
            feature_columns=list(dto.feature_columns),
            excluded_columns=list(dto.excluded_columns),
            missing_strategy=MissingStrategy(dto.missing_strategy),
            categorical_encoding_strategy=CategoricalEncodingStrategy(
                dto.categorical_encoding_strategy
            ),
            drop_duplicates=dto.drop_duplicates,
            test_size=dto.test_size,
            random_state=dto.random_state,
            stratify_enabled=dto.stratify_enabled,
        )

    return PreprocessingConfig(
        id=__import__(
            "dt_analytics.domain.value_objects", fromlist=["PreprocessingConfigId"]
        ).PreprocessingConfigId(dto.id),
        target_column=dto.target_column,
        feature_columns=list(dto.feature_columns),
        excluded_columns=list(dto.excluded_columns),
        missing_strategy=MissingStrategy(dto.missing_strategy),
        categorical_encoding_strategy=CategoricalEncodingStrategy(
            dto.categorical_encoding_strategy
        ),
        drop_duplicates=dto.drop_duplicates,
        test_size=dto.test_size,
        random_state=dto.random_state,
        stratify_enabled=dto.stratify_enabled,
    )


def to_domain_model_config(dto: ModelConfigDto) -> ModelConfig:
    """Преобразовать DTO конфигурации модели на уровне приложения в доменную сущность."""
    if dto.task_type != TaskType.CLASSIFICATION.value:
        raise ValueError(f"Неподдерживаемый MVP‑тип задачи: {dto.task_type}")

    if dto.id is None:
        return ModelConfig.create_classification_tree(
            criterion=dto.criterion,
            max_depth=dto.max_depth,
            min_samples_split=dto.min_samples_split,
            min_samples_leaf=dto.min_samples_leaf,
            max_features=dto.max_features,
            splitter=dto.splitter,
            class_weight=dto.class_weight,
            random_state=dto.random_state,
            additional_params=dto.additional_params,
        )

    return ModelConfig(
        id=__import__(
            "dt_analytics.domain.value_objects", fromlist=["ModelConfigId"]
        ).ModelConfigId(dto.id),
        task_type=TaskType(dto.task_type),
        algorithm_code=dto.algorithm_code,
        criterion=dto.criterion,
        max_depth=dto.max_depth,
        min_samples_split=dto.min_samples_split,
        min_samples_leaf=dto.min_samples_leaf,
        max_features=dto.max_features,
        splitter=dto.splitter,
        class_weight=dto.class_weight,
        random_state=dto.random_state,
        additional_params=dto.additional_params,
    )


def to_domain_experiment_execution_input(
    request: RunMlExperimentRequest,
) -> ExperimentExecutionInput:
    """
    Преобразовать DTO‑запроса на запуск эксперимента в доменный
    объект ExperimentExecutionInput.
    """
    from dt_analytics.domain.value_objects import DatasetId

    return ExperimentExecutionInput(
        dataset_id=DatasetId(request.dataset_id),
        task_type=TaskType(request.task_type),
        preprocessing_config=to_domain_preprocessing_config(request.preprocessing_config),
        model_config=to_domain_model_config(request.model_config),
        data_ref=request.data_ref,
        runtime_metadata=request.runtime_metadata,
    )


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


def _to_artifact_dto(artifact: ArtifactReference) -> ArtifactReferenceDto:
    return ArtifactReferenceDto(
        id=artifact.id.value,
        artifact_type=artifact.artifact_type.value,
        file_path=Path(artifact.file.path),
        metadata=artifact.metadata,
        created_at=artifact.created_at.isoformat(),
    )


def to_ml_experiment_result_dto(
    output: ExperimentExecutionOutput,
) -> MlExperimentResultDto:
    """Преобразовать доменный объект ExperimentExecutionOutput в DTO‑результат эксперимента."""
    prepared = output.prepared_dataset
    prepared_dto = PreparedDatasetSummaryDto(
        dataset_id=prepared.dataset_id.value,
        row_count=prepared.row_count,
        column_count=prepared.column_count,
        target_column=prepared.target_column,
        feature_columns=prepared.feature_columns,
        train_row_count=prepared.train_row_count,
        test_row_count=prepared.test_row_count,
    )

    return MlExperimentResultDto(
        prepared_dataset=prepared_dto,
        training_result=_to_training_result_dto(output.training_result),
        evaluation_result=_to_evaluation_result_dto(output.evaluation_result),
        artifacts=tuple(_to_artifact_dto(artifact) for artifact in output.artifacts),
        warnings=output.warnings,
        runtime_metadata=cast_json_dict(output.runtime_metadata),
    )


def cast_json_dict(value: JsonDict) -> JsonDict:
    """Вернуть JSON‑словарь без изменений, но явно помеченный типом для границ мапперов."""
    return value
