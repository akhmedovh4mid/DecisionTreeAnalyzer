"""Простой контейнер зависимостей для DT Analytics."""

from __future__ import annotations

from dataclasses import dataclass

from dt_analytics.bootstrap.runtime import RuntimeContext
from dt_analytics.config.schemas import AppSettings


@dataclass(slots=True)
class AppContainer:
    """
    Корень композиции приложения.

    На этом этапе он содержит только основные runtime-объекты.
    Позже он будет расширен репозиториями, сервисами,
    use case'ами, исполнителями задач и контроллерами представления.
    """

    settings: AppSettings
    runtime: RuntimeContext


def build_container(settings: AppSettings, runtime: RuntimeContext) -> AppContainer:
    """Создать корневой контейнер зависимостей."""
    return AppContainer(
        settings=settings,
        runtime=runtime,
    )
