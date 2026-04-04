"""Пакет начальной загрузки для DT Analytics."""

from dt_analytics.bootstrap.app_factory import ApplicationInstance, create_application
from dt_analytics.bootstrap.container import AppContainer, build_container
from dt_analytics.bootstrap.runtime import RuntimeContext, initialize_runtime

__all__ = [
    "ApplicationInstance",
    "AppContainer",
    "RuntimeContext",
    "build_container",
    "create_application",
    "initialize_runtime",
]
