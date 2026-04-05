"""Виджет навигации дерева проекта."""

from __future__ import annotations

# from PySide6.QtCore import Qt
from PySide6.QtCore import QModelIndex, Signal
from PySide6.QtWidgets import QTreeView

from dt_analytics.presentation.models import ProjectTreeModel

# from dt_analytics.presentation.models.project_tree_model import TreeNodePayload


class ProjectTreeWidget(QTreeView):
    """Дерево навигации по сущностям проекта."""

    node_activated = Signal(str, str)

    def __init__(self, model: ProjectTreeModel, parent=None) -> None:
        super().__init__(parent)
        self._model = model
        self.setModel(self._model)
        self.setHeaderHidden(False)
        self.setUniformRowHeights(True)
        self.setEditTriggers(QTreeView.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(QTreeView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTreeView.SelectionMode.SingleSelection)
        self.doubleClicked.connect(self._on_double_clicked)
        self.clicked.connect(self._on_clicked)

    def _emit_payload(self, index: QModelIndex) -> None:
        payload = self._model.payload_from_index(index)
        if payload is None:
            return
        entity_id = payload.entity_id or ""
        self.node_activated.emit(payload.node_type, entity_id)

    def _on_double_clicked(self, index: QModelIndex) -> None:
        self._emit_payload(index)

    def _on_clicked(self, index: QModelIndex) -> None:
        self._emit_payload(index)

    def expand_all_nodes(self) -> None:
        """Развёрнуть всё дерево."""
        self.expandAll()
