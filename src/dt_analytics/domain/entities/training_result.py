"""Сущность результата обучения."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from dt_analytics.domain.value_objects import TrainingResultId
from dt_analytics.shared.types import JsonDict


@dataclass(slots=True)
class TrainingResult:
    """Результат успешного обучения модели."""

    id: TrainingResultId
    train_score: float | None
    tree_depth: int
    leaf_count: int
    node_count: int
    feature_importance: JsonDict = field(default_factory=dict)
    class_labels: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def create(
        cls,
        tree_depth: int,
        leaf_count: int,
        node_count: int,
        train_score: float | None = None,
        feature_importance: JsonDict | None = None,
        class_labels: list[str] | None = None,
    ) -> TrainingResult:
        if tree_depth < 0:
            raise ValueError("Глубина дерева не может быть отрицательной.")

        if leaf_count < 0:
            raise ValueError("Количество листьев не может быть отрицательным.")

        if node_count < 0:
            raise ValueError("Количество узлов не может быть отрицательным.")

        if train_score is not None and not 0.0 <= train_score <= 1.0:
            raise ValueError("Обучающая метрика (train_score) должна быть от 0 до 1.")

        return cls(
            id=TrainingResultId.new(),
            train_score=train_score,
            tree_depth=tree_depth,
            leaf_count=leaf_count,
            node_count=node_count,
            feature_importance=feature_importance or {},
            class_labels=class_labels or [],
        )
