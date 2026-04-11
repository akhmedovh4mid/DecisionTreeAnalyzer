from __future__ import annotations

from pathlib import Path

import pytest

from src.core.data_loading import DataLoader
from src.core.decision_tree import DecisionTreeBuilder
from src.core.evaluation import (
    MissingActualValuesError,
    QualityEvaluator,
    UnsupportedAverageStrategyError,
)
from src.core.prediction import Predictor
from src.core.preprocessing import DataPreprocessor

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


@pytest.mark.parametrize(
    "file_name",
    [
        "iris.csv",
        "iris.json",
        "iris.xlsx",
        "iris.tsv",
    ],
)
def test_quality_evaluator_returns_metrics_for_real_pipeline(file_name: str) -> None:
    loader = DataLoader()
    preprocessor = DataPreprocessor(test_size=0.25, random_state=42)
    builder = DecisionTreeBuilder(random_state=42)
    predictor = Predictor()
    evaluator = QualityEvaluator()

    dataset = loader.load(DATA_DIR / file_name)
    processed = preprocessor.preprocess(dataset, target_column="species")
    model = builder.build(processed)
    prediction_result = predictor.predict(model, processed, on="test")

    metrics = evaluator.evaluate(prediction_result)

    assert metrics.source_dataset_name == dataset.name
    assert metrics.target_column == "species"
    assert metrics.prediction_scope == "test"
    assert metrics.average == "weighted"

    assert 0.0 <= metrics.accuracy <= 1.0
    assert 0.0 <= metrics.precision <= 1.0
    assert 0.0 <= metrics.recall <= 1.0
    assert 0.0 <= metrics.f1_score <= 1.0

    assert metrics.support == len(prediction_result.predicted_values)
    assert metrics.class_count == 3
    assert metrics.is_multiclass is True
    assert metrics.is_binary is False

    rows, cols = metrics.confusion_matrix_shape
    assert rows == 3
    assert cols == 3

    assert set(metrics.class_names) == {"setosa", "versicolor", "virginica"}
    assert sum(metrics.support_by_class.values()) == metrics.support
    assert sum(metrics.actual_class_distribution.values()) == metrics.support
    assert sum(metrics.predicted_class_distribution.values()) == metrics.support


def test_quality_evaluator_raises_when_actual_values_are_missing() -> None:
    loader = DataLoader()
    preprocessor = DataPreprocessor(test_size=0.25, random_state=42)
    builder = DecisionTreeBuilder(random_state=42)
    predictor = Predictor()
    evaluator = QualityEvaluator()

    dataset = loader.load(DATA_DIR / "iris.csv")
    processed = preprocessor.preprocess(dataset, target_column="species")
    model = builder.build(processed)

    external_features = processed.x_test.copy()
    prediction_result = predictor.predict_features(model, external_features)

    with pytest.raises(MissingActualValuesError):
        evaluator.evaluate(prediction_result)


def test_quality_evaluator_raises_for_unsupported_average() -> None:
    loader = DataLoader()
    preprocessor = DataPreprocessor(test_size=0.25, random_state=42)
    builder = DecisionTreeBuilder(random_state=42)
    predictor = Predictor()
    evaluator = QualityEvaluator()

    dataset = loader.load(DATA_DIR / "iris.csv")
    processed = preprocessor.preprocess(dataset, target_column="species")
    model = builder.build(processed)
    prediction_result = predictor.predict(model, processed, on="test")

    with pytest.raises(UnsupportedAverageStrategyError):
        evaluator.evaluate(prediction_result, average="samples")  # type: ignore[arg-type]


def test_quality_evaluator_binary_average_is_invalid_for_multiclass() -> None:
    loader = DataLoader()
    preprocessor = DataPreprocessor(test_size=0.25, random_state=42)
    builder = DecisionTreeBuilder(random_state=42)
    predictor = Predictor()
    evaluator = QualityEvaluator()

    dataset = loader.load(DATA_DIR / "iris.csv")
    processed = preprocessor.preprocess(dataset, target_column="species")
    model = builder.build(processed)
    prediction_result = predictor.predict(model, processed, on="test")

    with pytest.raises(UnsupportedAverageStrategyError):
        evaluator.evaluate(prediction_result, average="binary")
