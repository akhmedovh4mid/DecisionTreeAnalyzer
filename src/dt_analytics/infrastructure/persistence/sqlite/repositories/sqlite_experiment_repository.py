"""Реализация ExperimentRepository на основе SQLite."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime

from dt_analytics.domain.entities import (
    EvaluationResult,
    Experiment,
    ModelConfig,
    PreprocessingConfig,
    TrainingResult,
)
from dt_analytics.domain.enums import (
    CategoricalEncodingStrategy,
    ExperimentStatus,
    MissingStrategy,
    TaskType,
)
from dt_analytics.domain.repositories import ExperimentRepository
from dt_analytics.domain.value_objects import (
    DatasetId,
    EvaluationResultId,
    ExperimentId,
    ModelConfigId,
    PreprocessingConfigId,
    ProjectId,
    TrainingResultId,
)
from dt_analytics.shared import Result


class SqliteExperimentRepository(ExperimentRepository):
    """Репозиторий экспериментов, использующий SQLite."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def add(self, project_id: ProjectId, experiment: Experiment) -> Result[Experiment]:
        return self.save(project_id, experiment)

    def save(self, project_id: ProjectId, experiment: Experiment) -> Result[Experiment]:
        try:
            pre = experiment.preprocessing_config
            model = experiment.model_config
            tr = experiment.training_result
            ev = experiment.evaluation_result

            with self._connection:
                self._connection.execute(
                    """
                    INSERT INTO experiments (
                        id, project_id, dataset_id, name, status,
                        started_at, finished_at, error_message, notes,
                        preprocessing_config_id, preprocessing_target_column,
                        preprocessing_feature_columns_json, preprocessing_excluded_columns_json,
                        preprocessing_missing_strategy, preprocessing_categorical_encoding_strategy,
                        preprocessing_drop_duplicates, preprocessing_test_size,
                        preprocessing_random_state, preprocessing_stratify_enabled,
                        preprocessing_created_at,
                        model_config_id, model_task_type, model_algorithm_code,
                        model_criterion, model_max_depth, model_min_samples_split,
                        model_min_samples_leaf, model_max_features, model_splitter,
                        model_class_weight, model_random_state, model_additional_params_json,
                        training_result_id, training_train_score, training_tree_depth,
                        training_leaf_count, training_node_count,
                        training_feature_importance_json, training_class_labels_json,
                        training_created_at,
                        evaluation_result_id, evaluation_accuracy,
                        evaluation_precision_weighted, evaluation_recall_weighted,
                        evaluation_f1_weighted, evaluation_confusion_matrix_json,
                        evaluation_classification_report_json, evaluation_created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        dataset_id = excluded.dataset_id,
                        name = excluded.name,
                        status = excluded.status,
                        started_at = excluded.started_at,
                        finished_at = excluded.finished_at,
                        error_message = excluded.error_message,
                        notes = excluded.notes,
                        preprocessing_config_id = excluded.preprocessing_config_id,
                        preprocessing_target_column = excluded.preprocessing_target_column,
                        preprocessing_feature_columns_json = excluded.preprocessing_feature_columns_json,
                        preprocessing_excluded_columns_json = excluded.preprocessing_excluded_columns_json,
                        preprocessing_missing_strategy = excluded.preprocessing_missing_strategy,
                        preprocessing_categorical_encoding_strategy = excluded.preprocessing_categorical_encoding_strategy,
                        preprocessing_drop_duplicates = excluded.preprocessing_drop_duplicates,
                        preprocessing_test_size = excluded.preprocessing_test_size,
                        preprocessing_random_state = excluded.preprocessing_random_state,
                        preprocessing_stratify_enabled = excluded.preprocessing_stratify_enabled,
                        preprocessing_created_at = excluded.preprocessing_created_at,
                        model_config_id = excluded.model_config_id,
                        model_task_type = excluded.model_task_type,
                        model_algorithm_code = excluded.model_algorithm_code,
                        model_criterion = excluded.model_criterion,
                        model_max_depth = excluded.model_max_depth,
                        model_min_samples_split = excluded.model_min_samples_split,
                        model_min_samples_leaf = excluded.model_min_samples_leaf,
                        model_max_features = excluded.model_max_features,
                        model_splitter = excluded.model_splitter,
                        model_class_weight = excluded.model_class_weight,
                        model_random_state = excluded.model_random_state,
                        model_additional_params_json = excluded.model_additional_params_json,
                        training_result_id = excluded.training_result_id,
                        training_train_score = excluded.training_train_score,
                        training_tree_depth = excluded.training_tree_depth,
                        training_leaf_count = excluded.training_leaf_count,
                        training_node_count = excluded.training_node_count,
                        training_feature_importance_json = excluded.training_feature_importance_json,
                        training_class_labels_json = excluded.training_class_labels_json,
                        training_created_at = excluded.training_created_at,
                        evaluation_result_id = excluded.evaluation_result_id,
                        evaluation_accuracy = excluded.evaluation_accuracy,
                        evaluation_precision_weighted = excluded.evaluation_precision_weighted,
                        evaluation_recall_weighted = excluded.evaluation_recall_weighted,
                        evaluation_f1_weighted = excluded.evaluation_f1_weighted,
                        evaluation_confusion_matrix_json = excluded.evaluation_confusion_matrix_json,
                        evaluation_classification_report_json = excluded.evaluation_classification_report_json,
                        evaluation_created_at = excluded.evaluation_created_at
                    """,  # noqa: E501
                    (
                        experiment.id.value,
                        project_id.value,
                        experiment.dataset_id.value,
                        experiment.name,
                        experiment.status.value,
                        experiment.started_at.isoformat() if experiment.started_at else None,
                        experiment.finished_at.isoformat() if experiment.finished_at else None,
                        experiment.error_message,
                        experiment.notes,
                        pre.id.value,
                        pre.target_column,
                        json.dumps(pre.feature_columns),
                        json.dumps(pre.excluded_columns),
                        pre.missing_strategy.value,
                        pre.categorical_encoding_strategy.value,
                        int(pre.drop_duplicates),
                        pre.test_size,
                        pre.random_state,
                        int(pre.stratify_enabled),
                        pre.created_at.isoformat(),
                        model.id.value,
                        model.task_type.value,
                        model.algorithm_code,
                        model.criterion,
                        model.max_depth,
                        model.min_samples_split,
                        model.min_samples_leaf,
                        model.max_features,
                        model.splitter,
                        model.class_weight,
                        model.random_state,
                        json.dumps(model.additional_params),
                        tr.id.value if tr else None,
                        tr.train_score if tr else None,
                        tr.tree_depth if tr else None,
                        tr.leaf_count if tr else None,
                        tr.node_count if tr else None,
                        json.dumps(tr.feature_importance) if tr else None,
                        json.dumps(tr.class_labels) if tr else None,
                        tr.created_at.isoformat() if tr else None,
                        ev.id.value if ev else None,
                        ev.accuracy if ev else None,
                        ev.precision_weighted if ev else None,
                        ev.recall_weighted if ev else None,
                        ev.f1_weighted if ev else None,
                        json.dumps(ev.confusion_matrix) if ev else None,
                        json.dumps(ev.classification_report) if ev else None,
                        ev.created_at.isoformat() if ev else None,
                    ),
                )
            return Result.ok(experiment)
        except sqlite3.Error as exc:
            return Result.fail(
                code="experiment_save_failed",
                message="Не удалось сохранить эксперимент.",
                details=str(exc),
            )

    def get_by_id(self, project_id: ProjectId, experiment_id: ExperimentId) -> Result[Experiment]:
        try:
            row = self._connection.execute(
                "SELECT * FROM experiments WHERE project_id = ? AND id = ?",
                (project_id.value, experiment_id.value),
            ).fetchone()

            if row is None:
                return Result.fail(
                    code="experiment_not_found",
                    message="Эксперимент не найден.",
                    details=experiment_id.value,
                )

            return Result.ok(self._map_row_to_experiment(row))
        except sqlite3.Error as exc:
            return Result.fail(
                code="experiment_get_failed",
                message="Не удалось получить эксперимент.",
                details=str(exc),
            )

    def list_by_project(self, project_id: ProjectId) -> Result[list[Experiment]]:
        try:
            rows = self._connection.execute(
                "SELECT * FROM experiments WHERE project_id = ? ORDER BY rowid DESC",
                (project_id.value,),
            ).fetchall()
            return Result.ok([self._map_row_to_experiment(row) for row in rows])
        except sqlite3.Error as exc:
            return Result.fail(
                code="experiment_list_failed",
                message="Не удалось получить список экспериментов.",
                details=str(exc),
            )

    def remove(self, project_id: ProjectId, experiment_id: ExperimentId) -> Result[None]:
        try:
            with self._connection:
                self._connection.execute(
                    "DELETE FROM experiments WHERE project_id = ? AND id = ?",
                    (project_id.value, experiment_id.value),
                )
            return Result.ok(None)
        except sqlite3.Error as exc:
            return Result.fail(
                code="experiment_delete_failed",
                message="Не удалось удалить эксперимент.",
                details=str(exc),
            )

    @staticmethod
    def _map_row_to_experiment(row: sqlite3.Row) -> Experiment:
        pre = PreprocessingConfig(
            id=PreprocessingConfigId(row["preprocessing_config_id"]),
            target_column=row["preprocessing_target_column"],
            feature_columns=json.loads(row["preprocessing_feature_columns_json"]),
            excluded_columns=json.loads(row["preprocessing_excluded_columns_json"]),
            missing_strategy=MissingStrategy(row["preprocessing_missing_strategy"]),
            categorical_encoding_strategy=CategoricalEncodingStrategy(
                row["preprocessing_categorical_encoding_strategy"]
            ),
            drop_duplicates=bool(row["preprocessing_drop_duplicates"]),
            test_size=row["preprocessing_test_size"],
            random_state=row["preprocessing_random_state"],
            stratify_enabled=bool(row["preprocessing_stratify_enabled"]),
            created_at=datetime.fromisoformat(row["preprocessing_created_at"]),
        )

        model = ModelConfig(
            id=ModelConfigId(row["model_config_id"]),
            task_type=TaskType(row["model_task_type"]),
            algorithm_code=row["model_algorithm_code"],
            criterion=row["model_criterion"],
            max_depth=row["model_max_depth"],
            min_samples_split=row["model_min_samples_split"],
            min_samples_leaf=row["model_min_samples_leaf"],
            max_features=row["model_max_features"],
            splitter=row["model_splitter"],
            class_weight=row["model_class_weight"],
            random_state=row["model_random_state"],
            additional_params=json.loads(row["model_additional_params_json"]),
        )

        training_result = None
        if row["training_result_id"] is not None:
            training_result = TrainingResult(
                id=TrainingResultId(row["training_result_id"]),
                train_score=row["training_train_score"],
                tree_depth=row["training_tree_depth"],
                leaf_count=row["training_leaf_count"],
                node_count=row["training_node_count"],
                feature_importance=json.loads(row["training_feature_importance_json"] or "{}"),
                class_labels=json.loads(row["training_class_labels_json"] or "[]"),
                created_at=datetime.fromisoformat(row["training_created_at"]),
            )

        evaluation_result = None
        if row["evaluation_result_id"] is not None:
            evaluation_result = EvaluationResult(
                id=EvaluationResultId(row["evaluation_result_id"]),
                accuracy=row["evaluation_accuracy"],
                precision_weighted=row["evaluation_precision_weighted"],
                recall_weighted=row["evaluation_recall_weighted"],
                f1_weighted=row["evaluation_f1_weighted"],
                confusion_matrix=json.loads(row["evaluation_confusion_matrix_json"] or "[]"),
                classification_report=json.loads(
                    row["evaluation_classification_report_json"] or "{}"
                ),
                created_at=datetime.fromisoformat(row["evaluation_created_at"]),
            )

        return Experiment(
            id=ExperimentId(row["id"]),
            dataset_id=DatasetId(row["dataset_id"]),
            preprocessing_config=pre,
            model_config=model,
            name=row["name"],
            status=ExperimentStatus(row["status"]),
            started_at=datetime.fromisoformat(row["started_at"]) if row["started_at"] else None,
            finished_at=datetime.fromisoformat(row["finished_at"]) if row["finished_at"] else None,
            error_message=row["error_message"],
            notes=row["notes"],
            training_result=training_result,
            evaluation_result=evaluation_result,
            artifacts=[],
        )
