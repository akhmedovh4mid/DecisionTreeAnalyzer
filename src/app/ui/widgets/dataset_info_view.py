from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import (
    QAbstractItemView,
    QGroupBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.domain.dataset import Dataset
from src.domain.dataset_info import DatasetInfo


class DatasetInfoView(QGroupBox):
    def __init__(self, parent: QWidget | None = None):
        super().__init__("Информация о данных", parent)

        self._table = QTableWidget(self)
        self._table.setColumnCount(2)
        self._table.setHorizontalHeaderLabels(["Параметр", "Значение"])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        layout = QVBoxLayout()
        layout.addWidget(self._table)
        self.setLayout(layout)

    def clear(self) -> None:
        self._table.setRowCount(0)

    def show_dataset(self, dataset: Dataset) -> None:
        self._populate(
            [
                ("Имя набора", dataset.name),
                ("Путь", str(dataset.source_path)),
                ("Формат", dataset.file_format),
                ("Строк", dataset.row_count),
                ("Столбцов", dataset.column_count),
                ("Столбцы", ", ".join(dataset.columns)),
            ]
        )

    def show_dataset_info(self, dataset_info: DatasetInfo) -> None:
        self._populate(
            [
                ("Набор данных", dataset_info.source_dataset_name),
                ("Целевой столбец", dataset_info.target_column),
                ("Строк", dataset_info.row_count),
                ("Столбцов", dataset_info.column_count),
                ("Признаков", dataset_info.feature_count),
                ("Числовые признаки", ", ".join(dataset_info.numeric_columns) or "—"),
                (
                    "Категориальные признаки",
                    ", ".join(dataset_info.categorical_columns) or "—",
                ),
                ("Классов", dataset_info.class_count),
                (
                    "Распределение классов",
                    self._format_dict(dataset_info.class_distribution),
                ),
                ("Пропусков всего", dataset_info.total_missing_values),
                (
                    "Столбцы с пропусками",
                    ", ".join(dataset_info.missing_columns) or "—",
                ),
                ("Дубликатов строк", dataset_info.duplicate_row_count),
            ]
        )

    def _populate(self, rows: list[tuple[str, Any]]) -> None:
        self._table.setRowCount(len(rows))

        for row_index, (label, value) in enumerate(rows):
            self._table.setItem(row_index, 0, QTableWidgetItem(str(label)))
            self._table.setItem(row_index, 1, QTableWidgetItem(str(value)))

        self._table.resizeColumnsToContents()

    @staticmethod
    def _format_dict(values: dict[str, int]) -> str:
        if not values:
            return "—"
        return ", ".join(f"{key}: {value}" for key, value in values.items())
