"""Виджет отображения схемы набора данных."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
)

from dt_analytics.application.dto import FeatureDto


class ColumnSchemaTable(QTableWidget):
    """Таблица, отображающая схему столбцов набора данных."""

    HEADERS = [
        "Название",
        "Физический тип данных",
        "Логический тип",
        "Роль",
        "Null‑допустимый",
        "Пропуски",
        "Уникальных значений",
        "Позиция",
    ]

    def __init__(self, parent=None) -> None:
        super().__init__(0, len(self.HEADERS), parent)
        self.setHorizontalHeaderLabels(self.HEADERS)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

    def set_features(self, features: tuple[FeatureDto, ...]) -> None:
        """Заполнить таблицу описаниями признаков."""
        self.setRowCount(len(features))

        for row, feature in enumerate(features):
            self._set_item(row, 0, feature.name)
            self._set_item(row, 1, feature.physical_dtype)
            self._set_item(row, 2, feature.logical_type)
            self._set_item(row, 3, feature.role)
            self._set_item(row, 4, "Да" if feature.nullable else "Нет")
            self._set_item(row, 5, str(feature.missing_count))
            self._set_item(
                row, 6, str(feature.unique_count) if feature.unique_count is not None else "—"
            )
            self._set_item(row, 7, str(feature.ordinal_position))

    def clear_content(self) -> None:
        """Очистить строки таблицы."""
        self.setRowCount(0)

    def _set_item(self, row: int, column: int, text: str) -> None:
        item = QTableWidgetItem(text)
        self.setItem(row, column, item)
