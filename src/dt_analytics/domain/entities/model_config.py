"""Сущность конфигурации модели."""

from __future__ import annotations

from dataclasses import dataclass, field

from dt_analytics.domain.enums import TaskType
from dt_analytics.domain.value_objects import ModelConfigId
from dt_analytics.shared.types import JsonDict


@dataclass(slots=True)
class ModelConfig:
    """Конфигурация модели дерева решений."""

    id: ModelConfigId
    task_type: TaskType
    algorithm_code: str
    criterion: str = "gini"
    max_depth: int | None = None
    min_samples_split: int = 2
    min_samples_leaf: int = 1
    max_features: str | None = None
    splitter: str = "best"
    class_weight: str | None = None
    random_state: int = 42
    additional_params: JsonDict = field(default_factory=dict)

    @classmethod
    def create_classification_tree(
        cls,
        criterion: str = "gini",
        max_depth: int | None = None,
        min_samples_split: int = 2,
        min_samples_leaf: int = 1,
        max_features: str | None = None,
        splitter: str = "best",
        class_weight: str | None = None,
        random_state: int = 42,
        additional_params: JsonDict | None = None,
    ) -> ModelConfig:
        cls._validate_tree_params(
            max_depth=max_depth,
            min_samples_split=min_samples_split,
            min_samples_leaf=min_samples_leaf,
            random_state=random_state,
        )

        normalized_criterion = criterion.strip()
        if not normalized_criterion:
            raise ValueError("Критерий не может быть пустым.")

        normalized_splitter = splitter.strip()
        if not normalized_splitter:
            raise ValueError("Способ разделения (splitter) не может быть пустым.")

        return cls(
            id=ModelConfigId.new(),
            task_type=TaskType.CLASSIFICATION,
            algorithm_code="decision_tree_classifier",
            criterion=normalized_criterion,
            max_depth=max_depth,
            min_samples_split=min_samples_split,
            min_samples_leaf=min_samples_leaf,
            max_features=max_features,
            splitter=normalized_splitter,
            class_weight=class_weight,
            random_state=random_state,
            additional_params=additional_params or {},
        )

    @staticmethod
    def _validate_tree_params(
        *,
        max_depth: int | None,
        min_samples_split: int,
        min_samples_leaf: int,
        random_state: int,
    ) -> None:
        if max_depth is not None and max_depth <= 0:
            raise ValueError("Максимальная глубина должна быть положительной, если задана.")

        if min_samples_split < 2:
            raise ValueError("min_samples_split должно быть не меньше 2.")

        if min_samples_leaf < 1:
            raise ValueError("min_samples_leaf должно быть не меньше 1.")

        if random_state < 0:
            raise ValueError("Значение random_state должно быть неотрицательным.")
