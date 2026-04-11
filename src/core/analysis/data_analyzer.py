from __future__ import annotations

from typing import Any, cast

import pandas as pd
from pandas.api.types import is_numeric_dtype

from src.domain.dataset import Dataset
from src.domain.dataset_info import DatasetInfo


class DataAnalysisError(Exception):
    """Базовая ошибка модуля анализа данных."""


class EmptyDatasetAnalysisError(DataAnalysisError):
    """Ошибка: набор данных пуст и не может быть проанализирован."""


class InvalidAnalysisTargetColumnError(DataAnalysisError):
    """Ошибка: целевой столбец отсутствует или некорректен."""


class DataAnalyzer:
    """
    Минимальный, но полноценный сервис анализа набора данных.

    Текущая реализация:
    - анализирует исходный Dataset;
    - проверяет целевой столбец;
    - формирует статистическую сводку;
    - возвращает результат в виде DatasetInfo.
    """

    def analyze(self, dataset: Dataset, target_column: str) -> DatasetInfo:
        dataframe = self._validate_dataset_and_copy(dataset)
        target_column = self._validate_target_column(dataframe, target_column)

        feature_columns = [
            str(column)
            for column in dataframe.columns.tolist()
            if str(column) != target_column
        ]

        numeric_columns, categorical_columns = self._split_feature_columns(
            dataframe=dataframe,
            feature_columns=feature_columns,
        )

        missing_values_by_column = self._build_missing_values_summary(dataframe)
        duplicate_row_count = self._count_duplicates(dataframe)
        class_distribution = self._build_class_distribution(
            dataframe=dataframe,
            target_column=target_column,
        )
        numeric_summary = self._build_numeric_summary(
            dataframe=dataframe,
            numeric_columns=numeric_columns,
        )

        metadata = {
            "source_path": str(dataset.source_path),
            "file_format": dataset.file_format,
            "row_count": int(dataframe.shape[0]),
            "column_count": int(dataframe.shape[1]),
            "feature_count": int(len(feature_columns)),
            "numeric_feature_count": int(len(numeric_columns)),
            "categorical_feature_count": int(len(categorical_columns)),
            "total_missing_values": int(sum(missing_values_by_column.values())),
            "duplicate_row_count": duplicate_row_count,
            "class_count": int(len(class_distribution)),
        }

        return DatasetInfo(
            source_dataset_name=dataset.name,
            target_column=target_column,
            row_count=int(dataframe.shape[0]),
            column_count=int(dataframe.shape[1]),
            feature_columns=feature_columns,
            numeric_columns=numeric_columns,
            categorical_columns=categorical_columns,
            missing_values_by_column=missing_values_by_column,
            duplicate_row_count=duplicate_row_count,
            class_distribution=class_distribution,
            numeric_summary=numeric_summary,
            metadata=metadata,
        )

    @staticmethod
    def _validate_dataset_and_copy(dataset: Dataset) -> pd.DataFrame:
        if dataset.is_empty:
            raise EmptyDatasetAnalysisError(
                f"Невозможно выполнить анализ: dataset '{dataset.name}' пуст."
            )

        dataframe = dataset.data.copy()
        dataframe.columns = [str(column).strip() for column in dataframe.columns]
        return dataframe

    @staticmethod
    def _validate_target_column(dataframe: pd.DataFrame, target_column: str) -> str:
        normalized_target = str(target_column).strip()

        if not normalized_target:
            raise InvalidAnalysisTargetColumnError(
                "Имя целевого столбца не может быть пустым."
            )

        if normalized_target not in dataframe.columns:
            available = ", ".join(map(str, dataframe.columns.tolist()))
            raise InvalidAnalysisTargetColumnError(
                f"Целевой столбец '{normalized_target}' не найден. "
                f"Доступные столбцы: {available}"
            )

        return normalized_target

    @staticmethod
    def _split_feature_columns(
        dataframe: pd.DataFrame,
        feature_columns: list[str],
    ) -> tuple[list[str], list[str]]:
        numeric_columns: list[str] = []
        categorical_columns: list[str] = []

        for column in feature_columns:
            series = dataframe[column]
            if is_numeric_dtype(series):
                numeric_columns.append(column)
            else:
                categorical_columns.append(column)

        return numeric_columns, categorical_columns

    @staticmethod
    def _build_missing_values_summary(dataframe: pd.DataFrame) -> dict[str, int]:
        result: dict[str, int] = {}

        for column in dataframe.columns:
            missing_count = dataframe[column].isna().sum()
            result[str(column)] = DataAnalyzer._to_int(missing_count)

        return result

    @staticmethod
    def _count_duplicates(dataframe: pd.DataFrame) -> int:
        duplicate_count = dataframe.duplicated().sum()
        return DataAnalyzer._to_int(duplicate_count)

    @staticmethod
    def _build_class_distribution(
        dataframe: pd.DataFrame,
        target_column: str,
    ) -> dict[str, int]:
        target_series = cast(pd.Series, dataframe[target_column]).astype("string")
        counts = cast(pd.Series, target_series.value_counts(dropna=False))

        distribution: dict[str, int] = {}
        for class_name, count in counts.items():
            distribution[str(class_name)] = DataAnalyzer._to_int(count)

        return distribution

    @staticmethod
    def _build_numeric_summary(
        dataframe: pd.DataFrame,
        numeric_columns: list[str],
    ) -> dict[str, dict[str, float | None]]:
        summary: dict[str, dict[str, float | None]] = {}

        for column in numeric_columns:
            raw_series = cast(pd.Series, dataframe[column])

            numeric_series = raw_series.apply(
                lambda value: pd.to_numeric(value, errors="coerce")
            )
            numeric_series = cast(pd.Series, numeric_series.astype("float64"))

            min_value = numeric_series.min()
            max_value = numeric_series.max()
            mean_value = numeric_series.mean()
            median_value = numeric_series.median()
            std_value = numeric_series.std()

            summary[column] = {
                "min": DataAnalyzer._to_float_or_none(min_value),
                "max": DataAnalyzer._to_float_or_none(max_value),
                "mean": DataAnalyzer._to_float_or_none(mean_value),
                "median": DataAnalyzer._to_float_or_none(median_value),
                "std": DataAnalyzer._to_float_or_none(std_value),
            }

        return summary

    @staticmethod
    def _to_int(value: Any) -> int:
        if hasattr(value, "item"):
            try:
                return int(value.item())
            except TypeError, ValueError:
                pass
        return int(value)

    @staticmethod
    def _to_float_or_none(value: Any) -> float | None:
        if value is None:
            return None

        try:
            if bool(pd.isna(value)):
                return None
        except TypeError, ValueError:
            return None

        try:
            return float(value)
        except TypeError, ValueError:
            return None
