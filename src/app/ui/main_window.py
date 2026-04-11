from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from src.app.controller import ApplicationController, ControllerPipelineResult
from src.app.ui.widgets import (
    DatasetInfoView,
    FileSelectorWidget,
    MetricsView,
    TreeView,
)


class MainWindow(QMainWindow):
    def __init__(self, controller: ApplicationController | None = None) -> None:
        super().__init__()
        self._controller = controller or ApplicationController()
        self._init_ui()
        self._connect_signals()

    def _init_ui(self) -> None:
        self.setWindowTitle("Система анализа данных на основе дерева решений")
        self.resize(1400, 900)

        self._file_selector = FileSelectorWidget(self)
        self._dataset_info_view = DatasetInfoView(self)
        self._metrics_view = MetricsView(self)
        self._tree_view = TreeView(self)

        left_layout = QVBoxLayout()
        left_layout.addWidget(self._file_selector)
        left_layout.addWidget(self._dataset_info_view)

        left_widget = QWidget(self)
        left_widget.setLayout(left_layout)

        top_placeholder = QWidget(self)
        top_layout = QVBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.addWidget(self._metrics_view)
        top_placeholder.setLayout(top_layout)

        center_placeholder = QWidget(self)
        center_layout = QVBoxLayout()
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.addWidget(self._tree_view)
        center_placeholder.setLayout(center_layout)

        bottom_placeholder = QWidget(self)
        bottom_layout = QVBoxLayout()
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_placeholder.setLayout(bottom_layout)

        right_splitter = QSplitter(Qt.Orientation.Vertical, self)
        right_splitter.addWidget(top_placeholder)
        right_splitter.addWidget(center_placeholder)
        right_splitter.addWidget(bottom_placeholder)

        right_splitter.setCollapsible(0, True)
        right_splitter.setCollapsible(1, False)
        right_splitter.setCollapsible(2, True)
        right_splitter.setSizes([220, 620, 0])

        main_splitter = QSplitter(Qt.Orientation.Horizontal, self)
        main_splitter.addWidget(left_widget)
        main_splitter.addWidget(right_splitter)
        main_splitter.setSizes([460, 900])

        container = QWidget(self)
        container_layout = QHBoxLayout()
        container_layout.addWidget(main_splitter)
        container.setLayout(container_layout)

        self.setCentralWidget(container)
        self.setStatusBar(QStatusBar(self))
        self.statusBar().showMessage("Готово")

    def _connect_signals(self) -> None:
        self._file_selector.file_selected.connect(self._on_file_selected)
        self._file_selector.run_requested.connect(self._on_run_requested)

    def _on_file_selected(self, file_path: str) -> None:
        try:
            dataset = self._controller.load_dataset(file_path)
        except Exception as exc:
            self._clear_views()
            self._show_error("Ошибка загрузки данных", str(exc))
            self.statusBar().showMessage("Ошибка загрузки данных")
            return

        self._dataset_info_view.show_dataset(dataset)
        self._file_selector.set_available_columns(dataset.columns)
        self._file_selector.set_status(
            f"Файл '{Path(file_path).name}' успешно загружен"
        )
        self.statusBar().showMessage(f"Загружен файл: {Path(file_path).name}")

    def _on_run_requested(
        self,
        file_path: str,
        target_column: str,
        prediction_scope: str,
        evaluation_average: str,
        zero_division: int,
    ) -> None:
        self.statusBar().showMessage("Выполняется анализ данных...")

        prediction_scope = self._file_selector.prediction_scope
        evaluation_average = self._file_selector.evaluation_average

        try:
            result = self._controller.run_pipeline(
                file_path=file_path,
                target_column=target_column,
                prediction_scope=prediction_scope,
                evaluation_average=evaluation_average,
                zero_division=zero_division,
            )
        except Exception as exc:
            self._show_error("Ошибка выполнения сценария", str(exc))
            self.statusBar().showMessage("Ошибка выполнения сценария")
            return

        self._render_result(result)
        self._file_selector.set_status("Анализ успешно завершён")
        self.statusBar().showMessage("Анализ завершён")

    def _render_result(self, result: ControllerPipelineResult) -> None:
        self._dataset_info_view.show_dataset_info(result.dataset_info)
        self._metrics_view.show_metrics(result.evaluation_metrics)
        self._tree_view.show_visualization(result.visualization_data)

    def _clear_views(self) -> None:
        self._dataset_info_view.clear()
        self._metrics_view.clear()
        self._tree_view.clear()
        self._file_selector.clear_columns()

    @staticmethod
    def _show_error(title: str, message: str) -> None:
        dialog = QMessageBox()
        dialog.setIcon(QMessageBox.Icon.Critical)
        dialog.setWindowTitle(title)
        dialog.setText(message)
        dialog.exec()
