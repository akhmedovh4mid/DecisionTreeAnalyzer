"""Фабрика приложения для DT Analytics."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from PySide6.QtWidgets import QApplication

from dt_analytics.bootstrap.container import AppContainer
from dt_analytics.presentation.main_window import MainWindow, MainWindowController


@dataclass(slots=True)
class ApplicationInstance:
    """Полностью собранный экземпляр приложения."""

    qt_app: QApplication
    main_window: MainWindow


def create_application(
    argv: Sequence[str],
    container: AppContainer,
) -> ApplicationInstance:
    """Создать QApplication и корневые объекты UI."""
    qt_app = QApplication(list(argv))
    qt_app.setApplicationName(container.settings.metadata.name)
    qt_app.setOrganizationName(container.settings.metadata.organization_name)
    qt_app.setOrganizationDomain(container.settings.metadata.organization_domain)
    qt_app.setApplicationVersion(container.settings.metadata.version)

    controller = MainWindowController(
        settings=container.settings,
        create_project_use_case=container.create_project_use_case,
        open_project_use_case=container.open_project_use_case,
        save_project_use_case=container.save_project_use_case,
        get_dataset_preview_use_case=container.get_dataset_preview_use_case,
        import_csv_dataset_use_case=container.import_csv_dataset_use_case,
    )

    main_window = MainWindow(
        settings=container.settings,
        controller=controller,
    )

    return ApplicationInstance(
        qt_app=qt_app,
        main_window=main_window,
    )
