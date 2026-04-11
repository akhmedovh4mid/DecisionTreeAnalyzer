from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd


class BaseFileReader(ABC):
    """
    Базовый контракт для чтения табличных файлов.
    """

    supported_extensions: tuple[str, ...] = ()

    def can_read(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in self.supported_extensions

    @abstractmethod
    def read(self, file_path: Path) -> pd.DataFrame:
        """
        Считывает файл и возвращает DataFrame.
        """
        raise NotImplementedError
