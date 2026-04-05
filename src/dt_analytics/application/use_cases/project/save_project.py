"""Use‑case сохранения проекта."""

from __future__ import annotations

from dt_analytics.application.dto.project_dto import ProjectDto, SaveProjectRequest
from dt_analytics.domain import ProjectId
from dt_analytics.domain.entities import Project
from dt_analytics.domain.repositories import (
    ArtifactRepository,
    DatasetRepository,
    ExperimentRepository,
    ProjectRepository,
)
from dt_analytics.shared import Result


class SaveProjectUseCase:
    """Сохраняет состояние проекта вместе с наборами данных и экспериментами."""

    def __init__(
        self,
        project_repository: ProjectRepository,
        dataset_repository: DatasetRepository,
        experiment_repository: ExperimentRepository,
        artifact_repository: ArtifactRepository | None = None,
    ) -> None:
        self._project_repository = project_repository
        self._dataset_repository = dataset_repository
        self._experiment_repository = experiment_repository
        self._artifact_repository = artifact_repository

    def execute(self, request: SaveProjectRequest) -> Result[ProjectDto]:
        """Сохранить метаданные проекта и связанные сущности."""
        project_id = ProjectId(request.project_id)

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

        project = project_result.unwrap()

        if project.storage_path != request.storage_path.expanduser().resolve():
            project.storage_path = request.storage_path.expanduser().resolve()
            project.touch()

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

        project.touch()

        save_project_result = self._project_repository.save(project)
        if save_project_result.is_failure:
            return Result.fail(
                code=save_project_result.error.code
                if save_project_result.error
                else "project_save_failed",
                message=save_project_result.error.message
                if save_project_result.error
                else "Не удалось сохранить проект.",
                details=save_project_result.error.details if save_project_result.error else None,
                warnings=list(save_project_result.warnings),
            )

        for dataset in project.datasets:
            dataset_save_result = self._dataset_repository.save(project.id, dataset)
            if dataset_save_result.is_failure:
                return Result.fail(
                    code=dataset_save_result.error.code
                    if dataset_save_result.error
                    else "dataset_save_failed",
                    message=dataset_save_result.error.message
                    if dataset_save_result.error
                    else "Не удалось сохранить набор данных.",
                    details=dataset_save_result.error.details
                    if dataset_save_result.error
                    else None,
                    warnings=list(dataset_save_result.warnings),
                )

        for experiment in project.experiments:
            experiment_save_result = self._experiment_repository.save(project.id, experiment)
            if experiment_save_result.is_failure:
                return Result.fail(
                    code=experiment_save_result.error.code
                    if experiment_save_result.error
                    else "experiment_save_failed",
                    message=experiment_save_result.error.message
                    if experiment_save_result.error
                    else "Не удалось сохранить эксперимент.",
                    details=experiment_save_result.error.details
                    if experiment_save_result.error
                    else None,
                    warnings=list(experiment_save_result.warnings),
                )

            if self._artifact_repository is not None:
                for artifact in experiment.artifacts:
                    artifact_save_result = self._artifact_repository.add(
                        project_id=project.id,
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
                            else "Не удалось сохранить артефакт.",
                            details=artifact_save_result.error.details
                            if artifact_save_result.error
                            else None,
                            warnings=list(artifact_save_result.warnings),
                        )

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
