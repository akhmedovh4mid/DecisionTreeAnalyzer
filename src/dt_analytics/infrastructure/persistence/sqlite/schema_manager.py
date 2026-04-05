"""Управление схемой SQLite."""

from __future__ import annotations

import sqlite3

from dt_analytics.shared import PersistenceError

SCHEMA_STATEMENTS: tuple[str, ...] = (
    """
    CREATE TABLE IF NOT EXISTS projects (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        storage_path TEXT NOT NULL UNIQUE,
        app_version TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS datasets (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        name TEXT NOT NULL,
        source_file_path TEXT NOT NULL,
        source_file_exists INTEGER NOT NULL,
        source_file_checksum TEXT,
        local_copy_file_path TEXT NOT NULL,
        local_copy_file_exists INTEGER NOT NULL,
        local_copy_file_checksum TEXT,
        format TEXT NOT NULL,
        row_count INTEGER NOT NULL,
        column_count INTEGER NOT NULL,
        loaded_at TEXT NOT NULL,
        is_active INTEGER NOT NULL DEFAULT 1,
        profile_id TEXT,
        profiled_at TEXT,
        missing_total INTEGER,
        duplicate_count INTEGER,
        memory_usage_bytes INTEGER,
        profile_summary_json TEXT,
        UNIQUE(project_id, name),
        FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS feature_definitions (
        id TEXT PRIMARY KEY,
        dataset_id TEXT NOT NULL,
        name TEXT NOT NULL,
        physical_dtype TEXT NOT NULL,
        logical_type TEXT NOT NULL,
        role TEXT NOT NULL,
        nullable INTEGER NOT NULL,
        missing_count INTEGER NOT NULL,
        unique_count INTEGER,
        ordinal_position INTEGER NOT NULL,
        UNIQUE(dataset_id, name),
        FOREIGN KEY(dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS experiments (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        dataset_id TEXT NOT NULL,
        name TEXT NOT NULL,
        status TEXT NOT NULL,
        started_at TEXT,
        finished_at TEXT,
        error_message TEXT,
        notes TEXT,
        preprocessing_config_id TEXT NOT NULL,
        preprocessing_target_column TEXT NOT NULL,
        preprocessing_feature_columns_json TEXT NOT NULL,
        preprocessing_excluded_columns_json TEXT NOT NULL,
        preprocessing_missing_strategy TEXT NOT NULL,
        preprocessing_categorical_encoding_strategy TEXT NOT NULL,
        preprocessing_drop_duplicates INTEGER NOT NULL,
        preprocessing_test_size REAL NOT NULL,
        preprocessing_random_state INTEGER NOT NULL,
        preprocessing_stratify_enabled INTEGER NOT NULL,
        preprocessing_created_at TEXT NOT NULL,
        model_config_id TEXT NOT NULL,
        model_task_type TEXT NOT NULL,
        model_algorithm_code TEXT NOT NULL,
        model_criterion TEXT NOT NULL,
        model_max_depth INTEGER,
        model_min_samples_split INTEGER NOT NULL,
        model_min_samples_leaf INTEGER NOT NULL,
        model_max_features TEXT,
        model_splitter TEXT NOT NULL,
        model_class_weight TEXT,
        model_random_state INTEGER NOT NULL,
        model_additional_params_json TEXT NOT NULL,
        training_result_id TEXT,
        training_train_score REAL,
        training_tree_depth INTEGER,
        training_leaf_count INTEGER,
        training_node_count INTEGER,
        training_feature_importance_json TEXT,
        training_class_labels_json TEXT,
        training_created_at TEXT,
        evaluation_result_id TEXT,
        evaluation_accuracy REAL,
        evaluation_precision_weighted REAL,
        evaluation_recall_weighted REAL,
        evaluation_f1_weighted REAL,
        evaluation_confusion_matrix_json TEXT,
        evaluation_classification_report_json TEXT,
        evaluation_created_at TEXT,
        FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
        FOREIGN KEY(dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS artifacts (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        experiment_id TEXT,
        artifact_type TEXT NOT NULL,
        file_path TEXT NOT NULL,
        file_exists INTEGER NOT NULL,
        file_checksum TEXT,
        metadata_json TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
        FOREIGN KEY(experiment_id) REFERENCES experiments(id) ON DELETE CASCADE
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_datasets_project_id ON datasets(project_id);",
    "CREATE INDEX IF NOT EXISTS idx_features_dataset_id ON feature_definitions(dataset_id);",
    "CREATE INDEX IF NOT EXISTS idx_experiments_project_id ON experiments(project_id);",
    "CREATE INDEX IF NOT EXISTS idx_experiments_dataset_id ON experiments(dataset_id);",
    "CREATE INDEX IF NOT EXISTS idx_artifacts_project_id ON artifacts(project_id);",
    "CREATE INDEX IF NOT EXISTS idx_artifacts_experiment_id ON artifacts(experiment_id);",
)


def ensure_schema(connection: sqlite3.Connection) -> None:
    """Создать схему MVP, если она ещё не существует."""
    try:
        with connection:
            for statement in SCHEMA_STATEMENTS:
                connection.execute(statement)
    except sqlite3.Error as exc:
        raise PersistenceError(f"Не удалось инициализировать схему SQLite: {exc}") from exc
