"""Загрузчик настроек приложения."""

from __future__ import annotations

import os
from pathlib import Path

from dt_analytics.config import defaults
from dt_analytics.config.schemas import (
    AppMetadata,
    AppSettings,
    LoggingSettings,
    MlDefaults,
    PathSettings,
    WindowSettings,
)


def _get_env_bool(name: str, default: bool) -> bool:
    """Читать логическую переменную окружения."""
    value = os.getenv(name)
    if value is None:
        return default

    normalized = value.strip().lower()
    return normalized in {"1", "true", "yes", "on"}


def _get_env_int(name: str, default: int) -> int:
    """Читать целочисленную переменную окружения."""
    value = os.getenv(name)
    if value is None:
        return default

    try:
        return int(value)
    except ValueError:
        return default


def _get_env_float(name: str, default: float) -> float:
    """Читать переменную окружения с числом с плавающей точкой."""
    value = os.getenv(name)
    if value is None:
        return default

    try:
        return float(value)
    except ValueError:
        return default


def _get_env_str(name: str, default: str) -> str:
    """Читать строковую переменную окружения."""
    return os.getenv(name, default).strip() or default


def _get_env_path(name: str, default: Path) -> Path:
    """Читать путь файловой системы из переменной окружения."""
    value = os.getenv(name)
    if value is None:
        return default

    return Path(value).expanduser().resolve()


def load_settings() -> AppSettings:
    """
    Собрать настройки приложения из значений по умолчанию и переопределений из окружения.

    Поддерживаемые переменные окружения:
    - DT_ANALYTICS_LOG_LEVEL
    - DT_ANALYTICS_DEBUG
    - DT_ANALYTICS_DEFAULT_PROJECTS_DIR
    - DT_ANALYTICS_WINDOW_WIDTH
    - DT_ANALYTICS_WINDOW_HEIGHT
    - DT_ANALYTICS_RANDOM_STATE
    - DT_ANALYTICS_TEST_SIZE
    """
    metadata = AppMetadata(
        name=defaults.APP_NAME,
        organization_name=defaults.APP_ORGANIZATION_NAME,
        organization_domain=defaults.APP_ORGANIZATION_DOMAIN,
        version=defaults.APP_VERSION,
    )

    window = WindowSettings(
        title=_get_env_str("DT_ANALYTICS_WINDOW_TITLE", defaults.DEFAULT_WINDOW_TITLE),
        width=_get_env_int("DT_ANALYTICS_WINDOW_WIDTH", defaults.DEFAULT_WINDOW_WIDTH),
        height=_get_env_int("DT_ANALYTICS_WINDOW_HEIGHT", defaults.DEFAULT_WINDOW_HEIGHT),
        min_width=defaults.DEFAULT_MIN_WINDOW_WIDTH,
        min_height=defaults.DEFAULT_MIN_WINDOW_HEIGHT,
    )

    logging = LoggingSettings(
        level=_get_env_str("DT_ANALYTICS_LOG_LEVEL", defaults.DEFAULT_LOG_LEVEL).upper(),
        debug=_get_env_bool("DT_ANALYTICS_DEBUG", defaults.DEFAULT_DEBUG),
    )

    ml = MlDefaults(
        random_state=_get_env_int("DT_ANALYTICS_RANDOM_STATE", defaults.DEFAULT_RANDOM_STATE),
        test_size=_get_env_float("DT_ANALYTICS_TEST_SIZE", defaults.DEFAULT_TEST_SIZE),
    )

    paths = PathSettings(
        default_projects_dir=_get_env_path(
            "DT_ANALYTICS_DEFAULT_PROJECTS_DIR",
            defaults.DEFAULT_PROJECTS_DIR,
        )
    )

    return AppSettings(
        metadata=metadata,
        window=window,
        logging=logging,
        ml=ml,
        paths=paths,
    )
