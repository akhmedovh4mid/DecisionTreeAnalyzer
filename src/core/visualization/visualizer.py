from __future__ import annotations

from src.domain.dataset_info import DatasetInfo
from src.domain.decision_tree_model import DecisionTreeModel
from src.domain.evaluation_metrics import EvaluationMetrics
from src.domain.visualization_data import VisualizationData
from src.infrastructure.plotting import TreePlotter


class VisualizationError(Exception):
    """Ошибка подготовки данных визуализации."""


class Visualizer:
    def __init__(self, plotter: TreePlotter | None = None) -> None:
        self._plotter = plotter or TreePlotter()

    def prepare(
        self,
        dataset_info: DatasetInfo,
        model: DecisionTreeModel,
        metrics: EvaluationMetrics,
    ) -> VisualizationData:
        try:
            tree_text = self._plotter.export_tree_text(model)
        except Exception as exc:
            raise VisualizationError(
                f"Ошибка при подготовке текстового представления дерева: {exc}"
            ) from exc

        tree_image_path = self._plotter.render_tree_image(model)

        model_summary = {
            "target_column": model.target_column,
            "depth": model.depth,
            "node_count": model.node_count,
            "leaf_count": model.leaf_count,
            "class_count": len(model.class_names),
            "classes": ", ".join(model.class_names),
        }

        metrics_summary = {
            "accuracy": float(metrics.accuracy),
            "precision": float(metrics.precision),
            "recall": float(metrics.recall),
            "f1_score": float(metrics.f1_score),
            "average": metrics.average,
            "support": int(metrics.support),
        }

        dataset_summary = {
            "source_dataset_name": dataset_info.source_dataset_name,
            "target_column": dataset_info.target_column,
            "row_count": int(dataset_info.row_count),
            "column_count": int(dataset_info.column_count),
            "feature_count": int(dataset_info.feature_count),
            "class_count": int(dataset_info.class_count),
            "missing_values": int(dataset_info.total_missing_values),
            "duplicate_row_count": int(dataset_info.duplicate_row_count),
        }

        metadata = {
            "has_tree_image": bool(tree_image_path),
            "tree_image_path": tree_image_path,
            "class_distribution": dict(dataset_info.class_distribution),
            "numeric_columns": list(dataset_info.numeric_columns),
            "categorical_columns": list(dataset_info.categorical_columns),
            "model_parameters": dict(model.parameters),
            "prediction_scope": metrics.prediction_scope,
        }

        return VisualizationData(
            source_dataset_name=dataset_info.source_dataset_name,
            target_column=dataset_info.target_column,
            tree_text=tree_text,
            tree_image_path=tree_image_path,
            model_summary=model_summary,
            metrics_summary=metrics_summary,
            dataset_summary=dataset_summary,
            feature_importances=model.feature_importances,
            metadata=metadata,
        )
