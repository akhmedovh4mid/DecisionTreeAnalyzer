"""Определение типов признаков для предобработки ML."""

from __future__ import annotations

from dataclasses import dataclass, field

from dt_analytics.domain.entities import Dataset, FeatureDefinition, PreprocessingConfig
from dt_analytics.domain.enums import FeatureRole, LogicalFeatureType
from dt_analytics.shared import Result


@dataclass(frozen=True, slots=True)
class FeatureGroups:
    """Сгруппированные признаки, используемые при построении pipeline’а предобработки."""

    selected_features: tuple[str, ...]
    numeric_features: tuple[str, ...]
    categorical_features: tuple[str, ...]
    ignored_features: tuple[str, ...] = field(default_factory=tuple)

    @property
    def has_numeric(self) -> bool:
        return bool(self.numeric_features)

    @property
    def has_categorical(self) -> bool:
        return bool(self.categorical_features)

    @property
    def is_empty(self) -> bool:
        return not self.selected_features


class FeatureTypeResolver:
    """Определяет группы признаков по схеме набора данных и конфигурации предобработки."""

    SUPPORTED_NUMERIC_TYPES = {
        LogicalFeatureType.NUMERIC,
        LogicalFeatureType.BOOLEAN,
    }

    SUPPORTED_CATEGORICAL_TYPES = {
        LogicalFeatureType.CATEGORICAL,
        LogicalFeatureType.TEXT,
    }

    def resolve(
        self,
        dataset: Dataset,
        preprocessing_config: PreprocessingConfig,
    ) -> Result[FeatureGroups]:
        """
        Определить группы признаков для предобработки.

        Правила:
        - участвуют только признаки из preprocessing_config.feature_columns;
        - целевая колонка должна быть исключена;
        - явно исключённые столбцы не участвуют;
        - признаки с ролью identifier/excluded/target игнорируются;
        - numeric/boolean идут в numeric-ветку;
        - categorical/text идут в categorical-ветку;
        - неподдерживаемые логические типы игнорируются и попадают в warnings.
        """
        if not dataset.features:
            return Result.fail(
                code="dataset_schema_missing",
                message="Схема набора данных недоступна для предобработки.",
            )

        feature_map = {feature.name: feature for feature in dataset.features}

        missing_columns = [
            name for name in preprocessing_config.feature_columns if name not in feature_map
        ]
        if missing_columns:
            return Result.fail(
                code="feature_columns_not_found",
                message="Некоторые выбранные признаки отсутствуют в схеме набора данных.",
                details=str(missing_columns),
            )

        if preprocessing_config.target_column not in feature_map:
            return Result.fail(
                code="target_column_not_found",
                message="Целевая колонка отсутствует в схеме набора данных.",
                details=preprocessing_config.target_column,
            )

        selected_features: list[str] = []
        numeric_features: list[str] = []
        categorical_features: list[str] = []
        ignored_features: list[str] = []
        warnings: list[str] = []

        for feature_name in preprocessing_config.feature_columns:
            feature = feature_map[feature_name]

            resolution = self._resolve_feature(
                feature=feature,
                preprocessing_config=preprocessing_config,
            )

            if resolution == "ignored":
                ignored_features.append(feature_name)
                continue

            if resolution == "numeric":
                selected_features.append(feature_name)
                numeric_features.append(feature_name)
                continue

            if resolution == "categorical":
                selected_features.append(feature_name)
                categorical_features.append(feature_name)
                continue

            ignored_features.append(feature_name)
            warnings.append(
                f"Признак '{feature_name}' имеет неподдерживаемый логический тип "
                f"'{feature.logical_type.value}' и был проигнорирован."
            )

        if not selected_features:
            return Result.fail(
                code="no_supported_features",
                message="После разбора конфигурации не осталось поддерживаемых признаков.",
                details=str(preprocessing_config.feature_columns),
                warnings=warnings,
            )

        return Result.ok(
            FeatureGroups(
                selected_features=tuple(selected_features),
                numeric_features=tuple(numeric_features),
                categorical_features=tuple(categorical_features),
                ignored_features=tuple(ignored_features),
            ),
            warnings=warnings,
        )

    def _resolve_feature(
        self,
        feature: FeatureDefinition,
        preprocessing_config: PreprocessingConfig,
    ) -> str:
        """
        Определить тип признака как:
        - 'numeric'
        - 'categorical'
        - 'ignored'
        """
        if feature.name == preprocessing_config.target_column:
            return "ignored"

        if feature.name in preprocessing_config.excluded_columns:
            return "ignored"

        if feature.role in {
            FeatureRole.EXCLUDED,
            FeatureRole.IDENTIFIER,
            FeatureRole.TARGET,
        }:
            return "ignored"

        if feature.logical_type in self.SUPPORTED_NUMERIC_TYPES:
            return "numeric"

        if feature.logical_type in self.SUPPORTED_CATEGORICAL_TYPES:
            return "categorical"

        return "ignored"
