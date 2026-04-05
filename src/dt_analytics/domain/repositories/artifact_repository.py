"""Контракт репозитория артефактов."""

from __future__ import annotations

from typing import Protocol

from dt_analytics.domain.entities import ArtifactReference
from dt_analytics.domain.enums import ArtifactType
from dt_analytics.domain.value_objects import ArtifactId, ExperimentId, ProjectId
from dt_analytics.shared import Result


class ArtifactRepository(Protocol):
    """Контракт для хранения и извлечения артефактов."""

    def add(
        self,
        project_id: ProjectId,
        experiment_id: ExperimentId | None,
        artifact: ArtifactReference,
    ) -> Result[ArtifactReference]:
        """Сохранить ссылку на артефакт."""
        ...

    def get_by_id(
        self,
        project_id: ProjectId,
        artifact_id: ArtifactId,
    ) -> Result[ArtifactReference]:
        """Получить ссылку на артефакт по его идентификатору."""
        ...

    def list_by_project(self, project_id: ProjectId) -> Result[list[ArtifactReference]]:
        """Вернуть все артефакты проекта."""
        ...

    def list_by_experiment(
        self,
        project_id: ProjectId,
        experiment_id: ExperimentId,
    ) -> Result[list[ArtifactReference]]:
        """Вернуть все артефакты, привязанные к конкретному эксперименту."""
        ...

    def list_by_type(
        self,
        project_id: ProjectId,
        artifact_type: ArtifactType,
    ) -> Result[list[ArtifactReference]]:
        """Вернуть артефакты проекта указанного типа."""
        ...

    def remove(self, project_id: ProjectId, artifact_id: ArtifactId) -> Result[None]:
        """Удалить ссылку на артефакт."""
        ...
