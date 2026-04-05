"""Виджет отображения сообщений валидации."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QListWidget, QListWidgetItem, QVBoxLayout, QWidget


class ValidationMessagesWidget(QWidget):
    """Отображение ошибок и предупреждений валидации для страниц конфигурации."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self._title_label = QLabel("Валидация", self)
        self._list_widget = QListWidget(self)

        layout = QVBoxLayout(self)
        layout.addWidget(self._title_label)
        layout.addWidget(self._list_widget)

    def set_messages(
        self,
        *,
        errors: list[str] | tuple[str, ...] = (),
        warnings: list[str] | tuple[str, ...] = (),
    ) -> None:
        """Заполнить список сообщений валидации."""
        self._list_widget.clear()

        for error in errors:
            item = QListWidgetItem(f"Ошибка: {error}")
            self._list_widget.addItem(item)

        for warning in warnings:
            item = QListWidgetItem(f"Предупреждение: {warning}")
            self._list_widget.addItem(item)

        if not errors and not warnings:
            self._list_widget.addItem(QListWidgetItem("Нет проблем валидации."))

    def clear_messages(self) -> None:
        """Очистить список сообщений."""
        self._list_widget.clear()
        self._list_widget.addItem(QListWidgetItem("Нет проблем валидации."))
