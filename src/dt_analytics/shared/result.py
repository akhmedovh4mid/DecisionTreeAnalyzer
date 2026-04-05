"""Типизированный объект результата операции для DT Analytics."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, TypeVar

from dt_analytics.shared.exceptions import ErrorDetails

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class Result(Generic[T]):  # noqa: UP046
    """
    Типизированный объект результата, представляющий либо успех, либо ошибку.

    Используйте этот объект на границах приложения/сервисов, где
    предпочтительнее возвращать структурированное состояние успеха/ошибки,
    а не ad hoc словари или исключения для ожидаемых сценариев
    валидации и управления потоком выполнения.
    """

    is_success: bool
    value: T | None = None
    error: ErrorDetails | None = None
    warnings: tuple[str, ...] = field(default_factory=tuple)

    @property
    def is_failure(self) -> bool:
        """Возвращает True, если результат является ошибкой."""
        return not self.is_success

    def unwrap(self) -> T:
        """
        Вернуть успешное значение или вызвать ValueError, если результат неуспешен.
        """
        if self.is_failure:
            error_message = self.error.message if self.error else "Unknown error"
            raise ValueError(f"Невозможно извлечь failed Result: {error_message}")

        if self.value is None:
            raise ValueError("Невозможно извлечь Result: значение равно None.")

        return self.value

    @classmethod
    def ok(cls, value: T, warnings: list[str] | tuple[str, ...] | None = None) -> Result[T]:
        """Создать успешный Result."""
        return cls(
            is_success=True,
            value=value,
            error=None,
            warnings=tuple(warnings or ()),
        )

    @classmethod
    def fail(
        cls,
        code: str,
        message: str,
        details: str | None = None,
        warnings: list[str] | tuple[str, ...] | None = None,
    ) -> Result[T]:
        """Создать неуспешный Result."""
        return cls(
            is_success=False,
            value=None,
            error=ErrorDetails(code=code, message=message, details=details),
            warnings=tuple(warnings or ()),
        )
