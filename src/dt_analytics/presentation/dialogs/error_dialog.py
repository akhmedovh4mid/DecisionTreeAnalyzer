"""Диалог ошибки для пользовательских сбоев."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QTextEdit,
    QVBoxLayout,
)


class ErrorDialog(QDialog):
    """Диалог, показывающий пользовательское сообщение и технические детали ошибки."""

    def __init__(
        self,
        title: str,
        message: str,
        details: str | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(560, 320)

        layout = QVBoxLayout(self)

        message_label = QLabel(message, self)
        message_label.setWordWrap(True)
        layout.addWidget(message_label)

        self._details_edit = QTextEdit(self)
        self._details_edit.setReadOnly(True)
        self._details_edit.setPlainText(details or "Дополнительные детали отсутствуют.")
        layout.addWidget(self._details_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok, parent=self)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

    @classmethod
    def show_error(
        cls,
        *,
        title: str,
        message: str,
        details: str | None = None,
        parent=None,
    ) -> None:
        """Удобный метод для показа модального диалога ошибки."""
        dialog = cls(title=title, message=message, details=details, parent=parent)
        dialog.exec()
