from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction, QPixmap, QWheelEvent
from PySide6.QtWidgets import (
    QFrame,
    QGroupBox,
    QLabel,
    QPlainTextEdit,
    QScrollArea,
    QSizePolicy,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from src.domain.visualization_data import VisualizationData


class _ZoomableImageLabel(QLabel):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.setScaledContents(False)
        self.setText("Изображение дерева пока недоступно")

    def has_image(self) -> bool:
        pixmap = self.pixmap()
        return pixmap is not None and not pixmap.isNull()


class _ImageViewer(QFrame):
    _MIN_SCALE = 0.1
    _MAX_SCALE = 6.0
    _SCALE_STEP = 1.15

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._original_pixmap: QPixmap | None = None
        self._scale_factor = 1.0
        self._fit_to_window = True

        self._image_label = _ZoomableImageLabel(self)

        self._scroll_area = QScrollArea(self)
        self._scroll_area.setWidget(self._image_label)
        self._scroll_area.setWidgetResizable(False)
        self._scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        self._toolbar = QToolBar(self)
        self._toolbar.setMovable(False)

        self._zoom_in_action = QAction("Увеличить", self)
        self._zoom_out_action = QAction("Уменьшить", self)
        self._reset_zoom_action = QAction("100%", self)
        self._fit_action = QAction("Уместить", self)
        self._fit_action.setCheckable(True)
        self._fit_action.setChecked(True)

        self._zoom_in_action.triggered.connect(self.zoom_in)
        self._zoom_out_action.triggered.connect(self.zoom_out)
        self._reset_zoom_action.triggered.connect(self.reset_zoom)
        self._fit_action.triggered.connect(self.toggle_fit_to_window)

        self._toolbar.addAction(self._zoom_in_action)
        self._toolbar.addAction(self._zoom_out_action)
        self._toolbar.addAction(self._reset_zoom_action)
        self._toolbar.addAction(self._fit_action)

        layout = QVBoxLayout()
        layout.addWidget(self._toolbar)
        layout.addWidget(self._scroll_area)
        self.setLayout(layout)

        self._update_actions()

    def clear(self) -> None:
        self._original_pixmap = None
        self._scale_factor = 1.0
        self._fit_to_window = True
        self._fit_action.setChecked(True)
        self._image_label.clear()
        self._image_label.setText("Изображение дерева пока недоступно")
        self._image_label.adjustSize()
        self._update_actions()

    def set_message(self, text: str) -> None:
        self._original_pixmap = None
        self._scale_factor = 1.0
        self._image_label.setPixmap(QPixmap())
        self._image_label.setText(text)
        self._image_label.adjustSize()
        self._update_actions()

    def set_image(self, pixmap: QPixmap) -> None:
        if pixmap.isNull():
            self.set_message("Не удалось загрузить изображение дерева")
            return

        self._original_pixmap = pixmap
        self._image_label.setText("")
        self._scale_factor = 1.0
        self._apply_current_view()
        self._update_actions()

    def zoom_in(self) -> None:
        if not self._has_pixmap():
            return
        if self._fit_to_window:
            self._fit_to_window = False
            self._fit_action.setChecked(False)
        self._set_scale(self._scale_factor * self._SCALE_STEP)

    def zoom_out(self) -> None:
        if not self._has_pixmap():
            return
        if self._fit_to_window:
            self._fit_to_window = False
            self._fit_action.setChecked(False)
        self._set_scale(self._scale_factor / self._SCALE_STEP)

    def reset_zoom(self) -> None:
        if not self._has_pixmap():
            return
        self._fit_to_window = False
        self._fit_action.setChecked(False)
        self._set_scale(1.0)

    def toggle_fit_to_window(self) -> None:
        self._fit_to_window = self._fit_action.isChecked()
        self._apply_current_view()
        self._update_actions()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self._fit_to_window and self._has_pixmap():
            self._apply_current_view()

    def wheelEvent(self, event: QWheelEvent) -> None:
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            angle = event.angleDelta().y()
            if angle > 0:
                self.zoom_in()
            elif angle < 0:
                self.zoom_out()
            event.accept()
            return
        super().wheelEvent(event)

    def _set_scale(self, scale: float) -> None:
        bounded = max(self._MIN_SCALE, min(self._MAX_SCALE, scale))
        self._scale_factor = bounded
        self._apply_current_view()
        self._update_actions()

    def _apply_current_view(self) -> None:
        if not self._has_pixmap():
            return

        assert self._original_pixmap is not None

        if self._fit_to_window:
            viewport_size = self._scroll_area.viewport().size()
            if viewport_size.width() <= 1 or viewport_size.height() <= 1:
                return

            scaled = self._original_pixmap.scaled(
                viewport_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._image_label.setPixmap(scaled)
            self._image_label.resize(scaled.size())
            return

        original_size = self._original_pixmap.size()
        target_size = QSize(
            max(1, int(original_size.width() * self._scale_factor)),
            max(1, int(original_size.height() * self._scale_factor)),
        )
        scaled = self._original_pixmap.scaled(
            target_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._image_label.setPixmap(scaled)
        self._image_label.resize(scaled.size())

    def _has_pixmap(self) -> bool:
        return self._original_pixmap is not None and not self._original_pixmap.isNull()

    def _update_actions(self) -> None:
        has_image = self._has_pixmap()
        self._zoom_in_action.setEnabled(has_image)
        self._zoom_out_action.setEnabled(has_image)
        self._reset_zoom_action.setEnabled(has_image)
        self._fit_action.setEnabled(has_image)
        self._reset_zoom_action.setText(
            "100%" if not has_image else f"{int(self._scale_factor * 100)}%"
        )


class TreeView(QGroupBox):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Визуализация дерева решений", parent)

        self._image_viewer = _ImageViewer(self)

        self._text = QPlainTextEdit(self)
        self._text.setReadOnly(True)

        layout = QVBoxLayout()
        layout.addWidget(self._image_viewer, stretch=3)
        layout.addWidget(self._text, stretch=2)
        self.setLayout(layout)

    def clear(self) -> None:
        self._image_viewer.clear()
        self._text.clear()

    def show_visualization(self, data: VisualizationData) -> None:
        self._render_image(data.tree_image_path)
        self._text.setPlainText(self._build_text_block(data))

    def _render_image(self, image_path: str | None) -> None:
        if not image_path:
            self._image_viewer.set_message("PNG-визуализация дерева не была создана")
            return

        path = Path(image_path)
        if not path.exists():
            self._image_viewer.set_message(f"Файл визуализации не найден: {image_path}")
            return

        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            self._image_viewer.set_message("Не удалось загрузить изображение дерева")
            return

        self._image_viewer.set_image(pixmap)

    @staticmethod
    def _build_text_block(data: VisualizationData) -> str:
        model_lines = [
            "Сводка по модели:",
            *[f"- {key}: {value}" for key, value in data.model_summary.items()],
            "",
            "Сводка по метрикам:",
            *[f"- {key}: {value}" for key, value in data.metrics_summary.items()],
            "",
            "Наиболее важные признаки:",
        ]

        feature_lines = [
            f"- {feature}: {importance:.4f}"
            for feature, importance in data.top_features
        ]
        if not feature_lines:
            feature_lines = ["- Нет данных о важности признаков"]

        tree_lines = [
            "",
            "Текстовое представление дерева:",
            data.tree_text,
        ]

        return "\n".join([*model_lines, *feature_lines, *tree_lines])
