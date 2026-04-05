"""Страница конфигурации модели дерева решений."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from dt_analytics.presentation.widgets import ValidationMessagesWidget


class ModelConfigPage(QWidget):
    """UI‑страница настройки гиперпараметров дерева решений."""

    config_changed = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self._algorithm_label = QLabel("decision_tree_classifier", self)

        self._criterion_combo = QComboBox(self)
        self._criterion_combo.addItem("Gini", "gini")
        self._criterion_combo.addItem("Entropy", "entropy")
        self._criterion_combo.addItem("Log loss", "log_loss")

        self._splitter_combo = QComboBox(self)
        self._splitter_combo.addItem("Лучшее разбиение", "best")
        self._splitter_combo.addItem("Случайное разбиение", "random")

        self._max_depth_spin = QSpinBox(self)
        self._max_depth_spin.setRange(0, 999)
        self._max_depth_spin.setSpecialValueText("Без ограничения")
        self._max_depth_spin.setValue(0)

        self._min_samples_split_spin = QSpinBox(self)
        self._min_samples_split_spin.setRange(2, 999)
        self._min_samples_split_spin.setValue(2)

        self._min_samples_leaf_spin = QSpinBox(self)
        self._min_samples_leaf_spin.setRange(1, 999)
        self._min_samples_leaf_spin.setValue(1)

        self._max_features_edit = QLineEdit(self)
        self._max_features_edit.setPlaceholderText("Опционально, например sqrt")

        self._class_weight_combo = QComboBox(self)
        self._class_weight_combo.addItem("None", None)
        self._class_weight_combo.addItem("Balanced", "balanced")

        self._random_state_spin = QSpinBox(self)
        self._random_state_spin.setRange(0, 999999)
        self._random_state_spin.setValue(42)

        self._validation_widget = ValidationMessagesWidget(self)

        self._build_ui()
        self._wire_events()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        group = QGroupBox("Модель дерева решений", self)
        form = QFormLayout(group)
        form.addRow("Алгоритм:", self._algorithm_label)
        form.addRow("Критерий:", self._criterion_combo)
        form.addRow("Способ разбиения:", self._splitter_combo)
        form.addRow("Макс. глубина:", self._max_depth_spin)
        form.addRow("Мин. объектов для разбиения:", self._min_samples_split_spin)
        form.addRow("Мин. объектов в листе:", self._min_samples_leaf_spin)
        form.addRow("Макс. признаков:", self._max_features_edit)
        form.addRow("Вес классов:", self._class_weight_combo)
        form.addRow("Random state:", self._random_state_spin)

        layout.addWidget(group)
        layout.addWidget(self._validation_widget)
        layout.addStretch(1)

        self._validation_widget.clear_messages()

    def _wire_events(self) -> None:
        self._criterion_combo.currentIndexChanged.connect(self._emit_config_changed)
        self._splitter_combo.currentIndexChanged.connect(self._emit_config_changed)
        self._max_depth_spin.valueChanged.connect(self._emit_config_changed)
        self._min_samples_split_spin.valueChanged.connect(self._emit_config_changed)
        self._min_samples_leaf_spin.valueChanged.connect(self._emit_config_changed)
        self._max_features_edit.textChanged.connect(self._emit_config_changed)
        self._class_weight_combo.currentIndexChanged.connect(self._emit_config_changed)
        self._random_state_spin.valueChanged.connect(self._emit_config_changed)

    def get_algorithm_code(self) -> str:
        return "decision_tree_classifier"

    def get_task_type(self) -> str:
        return "classification"

    def get_criterion(self) -> str:
        return str(self._criterion_combo.currentData())

    def get_splitter(self) -> str:
        return str(self._splitter_combo.currentData())

    def get_max_depth(self) -> int | None:
        value = int(self._max_depth_spin.value())
        return None if value == 0 else value

    def get_min_samples_split(self) -> int:
        return int(self._min_samples_split_spin.value())

    def get_min_samples_leaf(self) -> int:
        return int(self._min_samples_leaf_spin.value())

    def get_max_features(self) -> str | None:
        value = self._max_features_edit.text().strip()
        return value or None

    def get_class_weight(self) -> str | None:
        return self._class_weight_combo.currentData()

    def get_random_state(self) -> int:
        return int(self._random_state_spin.value())

    def validate_configuration(self) -> tuple[list[str], list[str]]:
        """Проверить состояние формы настроек модели."""
        errors: list[str] = []
        warnings: list[str] = []

        if self.get_min_samples_split() < 2:
            errors.append("min_samples_split должно быть не меньше 2.")

        if self.get_min_samples_leaf() < 1:
            errors.append("min_samples_leaf должно быть не меньше 1.")

        max_depth = self.get_max_depth()
        if max_depth is not None and max_depth <= 0:
            errors.append("max_depth должно быть положительным или неограниченным.")

        if max_depth is not None and max_depth <= 2:
            warnings.append("Слишком малая глубина дерева может привести к недообучению.")

        return errors, warnings

    def show_validation(self, errors: list[str], warnings: list[str]) -> None:
        self._validation_widget.set_messages(errors=errors, warnings=warnings)

    def clear_content(self) -> None:
        """Сбросить форму до значений по умолчанию."""
        self._criterion_combo.setCurrentIndex(0)
        self._splitter_combo.setCurrentIndex(0)
        self._max_depth_spin.setValue(0)
        self._min_samples_split_spin.setValue(2)
        self._min_samples_leaf_spin.setValue(1)
        self._max_features_edit.clear()
        self._class_weight_combo.setCurrentIndex(0)
        self._random_state_spin.setValue(42)
        self._validation_widget.clear_messages()

    def _emit_config_changed(self) -> None:
        errors, warnings = self.validate_configuration()
        self.show_validation(errors, warnings)
        self.config_changed.emit()
