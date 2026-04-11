from __future__ import annotations

from pathlib import Path

import pandas as pd

from .base_reader import BaseFileReader


class ExcelReader(BaseFileReader):
    """
    Reader для Excel файлов.
    """

    supported_extensions = (".xlsx", ".xls")

    def read(self, file_path: Path) -> pd.DataFrame:
        return pd.read_excel(file_path)
