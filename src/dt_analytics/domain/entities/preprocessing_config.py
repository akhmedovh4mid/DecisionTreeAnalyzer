"""Сущность конфигурации предобработки."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from dt_analytics.domain.enums import CategoricalEncodingStrategy, MissingStrategy
from dt_analytics.domain.value_objects import PreprocessingConfigId


@dataclass(slots=True)
class PreprocessingConfig:
    """Конфигурация предобработки набора данных до обучения."""

    id: PreprocessingConfigId
    target_column: str
    feature_columns: list[str]
    excluded_columns: list[str] = field(default_factory=list)
    missing_strategy: MissingStrategy = MissingStrategy.MEDIAN_MODE
    categorical_encoding_strategy: CategoricalEncodingStrategy = CategoricalEncodingStrategy.ONE_HOT
    drop_duplicates: bool = False
    test_size: float = 0.2
    random_state: int = 42
    stratify_enabled: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def create(
        cls,
        target_column: str,
        feature_columns: list[str],
        excluded_columns: list[str] | None = None,
        missing_strategy: MissingStrategy = MissingStrategy.MEDIAN_MODE,
        categorical_encoding_strategy: CategoricalEncodingStrategy = (
            CategoricalEncodingStrategy.ONE_HOT
        ),
        drop_duplicates: bool = False,
        test_size: float = 0.2,
        random_state: int = 42,
        stratify_enabled: bool = True,
    ) -> PreprocessingConfig:
        normalized_target = target_column.strip()
        if not normalized_target:
            raise ValueError("Целевой столбец не может быть пустым.")

        normalized_features = [column.strip() for column in feature_columns if column.strip()]
        if not normalized_features:
            raise ValueError("Должен быть выбран как минимум один признак‑столбец.")

        if normalized_target in normalized_features:
            raise ValueError("Целевой столбец не должен входить в список признаков.")

        normalized_excluded = [
            column.strip() for column in (excluded_columns or []) if column.strip()
        ]

        if not 0.0 < test_size < 1.0:
            raise ValueError("Доля тестовой части должна быть между 0 и 1.")

        if random_state < 0:
            raise ValueError("Значение random_state должно быть неотрицательным.")

        if len(normalized_features) != len(set(normalized_features)):
            raise ValueError("Столбцы‑признаки должны быть уникальными.")

        if len(normalized_excluded) != len(set(normalized_excluded)):
            raise ValueError("Исключённые столбцы должны быть уникальными.")

        overlap = set(normalized_features).intersection(normalized_excluded)
        if overlap:
            raise ValueError(f"Признаки и исключённые столбцы пересекаются: {sorted(overlap)!r}")

        return cls(
            id=PreprocessingConfigId.new(),
            target_column=normalized_target,
            feature_columns=normalized_features,
            excluded_columns=normalized_excluded,
            missing_strategy=missing_strategy,
            categorical_encoding_strategy=categorical_encoding_strategy,
            drop_duplicates=drop_duplicates,
            test_size=test_size,
            random_state=random_state,
            stratify_enabled=stratify_enabled,
        )
