"""Контроллер рабочего процесса главного окна."""

from __future__ import annotations

from dataclasses import dataclass, field

from dt_analytics.application.dto import (
    CreateProjectRequest,
    CsvImportOptionsDto,
    DatasetDto,
    ExperimentDto,
    GetDatasetPreviewRequest,
    ImportCsvDatasetRequest,
    OpenProjectRequest,
    ProjectDto,
    SaveProjectRequest,
)
from dt_analytics.application.use_cases.datasets import (
    GetDatasetPreviewUseCase,
    ImportCsvDatasetUseCase,
    ProfileDatasetUseCase,
)
from dt_analytics.application.use_cases.project import (
    CreateProjectUseCase,
    OpenProjectUseCase,
    SaveProjectUseCase,
)
from dt_analytics.config.schemas import AppSettings
from dt_analytics.presentation.controllers import DatasetController
from dt_analytics.presentation.dialogs import (
    ErrorDialog,
    ImportDatasetDialog,
    NewProjectDialog,
)


@dataclass(slots=True)
class MainWindowState:
    """Текущее состояние представления главного окна."""

    project: ProjectDto | None = None
    datasets: list[DatasetDto] = field(default_factory=list)
    experiments: list[ExperimentDto] = field(default_factory=list)


class MainWindowController:
    """Связующее звено между MainWindow и прикладными use case'ами."""

    def __init__(
        self,
        *,
        settings: AppSettings,
        create_project_use_case: CreateProjectUseCase,
        open_project_use_case: OpenProjectUseCase,
        save_project_use_case: SaveProjectUseCase,
        get_dataset_preview_use_case: GetDatasetPreviewUseCase,
        import_csv_dataset_use_case: ImportCsvDatasetUseCase,
        profile_dataset_use_case: ProfileDatasetUseCase,
    ) -> None:
        self._settings = settings
        self._create_project_use_case = create_project_use_case
        self._open_project_use_case = open_project_use_case
        self._save_project_use_case = save_project_use_case
        self._get_dataset_preview_use_case = get_dataset_preview_use_case
        self._import_csv_dataset_use_case = import_csv_dataset_use_case
        self._profile_dataset_use_case = profile_dataset_use_case
        self._state = MainWindowState()
        self._view = None
        self._dataset_controller = DatasetController(
            get_dataset_preview_use_case=get_dataset_preview_use_case,
            profile_dataset_use_case=profile_dataset_use_case,
        )

    def bind_view(self, view) -> None:
        """Привязать Qt‑виджет к контроллеру."""
        self._view = view
        self._dataset_controller.bind_view(view.dataset_viewer_page)
        self._refresh_view()

    def create_project(self) -> None:
        """Обработать действие создания проекта."""
        if self._view is None:
            return

        dialog = NewProjectDialog(
            default_projects_dir=self._settings.paths.default_projects_dir,
            parent=self._view,
        )
        if dialog.exec() != dialog.DialogCode.Accepted:
            return

        dialog_result = dialog.get_result()
        result = self._create_project_use_case.execute(
            CreateProjectRequest(
                name=dialog_result.name,
                storage_path=dialog_result.storage_path,
                description=dialog_result.description,
                app_version=self._settings.metadata.version,
            )
        )

        if result.is_failure:
            self._show_error(
                title="Создание проекта завершилось ошибкой",
                message=result.error.message if result.error else "Неизвестная ошибка.",
                details=result.error.details if result.error else None,
            )
            return

        self._state.project = result.unwrap()
        self._state.datasets = []
        self._state.experiments = []
        self._dataset_controller.clear()
        self._refresh_view()
        self._view.show_status_message(f"Проект '{self._state.project.name}' создан.")

    def open_project(self) -> None:
        """Обработать действие открытия проекта."""
        if self._view is None:
            return

        dialog = NewProjectDialog(
            default_projects_dir=self._settings.paths.default_projects_dir,
            parent=self._view,
        )
        dialog.setWindowTitle("Открыть проект")
        if dialog.exec() != dialog.DialogCode.Accepted:
            return

        dialog_result = dialog.get_result()
        result = self._open_project_use_case.execute(
            OpenProjectRequest(storage_path=dialog_result.storage_path)
        )

        if result.is_failure:
            self._show_error(
                title="Ошибка открытия проекта",
                message=result.error.message if result.error else "Неизвестная ошибка.",
                details=result.error.details if result.error else None,
            )
            return

        self._state.project = result.unwrap()
        self._state.datasets = []
        self._state.experiments = []
        self._dataset_controller.clear()
        self._refresh_view()
        self._view.show_status_message(f"Проект '{self._state.project.name}' открыт.")

    def save_project(self) -> None:
        """Обработать действие сохранения проекта."""
        if self._view is None or self._state.project is None:
            return

        result = self._save_project_use_case.execute(
            SaveProjectRequest(
                project_id=self._state.project.id,
                storage_path=self._state.project.storage_path,
            )
        )

        if result.is_failure:
            self._show_error(
                title="Ошибка сохранения проекта",
                message=result.error.message if result.error else "Неизвестная ошибка.",
                details=result.error.details if result.error else None,
            )
            return

        self._state.project = result.unwrap()
        self._refresh_view()
        self._view.show_status_message(f"Проект '{self._state.project.name}' сохранён.")

    def import_csv_dataset(self) -> None:
        """Обработать действие импорта CSV‑набора данных."""
        if self._view is None:
            return

        if self._state.project is None:
            self._show_error(
                title="Нет открытого проекта",
                message="Откройте или создайте проект перед импортом набора данных.",
            )
            return

        dialog = ImportDatasetDialog(parent=self._view)
        if dialog.exec() != dialog.DialogCode.Accepted:
            return

        dialog_result = dialog.get_result()

        preview_result = self._get_dataset_preview_use_case.execute(
            GetDatasetPreviewRequest(
                csv_file_path=dialog_result.csv_file_path,
                options=CsvImportOptionsDto(
                    separator=dialog_result.separator,
                    encoding=dialog_result.encoding,
                    header=dialog_result.header,
                    decimal=dialog_result.decimal,
                    preview_rows=dialog_result.preview_rows,
                ),
            )
        )
        if preview_result.is_failure:
            self._show_error(
                title="Ошибка предпросмотра набора данных",
                message=preview_result.error.message
                if preview_result.error
                else "Неизвестная ошибка.",
                details=preview_result.error.details if preview_result.error else None,
            )
            return

        import_result = self._import_csv_dataset_use_case.execute(
            ImportCsvDatasetRequest(
                project_id=self._state.project.id,
                csv_file_path=dialog_result.csv_file_path,
                dataset_name=dialog_result.dataset_name,
                options=CsvImportOptionsDto(
                    separator=dialog_result.separator,
                    encoding=dialog_result.encoding,
                    header=dialog_result.header,
                    decimal=dialog_result.decimal,
                    preview_rows=dialog_result.preview_rows,
                ),
            )
        )

        if import_result.is_failure:
            self._show_error(
                title="Ошибка импорта набора данных",
                message=import_result.error.message
                if import_result.error
                else "Неизвестная ошибка.",
                details=import_result.error.details if import_result.error else None,
            )
            return

        imported = import_result.unwrap()
        self._state.datasets.append(imported.dataset)
        self._refresh_view()
        self._dataset_controller.load_dataset(
            project_id=self._state.project.id,
            dataset=imported.dataset,
        )
        self._view.switch_to_dataset_page()
        self._view.show_status_message(f"Набор данных '{imported.dataset.name}' импортирован.")

    def on_tree_node_activated(self, node_type: str, entity_id: str) -> None:
        """Обработать активацию узла дерева проекта."""
        if self._view is None:
            return

        if node_type == "project" and self._state.project is not None:
            self._view.switch_to_home_page()
            self._view.set_home_message(
                f"Проект: {self._state.project.name}\n"
                f"Наборы данных: {len(self._state.datasets)}\n"
                f"Эксперименты: {len(self._state.experiments)}"
            )
            return

        if node_type == "dataset" and self._state.project is not None:
            dataset = next((item for item in self._state.datasets if item.id == entity_id), None)
            if dataset is not None:
                self._dataset_controller.load_dataset(
                    project_id=self._state.project.id,
                    dataset=dataset,
                )
                self._view.switch_to_dataset_page()
            return

        if node_type == "experiment":
            experiment = next(
                (item for item in self._state.experiments if item.id == entity_id),
                None,
            )
            if experiment is not None:
                self._view.switch_to_home_page()
                self._view.set_home_message(
                    f"Эксперимент: {experiment.name}\nСтатус: {experiment.status}"
                )

    def _refresh_view(self) -> None:
        """Обновить привязанный виджет из текущего состояния."""
        if self._view is None:
            return

        self._view.update_project_tree(
            project=self._state.project,
            datasets=tuple(self._state.datasets),
            experiments=tuple(self._state.experiments),
        )

        if self._state.project is None:
            self._dataset_controller.clear()
            self._view.switch_to_home_page()
            self._view.set_home_message(
                "Нет открытого проекта.\nСоздайте или откройте проект, чтобы начать работу."
            )
            self._view.update_window_context(
                project_name=None,
                dataset_count=0,
                experiment_count=0,
            )
        else:
            self._view.switch_to_home_page()
            self._view.set_home_message(
                f"Проект '{self._state.project.name}' готов к работе.\n"
                "Вы можете импортировать наборы данных через панель инструментов или меню 'Файл'."
            )
            self._view.update_window_context(
                project_name=self._state.project.name,
                dataset_count=len(self._state.datasets),
                experiment_count=len(self._state.experiments),
            )

    def _show_error(self, *, title: str, message: str, details: str | None = None) -> None:
        """Показать модальный диалог ошибки."""
        if self._view is None:
            return
        ErrorDialog.show_error(
            title=title,
            message=message,
            details=details,
            parent=self._view,
        )
