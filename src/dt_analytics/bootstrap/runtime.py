"""Инициализация runtime для DT Analytics."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from platform import platform, python_version

from dt_analytics.config.schemas import AppSettings


@dataclass(frozen=True, slots=True)
class RuntimeContext:
    """Решённый runtime-контекст текущей сессии приложения."""

    settings: AppSettings
    runtime_dir: Path
    default_projects_dir: Path
    platform_name: str
    python_version: str


def initialize_runtime(settings: AppSettings) -> RuntimeContext:
    """
    Инициализировать runtime-среду.

    Обязанности:
    - убедиться, что необходимые директории существуют;
    - собрать базовые метаданные среды выполнения;
    - подготовить значения, повторно используемые во всём приложении.
    """
    default_projects_dir = settings.paths.default_projects_dir
    default_projects_dir.mkdir(parents=True, exist_ok=True)

    runtime_dir = default_projects_dir / ".runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)

    return RuntimeContext(
        settings=settings,
        runtime_dir=runtime_dir,
        default_projects_dir=default_projects_dir,
        platform_name=platform(),
        python_version=python_version(),
    )
