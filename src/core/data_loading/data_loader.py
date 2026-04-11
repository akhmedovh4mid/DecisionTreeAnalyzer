from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.domain.dataset import Dataset
from src.infrastructure.file_system import (
    BaseFileReader,
    CsvReader,
    ExcelReader,
    JsonReader,
    UnsupportedFileFormatError,
    detect_file_format,
)


class DataLoadingError(Exception):
    """
    Базовая ошибка модуля загрузки данных.
    """


class FileNotFoundDataLoadingError(DataLoadingError):
    """
    Ошибка: файл не найден.
    """


class EmptyDataError(DataLoadingError):
    """
    Ошибка: файл успешно прочитан, но данные пусты.
    """


class DataLoader:
    """
    Центральный сервис модуля загрузки данных.
    Определяет формат файла, выбирает reader и возвращает Dataset.
    """

    def __init__(self, readers: list[BaseFileReader] | None = None) -> None:
        self._readers: list[BaseFileReader] = readers or [
            CsvReader(),
            ExcelReader(),
            JsonReader(),
        ]

    def load(self, file_path: str | Path) -> Dataset:
        path = Path(file_path).expanduser().resolve()

        if not path.exists():
            raise FileNotFoundDataLoadingError(f"Файл не найден: {path}")

        if not path.is_file():
            raise FileNotFoundDataLoadingError(
                f"Указанный путь не является файлом: {path}"
            )

        try:
            file_format = detect_file_format(path)
            reader = self._get_reader_for_file(path)
            dataframe = reader.read(path)
        except UnsupportedFileFormatError as exc:
            raise DataLoadingError(str(exc)) from exc
        except Exception as exc:
            raise DataLoadingError(
                f"Ошибка при загрузке файла '{path.name}': {exc}"
            ) from exc

        dataframe = self._normalize_dataframe(dataframe)

        if dataframe.empty:
            raise EmptyDataError(f"Файл '{path.name}' не содержит данных.")

        return Dataset(
            name=path.stem,
            source_path=path,
            data=dataframe,
            file_format=file_format,
            metadata={
                "source_name": path.name,
                "row_count": int(dataframe.shape[0]),
                "column_count": int(dataframe.shape[1]),
            },
        )

    def _get_reader_for_file(self, file_path: Path) -> BaseFileReader:
        for reader in self._readers:
            if reader.can_read(file_path):
                return reader

        raise UnsupportedFileFormatError(
            f"Не найден reader для файла: {file_path.name}"
        )

    @staticmethod
    def _normalize_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
        normalized = dataframe.copy()

        normalized.columns = [str(column).strip() for column in normalized.columns]

        if normalized.index.name is not None:
            normalized.index.name = str(normalized.index.name).strip()

        return normalized
