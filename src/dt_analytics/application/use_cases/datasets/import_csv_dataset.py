"""Use‑case импорта CSV‑набора данных."""

from __future__ import annotations

from pathlib import Path

from dt_analytics.application.dto.dataset_dto import (
    CsvImportOptionsDto,
    DatasetDto,
    DatasetProfileDto,
    DatasetProfilingSummaryDto,
    FeatureDto,
    ImportCsvDatasetRequest,
    ImportedDatasetResultDto,
)
from dt_analytics.domain import Dataset, FileReference, ProjectId
from dt_analytics.domain.repositories import DatasetRepository, ProjectRepository
from dt_analytics.domain.services import DatasetProfileService
from dt_analytics.infrastructure.data_sources import CsvLoader, CsvLoadOptions
from dt_analytics.infrastructure.persistence.filesystem.dataset_store import DatasetStore
from dt_analytics.shared import Result


class ImportCsvDatasetUseCase:
    """Импортирует CSV‑файл в проект и сохраняет метаданные набора данных."""

    def __init__(
        self,
        project_repository: ProjectRepository,
        dataset_repository: DatasetRepository,
        csv_loader: CsvLoader,
        dataset_store: DatasetStore,
        dataset_profile_service: DatasetProfileService,
    ) -> None:
        self._project_repository = project_repository
        self._dataset_repository = dataset_repository
        self._csv_loader = csv_loader
        self._dataset_store = dataset_store
        self._dataset_profile_service = dataset_profile_service

    def execute(self, request: ImportCsvDatasetRequest) -> Result[ImportedDatasetResultDto]:
        """
        Импортировать CSV в хранилище проекта и зарегистрировать набор данных.
        """
        project_id = ProjectId(request.project_id)

        project_result = self._project_repository.get_by_id(project_id)
        if project_result.is_failure:
            return Result.fail(
                code=project_result.error.code if project_result.error else "project_not_found",
                message=project_result.error.message
                if project_result.error
                else "Проект не найден.",
                details=project_result.error.details if project_result.error else None,
                warnings=list(project_result.warnings),
            )

        project = project_result.unwrap()

        load_result = self._csv_loader.load(
            file_path=request.csv_file_path,
            options=self._to_loader_options(request.options),
        )
        if load_result.is_failure:
            return Result.fail(
                code=load_result.error.code if load_result.error else "csv_load_failed",
                message=load_result.error.message
                if load_result.error
                else "Не удалось загрузить CSV‑набор данных.",
                details=load_result.error.details if load_result.error else None,
                warnings=list(load_result.warnings),
            )

        csv_data = load_result.unwrap()

        copied_file_result = self._dataset_store.copy_into_project(
            source_path=csv_data.file_path,
            project_root=project.storage_path,
            target_name=csv_data.file_path.name,
        )
        if copied_file_result.is_failure:
            return Result.fail(
                code=copied_file_result.error.code
                if copied_file_result.error
                else "dataset_copy_failed",
                message=copied_file_result.error.message
                if copied_file_result.error
                else "Не удалось скопировать набор данных в хранилище проекта.",
                details=copied_file_result.error.details if copied_file_result.error else None,
                warnings=list(copied_file_result.warnings),
            )

        copied_file_path = copied_file_result.unwrap()

        source_checksum_result = self._dataset_store.checksum(csv_data.file_path)
        if source_checksum_result.is_failure:
            return Result.fail(
                code=source_checksum_result.error.code
                if source_checksum_result.error
                else "source_checksum_failed",
                message=source_checksum_result.error.message
                if source_checksum_result.error
                else "Не удалось вычислить контрольную сумму исходного файла.",
                details=source_checksum_result.error.details
                if source_checksum_result.error
                else None,
                warnings=list(source_checksum_result.warnings),
            )

        local_checksum_result = self._dataset_store.checksum(copied_file_path)
        if local_checksum_result.is_failure:
            return Result.fail(
                code=local_checksum_result.error.code
                if local_checksum_result.error
                else "local_checksum_failed",
                message=local_checksum_result.error.message
                if local_checksum_result.error
                else "Не удалось вычислить контрольную сумму скопированного набора данных.",
                details=local_checksum_result.error.details
                if local_checksum_result.error
                else None,
                warnings=list(local_checksum_result.warnings),
            )

        profiling_result = self._dataset_profile_service.profile_dataframe(csv_data.dataframe)
        if profiling_result.is_failure:
            return Result.fail(
                code=profiling_result.error.code
                if profiling_result.error
                else "dataset_profile_failed",
                message=profiling_result.error.message
                if profiling_result.error
                else "Не удалось профилировать набор данных.",
                details=profiling_result.error.details if profiling_result.error else None,
                warnings=list(profiling_result.warnings),
            )

        profile_data = profiling_result.unwrap()

        dataset_name = self._resolve_dataset_name(request.dataset_name, csv_data.file_path)

        try:
            dataset = Dataset.create(
                name=dataset_name,
                source_file=FileReference.from_path(
                    csv_data.file_path,
                    checksum=source_checksum_result.unwrap(),
                ),
                local_copy_file=FileReference.from_path(
                    copied_file_path,
                    checksum=local_checksum_result.unwrap(),
                ),
                format="csv",
                row_count=csv_data.row_count,
                column_count=csv_data.column_count,
            )
            dataset.replace_features(list(profile_data.features))
            dataset.attach_profile(profile_data.profile)
        except ValueError as exc:
            return Result.fail(
                code="dataset_build_failed",
                message="Не удалось построить объект набора данных.",
                details=str(exc),
            )

        save_result = self._dataset_repository.add(project_id=project.id, dataset=dataset)
        if save_result.is_failure:
            return Result.fail(
                code=save_result.error.code if save_result.error else "dataset_save_failed",
                message=save_result.error.message
                if save_result.error
                else "Не удалось сохранить набор данных.",
                details=save_result.error.details if save_result.error else None,
                warnings=list(save_result.warnings),
            )

        saved_dataset = save_result.unwrap()
        dto = ImportedDatasetResultDto(
            dataset=self._to_dataset_dto(saved_dataset),
            profiling_summary=self._to_profiling_summary(saved_dataset),
        )
        return Result.ok(dto)

    @staticmethod
    def _resolve_dataset_name(dataset_name: str | None, csv_file_path: Path) -> str:
        if dataset_name is not None and dataset_name.strip():
            return dataset_name.strip()
        return csv_file_path.stem.strip() or csv_file_path.name

    @staticmethod
    def _to_loader_options(options: CsvImportOptionsDto) -> CsvLoadOptions:
        return CsvLoadOptions(
            separator=options.separator,
            encoding=options.encoding,
            header=options.header,
            decimal=options.decimal,
            preview_rows=options.preview_rows,
        )

    @staticmethod
    def _to_feature_dto(feature) -> FeatureDto:
        return FeatureDto(
            id=feature.id.value,
            name=feature.name,
            physical_dtype=feature.physical_dtype,
            logical_type=feature.logical_type.value,
            role=feature.role.value,
            nullable=feature.nullable,
            missing_count=feature.missing_count,
            unique_count=feature.unique_count,
            ordinal_position=feature.ordinal_position,
        )

    @classmethod
    def _to_dataset_dto(cls, dataset: Dataset) -> DatasetDto:
        profile_dto = None
        if dataset.profile is not None:
            profile_dto = DatasetProfileDto(
                id=dataset.profile.id.value,
                profiled_at=dataset.profile.profiled_at.isoformat(),
                missing_total=dataset.profile.missing_total,
                duplicate_count=dataset.profile.duplicate_count,
                memory_usage_bytes=dataset.profile.memory_usage_bytes,
                summary=dataset.profile.summary,
            )

        return DatasetDto(
            id=dataset.id.value,
            name=dataset.name,
            source_file_path=dataset.source_file.path,
            local_copy_file_path=dataset.local_copy_file.path,
            format=dataset.format,
            row_count=dataset.row_count,
            column_count=dataset.column_count,
            loaded_at=dataset.loaded_at.isoformat(),
            is_active=dataset.is_active,
            features=tuple(cls._to_feature_dto(feature) for feature in dataset.features),
            profile=profile_dto,
        )

    @staticmethod
    def _to_profiling_summary(dataset: Dataset) -> DatasetProfilingSummaryDto:
        if dataset.profile is None:
            return DatasetProfilingSummaryDto(
                row_count=dataset.row_count,
                column_count=dataset.column_count,
                missing_total=0,
                duplicate_count=0,
                memory_usage_bytes=None,
                logical_type_counts={},
                nullable_column_count=0,
            )

        summary = dataset.profile.summary
        logical_type_counts = summary.get("logical_type_counts", {})
        nullable_column_count = summary.get("nullable_column_count", 0)

        return DatasetProfilingSummaryDto(
            row_count=dataset.row_count,
            column_count=dataset.column_count,
            missing_total=dataset.profile.missing_total,
            duplicate_count=dataset.profile.duplicate_count,
            memory_usage_bytes=dataset.profile.memory_usage_bytes,
            logical_type_counts=dict(logical_type_counts)
            if isinstance(logical_type_counts, dict)
            else {},
            nullable_column_count=int(nullable_column_count)
            if isinstance(nullable_column_count, int)
            else 0,
        )
