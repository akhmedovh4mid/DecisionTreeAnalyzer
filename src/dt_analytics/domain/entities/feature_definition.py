"""Сущность определения признака."""

from __future__ import annotations

from dataclasses import dataclass

from dt_analytics.domain.enums import FeatureRole, LogicalFeatureType
from dt_analytics.domain.value_objects import FeatureId


@dataclass(slots=True)
class FeatureDefinition:
    """Метаданные одного столбца набора данных."""

    id: FeatureId
    name: str
    physical_dtype: str
    logical_type: LogicalFeatureType
    role: FeatureRole
    nullable: bool
    missing_count: int = 0
    unique_count: int | None = None
    ordinal_position: int = 0

    @classmethod
    def create(
        cls,
        name: str,
        physical_dtype: str,
        logical_type: LogicalFeatureType,
        role: FeatureRole = FeatureRole.FEATURE,
        nullable: bool = True,
        missing_count: int = 0,
        unique_count: int | None = None,
        ordinal_position: int = 0,
    ) -> FeatureDefinition:
        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError("Имя признака не может быть пустым.")

        if missing_count < 0:
            raise ValueError("Количество пропусков не может быть отрицательным.")

        if unique_count is not None and unique_count < 0:
            raise ValueError("Количество уникальных значений не может быть отрицательным.")

        if ordinal_position < 0:
            raise ValueError("Порядковая позиция не может быть отрицательной.")

        return cls(
            id=FeatureId.new(),
            name=normalized_name,
            physical_dtype=physical_dtype.strip(),
            logical_type=logical_type,
            role=role,
            nullable=nullable,
            missing_count=missing_count,
            unique_count=unique_count,
            ordinal_position=ordinal_position,
        )

    def mark_as_target(self) -> None:
        """Пометить признак как целевой (target)."""
        self.role = FeatureRole.TARGET

    def mark_as_feature(self) -> None:
        """Пометить признак как обычную переменную модели (feature)."""
        self.role = FeatureRole.FEATURE

    def mark_as_excluded(self) -> None:
        """Пометить признак как исключённый из моделирования."""
        self.role = FeatureRole.EXCLUDED

    def mark_as_identifier(self) -> None:
        """Пометить признак как идентификатор‑подобный."""
        self.role = FeatureRole.IDENTIFIER

    @property
    def is_model_feature(self) -> bool:
        """Вернуть True, если столбец может использоваться как признак модели."""
        return self.role is FeatureRole.FEATURE

    @property
    def is_target(self) -> bool:
        """Вернуть True, если столбец является целевой переменной."""
        return self.role is FeatureRole.TARGET
