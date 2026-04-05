"""Построитель pipeline’ов предобработки для ML‑воркфлоу на sklearn."""

from __future__ import annotations

from dataclasses import dataclass, field

from sklearn.compose import ColumnTransformer

from dt_analytics.domain.entities import Dataset, PreprocessingConfig
from dt_analytics.infrastructure.ml.preprocessing.feature_type_resolver import (
    FeatureGroups,
    FeatureTypeResolver,
)
from dt_analytics.infrastructure.ml.preprocessing.transformers import (
    build_column_transformer,
)
from dt_analytics.shared import Result
from dt_analytics.shared.types import JsonDict


@dataclass(frozen=True, slots=True)
class PreprocessingBuildResult:
    """
    Структурированный результат построения pipeline’а предобработки.
    """

    feature_groups: FeatureGroups
    transformer: ColumnTransformer
    summary: JsonDict = field(default_factory=dict)


class SklearnPreprocessingPipelineBuilder:
    """
    Строит sklearn‑pipeline предобработки из доменного набора данных и конфигурации.
    """

    def __init__(self, feature_type_resolver: FeatureTypeResolver | None = None) -> None:
        self._feature_type_resolver = feature_type_resolver or FeatureTypeResolver()

    def build(
        self,
        dataset: Dataset,
        preprocessing_config: PreprocessingConfig,
    ) -> Result[PreprocessingBuildResult]:
        """
        Определить группы признаков и построить ColumnTransformer.
        """
        groups_result = self._feature_type_resolver.resolve(
            dataset=dataset,
            preprocessing_config=preprocessing_config,
        )
        if groups_result.is_failure:
            return Result.fail(
                code=groups_result.error.code
                if groups_result.error
                else "feature_resolution_failed",
                message=groups_result.error.message
                if groups_result.error
                else "Не удалось определить группы признаков.",
                details=groups_result.error.details if groups_result.error else None,
                warnings=list(groups_result.warnings),
            )

        feature_groups = groups_result.unwrap()

        try:
            transformer = build_column_transformer(
                numeric_features=feature_groups.numeric_features,
                categorical_features=feature_groups.categorical_features,
                preprocessing_config=preprocessing_config,
            )
        except ValueError as exc:
            return Result.fail(
                code="preprocessing_transformer_build_failed",
                message="Не удалось построить трансформер предобработки.",
                details=str(exc),
                warnings=list(groups_result.warnings),
            )

        summary: JsonDict = {
            "selected_feature_count": len(feature_groups.selected_features),
            "numeric_feature_count": len(feature_groups.numeric_features),
            "categorical_feature_count": len(feature_groups.categorical_features),
            "ignored_feature_count": len(feature_groups.ignored_features),
            "selected_features": list(feature_groups.selected_features),
            "numeric_features": list(feature_groups.numeric_features),
            "categorical_features": list(feature_groups.categorical_features),
            "ignored_features": list(feature_groups.ignored_features),
            "missing_strategy": preprocessing_config.missing_strategy.value,
            "categorical_encoding_strategy": (
                preprocessing_config.categorical_encoding_strategy.value
            ),
            "drop_duplicates": preprocessing_config.drop_duplicates,
            "test_size": preprocessing_config.test_size,
            "random_state": preprocessing_config.random_state,
            "stratify_enabled": preprocessing_config.stratify_enabled,
        }

        return Result.ok(
            PreprocessingBuildResult(
                feature_groups=feature_groups,
                transformer=transformer,
                summary=summary,
            ),
            warnings=list(groups_result.warnings),
        )
