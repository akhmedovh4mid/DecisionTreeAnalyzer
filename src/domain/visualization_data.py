from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class VisualizationData:
    source_dataset_name: str
    target_column: str
    tree_text: str
    tree_image_path: str | None
    model_summary: dict[str, int | float | str]
    metrics_summary: dict[str, int | float | str]
    dataset_summary: dict[str, int | float | str]
    feature_importances: dict[str, float]
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def has_tree_text(self) -> bool:
        return bool(self.tree_text.strip())

    @property
    def has_tree_image(self) -> bool:
        return bool(self.tree_image_path)

    @property
    def sorted_feature_importances(self) -> list[tuple[str, float]]:
        return sorted(
            self.feature_importances.items(),
            key=lambda item: item[1],
            reverse=True,
        )

    @property
    def top_features(self) -> list[tuple[str, float]]:
        return self.sorted_feature_importances[:15]
