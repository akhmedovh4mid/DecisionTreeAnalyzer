"""Извлечение важности признаков из обученного sklearn‑pipeline."""

from __future__ import annotations

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.tree import DecisionTreeClassifier

from dt_analytics.shared import Result
from dt_analytics.shared.types import JsonDict


class FeatureImportanceExtractor:
    """Извлечение значений важности признаков из обученного конвейера preprocessing + model."""

    def extract(self, pipeline: Pipeline) -> Result[JsonDict]:
        """Вернуть важность признаков, сопоставленную с их преобразованными именами."""
        preprocessing = pipeline.named_steps.get("preprocessing")
        model = pipeline.named_steps.get("model")

        if not isinstance(preprocessing, ColumnTransformer):
            return Result.fail(
                code="feature_importance_preprocessing_missing",
                message="В конвейере отсутствует валидный препроцессор признаков.",
            )

        if not isinstance(model, DecisionTreeClassifier):
            return Result.fail(
                code="feature_importance_model_missing",
                message="В конвейере отсутствует обученный DecisionTreeClassifier.",
            )

        if not hasattr(model, "feature_importances_"):
            return Result.fail(
                code="feature_importance_not_trained",
                message="Модель дерева решений не обучена.",
            )

        try:
            feature_names = list(preprocessing.get_feature_names_out())
            importances = list(model.feature_importances_)
        except Exception as exc:  # noqa: BLE001
            return Result.fail(
                code="feature_importance_extract_failed",
                message="Не удалось извлечь названия признаков или значения важности.",
                details=str(exc),
            )

        if len(feature_names) != len(importances):
            return Result.fail(
                code="feature_importance_length_mismatch",
                message="Длины вектора названий признаков и вектора важности не совпадают.",
                details=f"{len(feature_names)} != {len(importances)}",
            )

        result: JsonDict = {
            feature_name: float(importance)
            for feature_name, importance in zip(feature_names, importances, strict=True)
        }
        return Result.ok(result)
