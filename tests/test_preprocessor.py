from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.core.data_loading import DataLoader
from src.core.preprocessing import DataPreprocessor, InvalidTargetColumnError
from src.domain.processed_dataset import ProcessedDataset

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"


@pytest.mark.parametrize(
    "file_name",
    [
        "iris.csv",
        "iris.tsv",
        "iris.json",
        "iris.xlsx",
    ],
)
def test_preprocess_returns_processed_dataset_for_supported_formats(
    file_name: str,
) -> None:
    loader = DataLoader()
    preprocessor = DataPreprocessor(test_size=0.2, random_state=42)

    dataset = loader.load(DATA_DIR / file_name)
    processed = preprocessor.preprocess(dataset, target_column="species")

    assert isinstance(processed, ProcessedDataset)
    assert processed.train_size > 0
    assert processed.test_size > 0
    assert processed.feature_count > 0
    assert processed.target_column == "species"

    assert not processed.x_train.empty
    assert not processed.x_test.empty
    assert not processed.y_train.empty
    assert not processed.y_test.empty

    assert processed.x_train.isna().sum().sum() == 0
    assert processed.x_test.isna().sum().sum() == 0

    assert "species" not in processed.x_train.columns
    assert "species" not in processed.x_test.columns


def test_preprocess_splits_iris_dataset_with_expected_sizes() -> None:
    loader = DataLoader()
    preprocessor = DataPreprocessor(test_size=0.2, random_state=42)

    dataset = loader.load(DATA_DIR / "iris.csv")
    processed = preprocessor.preprocess(dataset, target_column="species")

    assert processed.train_size == 120
    assert processed.test_size == 30
    assert processed.class_count == 3


def test_transform_features_can_process_new_rows_after_fit() -> None:
    loader = DataLoader()
    preprocessor = DataPreprocessor(test_size=0.2, random_state=42)

    dataset = loader.load(DATA_DIR / "iris.csv")
    preprocessor.preprocess(dataset, target_column="species")

    new_rows = dataset.data.drop(columns=["species"]).head(5).copy()
    transformed = preprocessor.transform_features(new_rows)

    assert isinstance(transformed, pd.DataFrame)
    assert transformed.shape[0] == 5
    assert transformed.shape[1] > 0
    assert transformed.isna().sum().sum() == 0


def test_preprocess_raises_for_unknown_target_column() -> None:
    loader = DataLoader()
    preprocessor = DataPreprocessor()

    dataset = loader.load(DATA_DIR / "iris.csv")

    with pytest.raises(InvalidTargetColumnError):
        preprocessor.preprocess(dataset, target_column="unknown_target")
