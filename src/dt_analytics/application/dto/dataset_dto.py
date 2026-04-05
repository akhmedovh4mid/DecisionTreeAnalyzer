"""DTO‑модели, связанные с наборами данных."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from pandas import DataFrame

from dt_analytics.domain.enums import LogicalFeatureType


@dataclass(frozen=True, slots=True)
class CsvImportOptionsDto:
    """DTO параметров импорта CSV‑файла."""

    separator: str = ","
    encoding: str = "utf-8"
    header: int | None = 0
    decimal: str = "."
    preview_rows: int = 20


@dataclass(frozen=True, slots=True)
class ImportCsvDatasetRequest:
    """DTO запроса на импорт CSV‑набора данных в проект."""

    project_id: str
    csv_file_path: Path
    dataset_name: str | None = None
    options: CsvImportOptionsDto = field(default_factory=CsvImportOptionsDto)


@dataclass(frozen=True, slots=True)
class GetDatasetPreviewRequest:
    """DTO запроса на предпросмотр CSV‑набора данных до импорта."""

    csv_file_path: Path
    options: CsvImportOptionsDto = field(default_factory=CsvImportOptionsDto)


@dataclass(frozen=True, slots=True)
class ProfileDatasetRequest:
    """DTO запроса на профилирование уже зарегистрированного набора данных."""

    project_id: str
    dataset_id: str


@dataclass(frozen=True, slots=True)
class FeatureDto:
    """DTO признака набора данных для внешнего/API‑уровня."""

    id: str
    name: str
    physical_dtype: str
    logical_type: str
    role: str
    nullable: bool
    missing_count: int
    unique_count: int | None
    ordinal_position: int


@dataclass(frozen=True, slots=True)
class DatasetProfileDto:
    """DTO профиля набора данных для внешнего/API‑уровня."""

    id: str
    profiled_at: str
    missing_total: int
    duplicate_count: int
    memory_usage_bytes: int | None
    summary: dict[str, object]


@dataclass(frozen=True, slots=True)
class DatasetDto:
    """DTO набора данных для внешнего/API‑уровня."""

    id: str
    name: str
    source_file_path: Path
    local_copy_file_path: Path
    format: str
    row_count: int
    column_count: int
    loaded_at: str
    is_active: bool
    features: tuple[FeatureDto, ...] = ()
    profile: DatasetProfileDto | None = None


@dataclass(frozen=True, slots=True)
class DatasetPreviewDto:
    """
    DTO предпросмотра набора данных.

    `preview_frame` оставлен как DataFrame, потому что слой презентации далее
    будет использовать его как источник для табличной модели.
    """

    file_path: Path
    preview_frame: DataFrame
    preview_row_count: int
    columns: tuple[str, ...]
    dtypes: dict[str, object]


@dataclass(frozen=True, slots=True)
class DatasetProfilingSummaryDto:
    """Компактная сводка профилирования для UI и рабочего процесса приложения."""

    row_count: int
    column_count: int
    missing_total: int
    duplicate_count: int
    memory_usage_bytes: int | None
    logical_type_counts: dict[str, int]
    nullable_column_count: int


@dataclass(frozen=True, slots=True)
class ImportedDatasetResultDto:
    """DTO результата успешного импорта CSV‑набора данных в проект."""

    dataset: DatasetDto
    profiling_summary: DatasetProfilingSummaryDto


def logical_type_to_label(logical_type: LogicalFeatureType) -> str:
    """Преобразовать LogicalFeatureType в строковое представление для wire/API."""
    return logical_type.value
