"""Реализация ProjectRepository на основе SQLite."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from dt_analytics.domain.entities import Project
from dt_analytics.domain.repositories import ProjectRepository
from dt_analytics.domain.value_objects import ProjectId
from dt_analytics.shared import Result


class SqliteProjectRepository(ProjectRepository):
    """Репозиторий проектов, использующий SQLite."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def create(self, project: Project) -> Result[Project]:
        return self.save(project)

    def save(self, project: Project) -> Result[Project]:
        try:
            with self._connection:
                self._connection.execute(
                    """
                    INSERT INTO projects (
                        id, name, description, storage_path, app_version, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        name = excluded.name,
                        description = excluded.description,
                        storage_path = excluded.storage_path,
                        app_version = excluded.app_version,
                        updated_at = excluded.updated_at
                    """,
                    (
                        project.id.value,
                        project.name,
                        project.description,
                        str(project.storage_path),
                        project.app_version,
                        project.created_at.isoformat(),
                        project.updated_at.isoformat(),
                    ),
                )
            return Result.ok(project)
        except sqlite3.Error as exc:
            return Result.fail(
                code="project_save_failed",
                message="Не удалось сохранить проект.",
                details=str(exc),
            )

    def load(self, storage_path: Path) -> Result[Project]:
        try:
            row = self._connection.execute(
                """
                SELECT id, name, description, storage_path, app_version, created_at, updated_at
                FROM projects
                WHERE storage_path = ?
                """,
                (str(storage_path.expanduser().resolve()),),
            ).fetchone()

            if row is None:
                return Result.fail(
                    code="project_not_found",
                    message="Проект не найден.",
                    details=str(storage_path),
                )

            return Result.ok(self._map_row_to_project(row))
        except sqlite3.Error as exc:
            return Result.fail(
                code="project_load_failed",
                message="Не удалось загрузить проект.",
                details=str(exc),
            )

    def get_by_id(self, project_id: ProjectId) -> Result[Project]:
        try:
            row = self._connection.execute(
                """
                SELECT id, name, description, storage_path, app_version, created_at, updated_at
                FROM projects
                WHERE id = ?
                """,
                (project_id.value,),
            ).fetchone()

            if row is None:
                return Result.fail(
                    code="project_not_found",
                    message="Проект не найден.",
                    details=project_id.value,
                )

            return Result.ok(self._map_row_to_project(row))
        except sqlite3.Error as exc:
            return Result.fail(
                code="project_get_failed",
                message="Не удалось получить проект.",
                details=str(exc),
            )

    def exists(self, storage_path: Path) -> Result[bool]:
        try:
            row = self._connection.execute(
                "SELECT 1 FROM projects WHERE storage_path = ?",
                (str(storage_path.expanduser().resolve()),),
            ).fetchone()
            return Result.ok(row is not None)
        except sqlite3.Error as exc:
            return Result.fail(
                code="project_exists_failed",
                message="Не удалось проверить существование проекта.",
                details=str(exc),
            )

    def delete(self, project_id: ProjectId) -> Result[None]:
        try:
            with self._connection:
                self._connection.execute(
                    "DELETE FROM projects WHERE id = ?",
                    (project_id.value,),
                )
            return Result.ok(None)
        except sqlite3.Error as exc:
            return Result.fail(
                code="project_delete_failed",
                message="Не удалось удалить проект.",
                details=str(exc),
            )

    @staticmethod
    def _map_row_to_project(row: sqlite3.Row) -> Project:
        return Project(
            id=ProjectId(row["id"]),
            name=row["name"],
            description=row["description"],
            storage_path=Path(row["storage_path"]),
            app_version=row["app_version"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            datasets=[],
            experiments=[],
        )
