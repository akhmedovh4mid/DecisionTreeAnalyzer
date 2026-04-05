"""Извлечение метаданных дерева."""

from __future__ import annotations

from dataclasses import dataclass

from sklearn.pipeline import Pipeline
from sklearn.tree import DecisionTreeClassifier

from dt_analytics.shared import Result


@dataclass(frozen=True, slots=True)
class TreeMetadata:
    """Базовые структурные метаданные обученного дерева решений."""

    tree_depth: int
    leaf_count: int
    node_count: int
    class_labels: tuple[str, ...]


class TreeMetadataExtractor:
    """Извлечение структурных метаданных из обученного sklearn‑pipeline."""

    def extract(self, pipeline: Pipeline) -> Result[TreeMetadata]:
        """Извлечь метаданные дерева из pipeline."""
        model = pipeline.named_steps.get("model")
        if not isinstance(model, DecisionTreeClassifier):
            return Result.fail(
                code="tree_metadata_model_missing",
                message="В конвейере отсутствует обученный DecisionTreeClassifier.",
            )

        if not hasattr(model, "tree_"):
            return Result.fail(
                code="tree_metadata_not_trained",
                message="Модель дерева решений не обучена.",
            )

        try:
            metadata = TreeMetadata(
                tree_depth=int(model.get_depth()),
                leaf_count=int(model.get_n_leaves()),
                node_count=int(model.tree_.node_count),
                class_labels=tuple(str(label) for label in getattr(model, "classes_", [])),
            )
        except Exception as exc:  # noqa: BLE001
            return Result.fail(
                code="tree_metadata_extract_failed",
                message="Не удалось извлечь метаданные дерева.",
                details=str(exc),
            )

        return Result.ok(metadata)
