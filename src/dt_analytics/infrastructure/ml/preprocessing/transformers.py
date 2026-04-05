"""Фабрики sklearn‑трансформеров для предобработки."""

from __future__ import annotations

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder

from dt_analytics.domain.entities import PreprocessingConfig
from dt_analytics.domain.enums import CategoricalEncodingStrategy, MissingStrategy


def build_numeric_pipeline(
    preprocessing_config: PreprocessingConfig,
) -> Pipeline:
    """
    Построить pipeline для числовых признаков.

    Правила MVP:
    - DROP_ROWS обрабатывается вне sklearn pipeline, на уровне приложения/обучения.
    - MEDIAN_MODE → SimpleImputer(strategy="median")
    - CONSTANT → SimpleImputer(strategy="constant", fill_value=0)
    """
    if preprocessing_config.missing_strategy is MissingStrategy.MEDIAN_MODE:
        imputer = SimpleImputer(strategy="median")
    elif preprocessing_config.missing_strategy is MissingStrategy.CONSTANT:
        imputer = SimpleImputer(strategy="constant", fill_value=0)
    elif preprocessing_config.missing_strategy is MissingStrategy.DROP_ROWS:
        # handled earlier in data preparation; keep safe fallback
        imputer = SimpleImputer(strategy="median")
    else:
        raise ValueError(
            (
                "Неподдерживаемая стратегия пропусков для числовых признаков: ",
                f"{preprocessing_config.missing_strategy!s}",
            )
        )

    return Pipeline(
        steps=[
            ("imputer", imputer),
        ]
    )


def build_categorical_pipeline(
    preprocessing_config: PreprocessingConfig,
) -> Pipeline:
    """
    Построить pipeline для категориальных признаков.
    """
    if preprocessing_config.missing_strategy is MissingStrategy.MEDIAN_MODE:
        imputer = SimpleImputer(strategy="most_frequent")
    elif preprocessing_config.missing_strategy is MissingStrategy.CONSTANT:
        imputer = SimpleImputer(strategy="constant", fill_value="missing")
    elif preprocessing_config.missing_strategy is MissingStrategy.DROP_ROWS:
        # handled earlier in data preparation; keep safe fallback
        imputer = SimpleImputer(strategy="most_frequent")
    else:
        raise ValueError(
            (
                "Неподдерживаемая стратегия пропусков для категориальных признаков: ",
                f"{preprocessing_config.missing_strategy!s}",
            )
        )

    if preprocessing_config.categorical_encoding_strategy is CategoricalEncodingStrategy.ONE_HOT:
        encoder = OneHotEncoder(
            handle_unknown="ignore",
            sparse_output=False,
        )
    elif preprocessing_config.categorical_encoding_strategy is CategoricalEncodingStrategy.ORDINAL:
        encoder = OrdinalEncoder(
            handle_unknown="use_encoded_value",
            unknown_value=-1,
        )
    else:
        raise ValueError(
            "Неподдерживаемая стратегия кодирования категориальных признаков: "
            f"{preprocessing_config.categorical_encoding_strategy!s}"
        )

    return Pipeline(
        steps=[
            ("imputer", imputer),
            ("encoder", encoder),
        ]
    )


def build_column_transformer(
    *,
    numeric_features: tuple[str, ...],
    categorical_features: tuple[str, ...],
    preprocessing_config: PreprocessingConfig,
) -> ColumnTransformer:
    """
    Построить ColumnTransformer по уже размеченным группам признаков.
    """
    transformers: list[tuple[str, Pipeline, list[str]]] = []

    if numeric_features:
        transformers.append(
            (
                "numeric",
                build_numeric_pipeline(preprocessing_config),
                list(numeric_features),
            )
        )

    if categorical_features:
        transformers.append(
            (
                "categorical",
                build_categorical_pipeline(preprocessing_config),
                list(categorical_features),
            )
        )

    if not transformers:
        raise ValueError("Невозможно построить ColumnTransformer без признаков.")

    return ColumnTransformer(
        transformers=transformers,
        remainder="drop",
        verbose_feature_names_out=False,
    )
