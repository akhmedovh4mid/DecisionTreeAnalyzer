from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.core.data_loading import DataLoader
from src.core.decision_tree import DecisionTreeBuilder
from src.core.prediction import (
    EmptyPredictionInputError,
    IncompatibleFeatureSpaceError,
    Predictor,
)
from src.core.preprocessing import DataPreprocessor

DATA_DIR = Path("data")


def _build_ready_model_and_dataset(file_name: str = "iris.csv"):
    loader = DataLoader()
    preprocessor = DataPreprocessor(test_size=0.2, random_state=42)
    builder = DecisionTreeBuilder(random_state=42)
    predictor = Predictor()

    dataset = loader.load(DATA_DIR / file_name)
    processed = preprocessor.preprocess(dataset, target_column="species")
    model = builder.build(processed)

    return predictor, model, processed


def test_predictor_predict_on_test_returns_prediction_result() -> None:
    predictor, model, processed = _build_ready_model_and_dataset("iris.csv")

    result = predictor.predict(model, processed, on="test")

    assert result.row_count == processed.test_size
    assert result.has_actual_values is True
    assert result.has_probabilities is True
    assert list(result.feature_names) == list(model.feature_names)
    assert set(result.predicted_values.unique()).issubset(set(model.class_names))


def test_predictor_predict_on_full_returns_all_rows() -> None:
    predictor, model, processed = _build_ready_model_and_dataset("iris.tsv")

    result = predictor.predict(model, processed, on="full")

    assert result.row_count == len(processed.x_full)
    assert result.actual_values is not None
    assert len(result.predicted_values) == len(processed.y_full)


def test_predictor_predict_features_returns_external_result() -> None:
    predictor, model, processed = _build_ready_model_and_dataset("iris.xlsx")

    external_features = processed.x_test.copy()

    result = predictor.predict_features(
        model,
        external_features,
        source_dataset_name="external_iris_subset",
    )

    assert result.prediction_scope == "external"
    assert result.actual_values is None
    assert result.row_count == len(external_features)
    assert result.has_probabilities is True


def test_predictor_raises_on_missing_feature_columns() -> None:
    predictor, model, processed = _build_ready_model_and_dataset("iris.json")

    broken_features = processed.x_test.drop(columns=[processed.x_test.columns[0]])

    with pytest.raises(IncompatibleFeatureSpaceError):
        predictor.predict_features(model, broken_features)


def test_predictor_raises_on_extra_feature_columns() -> None:
    predictor, model, processed = _build_ready_model_and_dataset("iris.csv")

    broken_features = processed.x_test.copy()
    broken_features["unexpected_feature"] = 1

    with pytest.raises(IncompatibleFeatureSpaceError):
        predictor.predict_features(model, broken_features)


def test_predictor_raises_on_empty_dataframe() -> None:
    predictor, model, processed = _build_ready_model_and_dataset("iris.csv")

    empty_features = pd.DataFrame(columns=processed.x_test.columns)

    with pytest.raises(EmptyPredictionInputError):
        predictor.predict_features(model, empty_features)
