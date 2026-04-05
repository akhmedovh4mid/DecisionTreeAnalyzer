"""Файл‑связанные объекты значений."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dt_analytics.shared.types import PathLike


@dataclass(frozen=True, slots=True)
class FileReference:
    """Ссылка на ресурс файловой системы, используемый доменной моделью."""

    path: Path
    exists: bool = False
    checksum: str | None = None

    @classmethod
    def from_path(cls, path: PathLike, checksum: str | None = None) -> FileReference:
        resolved_path = Path(path).expanduser().resolve()
        return cls(
            path=resolved_path,
            exists=resolved_path.exists(),
            checksum=checksum,
        )

    @property
    def name(self) -> str:
        """Вернуть имя файла."""
        return self.path.name

    @property
    def suffix(self) -> str:
        """Вернуть расширение файла."""
        return self.path.suffix
