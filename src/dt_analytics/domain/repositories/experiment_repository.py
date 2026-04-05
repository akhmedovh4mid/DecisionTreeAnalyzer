"""Контракт репозитория экспериментов."""

from __future__ import annotations

from typing import Protocol

from dt_analytics.domain.entities import Experiment
from dt_analytics.domain.value_objects import ExperimentId, ProjectId
from dt_analytics.shared import Result


class ExperimentRepository(Protocol):
    """Контракт для хранения и извлечения экспериментов."""

    def add(self, project_id: ProjectId, experiment: Experiment) -> Result[Experiment]:
        """Прикрепить эксперимент к проекту и сохранить его."""
        ...

    def save(self, project_id: ProjectId, experiment: Experiment) -> Result[Experiment]:
        """Сохранить текущее состояние эксперимента."""
        ...

    def get_by_id(
        self,
        project_id: ProjectId,
        experiment_id: ExperimentId,
    ) -> Result[Experiment]:
        """Получить эксперимент по его идентификатору внутри проекта."""
        ...

    def list_by_project(self, project_id: ProjectId) -> Result[list[Experiment]]:
        """Вернуть все эксперименты, зарегистрированные в проекте."""
        ...

    def remove(self, project_id: ProjectId, experiment_id: ExperimentId) -> Result[None]:
        """Удалить эксперимент из проекта."""
        ...
