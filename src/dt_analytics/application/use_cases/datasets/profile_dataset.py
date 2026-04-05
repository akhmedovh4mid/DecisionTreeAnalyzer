"""Use‑case профилирования набора данных."""

from __future__ import annotations

from dt_analytics.application.dto.dataset_dto import (
    DatasetDto,
    DatasetProfileDto,
    DatasetProfilingSummaryDto,
    FeatureDto,
    ProfileDatasetRequest,
)
from dt_analytics.domain import DatasetId, ProjectId
from dt_analytics.domain.entities import Dataset
from dt_analytics.domain.repositories import DatasetRepository, ProjectRepository
from dt_analytics.shared import Result


class ProfileDatasetUseCase:
    """Возвращает информацию профилирования для зарегистрированного набора данных."""

    def __init__(
        self,
        project_repository: ProjectRepository,
        dataset_repository: DatasetRepository,
    ) -> None:
        self._project_repository = project_repository
        self._dataset_repository = dataset_repository

    def execute(self, request: ProfileDatasetRequest) -> Result[DatasetProfilingSummaryDto]:
        """Загрузить сводку профилирования уже импортированного набора данных."""
        project_id = ProjectId(request.project_id)
        dataset_id = DatasetId(request.dataset_id)

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

        dataset_result = self._dataset_repository.get_by_id(
            project_id=project_id, dataset_id=dataset_id
        )
        if dataset_result.is_failure:
            return Result.fail(
                code=dataset_result.error.code if dataset_result.error else "dataset_not_found",
                message=dataset_result.error.message
                if dataset_result.error
                else "Набор данных не найден.",
                details=dataset_result.error.details if dataset_result.error else None,
                warnings=list(dataset_result.warnings),
            )

        dataset = dataset_result.unwrap()
        return Result.ok(self._to_profiling_summary(dataset))

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
