from __future__ import annotations

from pathlib import Path

import pandas as pd

from .base_reader import BaseFileReader


class CsvReader(BaseFileReader):
    """
    Reader для CSV и TSV файлов.
    """

    supported_extensions = (".csv", ".tsv")

    def read(self, file_path: Path) -> pd.DataFrame:
        suffix = file_path.suffix.lower()

        if suffix == ".tsv":
            separator = "\t"
        else:
            separator = ","

        return pd.read_csv(file_path, sep=separator)
