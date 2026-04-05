"""Страница просмотра набора данных."""

from __future__ import annotations

from pandas import DataFrame
from PySide6.QtWidgets import (
    QLabel,
    QTableView,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from dt_analytics.application.dto import DatasetDto, DatasetProfilingSummaryDto
from dt_analytics.presentation.models import PandasTableModel
from dt_analytics.presentation.pages.dataset_profiling_page import DatasetProfilingPage


class DatasetViewerPage(QWidget):
    """Композитная страница набора данных с вкладками предпросмотра и профилирования."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self._title_label = QLabel("Просмотр набора данных", self)
        self._meta_label = QLabel("Набор данных не выбран", self)

        self._tabs = QTabWidget(self)

        self._preview_table_model = PandasTableModel(parent=self)
        self._preview_table = QTableView(self)
        self._preview_table.setModel(self._preview_table_model)
        self._preview_table.setAlternatingRowColors(True)
        self._preview_table.setSortingEnabled(False)

        preview_page = QWidget(self)
        preview_layout = QVBoxLayout(preview_page)
        preview_layout.addWidget(self._preview_table)

        self._profiling_page = DatasetProfilingPage(self)

        self._tabs.addTab(preview_page, "Предпросмотр данных")
        self._tabs.addTab(self._profiling_page, "Профилирование")

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.addWidget(self._title_label)
        layout.addWidget(self._meta_label)
        layout.addWidget(self._tabs)

    def set_dataset_content(
        self,
        *,
        dataset: DatasetDto,
        preview_frame: DataFrame,
        profiling_summary: DatasetProfilingSummaryDto,
    ) -> None:
        """Отобразить предпросмотр и профилирование набора данных."""
        self._title_label.setText(f"Просмотр набора данных — {dataset.name}")
        self._meta_label.setText(
            f"Строки: {dataset.row_count} | Столбцы: {dataset.column_count} |"
            f" Формат: {dataset.format}"
        )
        self._preview_table_model.set_dataframe(preview_frame)
        self._profiling_page.set_dataset_profile(dataset, profiling_summary)

    def clear_content(self) -> None:
        """Сбросить страницу в пустое состояние."""
        self._title_label.setText("Просмотр набора данных")
        self._meta_label.setText("Набор данных не выбран")
        self._preview_table_model.clear()
        self._profiling_page.clear_content()
