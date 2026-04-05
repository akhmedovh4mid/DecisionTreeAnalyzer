"""Страница профилирования набора данных."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from dt_analytics.application.dto import DatasetDto, DatasetProfilingSummaryDto
from dt_analytics.presentation.widgets import ColumnSchemaTable


class DatasetProfilingPage(QWidget):
    """Страница, отображающая компактное резюме профилирования набора данных."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self._dataset_name_label = QLabel("—", self)
        self._rows_label = QLabel("0", self)
        self._columns_label = QLabel("0", self)
        self._missing_label = QLabel("0", self)
        self._duplicates_label = QLabel("0", self)
        self._memory_label = QLabel("—", self)
        self._nullable_columns_label = QLabel("0", self)
        self._logical_types_label = QLabel("—", self)

        self._schema_table = ColumnSchemaTable(self)

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        summary_box = QGroupBox("Профилирование набора данных", self)
        summary_form = QFormLayout(summary_box)
        summary_form.addRow("Набор данных:", self._dataset_name_label)
        summary_form.addRow("Строки:", self._rows_label)
        summary_form.addRow("Столбцы:", self._columns_label)
        summary_form.addRow("Всего пропусков:", self._missing_label)
        summary_form.addRow("Дублирующиеся строки:", self._duplicates_label)
        summary_form.addRow("Использование памяти (байт):", self._memory_label)
        summary_form.addRow("Столбцы с null:", self._nullable_columns_label)
        summary_form.addRow("Подсчёт логических типов:", self._logical_types_label)

        layout.addWidget(summary_box)
        layout.addWidget(self._schema_table)

    def set_dataset_profile(
        self,
        dataset: DatasetDto,
        profiling_summary: DatasetProfilingSummaryDto,
    ) -> None:
        """Отобразить информацию профилирования."""
        self._dataset_name_label.setText(dataset.name)
        self._rows_label.setText(str(profiling_summary.row_count))
        self._columns_label.setText(str(profiling_summary.column_count))
        self._missing_label.setText(str(profiling_summary.missing_total))
        self._duplicates_label.setText(str(profiling_summary.duplicate_count))
        self._memory_label.setText(
            str(profiling_summary.memory_usage_bytes)
            if profiling_summary.memory_usage_bytes is not None
            else "—"
        )
        self._nullable_columns_label.setText(str(profiling_summary.nullable_column_count))
        self._logical_types_label.setText(
            ", ".join(
                f"{key}: {value}" for key, value in profiling_summary.logical_type_counts.items()
            )
            or "—"
        )
        self._schema_table.set_features(dataset.features)

    def clear_content(self) -> None:
        """Очистить содержимое страницы."""
        self._dataset_name_label.setText("—")
        self._rows_label.setText("0")
        self._columns_label.setText("0")
        self._missing_label.setText("0")
        self._duplicates_label.setText("0")
        self._memory_label.setText("—")
        self._nullable_columns_label.setText("0")
        self._logical_types_label.setText("—")
        self._schema_table.clear_content()
