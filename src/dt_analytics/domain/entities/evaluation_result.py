"""Сущность результата оценки."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from dt_analytics.domain.value_objects import EvaluationResultId
from dt_analytics.shared.types import JsonDict


@dataclass(slots=True)
class EvaluationResult:
    """Метрики оценки модели и связанные с ними артефакты."""

    id: EvaluationResultId
    accuracy: float | None
    precision_weighted: float | None
    recall_weighted: float | None
    f1_weighted: float | None
    confusion_matrix: list[list[int]] = field(default_factory=list)
    classification_report: JsonDict = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def create(
        cls,
        accuracy: float | None,
        precision_weighted: float | None,
        recall_weighted: float | None,
        f1_weighted: float | None,
        confusion_matrix: list[list[int]] | None = None,
        classification_report: JsonDict | None = None,
    ) -> EvaluationResult:
        for metric_name, metric_value in (
            ("accuracy", accuracy),
            ("precision_weighted", precision_weighted),
            ("recall_weighted", recall_weighted),
            ("f1_weighted", f1_weighted),
        ):
            if metric_value is not None and not 0.0 <= metric_value <= 1.0:
                raise ValueError(f"{metric_name} должна быть между 0 и 1.")

        return cls(
            id=EvaluationResultId.new(),
            accuracy=accuracy,
            precision_weighted=precision_weighted,
            recall_weighted=recall_weighted,
            f1_weighted=f1_weighted,
            confusion_matrix=confusion_matrix or [],
            classification_report=classification_report or {},
        )
