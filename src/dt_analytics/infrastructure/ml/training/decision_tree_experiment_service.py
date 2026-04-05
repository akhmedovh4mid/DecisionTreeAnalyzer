"""Конкретный сервис ML‑эксперимента для sklearn‑дерева решений (классификация)."""

from __future__ import annotations

from pathlib import Path
from typing import TypeVar

import pandas as pd
from pandas import DataFrame
from sklearn.pipeline import Pipeline

from dt_analytics.domain import (
    ArtifactReference,
    ArtifactType,
    Dataset,
    DatasetId,
    ExperimentExecutionInput,
    ExperimentExecutionOutput,
    MlExperimentService,
    TaskType,
    TrainingResult,
)
from dt_analytics.domain.services import PreparedDatasetSummary
from dt_analytics.domain.value_objects import FileReference
from dt_analytics.infrastructure.data_sources import DataFrameProfileService
from dt_analytics.infrastructure.ml.evaluation import ClassificationMetricsEvaluator
from dt_analytics.infrastructure.ml.interpretation import (
    FeatureImportanceExtractor,
    TreeMetadataExtractor,
)
from dt_analytics.infrastructure.ml.models import DecisionTreeClassifierFactory
from dt_analytics.infrastructure.ml.preprocessing import SklearnPreprocessingPipelineBuilder
from dt_analytics.infrastructure.ml.serialization import ModelSerializer
from dt_analytics.infrastructure.ml.training.trainer import (
    SklearnDecisionTreeTrainer,
)
from dt_analytics.shared import Result
from dt_analytics.shared.types import JsonDict

_T = TypeVar("_T")


