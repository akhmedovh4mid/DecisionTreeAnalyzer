"""Главное окно приложения."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QMainWindow, QStatusBar, QVBoxLayout, QWidget

from dt_analytics.config.schemas import AppSettings


class MainWindow(QMainWindow):
    """Главное окно приложения верхнего уровня."""

    def __init__(self, settings: AppSettings) -> None:
        super().__init__()
        self._settings = settings
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Настроить интерфейс главного окна."""
        self.setWindowTitle(self._settings.window.title)
        self.resize(self._settings.window.width, self._settings.window.height)
        self.setMinimumSize(
            self._settings.window.min_width,
            self._settings.window.min_height,
        )

        central_widget = QWidget(self)
        layout = QVBoxLayout(central_widget)

        title_label = QLabel("DT Analytics", central_widget)
        subtitle_label = QLabel(
            "Уровень bootstrap и конфигурации успешно инициализирован.",
            central_widget,
        )

        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)
        layout.addStretch(1)

        self.setCentralWidget(central_widget)

        status_bar = QStatusBar(self)
        status_bar.showMessage(
            f"Готово | Версия: {self._settings.metadata.version}",
        )
        self.setStatusBar(status_bar)
