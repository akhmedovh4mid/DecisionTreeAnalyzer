"""DTO‑модели, связанные с проектами."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class CreateProjectRequest:
    """DTO запроса на создание проекта."""

    name: str
    storage_path: Path
    description: str | None = None
    app_version: str = "0.1.0"


@dataclass(frozen=True, slots=True)
class OpenProjectRequest:
    """DTO запроса на открытие существующего проекта."""

    storage_path: Path


@dataclass(frozen=True, slots=True)
class SaveProjectRequest:
    """DTO запроса на сохранение проекта."""

    project_id: str
    storage_path: Path


@dataclass(frozen=True, slots=True)
class ProjectDto:
    """DTO проекта для внешнего взаимодействия (application/API)."""

    id: str
    name: str
    description: str | None
    storage_path: Path
    app_version: str
    created_at: str
    updated_at: str
    dataset_count: int
    experiment_count: int
