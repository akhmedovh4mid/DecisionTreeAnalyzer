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

from src.app.controller.application_controller import ControllerPipelineResult
from src.domain.dataset import Dataset


class DatasetInfoView(QGroupBox):
    def __init__(self, parent: QWidget | None = None) -> None:
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

    def show_pipeline_result(self, result: ControllerPipelineResult) -> None:
        processed = result.processed_dataset
        metrics = result.evaluation_metrics

        self._populate(
            [
                ("Набор данных", result.source_dataset_name),
                ("Целевой столбец", result.target_column),
                ("Признаков после кодирования", result.feature_count),
                ("Классов", result.class_count),
                ("Обучающая выборка", result.train_size),
                ("Тестовая выборка", result.test_size),
                ("Числовые признаки", ", ".join(processed.numeric_columns) or "—"),
                (
                    "Категориальные признаки",
                    ", ".join(processed.categorical_columns) or "—",
                ),
                ("Стратегия оценки", metrics.average),
            ]
        )

    def _populate(self, rows: list[tuple[str, Any]]) -> None:
        self._table.setRowCount(len(rows))

        for row_index, (label, value) in enumerate(rows):
            self._table.setItem(row_index, 0, QTableWidgetItem(str(label)))
            self._table.setItem(row_index, 1, QTableWidgetItem(str(value)))

        self._table.resizeColumnsToContents()
