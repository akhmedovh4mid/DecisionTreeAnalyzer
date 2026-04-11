from __future__ import annotations

from PySide6.QtWidgets import (
    QAbstractItemView,
    QGroupBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.domain.evaluation_metrics import EvaluationMetrics


class MetricsView(QGroupBox):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Метрики качества", parent)

        self._table = QTableWidget(self)
        self._table.setColumnCount(2)
        self._table.setHorizontalHeaderLabels(["Метрика", "Значение"])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        layout = QVBoxLayout()
        layout.addWidget(self._table)
        self.setLayout(layout)

    def clear(self) -> None:
        self._table.setRowCount(0)

    def show_metrics(self, metrics: EvaluationMetrics) -> None:
        rows = [
            ("Accuracy", f"{metrics.accuracy:.4f}"),
            ("Precision", f"{metrics.precision:.4f}"),
            ("Recall", f"{metrics.recall:.4f}"),
            ("F1-score", f"{metrics.f1_score:.4f}"),
            ("Support", metrics.support),
            ("Классов", metrics.class_count),
            ("Режим усреднения", metrics.average),
            ("Матрица ошибок", self._format_confusion_matrix(metrics.confusion_matrix)),
        ]

        self._table.setRowCount(len(rows))

        for row_index, (label, value) in enumerate(rows):
            self._table.setItem(row_index, 0, QTableWidgetItem(str(label)))
            self._table.setItem(row_index, 1, QTableWidgetItem(str(value)))

        self._table.resizeColumnsToContents()

    @staticmethod
    def _format_confusion_matrix(matrix: list[list[int]]) -> str:
        return " | ".join("[" + ", ".join(map(str, row)) + "]" for row in matrix)
