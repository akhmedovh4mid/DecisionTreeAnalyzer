"""Контракт репозитория проектов."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from dt_analytics.domain.entities import Project
from dt_analytics.domain.value_objects import ProjectId
from dt_analytics.shared import Result


class ProjectRepository(Protocol):
    """Контракт для хранения и извлечения проектов."""

    def create(self, project: Project) -> Result[Project]:
        """Сохранить новый проект."""
        ...

    def save(self, project: Project) -> Result[Project]:
        """Сохранить текущее состояние уже существующего проекта."""
        ...

    def load(self, storage_path: Path) -> Result[Project]:
        """Загрузить проект из указанной директории хранения."""
        ...

    def get_by_id(self, project_id: ProjectId) -> Result[Project]:
        """Получить проект по его идентификатору."""
        ...

    def exists(self, storage_path: Path) -> Result[bool]:
        """Проверить, существует ли проект в указанной директории."""
        ...

    def delete(self, project_id: ProjectId) -> Result[None]:
        """Удалить метаданные проекта и/или запись о проекте."""
        ...
