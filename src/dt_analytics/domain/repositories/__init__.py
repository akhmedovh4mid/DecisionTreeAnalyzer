"""Контракты репозиториев доменной модели."""

from dt_analytics.domain.repositories.artifact_repository import ArtifactRepository
from dt_analytics.domain.repositories.dataset_repository import DatasetRepository
from dt_analytics.domain.repositories.experiment_repository import ExperimentRepository
from dt_analytics.domain.repositories.project_repository import ProjectRepository

__all__ = [
    "ArtifactRepository",
    "DatasetRepository",
    "ExperimentRepository",
    "ProjectRepository",
]
