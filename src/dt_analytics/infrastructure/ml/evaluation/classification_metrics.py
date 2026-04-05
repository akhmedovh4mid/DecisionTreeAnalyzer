"""Оценка метрик классификации."""

from __future__ import annotations

from collections.abc import Sequence

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    precision_score,
    recall_score,
)

from dt_analytics.domain import EvaluationResult
from dt_analytics.infrastructure.ml.evaluation.confusion_matrix_builder import (
    build_confusion_matrix,
)
from dt_analytics.shared import Result
from dt_analytics.shared.types import JsonDict


class ClassificationMetricsEvaluator:
    """Вычисление метрик классификации и формирование доменного объекта EvaluationResult."""

    def evaluate(
        self,
        y_true: Sequence[object],
        y_pred: Sequence[object],
    ) -> Result[EvaluationResult]:
        """Оценить прогнозы для задачи классификации."""
        if len(y_true) == 0:
            return Result.fail(
                code="empty_evaluation_target",
                message="Не удалось оценить модель по пустой целевой последовательности.",
            )

        if len(y_true) != len(y_pred):
            return Result.fail(
                code="evaluation_length_mismatch",
                message="Длины векторов истинных и предсказанных меток не совпадают.",
                details=f"{len(y_true)} != {len(y_pred)}",
            )

        try:
            accuracy = float(accuracy_score(y_true, y_pred))
            precision_weighted = float(
                precision_score(y_true, y_pred, average="weighted", zero_division=0)  # pyright: ignore[reportArgumentType]
            )
            recall_weighted = float(
                recall_score(y_true, y_pred, average="weighted", zero_division=0)  # pyright: ignore[reportArgumentType]
            )
            f1_weighted = float(f1_score(y_true, y_pred, average="weighted", zero_division=0))  # pyright: ignore[reportArgumentType]
            confusion = build_confusion_matrix(y_true, y_pred)
            report = classification_report(
                y_true,
                y_pred,
                zero_division=0,  # pyright: ignore[reportArgumentType]
                output_dict=True,
            )
        except ValueError as exc:
            return Result.fail(
                code="classification_metrics_failed",
                message="Не удалось вычислить метрики классификации.",
                details=str(exc),
            )

        try:
            evaluation_result = EvaluationResult.create(
                accuracy=accuracy,
                precision_weighted=precision_weighted,
                recall_weighted=recall_weighted,
                f1_weighted=f1_weighted,
                confusion_matrix=confusion,
                classification_report=self._normalize_report(report),  # pyright: ignore[reportArgumentType]
            )
        except ValueError as exc:
            return Result.fail(
                code="evaluation_result_build_failed",
                message="Не удалось построить объект результата оценки.",
                details=str(exc),
            )

        return Result.ok(evaluation_result)

    @staticmethod
    def _normalize_report(raw_report: dict[str, object]) -> JsonDict:
        """Нормализовать classification_report из scikit-learn в словарь, пригодный для JSON."""
        return raw_report  # already JSON-serializable for MVP  # pyright: ignore[reportReturnType]
