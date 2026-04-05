"""Диалог создания нового проекта."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)


@dataclass(frozen=True, slots=True)
class NewProjectDialogResult:
    """Собранные данные о создании проекта из диалога."""

    name: str
    storage_path: Path
    description: str | None


class NewProjectDialog(QDialog):
    """Диалог ввода параметров создания проекта."""

    def __init__(self, default_projects_dir: Path, parent=None) -> None:
        super().__init__(parent)
        self._default_projects_dir = default_projects_dir.expanduser().resolve()

        self.setWindowTitle("Создать проект")
        self.resize(520, 260)

        self._name_edit = QLineEdit(self)
        self._path_edit = QLineEdit(str(self._default_projects_dir), self)
        self._description_edit = QTextEdit(self)
        self._description_edit.setPlaceholderText("Опциональное описание проекта")

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        form = QFormLayout()

        form.addRow("Название проекта:", self._name_edit)

        path_layout = QHBoxLayout()
        path_layout.addWidget(self._path_edit)

        browse_button = QPushButton("Обзор...", self)
        browse_button.clicked.connect(self._browse_for_directory)
        path_layout.addWidget(browse_button)

        form.addRow("Папка проекта:", path_layout)
        form.addRow("Описание:", self._description_edit)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse_for_directory(self) -> None:
        selected = QFileDialog.getExistingDirectory(
            self,
            "Выберите папку проекта",
            str(self._default_projects_dir),
        )
        if selected:
            self._path_edit.setText(selected)

    def _validate_and_accept(self) -> None:
        if self._name_edit.text().strip() and self._path_edit.text().strip():
            self.accept()

    def get_result(self) -> NewProjectDialogResult:
        """Вернуть типизированный результат диалога."""
        description = self._description_edit.toPlainText().strip() or None
        return NewProjectDialogResult(
            name=self._name_edit.text().strip(),
            storage_path=Path(self._path_edit.text().strip()).expanduser().resolve(),
            description=description,
        )
