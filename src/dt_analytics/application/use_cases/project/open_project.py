"""Use‑case открытия проекта."""

from __future__ import annotations

from dt_analytics.application.dto.project_dto import OpenProjectRequest, ProjectDto
from dt_analytics.domain import Project
from dt_analytics.domain.repositories import (
    DatasetRepository,
    ExperimentRepository,
    ProjectRepository,
)
from dt_analytics.infrastructure.persistence.filesystem.project_storage import ProjectStorage
from dt_analytics.infrastructure.persistence.sqlite.connection import create_connection
from dt_analytics.infrastructure.persistence.sqlite.schema_manager import ensure_schema
from dt_analytics.shared import Result


class OpenProjectUseCase:
    """Открывает существующий проект и загружает связанные агрегаты."""

    def __init__(
        self,
        project_repository: ProjectRepository,
        dataset_repository: DatasetRepository,
        experiment_repository: ExperimentRepository,
        project_storage: ProjectStorage,
    ) -> None:
        self._project_repository = project_repository
        self._dataset_repository = dataset_repository
        self._experiment_repository = experiment_repository
        self._project_storage = project_storage

    def execute(self, request: OpenProjectRequest) -> Result[ProjectDto]:
        """Открыть проект и загрузить наборы данных и эксперименты."""
        storage_path = request.storage_path.expanduser().resolve()

        storage_exists_result = self._project_storage.exists(storage_path)
        if storage_exists_result.is_failure:
            return Result.fail(
                code=storage_exists_result.error.code
                if storage_exists_result.error
                else "project_storage_check_failed",
                message=storage_exists_result.error.message
                if storage_exists_result.error
                else "Не удалось проверить хранилище проекта.",
                details=storage_exists_result.error.details
                if storage_exists_result.error
                else None,
                warnings=list(storage_exists_result.warnings),
            )

        if not storage_exists_result.unwrap():
            return Result.fail(
                code="project_storage_not_found",
                message="Хранилище проекта не найдено.",
                details=str(storage_path),
            )

        try:
            policy = self._project_storage.ensure_initialized(storage_path)
            connection = create_connection(policy.project_db)
            ensure_schema(connection)
            connection.close()
        except Exception as exc:  # noqa: BLE001
            return Result.fail(
                code="project_storage_prepare_failed",
                message="Не удалось подготовить хранилище проекта.",
                details=str(exc),
            )

        project_result = self._project_repository.load(storage_path)
        if project_result.is_failure:
            return Result.fail(
                code=project_result.error.code if project_result.error else "project_load_failed",
                message=project_result.error.message
                if project_result.error
                else "Не удалось загрузить проект.",
                details=project_result.error.details if project_result.error else None,
                warnings=list(project_result.warnings),
            )

        project = project_result.unwrap()

        datasets_result = self._dataset_repository.list_by_project(project.id)
        if datasets_result.is_failure:
            return Result.fail(
                code=datasets_result.error.code if datasets_result.error else "dataset_load_failed",
                message=datasets_result.error.message
                if datasets_result.error
                else "Не удалось загрузить наборы данных проекта.",
                details=datasets_result.error.details if datasets_result.error else None,
                warnings=list(datasets_result.warnings),
            )

        experiments_result = self._experiment_repository.list_by_project(project.id)
        if experiments_result.is_failure:
            return Result.fail(
                code=experiments_result.error.code
                if experiments_result.error
                else "experiment_load_failed",
                message=experiments_result.error.message
                if experiments_result.error
                else "Не удалось загрузить эксперименты проекта.",
                details=experiments_result.error.details if experiments_result.error else None,
                warnings=list(experiments_result.warnings),
            )

        project.datasets = datasets_result.unwrap()
        project.experiments = experiments_result.unwrap()

        return Result.ok(self._to_dto(project))

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
