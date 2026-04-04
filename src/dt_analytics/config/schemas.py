"""Типизированные схемы конфигурации для DT Analytics."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class AppMetadata:
    """Идентификационные данные и сведения о версии приложения."""

    name: str
    organization_name: str
    organization_domain: str
    version: str


@dataclass(frozen=True, slots=True)
class WindowSettings:
    """Настройки главного окна."""

    title: str
    width: int
    height: int
    min_width: int
    min_height: int


@dataclass(frozen=True, slots=True)
class LoggingSettings:
    """Конфигурация, связанная с логированием."""

    level: str
    debug: bool


@dataclass(frozen=True, slots=True)
class MlDefaults:
    """Конфигурация настроек машинного обучения по умолчанию."""

    random_state: int
    test_size: float


@dataclass(frozen=True, slots=True)
class PathSettings:
    """Конфигурация путей файловой системы."""

    default_projects_dir: Path


@dataclass(frozen=True, slots=True)
class AppSettings:
    """Типизированные настройки приложения верхнего уровня."""

    metadata: AppMetadata
    window: WindowSettings
    logging: LoggingSettings
    ml: MlDefaults
    paths: PathSettings
