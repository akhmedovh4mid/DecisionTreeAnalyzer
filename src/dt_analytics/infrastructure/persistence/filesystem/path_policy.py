"""Политика путей файловой системы для хранения проекта."""

from __future__ import annotations

from pathlib import Path

from dt_analytics.shared.constants import (
    ARTIFACTS_DIRNAME,
    ARTIFACTS_MODELS_DIRNAME,
    ARTIFACTS_PLOTS_DIRNAME,
    ARTIFACTS_REPORTS_DIRNAME,
    DATASETS_DIRNAME,
    DATASETS_IMPORTED_DIRNAME,
    DATASETS_PROCESSED_DIRNAME,
    EXPORTS_DIRNAME,
    LOGS_DIRNAME,
    PROJECT_DB_FILENAME,
    RUNTIME_DIRNAME,
    TMP_DIRNAME,
)


class ProjectPathPolicy:
    """Определяет стандартные пути к папкам проекта."""

    def __init__(self, project_root: Path) -> None:
        self._project_root = project_root.expanduser().resolve()

    @property
    def project_root(self) -> Path:
        return self._project_root

    @property
    def project_db(self) -> Path:
        return self._project_root / PROJECT_DB_FILENAME

    @property
    def datasets_dir(self) -> Path:
        return self._project_root / DATASETS_DIRNAME

    @property
    def datasets_imported_dir(self) -> Path:
        return self.datasets_dir / DATASETS_IMPORTED_DIRNAME

    @property
    def datasets_processed_dir(self) -> Path:
        return self.datasets_dir / DATASETS_PROCESSED_DIRNAME

    @property
    def artifacts_dir(self) -> Path:
        return self._project_root / ARTIFACTS_DIRNAME

    @property
    def artifacts_models_dir(self) -> Path:
        return self.artifacts_dir / ARTIFACTS_MODELS_DIRNAME

    @property
    def artifacts_plots_dir(self) -> Path:
        return self.artifacts_dir / ARTIFACTS_PLOTS_DIRNAME

    @property
    def artifacts_reports_dir(self) -> Path:
        return self.artifacts_dir / ARTIFACTS_REPORTS_DIRNAME

    @property
    def exports_dir(self) -> Path:
        return self._project_root / EXPORTS_DIRNAME

    @property
    def logs_dir(self) -> Path:
        return self._project_root / LOGS_DIRNAME

    @property
    def tmp_dir(self) -> Path:
        return self._project_root / TMP_DIRNAME

    @property
    def runtime_dir(self) -> Path:
        return self._project_root / RUNTIME_DIRNAME

    def all_required_directories(self) -> tuple[Path, ...]:
        """Возвращает все директории, которые должны существовать для проекта."""
        return (
            self.project_root,
            self.datasets_dir,
            self.datasets_imported_dir,
            self.datasets_processed_dir,
            self.artifacts_dir,
            self.artifacts_models_dir,
            self.artifacts_plots_dir,
            self.artifacts_reports_dir,
            self.exports_dir,
            self.logs_dir,
            self.tmp_dir,
            self.runtime_dir,
        )
