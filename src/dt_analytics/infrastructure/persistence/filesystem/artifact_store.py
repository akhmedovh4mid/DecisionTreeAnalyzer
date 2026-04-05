"""Хранилище файлов артефактов."""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

from dt_analytics.domain.enums import ArtifactType
from dt_analytics.infrastructure.persistence.filesystem.path_policy import ProjectPathPolicy
from dt_analytics.shared import Result


def _compute_checksum(file_path: Path) -> str:
    hash_md5 = hashlib.md5()
    with file_path.open("rb") as file_obj:
        for chunk in iter(lambda: file_obj.read(8192), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


class ArtifactStore:
    """Хранит файлы артефактов внутри структуры проекта."""

    def store_file(
        self,
        source_path: Path,
        project_root: Path,
        artifact_type: ArtifactType,
        target_name: str | None = None,
    ) -> Result[Path]:
        """Копирует файл артефакта в соответствующую папку артефактов."""
        try:
            source = source_path.expanduser().resolve()
            if not source.exists():
                return Result.fail(
                    code="artifact_source_not_found",
                    message="Исходный файл артефакта не найден.",
                    details=str(source),
                )

            policy = ProjectPathPolicy(project_root)
            destination_dir = self._resolve_destination_dir(policy, artifact_type)
            destination_dir.mkdir(parents=True, exist_ok=True)

            destination = destination_dir / (target_name or source.name)
            shutil.copy2(source, destination)

            return Result.ok(destination)
        except OSError as exc:
            return Result.fail(
                code="artifact_store_failed",
                message="Не удалось сохранить файл артефакта.",
                details=str(exc),
            )

    def checksum(self, file_path: Path) -> Result[str]:
        """Вычисляет контрольную сумму файла артефакта."""
        try:
            return Result.ok(_compute_checksum(file_path))
        except OSError as exc:
            return Result.fail(
                code="artifact_checksum_failed",
                message="Не удалось вычислить контрольную сумму артефакта.",
                details=str(exc),
            )

    @staticmethod
    def _resolve_destination_dir(
        policy: ProjectPathPolicy,
        artifact_type: ArtifactType,
    ) -> Path:
        if artifact_type is ArtifactType.MODEL:
            return policy.artifacts_models_dir
        if artifact_type in {
            ArtifactType.FEATURE_IMPORTANCE_PLOT,
            ArtifactType.TREE_PLOT,
        }:
            return policy.artifacts_plots_dir
        return policy.artifacts_reports_dir
