"""Инфраструктура загрузки CSV‑файлов."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
from pandas import DataFrame

from dt_analytics.shared import Result
from dt_analytics.shared.types import JsonDict, PathLike


@dataclass(frozen=True, slots=True)
class CsvLoadOptions:
    """
    Параметры чтения CSV‑файлов.

    Параметры
    ----------
    separator:
        Разделитель полей в CSV‑файле.
    encoding:
        Кодировка текста при чтении файла.
    header:
        Номер строки, используемой в качестве имён столбцов, или None при отсутствии заголовка.
    decimal:
        Разделитель десятичной части чисел с плавающей точкой.
    preview_rows:
        Количество строк, возвращаемых методами предпросмотра.
    """

    separator: str = ","
    encoding: str = "utf-8"
    header: int | None = 0
    decimal: str = "."
    preview_rows: int = 20


@dataclass(frozen=True, slots=True)
class CsvLoadResult:
    """Результат полной загрузки CSRF‑набора данных."""

    file_path: Path
    options: CsvLoadOptions
    dataframe: DataFrame
    row_count: int
    column_count: int
    columns: tuple[str, ...]
    dtypes: JsonDict = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CsvPreviewResult:
    """Результат предпросмотра CSV‑набора данных."""

    file_path: Path
    options: CsvLoadOptions
    preview_frame: DataFrame
    preview_row_count: int
    columns: tuple[str, ...]
    dtypes: JsonDict = field(default_factory=dict)


class CsvLoader:
    """Читает CSV‑файлы в объекты pandas DataFrame."""

    def preview(
        self,
        file_path: PathLike,
        options: CsvLoadOptions | None = None,
    ) -> Result[CsvPreviewResult]:
        """
        Загружает небольшой предпросмотр CSV, не читая весь файл целиком.
        """
        resolved_path = Path(file_path).expanduser().resolve()
        load_options = options or CsvLoadOptions()

        if not resolved_path.exists():
            return Result.fail(
                code="csv_file_not_found",
                message="CSV‑файл не найден.",
                details=str(resolved_path),
            )

        try:
            frame = pd.read_csv(
                resolved_path,
                sep=load_options.separator,
                encoding=load_options.encoding,
                header=load_options.header,
                decimal=load_options.decimal,
                nrows=load_options.preview_rows,
            )
        except UnicodeDecodeError as exc:
            return Result.fail(
                code="csv_decode_failed",
                message="Не удалось декодировать CSV‑файл с указанной кодировкой.",
                details=str(exc),
            )
        except pd.errors.EmptyDataError as exc:
            return Result.fail(
                code="csv_empty_file",
                message="CSV‑файл пуст.",
                details=str(exc),
            )
        except pd.errors.ParserError as exc:
            return Result.fail(
                code="csv_parse_failed",
                message="Не удалось распарсить CSV‑файл.",
                details=str(exc),
            )
        except OSError as exc:
            return Result.fail(
                code="csv_open_failed",
                message="Не удалось открыть CSV‑файл.",
                details=str(exc),
            )

        preview_result = CsvPreviewResult(
            file_path=resolved_path,
            options=load_options,
            preview_frame=frame,
            preview_row_count=len(frame.index),
            columns=tuple(str(column) for column in frame.columns),
            dtypes={
                str(key): str(value) for key, value in frame.dtypes.astype(str).to_dict().items()
            },
        )
        return Result.ok(preview_result)

    def load(
        self,
        file_path: PathLike,
        options: CsvLoadOptions | None = None,
    ) -> Result[CsvLoadResult]:
        """
        Полностью загружает CSV‑набор данных в память.
        """
        resolved_path = Path(file_path).expanduser().resolve()
        load_options = options or CsvLoadOptions()

        if not resolved_path.exists():
            return Result.fail(
                code="csv_file_not_found",
                message="CSV‑файл не найден.",
                details=str(resolved_path),
            )

        try:
            frame = pd.read_csv(
                resolved_path,
                sep=load_options.separator,
                encoding=load_options.encoding,
                header=load_options.header,
                decimal=load_options.decimal,
            )
        except UnicodeDecodeError as exc:
            return Result.fail(
                code="csv_decode_failed",
                message="Не удалось декодировать CSV‑файл с указанной кодировкой.",
                details=str(exc),
            )
        except pd.errors.EmptyDataError as exc:
            return Result.fail(
                code="csv_empty_file",
                message="CSV‑файл пуст.",
                details=str(exc),
            )
        except pd.errors.ParserError as exc:
            return Result.fail(
                code="csv_parse_failed",
                message="Не удалось распарсить CSV‑файл.",
                details=str(exc),
            )
        except OSError as exc:
            return Result.fail(
                code="csv_open_failed",
                message="Не удалось открыть CSV‑файл.",
                details=str(exc),
            )

        if frame.columns.duplicated().any():
            return Result.fail(
                code="csv_duplicate_columns",
                message="CSV‑файл содержит дублирующиеся имена столбцов.",
                details=str(list(frame.columns)),
            )

        result = CsvLoadResult(
            file_path=resolved_path,
            options=load_options,
            dataframe=frame,
            row_count=len(frame.index),
            column_count=len(frame.columns),
            columns=tuple(str(column) for column in frame.columns),
            dtypes={
                str(key): str(value) for key, value in frame.dtypes.astype(str).to_dict().items()
            },
        )
        return Result.ok(result)
