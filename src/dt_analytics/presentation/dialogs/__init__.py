"""Диалоги представления (UI‑диалоги)."""

from dt_analytics.presentation.dialogs.error_dialog import ErrorDialog
from dt_analytics.presentation.dialogs.import_dataset_dialog import (
    ImportDatasetDialog,
    ImportDatasetDialogResult,
)
from dt_analytics.presentation.dialogs.new_project_dialog import (
    NewProjectDialog,
    NewProjectDialogResult,
)

__all__ = [
    "ErrorDialog",
    "ImportDatasetDialog",
    "ImportDatasetDialogResult",
    "NewProjectDialog",
    "NewProjectDialogResult",
]
