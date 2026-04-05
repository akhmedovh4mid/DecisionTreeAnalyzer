"""Сущность профиля набора данных."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from dt_analytics.domain.value_objects import ProfileId
from dt_analytics.shared.types import JsonDict


@dataclass(slots=True)
class DatasetProfile:
    """Сводные статистические профили для набора данных."""

    id: ProfileId
    profiled_at: datetime
    missing_total: int
    duplicate_count: int
    memory_usage_bytes: int | None = None
    summary: JsonDict = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        missing_total: int,
        duplicate_count: int,
        memory_usage_bytes: int | None = None,
        summary: JsonDict | None = None,
    ) -> DatasetProfile:
        if missing_total < 0:
            raise ValueError("Общее количество пропущенных значений не может быть отрицательным.")

        if duplicate_count < 0:
            raise ValueError("Количество дубликатов не может быть отрицательным.")

        if memory_usage_bytes is not None and memory_usage_bytes < 0:
            raise ValueError("Объём потребляемой памяти не может быть отрицательным.")

        return cls(
            id=ProfileId.new(),
            profiled_at=datetime.now(UTC),
            missing_total=missing_total,
            duplicate_count=duplicate_count,
            memory_usage_bytes=memory_usage_bytes,
            summary=summary or {},
        )
