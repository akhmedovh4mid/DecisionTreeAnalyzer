"""Use‑case создания проекта."""

from __future__ import annotations

from pathlib import Path

from dt_analytics.application.dto.project_dto import CreateProjectRequest, ProjectDto
from dt_analytics.domain import Project
from dt_analytics.domain.repositories import ProjectRepository
from dt_analytics.infrastructure.persistence.filesystem.project_storage import ProjectStorage
from dt_analytics.infrastructure.persistence.sqlite.connection import create_connection
from dt_analytics.infrastructure.persistence.sqlite.schema_manager import ensure_schema
from dt_analytics.shared import Result


class CreateProjectUseCase:
    """Создаёт и инициализирует новый проект."""

    def __init__(
        self,
        project_repository: ProjectRepository,
        project_storage: ProjectStorage,
    ) -> None:
        self._project_repository = project_repository
        self._project_storage = project_storage

    def execute(self, request: CreateProjectRequest) -> Result[ProjectDto]:
        """Создать новый проект и инициализировать его хранилище."""
        normalized_name = request.name.strip()
        if not normalized_name:
            return Result.fail(
                code="project_name_empty",
                message="Имя проекта не может быть пустым.",
            )

        storage_path = request.storage_path.expanduser().resolve()

        exists_result = self._project_repository.exists(storage_path)
        if exists_result.is_failure:
            return Result.fail(
                code=exists_result.error.code if exists_result.error else "project_exists_failed",
                message=exists_result.error.message
                if exists_result.error
                else "Не удалось проверить существование проекта.",
                details=exists_result.error.details if exists_result.error else None,
                warnings=list(exists_result.warnings),
            )

        if exists_result.unwrap():
            return Result.fail(
                code="project_already_exists",
                message="Проект уже существует в выбранном расположении.",
                details=str(storage_path),
            )

        storage_result = self._project_storage.initialize(storage_path)
        if storage_result.is_failure:
            return Result.fail(
                code=storage_result.error.code
                if storage_result.error
                else "project_storage_init_failed",
                message=storage_result.error.message
                if storage_result.error
                else "Не удалось инициализировать хранилище проекта.",
                details=storage_result.error.details if storage_result.error else None,
                warnings=list(storage_result.warnings),
            )

        path_policy = storage_result.unwrap()

        try:
            connection = create_connection(path_policy.project_db)
            ensure_schema(connection)
            connection.close()
        except Exception as exc:  # noqa: BLE001
            return Result.fail(
                code="project_schema_init_failed",
                message="Не удалось инициализировать схему базы данных проекта.",
                details=str(exc),
            )

        try:
            project = Project.create(
                name=normalized_name,
                storage_path=Path(path_policy.project_root),
                description=request.description,
                app_version=request.app_version,
            )
        except ValueError as exc:
            return Result.fail(
                code="project_creation_failed",
                message="Не удалось создать объект проекта.",
                details=str(exc),
            )

        save_result = self._project_repository.create(project)
        if save_result.is_failure:
            return Result.fail(
                code=save_result.error.code if save_result.error else "project_save_failed",
                message=save_result.error.message
                if save_result.error
                else "Не удалось сохранить проект.",
                details=save_result.error.details if save_result.error else None,
                warnings=list(save_result.warnings),
            )

        saved_project = save_result.unwrap()
        return Result.ok(self._to_dto(saved_project))

    @staticmethod
    def _to_dto(project: Project) -> ProjectDto:
        return ProjectDto(
            id=project.id.value,
            name=project.name,
            description=project.description,
            storage_path=project.storage_path,
            app_version=project.app_version,
            created_at=project.created_at.isoformat(),
            updated_at=project.updated_at.isoformat(),
            dataset_count=len(project.datasets),
            experiment_count=len(project.experiments),
        )
