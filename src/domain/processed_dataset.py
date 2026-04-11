from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd


@dataclass(slots=True)
class ProcessedDataset:
    """
    Доменная сущность, представляющая результат предобработки данных.
    Используется как контракт между preprocessing -> decision_tree / prediction / evaluation.
    """

    source_dataset_name: str
    target_column: str

    x_full: pd.DataFrame
    y_full: pd.Series

    x_train: pd.DataFrame
    x_test: pd.DataFrame
    y_train: pd.Series
    y_test: pd.Series

    feature_names: list[str]
    numeric_columns: list[str]
    categorical_columns: list[str]

    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def train_size(self) -> int:
        return int(len(self.x_train))

    @property
    def test_size(self) -> int:
        return int(len(self.x_test))

    @property
    def feature_count(self) -> int:
        return int(len(self.feature_names))

    @property
    def class_count(self) -> int:
        return int(self.y_full.nunique(dropna=True))

    @property
    def is_empty(self) -> bool:
        return self.x_train.empty or self.x_test.empty
