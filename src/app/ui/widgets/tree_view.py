from __future__ import annotations

from PySide6.QtWidgets import QGroupBox, QPlainTextEdit, QVBoxLayout, QWidget
from sklearn.tree import export_text

from src.domain.decision_tree_model import DecisionTreeModel


class TreeView(QGroupBox):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Дерево решений", parent)

        self._text = QPlainTextEdit(self)
        self._text.setReadOnly(True)

        layout = QVBoxLayout()
        layout.addWidget(self._text)
        self.setLayout(layout)

    def clear(self) -> None:
        self._text.clear()

    def show_model(self, model: DecisionTreeModel) -> None:
        tree_text = export_text(model.model, feature_names=list(model.feature_names))
        header = self._build_header(model)
        self._text.setPlainText(f"{header}\n\n{tree_text}")

    @staticmethod
    def _build_header(model: DecisionTreeModel) -> str:
        importances = model.feature_importances
        ordered_importances = sorted(
            importances.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        importance_lines = [
            f"- {name}: {value:.4f}" for name, value in ordered_importances[:15]
        ]

        return "\n".join(
            [
                f"Целевой столбец: {model.target_column}",
                f"Глубина дерева: {model.depth}",
                f"Количество узлов: {model.node_count}",
                f"Количество листьев: {model.leaf_count}",
                f"Классы: {', '.join(model.class_names)}",
                "Важность признаков:",
                *importance_lines,
            ]
        )
