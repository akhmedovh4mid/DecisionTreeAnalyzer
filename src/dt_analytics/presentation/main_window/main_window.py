"""Главное окно приложения."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDockWidget,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStackedWidget,
    QStatusBar,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from dt_analytics.application.dto import DatasetDto, ExperimentDto, ProjectDto
from dt_analytics.config.schemas import AppSettings
from dt_analytics.presentation.main_window.main_window_controller import (
    MainWindowController,
)
from dt_analytics.presentation.models import ProjectTreeModel
from dt_analytics.presentation.pages import (
    DatasetViewerPage,
    ModelConfigPage,
    PreprocessingConfigPage,
)
from dt_analytics.presentation.widgets import ProjectTreeWidget


class MainWindow(QMainWindow):
    """Верхнеуровневое окно приложения."""

    def __init__(
        self,
        settings: AppSettings,
        controller: MainWindowController,
    ) -> None:
        super().__init__()
        self._settings = settings
        self._controller = controller

        self._project_tree_model = ProjectTreeModel()
        self._project_tree_widget = ProjectTreeWidget(self._project_tree_model, self)

        self._workspace_stack = QStackedWidget(self)
        self._home_page = QTextEdit(self)
        self._home_page.setReadOnly(True)

        self._dataset_viewer_page = DatasetViewerPage(self)

        self._experiment_config_page = QWidget(self)
        self._preprocessing_config_page = PreprocessingConfigPage(self)
        self._model_config_page = ModelConfigPage(self)

        experiment_layout = QVBoxLayout(self._experiment_config_page)
        splitter = QSplitter(Qt.Orientation.Horizontal, self._experiment_config_page)
        splitter.addWidget(self._preprocessing_config_page)
        splitter.addWidget(self._model_config_page)
        splitter.setSizes([600, 500])
        experiment_layout.addWidget(splitter)

        self._workspace_stack.addWidget(self._home_page)
        self._workspace_stack.addWidget(self._dataset_viewer_page)
        self._workspace_stack.addWidget(self._experiment_config_page)

        self._project_status_label = QLabel("Проект: —", self)
        self._dataset_status_label = QLabel("Наборы данных: 0", self)
        self._experiment_status_label = QLabel("Эксперименты: 0", self)

        self._setup_ui()
        self._controller.bind_view(self)

    @property
    def dataset_viewer_page(self) -> DatasetViewerPage:
        """Предоставить доступ к странице просмотра набора данных для привязки контроллера"""
        return self._dataset_viewer_page

    @property
    def preprocessing_config_page(self) -> PreprocessingConfigPage:
        return self._preprocessing_config_page

    @property
    def model_config_page(self) -> ModelConfigPage:
        return self._model_config_page

    def _setup_ui(self) -> None:
        """Настроить интерфейс главного окна."""
        self.setWindowTitle(self._settings.window.title)
        self.resize(self._settings.window.width, self._settings.window.height)
        self.setMinimumSize(
            self._settings.window.min_width,
            self._settings.window.min_height,
        )

        self._home_page.setPlainText("Нет открытого проекта.")
        self.setCentralWidget(self._workspace_stack)

        self._setup_menu_bar()
        self._setup_toolbar()
        self._setup_docks()
        self._setup_status_bar()

        self._project_tree_widget.node_activated.connect(self._controller.on_tree_node_activated)

    def _setup_menu_bar(self) -> None:
        """Создать строку меню."""
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("Файл")
        file_menu.addAction("Создать проект", self._controller.create_project)
        file_menu.addAction("Открыть проект", self._controller.open_project)
        file_menu.addAction("Сохранить проект", self._controller.save_project)
        file_menu.addSeparator()
        file_menu.addAction("Импортировать CSV‑набор данных", self._controller.import_csv_dataset)
        file_menu.addSeparator()
        file_menu.addAction("Выход", self.close)

        experiment_menu = menu_bar.addMenu("Эксперимент")
        experiment_menu.addAction(
            "Настроить эксперимент", self._controller.open_experiment_configuration
        )

        help_menu = menu_bar.addMenu("Справка")
        help_menu.addAction("О программе", self._show_about_dialog)

    def _setup_toolbar(self) -> None:
        """Создать верхнюю панель инструментов."""
        toolbar = QToolBar("Главная панель инструментов", self)
        toolbar.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)

        toolbar.addAction("Новый проект", self._controller.create_project)
        toolbar.addAction("Открыть проект", self._controller.open_project)
        toolbar.addAction("Сохранить проект", self._controller.save_project)
        toolbar.addSeparator()
        toolbar.addAction("Импорт CSV", self._controller.import_csv_dataset)
        toolbar.addSeparator()
        toolbar.addAction("Настроить эксперимент", self._controller.open_experiment_configuration)

    def _setup_docks(self) -> None:
        """Создать панели‑доки."""
        navigation_dock = QDockWidget("Проводник проекта", self)
        navigation_dock.setWidget(self._project_tree_widget)
        navigation_dock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
        )
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, navigation_dock)

    def _setup_status_bar(self) -> None:
        """Создать строку состояния."""
        status_bar = QStatusBar(self)
        status_bar.addPermanentWidget(self._project_status_label)
        status_bar.addPermanentWidget(self._dataset_status_label)
        status_bar.addPermanentWidget(self._experiment_status_label)
        self.setStatusBar(status_bar)

    def update_project_tree(
        self,
        *,
        project: ProjectDto | None,
        datasets: tuple[DatasetDto, ...],
        experiments: tuple[ExperimentDto, ...],
    ) -> None:
        """Обновить содержимое дерева навигации."""
        if project is None:
            self._project_tree_model.clear_to_empty()
        else:
            self._project_tree_model.populate(
                project=project,
                datasets=datasets,
                experiments=experiments,
            )
            self._project_tree_widget.expand_all_nodes()

    def switch_to_home_page(self) -> None:
        """Показать домашнюю страницу по умолчанию."""
        self._workspace_stack.setCurrentWidget(self._home_page)

    def switch_to_dataset_page(self) -> None:
        """Показать страницу просмотра набора данных."""
        self._workspace_stack.setCurrentWidget(self._dataset_viewer_page)

    def switch_to_experiment_config_page(self) -> None:
        self._workspace_stack.setCurrentWidget(self._experiment_config_page)

    def set_home_message(self, text: str) -> None:
        """Заменить текстовое сообщение на домашней странице."""
        self._home_page.setPlainText(text)

    def update_window_context(
        self,
        *,
        project_name: str | None,
        dataset_count: int,
        experiment_count: int,
    ) -> None:
        """Обновить надписи контекста на строке состояния."""
        self._project_status_label.setText(f"Проект: {project_name or '—'}")
        self._dataset_status_label.setText(f"Наборы данных: {dataset_count}")
        self._experiment_status_label.setText(f"Эксперименты: {experiment_count}")

    def show_status_message(self, message: str, timeout_ms: int = 5000) -> None:
        """Показать временное сообщение в строке состояния."""
        self.statusBar().showMessage(message, timeout_ms)

    def _show_about_dialog(self) -> None:
        """Показать диалог «О программе»."""
        QMessageBox.information(
            self,
            "О программе DT Analytics",
            (
                f"{self._settings.metadata.name}\n"
                f"Версия: {self._settings.metadata.version}\n\n"
                "Настольная информационная система для анализа данных "
                "с использованием методов деревьев решений."
            ),
        )
