from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd
from sklearn.tree import DecisionTreeClassifier

from src.domain.decision_tree_model import DecisionTreeModel
from src.domain.processed_dataset import ProcessedDataset


class DecisionTreeBuildingError(Exception):
    """Базовая ошибка модуля построения дерева решений."""


class EmptyTrainingDataError(DecisionTreeBuildingError):
    """Ошибка: обучающая выборка отсутствует или пуста."""


class InvalidDecisionTreeParameterError(DecisionTreeBuildingError):
    """Ошибка: переданы некорректные параметры дерева решений."""


class UnsupportedTargetError(DecisionTreeBuildingError):
    """Ошибка: целевая переменная непригодна для построения дерева классификации."""


@dataclass(slots=True)
class _DecisionTreeState:
    feature_names: list[str]
    target_column: str
    class_names: list[str]
    parameters: dict[str, Any]


class DecisionTreeBuilder:
    """
    Минимальный, но полноценный сервис построения дерева решений.

    Текущая реализация:
    - решает задачу классификации;
    - принимает ProcessedDataset;
    - обучает DecisionTreeClassifier;
    - возвращает доменную сущность DecisionTreeModel.

    Архитектурно класс готов к расширению:
    позже можно будет добавить поддержку регрессии или разных стратегий обучения
    без изменения контракта build(...).
    """

    _SUPPORTED_CRITERIA: tuple[str, ...] = ("gini", "entropy", "log_loss")

    def __init__(
        self,
        *,
        criterion: str = "gini",
        max_depth: int | None = None,
        min_samples_split: int = 2,
        min_samples_leaf: int = 1,
        random_state: int = 42,
    ) -> None:
        self._criterion = criterion
        self._max_depth = max_depth
        self._min_samples_split = min_samples_split
        self._min_samples_leaf = min_samples_leaf
        self._random_state = random_state
        self._state: _DecisionTreeState | None = None

        self._validate_init_params()

    @property
    def is_fitted(self) -> bool:
        return self._state is not None

    def build(self, dataset: ProcessedDataset) -> DecisionTreeModel:
        """
        Обучает дерево решений на подготовленных данных и возвращает модель.
        """
        self._validate_processed_dataset(dataset)

        x_train = dataset.x_train.copy()
        y_train = dataset.y_train.copy()

        self._validate_training_data(x_train, y_train)

        classifier = DecisionTreeClassifier(
            criterion=self._criterion,
            max_depth=self._max_depth,
            min_samples_split=self._min_samples_split,
            min_samples_leaf=self._min_samples_leaf,
            random_state=self._random_state,
        )

        try:
            classifier.fit(x_train, y_train)
        except Exception as exc:
            raise DecisionTreeBuildingError(
                f"Ошибка при обучении дерева решений: {exc}"
            ) from exc

        class_names = [str(class_name) for class_name in classifier.classes_]
        parameters = self.get_params()

        self._state = _DecisionTreeState(
            feature_names=list(dataset.feature_names),
            target_column=dataset.target_column,
            class_names=class_names,
            parameters=parameters,
        )

        metadata = {
            "source_dataset_name": dataset.source_dataset_name,
            "target_column": dataset.target_column,
            "train_size": int(len(x_train)),
            "test_size": int(len(dataset.x_test)),
            "feature_count": int(len(dataset.feature_names)),
            "class_count": int(y_train.nunique(dropna=True)),
            "node_count": int(classifier.tree_.node_count),
            "depth": int(classifier.get_depth()),
            "leaf_count": int(classifier.get_n_leaves()),
        }

        return DecisionTreeModel(
            model=classifier,
            target_column=dataset.target_column,
            feature_names=list(dataset.feature_names),
            class_names=class_names,
            parameters=parameters,
            metadata=metadata,
        )

    def get_params(self) -> dict[str, Any]:
        return {
            "criterion": self._criterion,
            "max_depth": self._max_depth,
            "min_samples_split": self._min_samples_split,
            "min_samples_leaf": self._min_samples_leaf,
            "random_state": self._random_state,
        }

    def _validate_init_params(self) -> None:
        if self._criterion not in self._SUPPORTED_CRITERIA:
            supported = ", ".join(self._SUPPORTED_CRITERIA)
            raise InvalidDecisionTreeParameterError(
                f"Неподдерживаемый criterion: '{self._criterion}'. "
                f"Поддерживаемые значения: {supported}"
            )

        if self._max_depth is not None and self._max_depth <= 0:
            raise InvalidDecisionTreeParameterError(
                "Параметр max_depth должен быть > 0 или None."
            )

        if self._min_samples_split < 2:
            raise InvalidDecisionTreeParameterError(
                "Параметр min_samples_split должен быть >= 2."
            )

        if self._min_samples_leaf < 1:
            raise InvalidDecisionTreeParameterError(
                "Параметр min_samples_leaf должен быть >= 1."
            )

    @staticmethod
    def _validate_processed_dataset(dataset: ProcessedDataset) -> None:
        if dataset.is_empty:
            raise EmptyTrainingDataError(
                "Невозможно построить дерево решений: ProcessedDataset пуст."
            )

        if dataset.x_train.empty or dataset.y_train.empty:
            raise EmptyTrainingDataError(
                "Невозможно построить дерево решений: обучающая выборка пуста."
            )

        if len(dataset.x_train) != len(dataset.y_train):
            raise DecisionTreeBuildingError("Размеры x_train и y_train не совпадают.")

        if not dataset.feature_names:
            raise DecisionTreeBuildingError(
                "Невозможно построить дерево решений: список признаков пуст."
            )

    @staticmethod
    def _validate_training_data(x_train: pd.DataFrame, y_train: pd.Series) -> None:
        if x_train.shape[1] == 0:
            raise EmptyTrainingDataError(
                "Невозможно построить дерево решений: отсутствуют признаки для обучения."
            )

        if y_train.nunique(dropna=True) < 2:
            raise UnsupportedTargetError(
                "Для классификации требуется как минимум 2 различных класса целевой переменной."
            )

        if y_train.isna().any():
            raise UnsupportedTargetError(
                "Целевая переменная содержит пропуски после предобработки."
            )

        non_numeric_columns = [
            str(column)
            for column in x_train.columns
            if not pd.api.types.is_numeric_dtype(x_train[column])
        ]
        if non_numeric_columns:
            raise DecisionTreeBuildingError(
                "После предобработки все признаки должны быть числовыми. "
                f"Некорректные столбцы: {non_numeric_columns}"
            )
