"""Модель дерева проекта для главной панели навигации."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItem, QStandardItemModel

from dt_analytics.application.dto import DatasetDto, ExperimentDto, ProjectDto


@dataclass(frozen=True, slots=True)
class TreeNodePayload:
    """Полезная нагрузка, хранящаяся в элементах дерева."""

    node_type: str
    entity_id: str | None = None


class ProjectTreeModel(QStandardItemModel):
    """Модель навигации, представляющая текущее состояние проекта."""

    NODE_ROLE = Qt.ItemDataRole.UserRole + 1

    def __init__(self) -> None:
        super().__init__()
        self.setHorizontalHeaderLabels(["Проект"])
        self.clear_to_empty()

    def clear_to_empty(self) -> None:
        """Сбросить дерево в пустое состояние."""
        self.clear()
        self.setHorizontalHeaderLabels(["Проект"])
        root = self.invisibleRootItem()
        placeholder = QStandardItem("Нет открытого проекта")
        placeholder.setEditable(False)
        placeholder.setData(TreeNodePayload(node_type="empty"), self.NODE_ROLE)
        root.appendRow(placeholder)

    def populate(
        self,
        project: ProjectDto,
        datasets: tuple[DatasetDto, ...] = (),
        experiments: tuple[ExperimentDto, ...] = (),
    ) -> None:
        """Заполнить модель структурой проекта."""
        self.clear()
        self.setHorizontalHeaderLabels(["Проект"])

        root = self.invisibleRootItem()

        project_item = QStandardItem(project.name)
        project_item.setEditable(False)
        project_item.setData(
            TreeNodePayload(node_type="project", entity_id=project.id),
            self.NODE_ROLE,
        )
        root.appendRow(project_item)

        datasets_item = QStandardItem("Наборы данных")
        datasets_item.setEditable(False)
        datasets_item.setData(TreeNodePayload(node_type="datasets_group"), self.NODE_ROLE)
        project_item.appendRow(datasets_item)

        if datasets:
            for dataset in datasets:
                item = QStandardItem(dataset.name)
                item.setEditable(False)
                item.setData(
                    TreeNodePayload(node_type="dataset", entity_id=dataset.id),
                    self.NODE_ROLE,
                )
                datasets_item.appendRow(item)
        else:
            empty_item = QStandardItem("Нет наборов данных")
            empty_item.setEditable(False)
            empty_item.setData(TreeNodePayload(node_type="empty"), self.NODE_ROLE)
            datasets_item.appendRow(empty_item)

        experiments_item = QStandardItem("Эксперименты")
        experiments_item.setEditable(False)
        experiments_item.setData(
            TreeNodePayload(node_type="experiments_group"),
            self.NODE_ROLE,
        )
        project_item.appendRow(experiments_item)

        if experiments:
            for experiment in experiments:
                item = QStandardItem(f"{experiment.name} [{experiment.status}]")
                item.setEditable(False)
                item.setData(
                    TreeNodePayload(node_type="experiment", entity_id=experiment.id),
                    self.NODE_ROLE,
                )
                experiments_item.appendRow(item)
        else:
            empty_item = QStandardItem("Нет экспериментов")
            empty_item.setEditable(False)
            empty_item.setData(TreeNodePayload(node_type="empty"), self.NODE_ROLE)
            experiments_item.appendRow(empty_item)

    def payload_from_index(self, index) -> TreeNodePayload | None:
        """Вернуть полезную нагрузку для заданного индекса модели."""
        if not index.isValid():
            return None
        payload = index.data(self.NODE_ROLE)
        return payload if isinstance(payload, TreeNodePayload) else None
