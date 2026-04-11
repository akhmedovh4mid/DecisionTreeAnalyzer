from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

import pandas as pd
from pandas.api.types import is_numeric_dtype
from sklearn.model_selection import train_test_split

from src.domain.dataset import Dataset
from src.domain.processed_dataset import ProcessedDataset


class PreprocessingError(Exception):
    """Базовая ошибка модуля предобработки."""


class InvalidTargetColumnError(PreprocessingError):
    """Ошибка: целевой столбец отсутствует или некорректен."""


class EmptyPreprocessedDataError(PreprocessingError):
    """Ошибка: после предобработки данные пусты или непригодны для работы."""


class NotFittedPreprocessorError(PreprocessingError):
    """Ошибка: препроцессор ещё не был обучен на данных."""


@dataclass(slots=True)
class _PreprocessingState:
    target_column: str
    numeric_columns: list[str]
    categorical_columns: list[str]
    fill_values: dict[str, Any]
    encoded_feature_names: list[str]
    raw_feature_columns: list[str]


class DataPreprocessor:
    """
    Минимальный, но полноценный сервис предобработки данных.

    Основной сценарий:
    1. Проверка target column
    2. Удаление строк без target
    3. Разделение на признаки и target
    4. train/test split
    5. Заполнение пропусков
    6. One-hot encoding категориальных признаков
    """

    def __init__(
        self,
        *,
        test_size: float = 0.2,
        random_state: int = 42,
        shuffle: bool = True,
    ) -> None:
        self._test_size = test_size
        self._random_state = random_state
        self._shuffle = shuffle
        self._state: _PreprocessingState | None = None

    @property
    def is_fitted(self) -> bool:
        return self._state is not None

    def preprocess(self, dataset: Dataset, target_column: str) -> ProcessedDataset:
        """
        Полный цикл предобработки:
        - fit на train части
        - transform train/test/full
        - возврат ProcessedDataset
        """
        dataframe = self._validate_dataset_and_copy(dataset)
        target_column = self._validate_target_column(dataframe, target_column)

        dataframe = dataframe.dropna(subset=[target_column]).reset_index(drop=True)
        if dataframe.empty:
            raise EmptyPreprocessedDataError(
                "После удаления строк без целевого признака данные пусты."
            )

        x_raw = dataframe.drop(columns=[target_column]).copy()
        y = cast(pd.Series, dataframe[target_column].copy())

        if x_raw.empty or x_raw.shape[1] == 0:
            raise EmptyPreprocessedDataError(
                "Невозможно выполнить предобработку: отсутствуют признаки."
            )

        x_train_raw, x_test_raw, y_train, y_test, stratified = self._split_data(
            x_raw, y
        )

        self._fit(x_train_raw, target_column=target_column)

        x_train = self.transform_features(x_train_raw)
        x_test = self.transform_features(x_test_raw)
        x_full = self.transform_features(x_raw)

        if x_train.empty or x_test.empty:
            raise EmptyPreprocessedDataError(
                "После предобработки train/test выборки оказались пустыми."
            )

        state = self._require_state()

        metadata = {
            "source_dataset_name": dataset.name,
            "source_file_format": dataset.file_format,
            "source_path": str(dataset.source_path),
            "row_count_before": int(dataset.row_count),
            "row_count_after_target_cleanup": int(len(dataframe)),
            "feature_count_before_encoding": int(len(state.raw_feature_columns)),
            "feature_count_after_encoding": int(len(state.encoded_feature_names)),
            "train_size": int(len(x_train)),
            "test_size": int(len(x_test)),
            "stratified_split": bool(stratified),
        }

        return ProcessedDataset(
            source_dataset_name=dataset.name,
            target_column=target_column,
            x_full=x_full,
            y_full=y.reset_index(drop=True),
            x_train=x_train.reset_index(drop=True),
            x_test=x_test.reset_index(drop=True),
            y_train=y_train.reset_index(drop=True),
            y_test=y_test.reset_index(drop=True),
            feature_names=list(x_train.columns),
            numeric_columns=list(state.numeric_columns),
            categorical_columns=list(state.categorical_columns),
            metadata=metadata,
        )

    def transform_features(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """
        Преобразует новые данные на основе уже обученного состояния препроцессора.
        Это пригодится в модуле прогнозирования.
        """
        state = self._require_state()

        missing_columns = [
            column
            for column in state.raw_feature_columns
            if column not in dataframe.columns
        ]
        if missing_columns:
            raise PreprocessingError(
                f"Во входных данных отсутствуют обязательные признаки: {missing_columns}"
            )

        prepared = dataframe.loc[:, state.raw_feature_columns].copy()

        for column in state.numeric_columns:
            prepared[column] = pd.to_numeric(prepared[column], errors="coerce")
            prepared[column] = prepared[column].fillna(state.fill_values[column])

        for column in state.categorical_columns:
            prepared[column] = prepared[column].astype("string")
            prepared[column] = prepared[column].fillna(state.fill_values[column])

        encoded = pd.get_dummies(
            prepared,
            columns=state.categorical_columns,
            dtype=int,
        )

        encoded = encoded.reindex(columns=state.encoded_feature_names, fill_value=0)
        return encoded

    def _fit(self, x_train_raw: pd.DataFrame, *, target_column: str) -> None:
        raw_feature_columns = [str(column) for column in x_train_raw.columns.tolist()]

        numeric_columns: list[str] = []
        categorical_columns: list[str] = []
        fill_values: dict[str, Any] = {}

        for column in raw_feature_columns:
            series = x_train_raw[column]
            if is_numeric_dtype(series):
                numeric_columns.append(column)
                numeric_series = cast(pd.Series, pd.to_numeric(series, errors="coerce"))
                median_value = numeric_series.median()
                if pd.isna(median_value):
                    median_value = 0.0
                fill_values[column] = float(median_value)
            else:
                categorical_columns.append(column)
                non_null = series.dropna()
                if non_null.empty:
                    fill_values[column] = "__missing__"
                else:
                    fill_values[column] = str(non_null.mode(dropna=True).iloc[0])

        prepared_train = x_train_raw.copy()

        for column in numeric_columns:
            prepared_train[column] = pd.to_numeric(
                prepared_train[column], errors="coerce"
            )
            prepared_train[column] = prepared_train[column].fillna(fill_values[column])

        for column in categorical_columns:
            prepared_train[column] = prepared_train[column].astype("string")
            prepared_train[column] = prepared_train[column].fillna(fill_values[column])

        encoded_train = pd.get_dummies(
            prepared_train,
            columns=categorical_columns,
            dtype=int,
        )

        self._state = _PreprocessingState(
            target_column=target_column,
            numeric_columns=numeric_columns,
            categorical_columns=categorical_columns,
            fill_values=fill_values,
            encoded_feature_names=[
                str(column) for column in encoded_train.columns.tolist()
            ],
            raw_feature_columns=raw_feature_columns,
        )

    def _split_data(
        self,
        x_raw: pd.DataFrame,
        y: pd.Series,
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, bool]:
        stratify = None
        stratified = False

        unique_classes = y.nunique(dropna=True)
        min_class_count = y.value_counts(dropna=True).min() if unique_classes > 0 else 0

        if unique_classes > 1 and min_class_count >= 2:
            stratify = y

        try:
            split_result = train_test_split(
                x_raw,
                y,
                test_size=self._test_size,
                random_state=self._random_state,
                shuffle=self._shuffle,
                stratify=stratify,
            )
            x_train, x_test, y_train, y_test = cast(
                tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series],
                split_result,
            )
            stratified = stratify is not None
            return x_train, x_test, y_train, y_test, stratified
        except ValueError:
            split_result = train_test_split(
                x_raw,
                y,
                test_size=self._test_size,
                random_state=self._random_state,
                shuffle=self._shuffle,
                stratify=None,
            )
            x_train, x_test, y_train, y_test = cast(
                tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series],
                split_result,
            )
            return x_train, x_test, y_train, y_test, False

    @staticmethod
    def _validate_dataset_and_copy(dataset: Dataset) -> pd.DataFrame:
        if dataset.is_empty:
            raise EmptyPreprocessedDataError(
                f"Невозможно выполнить предобработку: dataset '{dataset.name}' пуст."
            )

        dataframe = dataset.data.copy()
        dataframe.columns = [str(column).strip() for column in dataframe.columns]
        return dataframe

    @staticmethod
    def _validate_target_column(dataframe: pd.DataFrame, target_column: str) -> str:
        normalized_target = str(target_column).strip()

        if not normalized_target:
            raise InvalidTargetColumnError("Имя целевого столбца не может быть пустым.")

        if normalized_target not in dataframe.columns:
            available = ", ".join(map(str, dataframe.columns.tolist()))
            raise InvalidTargetColumnError(
                f"Целевой столбец '{normalized_target}' не найден. "
                f"Доступные столбцы: {available}"
            )

        return normalized_target

    def _require_state(self) -> _PreprocessingState:
        if self._state is None:
            raise NotFittedPreprocessorError(
                "Препроцессор ещё не обучен. Сначала вызови preprocess(...)."
            )
        return self._state
