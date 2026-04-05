"""Реализация DatasetRepository на основе SQLite."""

from __future__ import annotations

import json
import sqlite3
from typing import cast

from dt_analytics.domain.entities import Dataset, DatasetProfile, FeatureDefinition
from dt_analytics.domain.enums import FeatureRole, LogicalFeatureType
from dt_analytics.domain.repositories import DatasetRepository
from dt_analytics.domain.value_objects import (
    DatasetId,
    FeatureId,
    FileReference,
    ProfileId,
    ProjectId,
)
from dt_analytics.shared import Result


class SqliteDatasetRepository(DatasetRepository):
    """Репозиторий наборов данных, использующий SQLite."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def add(self, project_id: ProjectId, dataset: Dataset) -> Result[Dataset]:
        return self.save(project_id, dataset)

    def save(self, project_id: ProjectId, dataset: Dataset) -> Result[Dataset]:
        try:
            with self._connection:
                self._connection.execute(
                    """
                    INSERT INTO datasets (
                        id, project_id, name,
                        source_file_path, source_file_exists, source_file_checksum,
                        local_copy_file_path, local_copy_file_exists, local_copy_file_checksum,
                        format, row_count, column_count, loaded_at, is_active,
                        profile_id, profiled_at, missing_total, duplicate_count,
                        memory_usage_bytes, profile_summary_json
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        name = excluded.name,
                        source_file_path = excluded.source_file_path,
                        source_file_exists = excluded.source_file_exists,
                        source_file_checksum = excluded.source_file_checksum,
                        local_copy_file_path = excluded.local_copy_file_path,
                        local_copy_file_exists = excluded.local_copy_file_exists,
                        local_copy_file_checksum = excluded.local_copy_file_checksum,
                        format = excluded.format,
                        row_count = excluded.row_count,
                        column_count = excluded.column_count,
                        loaded_at = excluded.loaded_at,
                        is_active = excluded.is_active,
                        profile_id = excluded.profile_id,
                        profiled_at = excluded.profiled_at,
                        missing_total = excluded.missing_total,
                        duplicate_count = excluded.duplicate_count,
                        memory_usage_bytes = excluded.memory_usage_bytes,
                        profile_summary_json = excluded.profile_summary_json
                    """,
                    (
                        dataset.id.value,
                        project_id.value,
                        dataset.name,
                        str(dataset.source_file.path),
                        int(dataset.source_file.exists),
                        dataset.source_file.checksum,
                        str(dataset.local_copy_file.path),
                        int(dataset.local_copy_file.exists),
                        dataset.local_copy_file.checksum,
                        dataset.format,
                        dataset.row_count,
                        dataset.column_count,
                        dataset.loaded_at.isoformat(),
                        int(dataset.is_active),
                        dataset.profile.id.value if dataset.profile else None,
                        dataset.profile.profiled_at.isoformat() if dataset.profile else None,
                        dataset.profile.missing_total if dataset.profile else None,
                        dataset.profile.duplicate_count if dataset.profile else None,
                        dataset.profile.memory_usage_bytes if dataset.profile else None,
                        json.dumps(dataset.profile.summary) if dataset.profile else None,
                    ),
                )

                self._connection.execute(
                    "DELETE FROM feature_definitions WHERE dataset_id = ?",
                    (dataset.id.value,),
                )

                for feature in dataset.features:
                    self._connection.execute(
                        """
                        INSERT INTO feature_definitions (
                            id, dataset_id, name, physical_dtype, logical_type, role,
                            nullable, missing_count, unique_count, ordinal_position
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            feature.id.value,
                            dataset.id.value,
                            feature.name,
                            feature.physical_dtype,
                            feature.logical_type.value,
                            feature.role.value,
                            int(feature.nullable),
                            feature.missing_count,
                            feature.unique_count,
                            feature.ordinal_position,
                        ),
                    )

            return Result.ok(dataset)
        except sqlite3.Error as exc:
            return Result.fail(
                code="dataset_save_failed",
                message="Не удалось сохранить набор данных.",
                details=str(exc),
            )

    def get_by_id(self, project_id: ProjectId, dataset_id: DatasetId) -> Result[Dataset]:
        try:
            row = self._connection.execute(
                "SELECT * FROM datasets WHERE project_id = ? AND id = ?",
                (project_id.value, dataset_id.value),
            ).fetchone()

            if row is None:
                return Result.fail(
                    code="dataset_not_found",
                    message="Набор данных не найден.",
                    details=dataset_id.value,
                )

            features = self._load_features(dataset_id)
            dataset = self._map_row_to_dataset(row, features)
            return Result.ok(dataset)
        except sqlite3.Error as exc:
            return Result.fail(
                code="dataset_get_failed",
                message="Не удалось получить набор данных.",
                details=str(exc),
            )

    def list_by_project(self, project_id: ProjectId) -> Result[list[Dataset]]:
        try:
            rows = self._connection.execute(
                "SELECT * FROM datasets WHERE project_id = ? ORDER BY loaded_at DESC",
                (project_id.value,),
            ).fetchall()

            datasets: list[Dataset] = []
            for row in rows:
                dataset_id = DatasetId(row["id"])
                features = self._load_features(dataset_id)
                datasets.append(self._map_row_to_dataset(row, features))

            return Result.ok(datasets)
        except sqlite3.Error as exc:
            return Result.fail(
                code="dataset_list_failed",
                message="Не удалось получить список наборов данных.",
                details=str(exc),
            )

    def remove(self, project_id: ProjectId, dataset_id: DatasetId) -> Result[None]:
        try:
            with self._connection:
                self._connection.execute(
                    "DELETE FROM datasets WHERE project_id = ? AND id = ?",
                    (project_id.value, dataset_id.value),
                )
            return Result.ok(None)
        except sqlite3.Error as exc:
            return Result.fail(
                code="dataset_delete_failed",
                message="Не удалось удалить набор данных.",
                details=str(exc),
            )

    def _load_features(self, dataset_id: DatasetId) -> list[FeatureDefinition]:
        rows = self._connection.execute(
            """
            SELECT *
            FROM feature_definitions
            WHERE dataset_id = ?
            ORDER BY ordinal_position ASC
            """,
            (dataset_id.value,),
        ).fetchall()

        features: list[FeatureDefinition] = []
        for row in rows:
            features.append(
                FeatureDefinition(
                    id=FeatureId(row["id"]),
                    name=row["name"],
                    physical_dtype=row["physical_dtype"],
                    logical_type=LogicalFeatureType(row["logical_type"]),
                    role=FeatureRole(row["role"]),
                    nullable=bool(row["nullable"]),
                    missing_count=row["missing_count"],
                    unique_count=row["unique_count"],
                    ordinal_position=row["ordinal_position"],
                )
            )
        return features

    @staticmethod
    def _map_row_to_dataset(row: sqlite3.Row, features: list[FeatureDefinition]) -> Dataset:
        profile = None
        if row["profile_id"] is not None:
            summary_raw = row["profile_summary_json"] or "{}"
            profile = DatasetProfile(
                id=ProfileId(row["profile_id"]),
                profiled_at=__import__("datetime").datetime.fromisoformat(row["profiled_at"]),
                missing_total=row["missing_total"] or 0,
                duplicate_count=row["duplicate_count"] or 0,
                memory_usage_bytes=row["memory_usage_bytes"],
                summary=json.loads(summary_raw),
            )

        return Dataset(
            id=DatasetId(row["id"]),
            name=row["name"],
            source_file=FileReference.from_path(
                row["source_file_path"],
                checksum=row["source_file_checksum"],
            ),
            local_copy_file=FileReference.from_path(
                row["local_copy_file_path"],
                checksum=row["local_copy_file_checksum"],
            ),
            format=row["format"],
            row_count=row["row_count"],
            column_count=row["column_count"],
            loaded_at=__import__("datetime").datetime.fromisoformat(row["loaded_at"]),
            is_active=bool(row["is_active"]),
            features=features,
            profile=profile,
        )
