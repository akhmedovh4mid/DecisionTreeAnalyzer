from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sklearn.tree import DecisionTreeClassifier


@dataclass(slots=True)
class DecisionTreeModel:
    """
    Доменная сущность обученной модели дерева решений.

    Используется как контракт между:
    decision_tree -> prediction / evaluation / visualization
    """

    model: DecisionTreeClassifier
    target_column: str
    feature_names: list[str]
    class_names: list[str]
    parameters: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def node_count(self) -> int:
        return int(self.model.tree_.node_count)

    @property
    def depth(self) -> int:
        return int(self.model.get_depth())

    @property
    def leaf_count(self) -> int:
        return int(self.model.get_n_leaves())

    @property
    def feature_importances(self) -> dict[str, float]:
        importances = self.model.feature_importances_
        return {
            feature_name: float(importance)
            for feature_name, importance in zip(
                self.feature_names, importances, strict=False
            )
        }

    @property
    def is_fitted(self) -> bool:
        return hasattr(self.model, "tree_")
