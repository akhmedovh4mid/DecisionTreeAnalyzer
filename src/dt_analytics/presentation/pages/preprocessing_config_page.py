"""Страница конфигурации предобработки."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from dt_analytics.application.dto import DatasetDto
from dt_analytics.presentation.widgets import ValidationMessagesWidget


class PreprocessingConfigPage(QWidget):
    """UI‑страница выбора целевой/факторных колонок и параметров предобработки."""

    config_changed = Signal()
    create_experiment_requested = Signal()
    run_experiment_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self._dataset: DatasetDto | None = None

        self._dataset_label = QLabel("Набор данных не выбран", self)

        self._target_combo = QComboBox(self)

        self._features_list = QListWidget(self)
        self._features_list.setSelectionMode(QListWidget.SelectionMode.NoSelection)

        self._missing_strategy_combo = QComboBox(self)
        self._missing_strategy_combo.addItem("Медиана / Режим", "median_mode")
        self._missing_strategy_combo.addItem("Константа", "constant")
        self._missing_strategy_combo.addItem("Удалить строки", "drop_rows")

        self._categorical_encoding_combo = QComboBox(self)
        self._categorical_encoding_combo.addItem("One-hot", "one_hot")
        self._categorical_encoding_combo.addItem("Порядковое кодирование", "ordinal")

        self._drop_duplicates_check = QCheckBox("Удалить дублирующие строки", self)
        self._stratify_check = QCheckBox("Включить стратифицированное разбиение", self)
        self._stratify_check.setChecked(True)

        self._test_size_spin = QDoubleSpinBox(self)
        self._test_size_spin.setRange(0.05, 0.95)
        self._test_size_spin.setDecimals(2)
        self._test_size_spin.setSingleStep(0.05)
        self._test_size_spin.setValue(0.20)

        self._random_state_spin = QSpinBox(self)
        self._random_state_spin.setRange(0, 999999)
        self._random_state_spin.setValue(42)

        self._validation_widget = ValidationMessagesWidget(self)

        self._create_experiment_button = QPushButton("Создать эксперимент", self)
        self._run_experiment_button = QPushButton("Создать и запустить", self)

        self._build_ui()
        self._wire_events()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        layout.addWidget(self._dataset_label)

        selection_group = QGroupBox("Столбцы", self)
        selection_form = QFormLayout(selection_group)
        selection_form.addRow("Целевой столбец:", self._target_combo)
        selection_form.addRow("Столбцы‑признаки:", self._features_list)

        preprocessing_group = QGroupBox("Предобработка", self)
        preprocessing_form = QFormLayout(preprocessing_group)
        preprocessing_form.addRow("Стратегия для пропусков:", self._missing_strategy_combo)
        preprocessing_form.addRow(
            "Кодирование категорий:",
            self._categorical_encoding_combo,
        )
        preprocessing_form.addRow("Доля тестовой выборки:", self._test_size_spin)
        preprocessing_form.addRow("Random state:", self._random_state_spin)
        preprocessing_form.addRow("", self._drop_duplicates_check)
        preprocessing_form.addRow("", self._stratify_check)

        layout.addWidget(selection_group)
        layout.addWidget(preprocessing_group)
        layout.addWidget(self._validation_widget)
        layout.addWidget(self._create_experiment_button)
        layout.addWidget(self._run_experiment_button)
        layout.addStretch(1)

        self._validation_widget.clear_messages()

    def _wire_events(self) -> None:
        self._target_combo.currentIndexChanged.connect(self._on_config_changed)
        self._missing_strategy_combo.currentIndexChanged.connect(self._on_config_changed)
        self._categorical_encoding_combo.currentIndexChanged.connect(self._on_config_changed)
        self._drop_duplicates_check.stateChanged.connect(self._on_config_changed)
        self._stratify_check.stateChanged.connect(self._on_config_changed)
        self._test_size_spin.valueChanged.connect(self._on_config_changed)
        self._random_state_spin.valueChanged.connect(self._on_config_changed)

        self._create_experiment_button.clicked.connect(self.create_experiment_requested.emit)
        self._run_experiment_button.clicked.connect(self.run_experiment_requested.emit)

    def set_dataset(self, dataset: DatasetDto) -> None:
        """Связать выбранный набор данных с формой."""
        self._dataset = dataset
        self._dataset_label.setText(
            f"Набор данных: {dataset.name} | Строки: {dataset.row_count} | "
            "Столбцы: {dataset.column_count}"
        )

        self._target_combo.blockSignals(True)
        self._target_combo.clear()
        self._features_list.clear()

        for feature in dataset.features:
            self._target_combo.addItem(feature.name, feature.name)

        for feature in dataset.features:
            item = QListWidgetItem(feature.name)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            self._features_list.addItem(item)

        if self._target_combo.count() > 0:
            self._target_combo.setCurrentIndex(0)
            self._sync_feature_checks_with_target()

        self._target_combo.blockSignals(False)
        self._validate()

    def clear_content(self) -> None:
        """Сбросить форму."""
        self._dataset = None
        self._dataset_label.setText("Набор данных не выбран")
        self._target_combo.clear()
        self._features_list.clear()
        self._validation_widget.clear_messages()

    def get_target_column(self) -> str:
        """Вернуть выбранный целевой столбец."""
        return self._target_combo.currentData() or self._target_combo.currentText()

    def get_feature_columns(self) -> tuple[str, ...]:
        """Вернуть выбранные столбцы‑признаки (без целевого)."""
        feature_names: list[str] = []
        target = self.get_target_column()

        for row in range(self._features_list.count()):
            item = self._features_list.item(row)
            if item is None:
                continue
            if item.checkState() == Qt.CheckState.Checked and item.text() != target:
                feature_names.append(item.text())

        return tuple(feature_names)

    def get_excluded_columns(self) -> tuple[str, ...]:
        """Вернуть непомеченные столбцы (без целевого)."""
        excluded: list[str] = []
        target = self.get_target_column()

        for row in range(self._features_list.count()):
            item = self._features_list.item(row)
            if item is None:
                continue
            if item.text() != target and item.checkState() != Qt.CheckState.Checked:
                excluded.append(item.text())

        return tuple(excluded)

    def get_missing_strategy(self) -> str:
        return str(self._missing_strategy_combo.currentData())

    def get_categorical_encoding_strategy(self) -> str:
        return str(self._categorical_encoding_combo.currentData())

    def get_drop_duplicates(self) -> bool:
        return self._drop_duplicates_check.isChecked()

    def get_test_size(self) -> float:
        return float(self._test_size_spin.value())

    def get_random_state(self) -> int:
        return int(self._random_state_spin.value())

    def get_stratify_enabled(self) -> bool:
        return self._stratify_check.isChecked()

    def validate_configuration(self) -> tuple[list[str], list[str]]:
        """Проверить заполнение формы предобработки."""
        errors: list[str] = []
        warnings: list[str] = []

        if self._dataset is None:
            errors.append("Набор данных не выбран.")
            return errors, warnings

        target = self.get_target_column()
        features = self.get_feature_columns()

        if not target:
            errors.append("Не выбран целевой столбец.")

        if not features:
            errors.append("Должен быть выбран хотя бы один столбец‑признак.")

        if target and target in features:
            errors.append("Целевой столбец не должен входить в список признаков.")

        if len(features) != len(set(features)):
            errors.append("Столбцы‑признаки должны быть уникальными.")

        if self.get_test_size() <= 0.0 or self.get_test_size() >= 1.0:
            errors.append("Доля тестовой выборки должна быть в диапазоне (0; 1).")

        if len(features) == 1:
            warnings.append("Выбран только один признак.")

        return errors, warnings

    def show_validation(self, errors: list[str], warnings: list[str]) -> None:
        """Показать сообщения валидации."""
        self._validation_widget.set_messages(errors=errors, warnings=warnings)

    def _on_config_changed(self) -> None:
        self._sync_feature_checks_with_target()
        self._validate()
        self.config_changed.emit()

    def _validate(self) -> None:
        errors, warnings = self.validate_configuration()
        self.show_validation(errors, warnings)

    def _sync_feature_checks_with_target(self) -> None:
        target = self.get_target_column()

        for row in range(self._features_list.count()):
            item = self._features_list.item(row)
            if item is None:
                continue

            if item.text() == target:
                item.setCheckState(Qt.CheckState.Unchecked)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
            else:
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEnabled)
