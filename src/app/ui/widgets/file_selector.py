from __future__ import annotations

from pathlib import Path
from typing import cast

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from src.app.controller.application_controller import EvaluationAverage, PredictionScope


class FileSelectorWidget(QGroupBox):
    file_selected = Signal(str)
    run_requested = Signal(str, str, str, str, int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Источник данных", parent)
        self._build_ui()

    def _build_ui(self) -> None:
        self._path_edit = QLineEdit(self)
        self._path_edit.setPlaceholderText(
            "Выберите CSV / TSV / XLSX / XLS / JSON файл..."
        )

        self._browse_button = QPushButton("Обзор...", self)
        self._browse_button.clicked.connect(self._choose_file)

        path_layout = QHBoxLayout()
        path_layout.addWidget(self._path_edit)
        path_layout.addWidget(self._browse_button)

        self._target_combo = QComboBox(self)
        self._target_combo.setEnabled(False)

        self._prediction_scope_combo = QComboBox(self)
        self._prediction_scope_combo.addItems(["test", "train", "full"])
        self._prediction_scope_combo.setCurrentText("test")

        self._average_combo = QComboBox(self)
        self._average_combo.addItems(["weighted", "macro", "micro", "binary"])
        self._average_combo.setCurrentText("weighted")

        self._zero_division_spin = QSpinBox(self)
        self._zero_division_spin.setRange(0, 1)
        self._zero_division_spin.setValue(0)

        self._run_button = QPushButton("Запустить анализ", self)
        self._run_button.setEnabled(False)
        self._run_button.clicked.connect(self._emit_run_requested)

        self._status_label = QLabel("Файл не выбран", self)

        form_layout = QFormLayout()
        form_layout.addRow("Файл:", path_layout)
        form_layout.addRow("Целевой столбец:", self._target_combo)
        form_layout.addRow("Область прогноза:", self._prediction_scope_combo)
        form_layout.addRow("Усреднение метрик:", self._average_combo)
        form_layout.addRow("zero_division:", self._zero_division_spin)

        layout = QVBoxLayout()
        layout.addLayout(form_layout)
        layout.addWidget(self._run_button)
        layout.addWidget(self._status_label)
        self.setLayout(layout)

    @property
    def prediction_scope(self) -> PredictionScope:
        return cast(PredictionScope, self._prediction_scope_combo.currentText().strip())

    @property
    def evaluation_average(self) -> EvaluationAverage:
        return cast(EvaluationAverage, self._average_combo.currentText().strip())

    @property
    def zero_division(self) -> int:
        return int(self._zero_division_spin.value())

    @property
    def selected_path(self) -> str:
        return self._path_edit.text().strip()

    def set_available_columns(self, columns: list[str]) -> None:
        self._target_combo.clear()
        self._target_combo.addItems(columns)

        enabled = bool(columns)
        self._target_combo.setEnabled(enabled)
        self._run_button.setEnabled(enabled and bool(self.selected_path))

        if enabled:
            self._status_label.setText(f"Доступно столбцов: {len(columns)}")
        else:
            self._status_label.setText("Не удалось определить столбцы")

    def clear_columns(self) -> None:
        self._target_combo.clear()
        self._target_combo.setEnabled(False)
        self._run_button.setEnabled(False)

    def set_status(self, text: str) -> None:
        self._status_label.setText(text)

    def _choose_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выбор набора данных",
            "",
            "Datasets (*.csv *.tsv *.xlsx *.xls *.json);;All Files (*)",
        )
        if not file_path:
            return

        normalized = str(Path(file_path).expanduser())
        self._path_edit.setText(normalized)
        self._run_button.setEnabled(bool(self._target_combo.count()))
        self.file_selected.emit(normalized)

    def _emit_run_requested(self) -> None:
        file_path = self.selected_path
        target_column = self._target_combo.currentText().strip()
        prediction_scope = self._prediction_scope_combo.currentText().strip()
        evaluation_average = self._average_combo.currentText().strip()
        zero_division = int(self._zero_division_spin.value())

        if not file_path or not target_column:
            self._status_label.setText("Сначала выберите файл и целевой столбец")
            return

        self.run_requested.emit(
            file_path,
            target_column,
            prediction_scope,
            evaluation_average,
            zero_division,
        )
