from __future__ import annotations

from pathlib import Path

import pytest

from src.core.data_loading.data_loader import (
    DataLoader,
    DataLoadingError,
    FileNotFoundDataLoadingError,
)


@pytest.fixture(scope="module")
def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def data_dir(project_root: Path) -> Path:
    path = project_root / "data"
    if not path.exists():
        pytest.fail(f"Каталог с тестовыми данными не найден: {path}")
    return path


@pytest.fixture(scope="module")
def loader() -> DataLoader:
    return DataLoader()


def test_load_csv_success(loader: DataLoader, data_dir: Path) -> None:
    file_path = data_dir / "iris.csv"

    dataset = loader.load(file_path)

    assert dataset.name == "iris"
    assert dataset.file_format == "csv"
    assert dataset.row_count > 0
    assert dataset.column_count > 0
    assert len(dataset.columns) == dataset.column_count
    assert not dataset.is_empty


def test_load_tsv_success(loader: DataLoader, data_dir: Path) -> None:
    file_path = data_dir / "iris.tsv"

    dataset = loader.load(file_path)

    assert dataset.name == "iris"
    assert dataset.file_format == "tsv"
    assert dataset.row_count > 0
    assert dataset.column_count > 0
    assert len(dataset.columns) == dataset.column_count
    assert not dataset.is_empty


def test_load_json_success(loader: DataLoader, data_dir: Path) -> None:
    file_path = data_dir / "iris.json"

    dataset = loader.load(file_path)

    assert dataset.name == "iris"
    assert dataset.file_format == "json"
    assert dataset.row_count > 0
    assert dataset.column_count > 0
    assert len(dataset.columns) == dataset.column_count
    assert not dataset.is_empty


def test_load_excel_success(loader: DataLoader, data_dir: Path) -> None:
    file_path = data_dir / "iris.xlsx"

    dataset = loader.load(file_path)

    assert dataset.name == "iris"
    assert dataset.file_format == "xlsx"
    assert dataset.row_count > 0
    assert dataset.column_count > 0
    assert len(dataset.columns) == dataset.column_count
    assert not dataset.is_empty


def test_loaded_datasets_have_same_shape(loader: DataLoader, data_dir: Path) -> None:
    csv_dataset = loader.load(data_dir / "iris.csv")
    tsv_dataset = loader.load(data_dir / "iris.tsv")
    json_dataset = loader.load(data_dir / "iris.json")
    xlsx_dataset = loader.load(data_dir / "iris.xlsx")

    expected_shape = csv_dataset.data.shape

    assert tsv_dataset.data.shape == expected_shape
    assert json_dataset.data.shape == expected_shape
    assert xlsx_dataset.data.shape == expected_shape


def test_loaded_datasets_have_same_columns(loader: DataLoader, data_dir: Path) -> None:
    csv_dataset = loader.load(data_dir / "iris.csv")
    tsv_dataset = loader.load(data_dir / "iris.tsv")
    json_dataset = loader.load(data_dir / "iris.json")
    xlsx_dataset = loader.load(data_dir / "iris.xlsx")

    expected_columns = csv_dataset.columns

    assert tsv_dataset.columns == expected_columns
    assert json_dataset.columns == expected_columns
    assert xlsx_dataset.columns == expected_columns


def test_file_not_found(loader: DataLoader, data_dir: Path) -> None:
    missing_file = data_dir / "missing_file.csv"

    with pytest.raises(FileNotFoundDataLoadingError):
        loader.load(missing_file)


def test_unsupported_format(loader: DataLoader, tmp_path: Path) -> None:
    file_path = tmp_path / "test.xml"
    file_path.write_text("<root></root>", encoding="utf-8")

    with pytest.raises(DataLoadingError):
        loader.load(file_path)
