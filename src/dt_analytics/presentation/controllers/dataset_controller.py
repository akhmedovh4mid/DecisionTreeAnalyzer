"""Контроллер страницы отображения набора данных."""

from __future__ import annotations

from dataclasses import dataclass

from dt_analytics.application.dto import (
    CsvImportOptionsDto,
    DatasetDto,
    DatasetPreviewDto,
    DatasetProfilingSummaryDto,
    GetDatasetPreviewRequest,
    ProfileDatasetRequest,
)
from dt_analytics.application.use_cases.datasets import (
    GetDatasetPreviewUseCase,
    ProfileDatasetUseCase,
)
from dt_analytics.presentation.dialogs import ErrorDialog
from dt_analytics.presentation.pages import DatasetViewerPage


@dataclass(slots=True)
class DatasetPageState:
    """Состояние текущей страницы набора данных."""

    dataset: DatasetDto | None = None
    preview: DatasetPreviewDto | None = None
    profiling_summary: DatasetProfilingSummaryDto | None = None


class DatasetController:
    """Контроллер, отвечающий за загрузку и обновление страницы набора данных."""

    def __init__(
        self,
        *,
        get_dataset_preview_use_case: GetDatasetPreviewUseCase,
        profile_dataset_use_case: ProfileDatasetUseCase,
    ) -> None:
        self._get_dataset_preview_use_case = get_dataset_preview_use_case
        self._profile_dataset_use_case = profile_dataset_use_case
        self._view: DatasetViewerPage | None = None
        self._state = DatasetPageState()

    def bind_view(self, view: DatasetViewerPage) -> None:
        """Привязать контроллер к странице (view)."""
        self._view = view
        self._refresh_view()

    def load_dataset(
        self,
        *,
        project_id: str,
        dataset: DatasetDto,
    ) -> None:
        """Загрузить предпросмотр и профилирование набора данных на страницу."""
        if self._view is None:
            return

        preview_result = self._get_dataset_preview_use_case.execute(
            GetDatasetPreviewRequest(
                csv_file_path=dataset.local_copy_file_path,
                options=CsvImportOptionsDto(),
            )
        )
        if preview_result.is_failure:
            self._show_error(
                title="Предпросмотр набора данных завершился ошибкой",
                message=preview_result.error.message
                if preview_result.error
                else "Неизвестная ошибка.",
                details=preview_result.error.details if preview_result.error else None,
            )
            return

        profiling_result = self._profile_dataset_use_case.execute(
            ProfileDatasetRequest(
                project_id=project_id,
                dataset_id=dataset.id,
            )
        )
        if profiling_result.is_failure:
            self._show_error(
                title="Профилирование набора данных завершилось ошибкой",
                message=profiling_result.error.message
                if profiling_result.error
                else "Неизвестная ошибка.",
                details=profiling_result.error.details if profiling_result.error else None,
            )
            return

        self._state.dataset = dataset
        self._state.preview = preview_result.unwrap()
        self._state.profiling_summary = profiling_result.unwrap()
        self._refresh_view()

    def clear(self) -> None:
        """Сбросить состояние текущей страницы набора данных."""
        self._state = DatasetPageState()
        self._refresh_view()

    def _refresh_view(self) -> None:
        """Обновить привязанное представление."""
        if self._view is None:
            return

        if (
            self._state.dataset is None
            or self._state.preview is None
            or self._state.profiling_summary is None
        ):
            self._view.clear_content()
            return

        self._view.set_dataset_content(
            dataset=self._state.dataset,
            preview_frame=self._state.preview.preview_frame,
            profiling_summary=self._state.profiling_summary,
        )

    def _show_error(self, *, title: str, message: str, details: str | None = None) -> None:
        if self._view is None:
            return
        ErrorDialog.show_error(
            title=title,
            message=message,
            details=details,
            parent=self._view,
        )
