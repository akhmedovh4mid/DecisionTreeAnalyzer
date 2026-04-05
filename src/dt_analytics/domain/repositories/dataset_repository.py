"""Контракт репозитория наборов данных."""

from __future__ import annotations

from typing import Protocol

from dt_analytics.domain.entities import Dataset
from dt_analytics.domain.value_objects import DatasetId, ProjectId
from dt_analytics.shared import Result


class DatasetRepository(Protocol):
    """Контракт для хранения и извлечения наборов данных."""

    def add(self, project_id: ProjectId, dataset: Dataset) -> Result[Dataset]:
        """Прикрепить набор данных к проекту и сохранить его."""
        ...

    def save(self, project_id: ProjectId, dataset: Dataset) -> Result[Dataset]:
        """Сохранить текущее состояние набора данных."""
        ...

    def get_by_id(self, project_id: ProjectId, dataset_id: DatasetId) -> Result[Dataset]:
        """Получить набор данных по его идентификатору внутри проекта."""
        ...

    def list_by_project(self, project_id: ProjectId) -> Result[list[Dataset]]:
        """Вернуть все наборы данных, зарегистрированные в проекте."""
        ...

    def remove(self, project_id: ProjectId, dataset_id: DatasetId) -> Result[None]:
        """Удалить набор данных из проекта."""
        ...
