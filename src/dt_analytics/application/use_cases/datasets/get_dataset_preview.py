"""Use‑case получения предпросмотра набора данных."""

from __future__ import annotations

from dt_analytics.application.dto.dataset_dto import (
    CsvImportOptionsDto,
    DatasetPreviewDto,
    GetDatasetPreviewRequest,
)
from dt_analytics.infrastructure.data_sources import CsvLoader, CsvLoadOptions
from dt_analytics.shared import Result


class GetDatasetPreviewUseCase:
    """Загружает лёгкий предпросмотр CSV для UI и подготовки импорта."""

    def __init__(self, csv_loader: CsvLoader) -> None:
        self._csv_loader = csv_loader

    def execute(self, request: GetDatasetPreviewRequest) -> Result[DatasetPreviewDto]:
        """Предпросмотреть CSV‑файл без его импорта в проект."""
        load_options = self._to_loader_options(request.options)

        preview_result = self._csv_loader.preview(
            file_path=request.csv_file_path,
            options=load_options,
        )
        if preview_result.is_failure:
            return Result.fail(
                code=preview_result.error.code
                if preview_result.error
                else "dataset_preview_failed",
                message=preview_result.error.message
                if preview_result.error
                else "Не удалось получить предпросмотр набора данных.",
                details=preview_result.error.details if preview_result.error else None,
                warnings=list(preview_result.warnings),
            )

        preview = preview_result.unwrap()
        return Result.ok(
            DatasetPreviewDto(
                file_path=preview.file_path,
                preview_frame=preview.preview_frame,
                preview_row_count=preview.preview_row_count,
                columns=preview.columns,
                dtypes=dict(preview.dtypes),
            )
        )

    @staticmethod
    def _to_loader_options(options: CsvImportOptionsDto) -> CsvLoadOptions:
        return CsvLoadOptions(
            separator=options.separator,
            encoding=options.encoding,
            header=options.header,
            decimal=options.decimal,
            preview_rows=options.preview_rows,
        )
