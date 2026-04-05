"""Простой контейнер зависимостей для DT Analytics."""

from __future__ import annotations

from dataclasses import dataclass

# from pathlib import Path
from dt_analytics.application.use_cases.datasets import (
    GetDatasetPreviewUseCase,
    ImportCsvDatasetUseCase,
)
from dt_analytics.application.use_cases.project import (
    CreateProjectUseCase,
    OpenProjectUseCase,
    SaveProjectUseCase,
)
from dt_analytics.bootstrap.runtime import RuntimeContext
from dt_analytics.config.schemas import AppSettings
from dt_analytics.infrastructure.data_sources import CsvLoader, DataFrameProfileService
from dt_analytics.infrastructure.persistence.filesystem.dataset_store import DatasetStore
from dt_analytics.infrastructure.persistence.filesystem.project_storage import ProjectStorage
from dt_analytics.infrastructure.persistence.sqlite.connection import create_connection
from dt_analytics.infrastructure.persistence.sqlite.repositories import (
    SqliteArtifactRepository,
    SqliteDatasetRepository,
    SqliteExperimentRepository,
    SqliteProjectRepository,
)
from dt_analytics.infrastructure.persistence.sqlite.schema_manager import ensure_schema


@dataclass(slots=True)
class AppContainer:
    """Корень композиции приложения (composition root)."""

    settings: AppSettings
    runtime: RuntimeContext

    create_project_use_case: CreateProjectUseCase
    open_project_use_case: OpenProjectUseCase
    save_project_use_case: SaveProjectUseCase

    get_dataset_preview_use_case: GetDatasetPreviewUseCase
    import_csv_dataset_use_case: ImportCsvDatasetUseCase


def build_container(settings: AppSettings, runtime: RuntimeContext) -> AppContainer:
    """Создать корневой контейнер зависимостей."""
    shared_storage_root = runtime.runtime_dir / "app_state"
    shared_storage_root.mkdir(parents=True, exist_ok=True)

    app_db_path = shared_storage_root / "application.db"
    connection = create_connection(app_db_path)
    ensure_schema(connection)

    project_repository = SqliteProjectRepository(connection)
    dataset_repository = SqliteDatasetRepository(connection)
    experiment_repository = SqliteExperimentRepository(connection)
    artifact_repository = SqliteArtifactRepository(connection)

    project_storage = ProjectStorage()
    dataset_store = DatasetStore()

    csv_loader = CsvLoader()
    dataframe_profile_service = DataFrameProfileService()

    create_project_use_case = CreateProjectUseCase(
        project_repository=project_repository,
        project_storage=project_storage,
    )
    open_project_use_case = OpenProjectUseCase(
        project_repository=project_repository,
        dataset_repository=dataset_repository,
        experiment_repository=experiment_repository,
        project_storage=project_storage,
    )
    save_project_use_case = SaveProjectUseCase(
        project_repository=project_repository,
        dataset_repository=dataset_repository,
        experiment_repository=experiment_repository,
        artifact_repository=artifact_repository,
    )

    get_dataset_preview_use_case = GetDatasetPreviewUseCase(csv_loader=csv_loader)
    import_csv_dataset_use_case = ImportCsvDatasetUseCase(
        project_repository=project_repository,
        dataset_repository=dataset_repository,
        csv_loader=csv_loader,
        dataset_store=dataset_store,
        dataset_profile_service=dataframe_profile_service,
    )

    return AppContainer(
        settings=settings,
        runtime=runtime,
        create_project_use_case=create_project_use_case,
        open_project_use_case=open_project_use_case,
        save_project_use_case=save_project_use_case,
        get_dataset_preview_use_case=get_dataset_preview_use_case,
        import_csv_dataset_use_case=import_csv_dataset_use_case,
    )
