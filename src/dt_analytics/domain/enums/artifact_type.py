"""Перечисление типов артефактов."""

from __future__ import annotations

from enum import StrEnum


class ArtifactType(StrEnum):
    """Типы генерируемых артефактов эксперимента."""

    MODEL = "model"
    FEATURE_IMPORTANCE_PLOT = "feature_importance_plot"
    TREE_PLOT = "tree_plot"
    METRICS_EXPORT = "metrics_export"
    REPORT = "report"
    PROCESSED_DATASET = "processed_dataset"