class SklearnDecisionTreeExperimentService(MlExperimentService):
    """Запуск полного эксперимента с деревом решений на CSV‑данных."""

    def __init__(
        self,
        dataframe_profile_service: DataFrameProfileService,
        preprocessing_builder: SklearnPreprocessingPipelineBuilder,
        model_factory: DecisionTreeClassifierFactory,
        trainer: SklearnDecisionTreeTrainer,
        evaluator: ClassificationMetricsEvaluator,
        tree_metadata_extractor: TreeMetadataExtractor,
        feature_importance_extractor: FeatureImportanceExtractor,
        model_serializer: ModelSerializer | None = None,
    ) -> None:
        self._dataframe_profile_service = dataframe_profile_service
        self._preprocessing_builder = preprocessing_builder
        self._model_factory = model_factory
        self._trainer = trainer
        self._evaluator = evaluator
        self._tree_metadata_extractor = tree_metadata_extractor
        self._feature_importance_extractor = feature_importance_extractor
        self._model_serializer = model_serializer

    def run(self, request: ExperimentExecutionInput) -> Result[ExperimentExecutionOutput]:
        """Выполнить эксперимент по классификации от начала до конца."""
        if request.task_type is not TaskType.CLASSIFICATION:
            return Result.fail(
                code="unsupported_ml_task",
                message="Сервис MVP поддерживает только задачу классификации.",
                details=request.task_type.value,
            )

        dataframe_result = self._load_dataframe(request.data_ref)
        if dataframe_result.is_failure:
            return self._map_failure(
                source_result=dataframe_result,
                fallback_code="ml_data_load_failed",
                fallback_message="Не удалось загрузить набор данных для ML‑эксперимента.",
            )
        dataframe = dataframe_result.unwrap()

        dataset_result = self._build_transient_dataset(
            dataset_id=request.dataset_id.value,
            dataframe=dataframe,
            source_ref=request.data_ref,
        )
        if dataset_result.is_failure:
            return self._map_failure(
                source_result=dataset_result,
                fallback_code="transient_dataset_build_failed",
                fallback_message="Не удалось построить переходный набор данных для предобработки.",
            )
        dataset = dataset_result.unwrap()

        preprocessing_result = self._preprocessing_builder.build(
            dataset=dataset,
            preprocessing_config=request.preprocessing_config,
        )
        if preprocessing_result.is_failure:
            return self._map_failure(
                source_result=preprocessing_result,
                fallback_code="preprocessing_build_failed",
                fallback_message="Не удалось построить pipeline предобработки.",
            )
        preprocessing_build = preprocessing_result.unwrap()

        model_result = self._model_factory.create(request.model_config)
        if model_result.is_failure:
            return self._map_failure(
                source_result=model_result,
                fallback_code="model_factory_failed",
                fallback_message="Не удалось создать модель.",
                extra_warnings=list(preprocessing_result.warnings),
            )

        training_result = self._trainer.train(
            dataframe=dataframe,
            preprocessing_config=request.preprocessing_config,
            transformer=preprocessing_build.transformer,
            model=model_result.unwrap(),
        )
        if training_result.is_failure:
            return self._map_failure(
                source_result=training_result,
                fallback_code="model_training_failed",
                fallback_message="Не удалось обучить модель.",
                extra_warnings=list(preprocessing_result.warnings),
            )
        training_artifacts = training_result.unwrap()

        prediction_result = self._predict(
            pipeline=training_artifacts.pipeline,
            x_test=training_artifacts.x_test,
        )
        if prediction_result.is_failure:
            return self._map_failure(
                source_result=prediction_result,
                fallback_code="prediction_failed",
                fallback_message="Не удалось выполнить предсказания на тестовом наборе.",
                extra_warnings=list(preprocessing_result.warnings),
            )
        y_pred = prediction_result.unwrap()

        evaluation_result = self._evaluator.evaluate(
            y_true=training_artifacts.y_test.tolist(),
            y_pred=y_pred,
        )
        if evaluation_result.is_failure:
            return self._map_failure(
                source_result=evaluation_result,
                fallback_code="evaluation_failed",
                fallback_message="Не удалось провести оценку модели.",
                extra_warnings=list(preprocessing_result.warnings),
            )

        tree_metadata_result = self._tree_metadata_extractor.extract(training_artifacts.pipeline)
        if tree_metadata_result.is_failure:
            return self._map_failure(
                source_result=tree_metadata_result,
                fallback_code="tree_metadata_failed",
                fallback_message="Не удалось извлечь метаданные дерева.",
                extra_warnings=list(preprocessing_result.warnings),
            )
        tree_metadata = tree_metadata_result.unwrap()

        feature_importance_result = self._feature_importance_extractor.extract(
            training_artifacts.pipeline
        )
        if feature_importance_result.is_failure:
            return self._map_failure(
                source_result=feature_importance_result,
                fallback_code="feature_importance_failed",
                fallback_message="Не удалось извлечь важность признаков.",
                extra_warnings=list(preprocessing_result.warnings),
            )
        feature_importance = feature_importance_result.unwrap()

        training_domain_result = self._build_training_result(
            train_score=training_artifacts.train_score,
            tree_depth=tree_metadata.tree_depth,
            leaf_count=tree_metadata.leaf_count,
            node_count=tree_metadata.node_count,
            feature_importance=feature_importance,
            class_labels=tree_metadata.class_labels,
        )
        if training_domain_result.is_failure:
            return self._map_failure(
                source_result=training_domain_result,
                fallback_code="training_result_build_failed",
                fallback_message="Не удалось построить объект результата обучения.",
                extra_warnings=list(preprocessing_result.warnings),
            )

        artifacts_result = self._maybe_serialize_model(
            pipeline=training_artifacts.pipeline,
            runtime_metadata=request.runtime_metadata,
        )
        if artifacts_result.is_failure:
            return self._map_failure(
                source_result=artifacts_result,
                fallback_code="model_serialize_failed",
                fallback_message="Не удалось сериализовать модель.",
                extra_warnings=list(preprocessing_result.warnings),
            )

        output = ExperimentExecutionOutput(
            prepared_dataset=PreparedDatasetSummary(
                dataset_id=request.dataset_id,
                row_count=int(len(dataframe.index)),
                column_count=int(len(dataframe.columns)),
                target_column=request.preprocessing_config.target_column,
                feature_columns=preprocessing_build.feature_groups.selected_features,
                train_row_count=int(len(training_artifacts.x_train.index)),
                test_row_count=int(len(training_artifacts.x_test.index)),
            ),
            training_result=training_domain_result.unwrap(),
            evaluation_result=evaluation_result.unwrap(),
            artifacts=artifacts_result.unwrap(),
            warnings=tuple(preprocessing_result.warnings),
            runtime_metadata=self._build_runtime_metadata(
                request_runtime_metadata=request.runtime_metadata,
                preprocessing_summary=preprocessing_build.summary,
            ),
        )
        return Result.ok(output, warnings=list(preprocessing_result.warnings))

    def _load_dataframe(self, data_ref: str) -> Result[DataFrame]:
        """Загрузить табличные данные из файла CSV."""
        try:
            path = Path(data_ref).expanduser().resolve()
            if not path.exists():
                return Result.fail(
                    code="ml_data_ref_not_found",
                    message="Источник ML‑данных не найден.",
                    details=str(path),
                )

            dataframe = pd.read_csv(path)
        except Exception as exc:  # noqa: BLE001
            return Result.fail(
                code="ml_data_load_failed",
                message="Не удалось загрузить набор данных ML из ссылки.",
                details=str(exc),
            )

        if dataframe.empty and len(dataframe.columns) == 0:
            return Result.fail(
                code="ml_data_empty",
                message="Загруженный набор данных ML пустой.",
            )

        return Result.ok(dataframe)

    def _build_transient_dataset(
        self,
        dataset_id: str,
        dataframe: DataFrame,
        source_ref: str,
    ) -> Result[Dataset]:
        """Построить переходный объект Dataset на основе профилирования dataframe."""
        profiling_result = self._dataframe_profile_service.profile_dataframe(dataframe)
        if profiling_result.is_failure:
            return Result.fail(
                code=profiling_result.error.code
                if profiling_result.error
                else "transient_dataset_profile_failed",
                message=profiling_result.error.message
                if profiling_result.error
                else "Не удалось профилировать переходный набор данных ML.",
                details=profiling_result.error.details if profiling_result.error else None,
            )

        profile_data = profiling_result.unwrap()

        try:
            dataset = Dataset.create(
                name=Path(source_ref).stem or "ml_dataset",
                source_file=FileReference.from_path(source_ref),
                local_copy_file=FileReference.from_path(source_ref),
                format="csv",
                row_count=int(len(dataframe.index)),
                column_count=int(len(dataframe.columns)),
            )
            dataset.id = DatasetId(dataset_id)
            dataset.replace_features(list(profile_data.features))
            dataset.attach_profile(profile_data.profile)
        except ValueError as exc:
            return Result.fail(
                code="transient_dataset_build_failed",
                message=(
                    "Не удалось построить объект переходного набора данных для ML‑предобработки."
                ),
                details=str(exc),
            )

        return Result.ok(dataset)

    def _predict(self, pipeline: Pipeline, x_test: DataFrame) -> Result[list[object]]:
        """Выполнить предсказания на тестовой выборке."""
        try:
            predictions = pipeline.predict(x_test)
        except Exception as exc:  # noqa: BLE001
            return Result.fail(
                code="prediction_failed",
                message="Не удалось выполнить предсказания модели.",
                details=str(exc),
            )

        return Result.ok(list(predictions))

    def _build_training_result(
        self,
        *,
        train_score: float | None,
        tree_depth: int,
        leaf_count: int,
        node_count: int,
        feature_importance: JsonDict,
        class_labels: tuple[str, ...],
    ) -> Result[TrainingResult]:
        """Построить доменный объект результата обучения."""
        try:
            result = TrainingResult.create(
                train_score=train_score,
                tree_depth=tree_depth,
                leaf_count=leaf_count,
                node_count=node_count,
                feature_importance=feature_importance,
                class_labels=list(class_labels),
            )
        except ValueError as exc:
            return Result.fail(
                code="training_result_build_failed",
                message="Не удалось построить объект результата обучения.",
                details=str(exc),
            )

        return Result.ok(result)

    def _maybe_serialize_model(
        self,
        *,
        pipeline: Pipeline,
        runtime_metadata: JsonDict,
    ) -> Result[tuple[ArtifactReference, ...]]:
        """Сериализовать модель, если runtime metadata того требуют."""
        if self._model_serializer is None:
            return Result.ok(())

        destination_raw = runtime_metadata.get("model_output_path")
        if not isinstance(destination_raw, str) or not destination_raw.strip():
            return Result.ok(())

        save_result = self._model_serializer.save(
            pipeline=pipeline,
            file_path=Path(destination_raw),
        )
        if save_result.is_failure:
            return Result.fail(
                code=save_result.error.code if save_result.error else "model_serialize_failed",
                message=save_result.error.message
                if save_result.error
                else "Не удалось сериализовать модель.",
                details=save_result.error.details if save_result.error else None,
            )

        model_path = save_result.unwrap()
        artifact = ArtifactReference.create(
            artifact_type=ArtifactType.MODEL,
            file=FileReference.from_path(model_path),
            metadata={"serializer": "joblib"},
        )
        return Result.ok((artifact,))

    @staticmethod
    def _build_runtime_metadata(
        *,
        request_runtime_metadata: JsonDict,
        preprocessing_summary: JsonDict,
    ) -> JsonDict:
        """Слияние runtime metadata с итогом предобработки."""
        return {
            **request_runtime_metadata,
            "preprocessing_summary": preprocessing_summary,
        }

    @staticmethod
    def _map_failure(
        *,
        source_result: Result[_T],
        fallback_code: str,
        fallback_message: str,
        extra_warnings: list[str] | None = None,
    ) -> Result[ExperimentExecutionOutput]:
        """Преобразовать промежуточную ошибку Result[T] в Result[ExperimentExecutionOutput]."""
        warnings = list(source_result.warnings)
        if extra_warnings:
            warnings = list(extra_warnings) + warnings

        return Result.fail(
            code=source_result.error.code if source_result.error else fallback_code,
            message=source_result.error.message if source_result.error else fallback_message,
            details=source_result.error.details if source_result.error else None,
            warnings=warnings,
        )
