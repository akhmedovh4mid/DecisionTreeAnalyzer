from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass(slots=True)
class Dataset:
    """
    Доменная сущность, представляющая загруженный набор данных.
    """

    name: str
    source_path: Path
    data: pd.DataFrame
    file_format: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def row_count(self) -> int:
        return int(self.data.shape[0])

    @property
    def column_count(self) -> int:
        return int(self.data.shape[1])

    @property
    def columns(self) -> list[str]:
        return [str(column) for column in self.data.columns.tolist()]

    @property
    def is_empty(self) -> bool:
        return self.data.empty
