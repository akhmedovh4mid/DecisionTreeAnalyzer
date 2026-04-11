from __future__ import annotations

from typing import Literal

import pandas as pd

from src.domain.decision_tree_model import DecisionTreeModel
from src.domain.prediction_result import PredictionResult
from src.domain.processed_dataset import ProcessedDataset


class PredictionError(Exception):
    """Базовая ошибка модуля прогнозирования."""


class NotFittedModelPredictionError(PredictionError):
    """Ошибка: модель дерева решений ещё не обучена."""


class EmptyPredictionInputError(PredictionError):
    """Ошибка: входные данные для прогнозирования пусты."""


class IncompatibleFeatureSpaceError(PredictionError):
    """Ошибка: признаки входных данных несовместимы с моделью."""


PredictionDatasetKind = Literal["train", "test", "full"]


class Predictor:
    """
    Минимальный, но расширяемый сервис прогнозирования.

    Поддерживает:
    - прогноз на train/test/full из ProcessedDataset;
    - прогноз на новых уже подготовленных признаках (DataFrame);
    - возврат классов и вероятностей классов;
    - строгую проверку пространства признаков.
    """

    def predict(
        self,
        model: DecisionTreeModel,
        dataset: ProcessedDataset,
        *,
        on: PredictionDatasetKind = "test",
    ) -> PredictionResult:
        """
        Выполняет прогноз на одной из выборок ProcessedDataset.

        Parameters
        ----------
        model:
            Обученная модель дерева решений.
        dataset:
            Подготовленный датасет.
        on:
            Выборка для прогнозирования: "train", "test", "full".

        Returns
        -------
        PredictionResult
        """
        self._validate_model(model)

        x_data, y_true = self._select_dataset_slice(dataset, on=on)
        self._validate_features(x_data, expected_feature_names=model.feature_names)

        predicted_labels = self._predict_labels(model, x_data)
        predicted_probabilities = self._predict_probabilities(model, x_data)

        metadata = {
            "source_dataset_name": dataset.source_dataset_name,
            "target_column": dataset.target_column,
            "prediction_scope": on,
            "row_count": int(len(x_data)),
            "feature_count": int(x_data.shape[1]),
            "class_names": list(model.class_names),
        }

        return PredictionResult(
            source_dataset_name=dataset.source_dataset_name,
            target_column=dataset.target_column,
            prediction_scope=on,
            feature_names=list(model.feature_names),
            class_names=list(model.class_names),
            input_features=x_data.reset_index(drop=True),
            actual_values=y_true.reset_index(drop=True) if y_true is not None else None,
            predicted_values=predicted_labels.reset_index(drop=True),
            predicted_probabilities=predicted_probabilities.reset_index(drop=True)
            if predicted_probabilities is not None
            else None,
            metadata=metadata,
        )

    def predict_features(
        self,
        model: DecisionTreeModel,
        features: pd.DataFrame,
        *,
        source_dataset_name: str = "external",
        target_column: str | None = None,
    ) -> PredictionResult:
        """
        Выполняет прогноз на новых уже подготовленных признаках.

        Важно:
        Этот метод ожидает, что признаки уже приведены к тому же виду,
        что и при обучении модели (после preprocess/transform_features).

        Parameters
        ----------
        model:
            Обученная модель дерева решений.
        features:
            DataFrame с уже подготовленными числовыми признаками.
        source_dataset_name:
            Имя источника данных для metadata/result.
        target_column:
            Имя целевого столбца, если нужно явно указать.

        Returns
        -------
        PredictionResult
        """
        self._validate_model(model)
        self._validate_features(features, expected_feature_names=model.feature_names)

        predicted_labels = self._predict_labels(model, features)
        predicted_probabilities = self._predict_probabilities(model, features)

        metadata = {
            "source_dataset_name": source_dataset_name,
            "target_column": target_column or model.target_column,
            "prediction_scope": "external",
            "row_count": int(len(features)),
            "feature_count": int(features.shape[1]),
            "class_names": list(model.class_names),
        }

        return PredictionResult(
            source_dataset_name=source_dataset_name,
            target_column=target_column or model.target_column,
            prediction_scope="external",
            feature_names=list(model.feature_names),
            class_names=list(model.class_names),
            input_features=features.reset_index(drop=True),
            actual_values=None,
            predicted_values=predicted_labels.reset_index(drop=True),
            predicted_probabilities=predicted_probabilities.reset_index(drop=True)
            if predicted_probabilities is not None
            else None,
            metadata=metadata,
        )

    @staticmethod
    def _validate_model(model: DecisionTreeModel) -> None:
        if not model.is_fitted:
            raise NotFittedModelPredictionError(
                "Невозможно выполнить прогноз: модель дерева решений не обучена."
            )

    @staticmethod
    def _select_dataset_slice(
        dataset: ProcessedDataset,
        *,
        on: PredictionDatasetKind,
    ) -> tuple[pd.DataFrame, pd.Series | None]:
        if on == "train":
            x_data = dataset.x_train.copy()
            y_true = dataset.y_train.copy()
        elif on == "test":
            x_data = dataset.x_test.copy()
            y_true = dataset.y_test.copy()
        elif on == "full":
            x_data = dataset.x_full.copy()
            y_true = dataset.y_full.copy()
        else:
            raise PredictionError(
                f"Неподдерживаемый режим прогнозирования: '{on}'. "
                "Ожидается one of: 'train', 'test', 'full'."
            )

        if x_data.empty:
            raise EmptyPredictionInputError(
                f"Невозможно выполнить прогноз: выборка '{on}' пуста."
            )

        return x_data, y_true

    @staticmethod
    def _validate_features(
        features: pd.DataFrame,
        *,
        expected_feature_names: list[str],
    ) -> None:
        if features.empty:
            raise EmptyPredictionInputError(
                "Невозможно выполнить прогноз: входные признаки пусты."
            )

        current_feature_names = [str(column) for column in features.columns.tolist()]

        missing_columns = [
            column
            for column in expected_feature_names
            if column not in current_feature_names
        ]
        extra_columns = [
            column
            for column in current_feature_names
            if column not in expected_feature_names
        ]

        if missing_columns or extra_columns:
            raise IncompatibleFeatureSpaceError(
                "Пространство признаков несовместимо с моделью. "
                f"Отсутствуют признаки: {missing_columns or 'нет'}. "
                f"Лишние признаки: {extra_columns or 'нет'}."
            )

        non_numeric_columns = [
            str(column)
            for column in features.columns
            if not pd.api.types.is_numeric_dtype(features[column])
        ]
        if non_numeric_columns:
            raise IncompatibleFeatureSpaceError(
                "Для прогнозирования все признаки должны быть числовыми. "
                f"Некорректные столбцы: {non_numeric_columns}"
            )

    @staticmethod
    def _predict_labels(
        model: DecisionTreeModel,
        features: pd.DataFrame,
    ) -> pd.Series:
        ordered_features = features.loc[:, model.feature_names].copy()
        try:
            predicted = model.model.predict(ordered_features)
        except Exception as exc:
            raise PredictionError(
                f"Ошибка при выполнении прогнозирования: {exc}"
            ) from exc

        return pd.Series(predicted, name="predicted")

    @staticmethod
    def _predict_probabilities(
        model: DecisionTreeModel,
        features: pd.DataFrame,
    ) -> pd.DataFrame | None:
        ordered_features = features.loc[:, model.feature_names].copy()

        if not hasattr(model.model, "predict_proba"):
            return None

        try:
            probabilities = model.model.predict_proba(ordered_features)
        except Exception as exc:
            raise PredictionError(
                f"Ошибка при вычислении вероятностей классов: {exc}"
            ) from exc

        probability_columns = [
            f"proba_{class_name}" for class_name in model.class_names
        ]
        return pd.DataFrame(probabilities, columns=probability_columns)
