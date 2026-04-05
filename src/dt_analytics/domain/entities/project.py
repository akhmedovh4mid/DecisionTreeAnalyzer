"""Сущность проекта."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from dt_analytics.domain.entities.dataset import Dataset
from dt_analytics.domain.entities.experiment import Experiment
from dt_analytics.domain.value_objects import ProjectId


@dataclass(slots=True)
class Project:
    """Корневой агрегат, представляющий проект анализа."""

    id: ProjectId
    name: str
    storage_path: Path
    created_at: datetime
    updated_at: datetime
    description: str | None = None
    app_version: str = "0.1.0"
    datasets: list[Dataset] = field(default_factory=list)
    experiments: list[Experiment] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        name: str,
        storage_path: Path,
        description: str | None = None,
        app_version: str = "0.1.0",
    ) -> Project:
        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError("Имя проекта не может быть пустым.")

        now = datetime.now(UTC)
        return cls(
            id=ProjectId.new(),
            name=normalized_name,
            storage_path=storage_path.expanduser().resolve(),
            created_at=now,
            updated_at=now,
            description=description.strip() if description else None,
            app_version=app_version,
        )

    def add_dataset(self, dataset: Dataset) -> None:
        """Добавить набор данных в проект."""
        if any(existing.id == dataset.id for existing in self.datasets):
            raise ValueError(f"Набор данных с id {dataset.id} уже есть в проекте.")

        if any(existing.name == dataset.name for existing in self.datasets):
            raise ValueError(f"Набор данных с именем {dataset.name!r} уже существует в проекте.")

        self.datasets.append(dataset)
        self.touch()

    def add_experiment(self, experiment: Experiment) -> None:
        """Добавить эксперимент в проект."""
        if any(existing.id == experiment.id for existing in self.experiments):
            raise ValueError(f"Эксперимент с id {experiment.id} уже есть в проекте.")

        self.experiments.append(experiment)
        self.touch()

    def find_dataset(self, dataset_id: str) -> Dataset | None:
        """Найти набор данных по его идентификатору (строковому значению)."""
        for dataset in self.datasets:
            if dataset.id.value == dataset_id:
                return dataset
        return None

    def find_experiment(self, experiment_id: str) -> Experiment | None:
        """Найти эксперимент по его идентификатору (строковому значению)."""
        for experiment in self.experiments:
            if experiment.id.value == experiment_id:
                return experiment
        return None

    def touch(self) -> None:
        """Обновить отметку времени изменения проекта."""
        self.updated_at = datetime.now(UTC)
