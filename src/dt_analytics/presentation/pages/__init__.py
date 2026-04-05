"""Страницы уровня представления (UI‑страницы)."""

from dt_analytics.presentation.pages.dataset_profiling_page import DatasetProfilingPage
from dt_analytics.presentation.pages.dataset_viewer_page import DatasetViewerPage
from dt_analytics.presentation.pages.model_config_page import ModelConfigPage
from dt_analytics.presentation.pages.preprocessing_config_page import PreprocessingConfigPage

__all__ = [
    "DatasetProfilingPage",
    "DatasetViewerPage",
    "ModelConfigPage",
    "PreprocessingConfigPage",
]
