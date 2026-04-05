"""Диалог импорта CSV‑набора данных."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)


@dataclass(frozen=True, slots=True)
class ImportDatasetDialogResult:
    """Собранные параметры импорта CSV."""

    csv_file_path: Path
    dataset_name: str | None
    separator: str
    encoding: str
    header: int | None
    decimal: str
    preview_rows: int


class ImportDatasetDialog(QDialog):
    """Диалог выбора параметров импорта CSV‑файла."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Импорт CSV‑набора данных")
        self.resize(520, 220)

        self._path_edit = QLineEdit(self)
        self._dataset_name_edit = QLineEdit(self)

        self._separator_edit = QLineEdit(",", self)
        self._encoding_combo = QComboBox(self)
        self._encoding_combo.addItems(["utf-8", "cp1251", "latin-1"])

        self._header_combo = QComboBox(self)
        self._header_combo.addItem("Заголовок в первой строке", 0)
        self._header_combo.addItem("Без заголовка", None)

        self._decimal_edit = QLineEdit(".", self)

        self._preview_rows_spin = QSpinBox(self)
        self._preview_rows_spin.setRange(1, 1000)
        self._preview_rows_spin.setValue(20)

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()

        path_layout = QHBoxLayout()
        path_layout.addWidget(self._path_edit)
        browse_button = QPushButton("Обзор...", self)
        browse_button.clicked.connect(self._browse_for_file)
        path_layout.addWidget(browse_button)

        form.addRow("CSV‑файл:", path_layout)
        form.addRow("Название набора данных:", self._dataset_name_edit)
        form.addRow("Разделитель:", self._separator_edit)
        form.addRow("Кодировка:", self._encoding_combo)
        form.addRow("Заголовок:", self._header_combo)
        form.addRow("Разделитель десятичной части:", self._decimal_edit)
        form.addRow("Строки предпросмотра:", self._preview_rows_spin)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse_for_file(self) -> None:
        selected, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите CSV‑файл",
            "",
            "CSV‑файлы (*.csv);;Все файлы (*.*)",
        )
        if selected:
            self._path_edit.setText(selected)
            if not self._dataset_name_edit.text().strip():
                self._dataset_name_edit.setText(Path(selected).stem)

    def _validate_and_accept(self) -> None:
        if self._path_edit.text().strip():
            self.accept()

    def get_result(self) -> ImportDatasetDialogResult:
        """Вернуть типизированный результат диалога."""
        dataset_name = self._dataset_name_edit.text().strip() or None
        return ImportDatasetDialogResult(
            csv_file_path=Path(self._path_edit.text().strip()).expanduser().resolve(),
            dataset_name=dataset_name,
            separator=self._separator_edit.text() or ",",
            encoding=self._encoding_combo.currentData()
            if self._encoding_combo.currentData() is not None
            else self._encoding_combo.currentText(),
            header=self._header_combo.currentData(),
            decimal=self._decimal_edit.text() or ".",
            preview_rows=int(self._preview_rows_spin.value()),
        )
