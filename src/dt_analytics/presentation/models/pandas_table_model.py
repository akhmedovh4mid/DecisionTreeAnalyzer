"""Qt‑таблица, основанная на pandas DataFrame."""

from __future__ import annotations

from pandas import DataFrame
from PySide6.QtCore import QAbstractTableModel, QModelIndex, QPersistentModelIndex, Qt

type IndexType = QModelIndex | QPersistentModelIndex


class PandasTableModel(QAbstractTableModel):
    """Таблица только для чтения, отображающая pandas DataFrame в виджетах Qt."""

    def __init__(self, dataframe: DataFrame | None = None, parent=None) -> None:
        super().__init__(parent)
        self._dataframe = dataframe.copy() if dataframe is not None else DataFrame()

    def set_dataframe(self, dataframe: DataFrame) -> None:
        """Заменить данные модели новым DataFrame."""
        self.beginResetModel()
        self._dataframe = dataframe.copy()
        self.endResetModel()

    def clear(self) -> None:
        """Очистить данные модели."""
        self.beginResetModel()
        self._dataframe = DataFrame()
        self.endResetModel()

    def rowCount(self, parent: IndexType = QModelIndex()) -> int:  # noqa: B008, N802
        if parent.isValid():
            return 0
        return len(self._dataframe.index)

    def columnCount(self, parent: IndexType = QModelIndex()) -> int:  # noqa: B008, N802
        if parent.isValid():
            return 0
        return len(self._dataframe.columns)

    def data(self, index: IndexType, role: int = Qt.ItemDataRole.DisplayRole):  # noqa: ANN001
        if not index.isValid():
            return None

        if role not in {
            Qt.ItemDataRole.DisplayRole,
            Qt.ItemDataRole.ToolTipRole,
        }:
            return None

        value = self._dataframe.iat[index.row(), index.column()]
        if value is None:
            return ""
        return str(value)

    def headerData(  # noqa: N802
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ):  # noqa: ANN001
        if role != Qt.ItemDataRole.DisplayRole:
            return None

        if orientation == Qt.Orientation.Horizontal:
            if 0 <= section < len(self._dataframe.columns):
                return str(self._dataframe.columns[section])
            return None

        if 0 <= section < len(self._dataframe.index):
            return str(self._dataframe.index[section])

        return None

    @property
    def dataframe(self) -> DataFrame:
        """Вернуть защитную копию хранящегося DataFrame."""
        return self._dataframe.copy()
