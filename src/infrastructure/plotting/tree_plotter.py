from __future__ import annotations

import tempfile
from pathlib import Path

from sklearn.tree import export_text, plot_tree

from src.domain.decision_tree_model import DecisionTreeModel


class TreePlottingError(Exception):
    """Ошибка при подготовке визуализации дерева решений."""


class TreePlotter:
    def __init__(
        self,
        *,
        output_dir: str | Path | None = None,
        dpi: int = 150,
        figure_width: float = 18.0,
        figure_height: float = 10.0,
    ) -> None:
        if output_dir is None:
            base_dir = Path(tempfile.gettempdir()) / "decision_tree_analysis_system"
        else:
            base_dir = Path(output_dir)

        self._output_dir = base_dir.expanduser().resolve()
        self._dpi = dpi
        self._figure_width = figure_width
        self._figure_height = figure_height

    def export_tree_text(self, model: DecisionTreeModel) -> str:
        try:
            return export_text(
                model.model,
                feature_names=list(model.feature_names),
            )
        except Exception as exc:
            raise TreePlottingError(
                f"Не удалось сформировать текстовое представление дерева: {exc}"
            ) from exc

    def render_tree_image(
        self,
        model: DecisionTreeModel,
        *,
        file_name: str | None = None,
    ) -> str | None:
        """
        Возвращает путь к PNG-файлу или None, если отрисовка не удалась.
        Визуализация не должна ломать весь pipeline, поэтому вызывающий код
        может безопасно использовать fallback на текстовое представление.
        """
        try:
            import matplotlib

            matplotlib.use("Agg")

            import matplotlib.pyplot as plt
        except Exception:
            return None

        try:
            self._output_dir.mkdir(parents=True, exist_ok=True)

            safe_dataset = self._sanitize_name(
                model.metadata.get("source_dataset_name", "dataset")
            )
            safe_target = self._sanitize_name(model.target_column)

            resolved_file_name = file_name or f"tree_{safe_dataset}_{safe_target}.png"
            output_path = self._output_dir / resolved_file_name

            figure = plt.figure(
                figsize=(self._figure_width, self._figure_height),
                dpi=self._dpi,
            )
            try:
                plot_tree(
                    model.model,
                    feature_names=list(model.feature_names),
                    class_names=list(model.class_names),
                    filled=True,
                    rounded=True,
                    fontsize=8,
                )
                figure.tight_layout()
                figure.savefig(output_path, bbox_inches="tight")
            finally:
                plt.close(figure)

            return str(output_path)
        except Exception:
            return None

    @staticmethod
    def _sanitize_name(value: object) -> str:
        text = str(value).strip().lower()
        if not text:
            return "unknown"
        safe = []
        for char in text:
            if char.isalnum() or char in ("-", "_"):
                safe.append(char)
            else:
                safe.append("_")
        return "".join(safe).strip("_") or "unknown"
