from __future__ import annotations

from typing import Literal

import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

from src.domain.evaluation_metrics import EvaluationMetrics
from src.domain.prediction_result import PredictionResult


class EvaluationError(Exception):
    """Базовая ошибка модуля оценки качества."""


class EmptyEvaluationInputError(EvaluationError):
    """Ошибка: входные данные для оценки пусты."""


class MissingActualValuesError(EvaluationError):
    """Ошибка: отсутствуют реальные значения целевой переменной."""


class IncompatibleEvaluationInputError(EvaluationError):
    """Ошибка: входные данные для оценки несовместимы."""


class UnsupportedAverageStrategyError(EvaluationError):
    """Ошибка: передана неподдерживаемая стратегия усреднения метрик."""


AverageStrategy = Literal["binary", "macro", "micro", "weighted"]


class QualityEvaluator:
    """
    Минимальный, но полноценный сервис оценки качества классификации.

    Текущая реализация:
    - работает только для задач классификации;
    - принимает PredictionResult;
    - рассчитывает accuracy, precision, recall, f1-score;
    - формирует confusion matrix;
    - возвращает доменную сущность EvaluationMetrics.

    Архитектурная роль:
    - не зависит от UI;
    - не знает ничего о способе построения модели;
    - работает только с контрактом PredictionResult.
    """

    _SUPPORTED_AVERAGES: tuple[str, ...] = ("binary", "macro", "micro", "weighted")

    def evaluate(
        self,
        prediction_result: PredictionResult,
        *,
        average: AverageStrategy = "weighted",
        zero_division: int = 0,
    ) -> EvaluationMetrics:
        self._validate_average(average)
        y_true, y_pred = self._extract_and_validate_vectors(prediction_result)
        labels = self._resolve_labels(prediction_result, y_true, y_pred)

        precision_average = self._resolve_average_for_data(
            average=average,
            y_true=y_true,
            labels=labels,
        )

        try:
            accuracy = float(accuracy_score(y_true, y_pred))
            precision = float(
                precision_score(
                    y_true,
                    y_pred,
                    average=precision_average,
                    zero_division=zero_division,  # pyright: ignore[reportArgumentType]
                )
            )
            recall = float(
                recall_score(
                    y_true,
                    y_pred,
                    average=precision_average,
                    zero_division=zero_division,  # pyright: ignore[reportArgumentType]
                )
            )
            f1 = float(
                f1_score(
                    y_true,
                    y_pred,
                    average=precision_average,
                    zero_division=zero_division,  # pyright: ignore[reportArgumentType]
                )
            )
            matrix = confusion_matrix(y_true, y_pred, labels=labels)
        except Exception as exc:
            raise EvaluationError(
                f"Ошибка при вычислении метрик качества: {exc}"
            ) from exc

        support_by_class = self._build_support_by_class(y_true, labels)
        actual_distribution = self._build_distribution(y_true)
        predicted_distribution = self._build_distribution(y_pred)

        metadata = {
            "source_dataset_name": prediction_result.source_dataset_name,
            "target_column": prediction_result.target_column,
            "prediction_scope": prediction_result.prediction_scope,
            "row_count": int(len(y_true)),
            "class_count": int(len(labels)),
            "average": precision_average,
            "zero_division": int(zero_division),
            "has_probabilities": bool(prediction_result.has_probabilities),
        }

        return EvaluationMetrics(
            source_dataset_name=prediction_result.source_dataset_name,
            target_column=prediction_result.target_column,
            prediction_scope=prediction_result.prediction_scope,
            average=precision_average,
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1,
            class_names=labels,
            support=int(len(y_true)),
            support_by_class=support_by_class,
            confusion_matrix=matrix.tolist(),
            actual_class_distribution=actual_distribution,
            predicted_class_distribution=predicted_distribution,
            metadata=metadata,
        )

    def _validate_average(self, average: AverageStrategy) -> None:
        if average not in self._SUPPORTED_AVERAGES:
            supported = ", ".join(self._SUPPORTED_AVERAGES)
            raise UnsupportedAverageStrategyError(
                f"Неподдерживаемая стратегия усреднения: '{average}'. "
                f"Поддерживаемые значения: {supported}"
            )

    @staticmethod
    def _extract_and_validate_vectors(
        prediction_result: PredictionResult,
    ) -> tuple[pd.Series, pd.Series]:
        if prediction_result.is_empty:
            raise EmptyEvaluationInputError(
                "Невозможно выполнить оценку качества: PredictionResult пуст."
            )

        if (
            not prediction_result.has_actual_values
            or prediction_result.actual_values is None
        ):
            raise MissingActualValuesError(
                "Невозможно выполнить оценку качества: отсутствуют реальные значения "
                "целевой переменной."
            )

        y_true = prediction_result.actual_values.copy()
        y_pred = prediction_result.predicted_values.copy()

        if y_true.empty or y_pred.empty:
            raise EmptyEvaluationInputError(
                "Невозможно выполнить оценку качества: векторы y_true/y_pred пусты."
            )

        if len(y_true) != len(y_pred):
            raise IncompatibleEvaluationInputError(
                "Невозможно выполнить оценку качества: размеры y_true и y_pred не совпадают."
            )

        if y_true.isna().any():
            raise IncompatibleEvaluationInputError(
                "Невозможно выполнить оценку качества: y_true содержит пропуски."
            )

        if y_pred.isna().any():
            raise IncompatibleEvaluationInputError(
                "Невозможно выполнить оценку качества: y_pred содержит пропуски."
            )

        return y_true.reset_index(drop=True), y_pred.reset_index(drop=True)

    @staticmethod
    def _resolve_labels(
        prediction_result: PredictionResult,
        y_true: pd.Series,
        y_pred: pd.Series,
    ) -> list[str]:
        if prediction_result.class_names:
            return [str(label) for label in prediction_result.class_names]

        observed_labels = pd.Index(y_true.astype("string")).union(
            pd.Index(y_pred.astype("string"))
        )
        return [str(label) for label in observed_labels.tolist()]

    @staticmethod
    def _resolve_average_for_data(
        *,
        average: AverageStrategy,
        y_true: pd.Series,
        labels: list[str],
    ) -> str:
        unique_class_count = int(y_true.nunique(dropna=True))

        if average == "binary":
            if unique_class_count != 2 or len(labels) != 2:
                raise UnsupportedAverageStrategyError(
                    "Стратегия 'binary' допустима только для бинарной классификации."
                )
            return "binary"

        return average

    @staticmethod
    def _build_support_by_class(y_true: pd.Series, labels: list[str]) -> dict[str, int]:
        counts = y_true.astype("string").value_counts(dropna=False).to_dict()
        result: dict[str, int] = {}
        for label in labels:
            result[str(label)] = int(counts.get(str(label), 0))
        return result

    @staticmethod
    def _build_distribution(values: pd.Series) -> dict[str, int]:
        distribution = values.astype("string").value_counts(dropna=False).to_dict()
        return {str(label): int(count) for label, count in distribution.items()}
