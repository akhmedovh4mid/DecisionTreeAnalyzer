"""Фабрика sklearn‑моделей деревьев решений."""

from __future__ import annotations

from sklearn.tree import DecisionTreeClassifier

from dt_analytics.domain import ModelConfig, TaskType
from dt_analytics.shared import Result


class DecisionTreeClassifierFactory:
    """
    Строит экземпляр sklearn.DecisionTreeClassifier из доменной конфигурации модели.
    """

    SUPPORTED_CRITERIA = {"gini", "entropy", "log_loss"}
    SUPPORTED_SPLITTERS = {"best", "random"}

    def create(self, model_config: ModelConfig) -> Result[DecisionTreeClassifier]:
        """
        Создать экземпляр classificatorа из доменной конфигурации.
        """
        if model_config.task_type is not TaskType.CLASSIFICATION:
            return Result.fail(
                code="unsupported_task_type",
                message=(
                    "DecisionTreeClassifierFactory поддерживает только задачу 'CLASSIFICATION'."
                ),
                details=model_config.task_type.value,
            )

        if model_config.algorithm_code != "decision_tree_classifier":
            return Result.fail(
                code="unsupported_algorithm_code",
                message="Неподдерживаемый код алгоритма для DecisionTreeClassifierFactory.",
                details=model_config.algorithm_code,
            )

        if model_config.criterion not in self.SUPPORTED_CRITERIA:
            return Result.fail(
                code="unsupported_criterion",
                message="Неподдерживаемый критерий для дерева решений.",
                details=model_config.criterion,
            )

        if model_config.splitter not in self.SUPPORTED_SPLITTERS:
            return Result.fail(
                code="unsupported_splitter",
                message="Неподдерживаемый сплиттер для дерева решений.",
                details=model_config.splitter,
            )

        try:
            model = DecisionTreeClassifier(
                criterion=model_config.criterion,
                max_depth=model_config.max_depth,
                min_samples_split=model_config.min_samples_split,
                min_samples_leaf=model_config.min_samples_leaf,
                max_features=model_config.max_features,
                splitter=model_config.splitter,
                class_weight=model_config.class_weight,
                random_state=model_config.random_state,
                **model_config.additional_params,  # pyright: ignore[reportArgumentType]
            )
        except (TypeError, ValueError) as exc:
            return Result.fail(
                code="model_factory_failed",
                message="Не удалось создать экземпляр DecisionTreeClassifier.",
                details=str(exc),
            )

        return Result.ok(model)
