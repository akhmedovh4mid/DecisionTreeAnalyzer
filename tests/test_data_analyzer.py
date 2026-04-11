from __future__ import annotations

from pathlib import Path

import pytest

from src.core.analysis import (
    DataAnalyzer,
    EmptyDatasetAnalysisError,
    InvalidAnalysisTargetColumnError,
)
from src.core.data_loading import DataLoader


@pytest.fixture()
def data_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "data"


@pytest.fixture()
def analyzer() -> DataAnalyzer:
    return DataAnalyzer()


@pytest.fixture()
def loader() -> DataLoader:
    return DataLoader()


def test_analyze_iris_csv(
    loader: DataLoader, analyzer: DataAnalyzer, data_dir: Path
) -> None:
    dataset = loader.load(data_dir / "iris.csv")

    result = analyzer.analyze(dataset, "species")

    assert result.source_dataset_name == "iris"
    assert result.target_column == "species"
    assert result.row_count > 0
    assert result.column_count > 0
    assert result.feature_count == 5
    assert result.class_count == 3
    assert "species" not in result.feature_columns
    assert len(result.numeric_columns) == 5
    assert len(result.categorical_columns) == 0
    assert result.total_missing_values >= 0
    assert isinstance(result.class_distribution, dict)
    assert sum(result.class_distribution.values()) == result.row_count


def test_analyze_iris_tsv(
    loader: DataLoader, analyzer: DataAnalyzer, data_dir: Path
) -> None:
    dataset = loader.load(data_dir / "iris.tsv")

    result = analyzer.analyze(dataset, "species")

    assert result.target_column == "species"
    assert result.class_count == 3
    assert result.feature_count == 5


def test_analyze_invalid_target_column(
    loader: DataLoader,
    analyzer: DataAnalyzer,
    data_dir: Path,
) -> None:
    dataset = loader.load(data_dir / "iris.csv")

    with pytest.raises(InvalidAnalysisTargetColumnError):
        analyzer.analyze(dataset, "unknown_target")


def test_analyze_empty_dataset(analyzer: DataAnalyzer) -> None:
    import pandas as pd

    from src.domain.dataset import Dataset

    dataset = Dataset(
        name="empty",
        source_path=Path("empty.csv"),
        data=pd.DataFrame(),
        file_format="csv",
    )

    with pytest.raises(EmptyDatasetAnalysisError):
        analyzer.analyze(dataset, "target")
