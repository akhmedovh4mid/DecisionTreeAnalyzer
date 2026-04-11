from __future__ import annotations

from pathlib import Path


class UnsupportedFileFormatError(ValueError):
    """
    Ошибка при попытке загрузить неподдерживаемый формат файла.
    """


def detect_file_format(file_path: Path) -> str:
    suffix = file_path.suffix.lower()

    mapping = {
        ".csv": "csv",
        ".tsv": "tsv",
        ".xlsx": "xlsx",
        ".xls": "xls",
        ".json": "json",
    }

    if suffix not in mapping:
        supported = ", ".join(mapping.keys())
        raise UnsupportedFileFormatError(
            f"Формат файла '{suffix}' не поддерживается. "
            f"Поддерживаемые форматы: {supported}"
        )

    return mapping[suffix]
