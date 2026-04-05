"""Общий базовый пакет для DT Analytics."""

from dt_analytics.shared.exceptions import (
    BootstrapError,
    ConfigurationError,
    DtAnalyticsError,
    ErrorDetails,
    ExternalServiceError,
    NotFoundError,
    PersistenceError,
    SerializationError,
    ValidationError,
)
from dt_analytics.shared.result import Result

__all__ = [
    "BootstrapError",
    "ConfigurationError",
    "DtAnalyticsError",
    "ErrorDetails",
    "ExternalServiceError",
    "NotFoundError",
    "PersistenceError",
    "Result",
    "SerializationError",
    "ValidationError",
]
