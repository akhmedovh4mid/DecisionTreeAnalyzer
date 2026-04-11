from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class DatasetInfo:
    source_dataset_name: str
    target_column: str
    row_count: int
    column_count: int
    feature_columns: list[str]
    numeric_columns: list[str]
    categorical_columns: list[str]
    missing_values_by_column: dict[str, int]
    duplicate_row_count: int
    class_distribution: dict[str, int]
    numeric_summary: dict[str, dict[str, float | None]]
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def feature_count(self) -> int:
        return int(len(self.feature_columns))

    @property
    def class_count(self) -> int:
        return int(len(self.class_distribution))

    @property
    def total_missing_values(self) -> int:
        return int(sum(self.missing_values_by_column.values()))

    @property
    def has_missing_values(self) -> bool:
        return self.total_missing_values > 0

    @property
    def has_duplicates(self) -> bool:
        return self.duplicate_row_count > 0

    @property
    def missing_columns(self) -> list[str]:
        return [
            column
            for column, missing_count in self.missing_values_by_column.items()
            if int(missing_count) > 0
        ]

    @property
    def summary(self) -> dict[str, int | str]:
        return {
            "source_dataset_name": self.source_dataset_name,
            "target_column": self.target_column,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "feature_count": self.feature_count,
            "class_count": self.class_count,
            "total_missing_values": self.total_missing_values,
            "duplicate_row_count": self.duplicate_row_count,
        }
