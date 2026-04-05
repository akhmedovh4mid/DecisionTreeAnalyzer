"""Реализация ArtifactRepository на основе SQLite."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime

from dt_analytics.domain.entities import ArtifactReference
from dt_analytics.domain.enums import ArtifactType
from dt_analytics.domain.repositories import ArtifactRepository
from dt_analytics.domain.value_objects import ArtifactId, ExperimentId, FileReference, ProjectId
from dt_analytics.shared import Result


class SqliteArtifactRepository(ArtifactRepository):
    """Репозиторий артефактов, использующий SQLite."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def add(
        self,
        project_id: ProjectId,
        experiment_id: ExperimentId | None,
        artifact: ArtifactReference,
    ) -> Result[ArtifactReference]:
        try:
            with self._connection:
                self._connection.execute(
                    """
                    INSERT INTO artifacts (
                        id, project_id, experiment_id, artifact_type,
                        file_path, file_exists, file_checksum,
                        metadata_json, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        project_id = excluded.project_id,
                        experiment_id = excluded.experiment_id,
                        artifact_type = excluded.artifact_type,
                        file_path = excluded.file_path,
                        file_exists = excluded.file_exists,
                        file_checksum = excluded.file_checksum,
                        metadata_json = excluded.metadata_json,
                        created_at = excluded.created_at
                    """,
                    (
                        artifact.id.value,
                        project_id.value,
                        experiment_id.value if experiment_id else None,
                        artifact.artifact_type.value,
                        str(artifact.file.path),
                        int(artifact.file.exists),
                        artifact.file.checksum,
                        json.dumps(artifact.metadata),
                        artifact.created_at.isoformat(),
                    ),
                )
            return Result.ok(artifact)
        except sqlite3.Error as exc:
            return Result.fail(
                code="artifact_save_failed",
                message="Не удалось сохранить ссылку на артефакт.",
                details=str(exc),
            )

    def get_by_id(
        self, project_id: ProjectId, artifact_id: ArtifactId
    ) -> Result[ArtifactReference]:
        try:
            row = self._connection.execute(
                "SELECT * FROM artifacts WHERE project_id = ? AND id = ?",
                (project_id.value, artifact_id.value),
            ).fetchone()

            if row is None:
                return Result.fail(
                    code="artifact_not_found",
                    message="Артефакт не найден.",
                    details=artifact_id.value,
                )

            return Result.ok(self._map_row(row))
        except sqlite3.Error as exc:
            return Result.fail(
                code="artifact_get_failed",
                message="Не удалось получить артефакт.",
                details=str(exc),
            )

    def list_by_project(self, project_id: ProjectId) -> Result[list[ArtifactReference]]:
        try:
            rows = self._connection.execute(
                "SELECT * FROM artifacts WHERE project_id = ? ORDER BY created_at DESC",
                (project_id.value,),
            ).fetchall()
            return Result.ok([self._map_row(row) for row in rows])
        except sqlite3.Error as exc:
            return Result.fail(
                code="artifact_list_failed",
                message="Не удалось получить список артефактов проекта.",
                details=str(exc),
            )

    def list_by_experiment(
        self,
        project_id: ProjectId,
        experiment_id: ExperimentId,
    ) -> Result[list[ArtifactReference]]:
        try:
            rows = self._connection.execute(
                """
                SELECT * FROM artifacts
                WHERE project_id = ? AND experiment_id = ?
                ORDER BY created_at DESC
                """,
                (project_id.value, experiment_id.value),
            ).fetchall()
            return Result.ok([self._map_row(row) for row in rows])
        except sqlite3.Error as exc:
            return Result.fail(
                code="artifact_list_by_experiment_failed",
                message="Не удалось получить список артефактов эксперимента.",
                details=str(exc),
            )

    def list_by_type(
        self,
        project_id: ProjectId,
        artifact_type: ArtifactType,
    ) -> Result[list[ArtifactReference]]:
        try:
            rows = self._connection.execute(
                """
                SELECT * FROM artifacts
                WHERE project_id = ? AND artifact_type = ?
                ORDER BY created_at DESC
                """,
                (project_id.value, artifact_type.value),
            ).fetchall()
            return Result.ok([self._map_row(row) for row in rows])
        except sqlite3.Error as exc:
            return Result.fail(
                code="artifact_list_by_type_failed",
                message="Не удалось получить список артефактов по типу.",
                details=str(exc),
            )

    def remove(self, project_id: ProjectId, artifact_id: ArtifactId) -> Result[None]:
        try:
            with self._connection:
                self._connection.execute(
                    "DELETE FROM artifacts WHERE project_id = ? AND id = ?",
                    (project_id.value, artifact_id.value),
                )
            return Result.ok(None)
        except sqlite3.Error as exc:
            return Result.fail(
                code="artifact_delete_failed",
                message="Не удалось удалить артефакт.",
                details=str(exc),
            )

    @staticmethod
    def _map_row(row: sqlite3.Row) -> ArtifactReference:
        return ArtifactReference(
            id=ArtifactId(row["id"]),
            artifact_type=ArtifactType(row["artifact_type"]),
            file=FileReference.from_path(
                row["file_path"],
                checksum=row["file_checksum"],
            ),
            metadata=json.loads(row["metadata_json"] or "{}"),
            created_at=datetime.fromisoformat(row["created_at"]),
        )
