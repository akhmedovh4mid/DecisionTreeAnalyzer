from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class EvaluationMetrics:
    """
    Доменная сущность результата оценки качества модели классификации.
    """

    source_dataset_name: str
    target_column: str
    prediction_scope: str
    average: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    class_names: list[str]
    support: int
    support_by_class: dict[str, int]
    confusion_matrix: list[list[int]]
    actual_class_distribution: dict[str, int]
    predicted_class_distribution: dict[str, int]
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def class_count(self) -> int:
        return int(len(self.class_names))

    @property
    def is_binary(self) -> bool:
        return self.class_count == 2

    @property
    def is_multiclass(self) -> bool:
        return self.class_count > 2

    @property
    def score_summary(self) -> dict[str, float]:
        return {
            "accuracy": float(self.accuracy),
            "precision": float(self.precision),
            "recall": float(self.recall),
            "f1_score": float(self.f1_score),
        }

    @property
    def best_available_score(self) -> float:
        return float(self.f1_score)

    @property
    def confusion_matrix_shape(self) -> tuple[int, int]:
        row_count = len(self.confusion_matrix)
        column_count = len(self.confusion_matrix[0]) if self.confusion_matrix else 0
        return int(row_count), int(column_count)
