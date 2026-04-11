from __future__ import annotations

from pathlib import Path

import pytest

from src.core.data_loading import DataLoader
from src.core.decision_tree import (
    DecisionTreeBuilder,
    EmptyTrainingDataError,
    InvalidDecisionTreeParameterError,
    UnsupportedTargetError,
)
from src.core.preprocessing import DataPreprocessor
from src.domain.processed_dataset import ProcessedDataset

DATA_DIR = Path("data")


def test_tree_builder_builds_model_from_iris_csv() -> None:
    loader = DataLoader()
    preprocessor = DataPreprocessor(test_size=0.2, random_state=42)
    builder = DecisionTreeBuilder(random_state=42)

    dataset = loader.load(DATA_DIR / "iris.csv")
    processed = preprocessor.preprocess(dataset, target_column="species")
    model = builder.build(processed)

    assert model.is_fitted is True
    assert model.target_column == "species"
    assert len(model.feature_names) > 0
    assert len(model.class_names) == 3
    assert model.depth >= 1
    assert model.node_count >= 1
    assert model.leaf_count >= 1
    assert isinstance(model.feature_importances, dict)
    assert set(model.feature_importances.keys()) == set(model.feature_names)


def test_tree_builder_uses_parameters() -> None:
    loader = DataLoader()
    preprocessor = DataPreprocessor(test_size=0.2, random_state=42)
    builder = DecisionTreeBuilder(
        criterion="entropy",
        max_depth=3,
        min_samples_split=4,
        min_samples_leaf=2,
        random_state=7,
    )

    dataset = loader.load(DATA_DIR / "iris.csv")
    processed = preprocessor.preprocess(dataset, target_column="species")
    model = builder.build(processed)

    assert model.parameters["criterion"] == "entropy"
    assert model.parameters["max_depth"] == 3
    assert model.parameters["min_samples_split"] == 4
    assert model.parameters["min_samples_leaf"] == 2
    assert model.parameters["random_state"] == 7


def test_tree_builder_raises_for_invalid_criterion() -> None:
    with pytest.raises(InvalidDecisionTreeParameterError):
        DecisionTreeBuilder(criterion="invalid")


def test_tree_builder_raises_for_single_class_target() -> None:
    loader = DataLoader()
    preprocessor = DataPreprocessor(test_size=0.2, random_state=42)
    dataset = loader.load(DATA_DIR / "iris.csv")
    processed = preprocessor.preprocess(dataset, target_column="species")

    single_class_processed = ProcessedDataset(
        source_dataset_name=processed.source_dataset_name,
        target_column=processed.target_column,
        x_full=processed.x_full.copy(),
        y_full=processed.y_full.map(lambda _: "only_one_class"),
        x_train=processed.x_train.copy(),
        x_test=processed.x_test.copy(),
        y_train=processed.y_train.map(lambda _: "only_one_class"),
        y_test=processed.y_test.map(lambda _: "only_one_class"),
        feature_names=list(processed.feature_names),
        numeric_columns=list(processed.numeric_columns),
        categorical_columns=list(processed.categorical_columns),
        metadata=dict(processed.metadata),
    )

    builder = DecisionTreeBuilder()

    with pytest.raises(UnsupportedTargetError):
        builder.build(single_class_processed)


def test_tree_builder_raises_for_empty_train_data() -> None:
    processed = ProcessedDataset(
        source_dataset_name="empty",
        target_column="target",
        x_full=__import__("pandas").DataFrame(),
        y_full=__import__("pandas").Series(dtype="object"),
        x_train=__import__("pandas").DataFrame(),
        x_test=__import__("pandas").DataFrame(),
        y_train=__import__("pandas").Series(dtype="object"),
        y_test=__import__("pandas").Series(dtype="object"),
        feature_names=[],
        numeric_columns=[],
        categorical_columns=[],
        metadata={},
    )

    builder = DecisionTreeBuilder()

    with pytest.raises(EmptyTrainingDataError):
        builder.build(processed)
