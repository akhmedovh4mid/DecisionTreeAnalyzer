from __future__ import annotations

from pathlib import Path

import pandas as pd

from .base_reader import BaseFileReader


class JsonReader(BaseFileReader):
    """
    Reader для JSON файлов.
    Ожидает JSON, который может быть преобразован в табличную структуру.
    """

    supported_extensions = (".json",)

    def read(self, file_path: Path) -> pd.DataFrame:
        return pd.read_json(file_path)
