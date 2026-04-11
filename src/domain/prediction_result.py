from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd


@dataclass(slots=True)
class PredictionResult:
    source_dataset_name: str
    target_column: str
    prediction_scope: str
    feature_names: list[str]
    class_names: list[str]
    input_features: pd.DataFrame
    predicted_values: pd.Series
    actual_values: pd.Series | None = None
    predicted_probabilities: pd.DataFrame | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def row_count(self) -> int:
        return int(len(self.predicted_values))

    @property
    def has_actual_values(self) -> bool:
        return self.actual_values is not None

    @property
    def has_probabilities(self) -> bool:
        return self.predicted_probabilities is not None

    @property
    def is_empty(self) -> bool:
        return self.predicted_values.empty

    @property
    def predicted_class_distribution(self) -> dict[str, int]:
        distribution = self.predicted_values.value_counts(dropna=False).to_dict()
        return {str(label): int(count) for label, count in distribution.items()}
