"""Управление хранилищем папки проекта."""

from __future__ import annotations

from pathlib import Path

from dt_analytics.infrastructure.persistence.filesystem.path_policy import ProjectPathPolicy
from dt_analytics.shared import PersistenceError, Result


class ProjectStorage:
    """Управляет структурой папок проекта на диске."""

    def initialize(self, project_root: Path) -> Result[ProjectPathPolicy]:
        """Создаёт дерево директорий проекта."""
        try:
            policy = ProjectPathPolicy(project_root)
            for directory in policy.all_required_directories():
                directory.mkdir(parents=True, exist_ok=True)
            return Result.ok(policy)
        except OSError as exc:
            return Result.fail(
                code="project_storage_init_failed",
                message="Не удалось инициализировать хранилище проекта.",
                details=str(exc),
            )

    def exists(self, project_root: Path) -> Result[bool]:
        """Проверяет, выглядит ли папка как корень хранилища проекта."""
        try:
            policy = ProjectPathPolicy(project_root)
            return Result.ok(policy.project_db.exists() or policy.project_root.exists())
        except OSError as exc:
            return Result.fail(
                code="project_storage_exists_failed",
                message="Не удалось проверить хранилище проекта.",
                details=str(exc),
            )

    def ensure_initialized(self, project_root: Path) -> ProjectPathPolicy:
        """Инициализирует или возвращает политику путей, выбрасывает исключение при ошибке."""
        result = self.initialize(project_root)
        if result.is_failure:
            details = result.error.details if result.error else "Неизвестная ошибка хранилища"
            raise PersistenceError(details)
        return result.unwrap()
