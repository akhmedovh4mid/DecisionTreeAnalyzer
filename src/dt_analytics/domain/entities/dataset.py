"""Сущность набора данных."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from dt_analytics.domain.entities.dataset_profile import DatasetProfile
from dt_analytics.domain.entities.feature_definition import FeatureDefinition
from dt_analytics.domain.value_objects import DatasetId, FileReference


@dataclass(slots=True)
class Dataset:
    """Импортированный набор данных, зарегистрированный внутри проекта."""

    id: DatasetId
    name: str
    source_file: FileReference
    local_copy_file: FileReference
    format: str
    row_count: int
    column_count: int
    loaded_at: datetime
    is_active: bool = True
    features: list[FeatureDefinition] = field(default_factory=list)
    profile: DatasetProfile | None = None

    @classmethod
    def create(
        cls,
        name: str,
        source_file: FileReference,
        local_copy_file: FileReference,
        format: str,
        row_count: int,
        column_count: int,
    ) -> Dataset:
        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError("Имя набора данных не может быть пустым.")

        if row_count < 0:
            raise ValueError("Количество строк не может быть отрицательным.")

        if column_count < 0:
            raise ValueError("Количество столбцов не может быть отрицательным.")

        normalized_format = format.strip().lower()
        if not normalized_format:
            raise ValueError("Формат набора данных не может быть пустым.")

        return cls(
            id=DatasetId.new(),
            name=normalized_name,
            source_file=source_file,
            local_copy_file=local_copy_file,
            format=normalized_format,
            row_count=row_count,
            column_count=column_count,
            loaded_at=datetime.now(UTC),
        )

    def replace_features(self, features: list[FeatureDefinition]) -> None:
        """Заменить полную схему набора данных."""
        names = [feature.name for feature in features]
        if len(names) != len(set(names)):
            raise ValueError("Имена признаков должны быть уникальными внутри набора данных.")

        self.features = sorted(features, key=lambda item: item.ordinal_position)
        self.column_count = len(self.features)

    def attach_profile(self, profile: DatasetProfile) -> None:
        """Присоединить профиль набора данных."""
        self.profile = profile

    def deactivate(self) -> None:
        """Пометить набор данных как неактивный."""
        self.is_active = False

    def activate(self) -> None:
        """Пометить набор данных как активный."""
        self.is_active = True

    def get_feature_names(self) -> list[str]:
        """Вернуть имена признаков в порядковом порядке."""
        return [feature.name for feature in self.features]

    def find_feature(self, name: str) -> FeatureDefinition | None:
        """Найти признак по имени."""
        for feature in self.features:
            if feature.name == name:
                return feature
        return None

    @property
    def source_path(self) -> Path:
        """Вернуть путь к исходному файлу."""
        return self.source_file.path

    @property
    def local_copy_path(self) -> Path:
        """Вернуть путь к локальной копии набора данных в проекте."""
        return self.local_copy_file.path
