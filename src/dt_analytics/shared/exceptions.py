"""Общая иерархия исключений для DT Analytics."""

from __future__ import annotations

from dataclasses import dataclass


class DtAnalyticsError(Exception):
    """Базовое исключение приложения для всех ошибок, специфичных для проекта."""


class ConfigurationError(DtAnalyticsError):
    """Вызывается, когда конфигурация приложения некорректна или неполна."""


class BootstrapError(DtAnalyticsError):
    """Вызывается при сбое начальной загрузки приложения."""


class ValidationError(DtAnalyticsError):
    """Базовая ошибка валидации для не-домен-специфичных ошибок проверки."""


class NotFoundError(DtAnalyticsError):
    """Вызывается, когда запрошенная сущность или ресурс не найдены."""


class PersistenceError(DtAnalyticsError):
    """Вызывается, когда данные не удаётся корректно сохранить или загрузить."""


class SerializationError(DtAnalyticsError):
    """Вызывается при сбое сериализации или десериализации."""


class ExternalServiceError(DtAnalyticsError):
    """
    Вызывается, когда внешний библиотечный компонент
    или техническая зависимость выходит из строя.
    """


@dataclass(frozen=True, slots=True)
class ErrorDetails:
    """
    Структурированный payload ошибки, который можно прикрепить к Result или сообщению UI.

    Атрибуты
    ----------
    code:
        Стабильный машинно-читаемый код ошибки.
    message:
        Сообщение об ошибке для пользователя или разработчика.
    details:
        Необязательные технические детали для диагностики.
    """

    code: str
    message: str
    details: str | None = None
