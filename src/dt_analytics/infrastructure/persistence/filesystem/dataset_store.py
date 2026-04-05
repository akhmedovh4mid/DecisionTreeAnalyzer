"""Хранилище файлов набора данных."""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

from dt_analytics.infrastructure.persistence.filesystem.path_policy import ProjectPathPolicy
from dt_analytics.shared import Result


def _compute_checksum(file_path: Path) -> str:
    hash_md5 = hashlib.md5()
    with file_path.open("rb") as file_obj:
        for chunk in iter(lambda: file_obj.read(8192), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


class DatasetStore:
    """Хранит импортированные файлы наборов данных внутри проекта."""

    def copy_into_project(
        self,
        source_path: Path,
        project_root: Path,
        target_name: str | None = None,
    ) -> Result[Path]:
        """
        Копирует исходный файл набора данных в хранилище проекта.
        """
        try:
            source = source_path.expanduser().resolve()
            if not source.exists():
                return Result.fail(
                    code="dataset_source_not_found",
                    message="Исходный файл набора данных не найден.",
                    details=str(source),
                )

            policy = ProjectPathPolicy(project_root)
            policy.datasets_imported_dir.mkdir(parents=True, exist_ok=True)

            destination_name = target_name or source.name
            destination = policy.datasets_imported_dir / destination_name

            shutil.copy2(source, destination)
            return Result.ok(destination)
        except OSError as exc:
            return Result.fail(
                code="dataset_copy_failed",
                message="Не удалось скопировать набор данных в хранилище проекта.",
                details=str(exc),
            )

    def checksum(self, file_path: Path) -> Result[str]:
        """Вычисляет контрольную сумму файла."""
        try:
            return Result.ok(_compute_checksum(file_path))
        except OSError as exc:
            return Result.fail(
                code="dataset_checksum_failed",
                message="Не удалось вычислить контрольную сумму файла.",
                details=str(exc),
            )
