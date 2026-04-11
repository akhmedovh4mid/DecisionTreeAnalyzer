from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from src.core.analysis import DataAnalyzer
from src.core.data_loading import DataLoader
from src.core.decision_tree import DecisionTreeBuilder
from src.core.evaluation import QualityEvaluator
from src.core.prediction import Predictor
from src.core.preprocessing import DataPreprocessor
from src.domain.dataset import Dataset
from src.domain.dataset_info import DatasetInfo
from src.domain.decision_tree_model import DecisionTreeModel
from src.domain.evaluation_metrics import EvaluationMetrics
from src.domain.prediction_result import PredictionResult
from src.domain.processed_dataset import ProcessedDataset


class ScenarioControllerError(Exception):
    """Базовая ошибка модуля управления сценарием работы."""

    pass


class PipelineNotExecutedError(ScenarioControllerError):
    """Ошибка: попытка получить результат до выполнения pipeline."""

    pass


PredictionScope = Literal["train", "test", "full"]
EvaluationAverage = Literal["binary", "macro", "micro", "weighted"]


@dataclass(slots=True)
class ControllerPipelineConfig:
    """
    Конфигурация запуска pipeline.

    Attributes:
        target_column: Имя целевого столбца.
        prediction_scope: На какой выборке выполнять прогнозирование.
        evaluation_average: Стратегия усреднения для метрик качества.
        zero_division: Значение для sklearn-метрик при делении на ноль.
    """

    target_column: str
    prediction_scope: PredictionScope = "test"
    evaluation_average: EvaluationAverage = "weighted"
    zero_division: int = 0


@dataclass(slots=True)
class ControllerPipelineResult:
    """
    Полный результат выполнения сценария анализа данных.

    Хранит артефакты всех уже реализованных этапов:
    - загрузка данных
    - предобработка
    - обучение дерева решений
    - прогнозирование
    - оценка качества

    Этот объект можно напрямую использовать в UI-слое.
    """

    dataset: Dataset
    dataset_info: DatasetInfo
    processed_dataset: ProcessedDataset
    model: DecisionTreeModel
    prediction_result: PredictionResult
    evaluation_metrics: EvaluationMetrics

    @property
    def source_dataset_name(self) -> str:
        return self.dataset.name

    @property
    def target_column(self) -> str:
        return self.processed_dataset.target_column

    @property
    def train_size(self) -> int:
        return self.processed_dataset.train_size

    @property
    def test_size(self) -> int:
        return self.processed_dataset.test_size

    @property
    def feature_count(self) -> int:
        return self.processed_dataset.feature_count

    @property
    def class_count(self) -> int:
        return self.processed_dataset.class_count


class ApplicationController:
    """
    Координатор сценария работы системы анализа данных.

    Назначение:
    - связывает между собой функциональные модули ядра;
    - управляет последовательностью этапов pipeline;
    - предоставляет единый API для UI-слоя;
    - хранит последний успешный результат выполнения сценария.

    Текущий pipeline:
        load -> preprocess -> build tree -> predict -> evaluate

    Архитектурно контроллер:
    - не содержит ML-логики;
    - не содержит логики чтения файлов;
    - не зависит от Qt;
    - пригоден как для Desktop UI, так и для CLI / API.

    Это позволяет встроить его в проект уже сейчас и не переделывать позже.
    """

    def __init__(
        self,
        *,
        data_loader=None,
        preprocessor=None,
        analyzer=None,
        tree_builder=None,
        predictor=None,
        evaluator=None,
    ):
        self._data_loader = data_loader or DataLoader()
        self._preprocessor = preprocessor or DataPreprocessor()
        self._analyzer = analyzer or DataAnalyzer()
        self._tree_builder = tree_builder or DecisionTreeBuilder()
        self._predictor = predictor or Predictor()
        self._evaluator = evaluator or QualityEvaluator()

        self._last_result: ControllerPipelineResult | None = None
        self._last_config: ControllerPipelineConfig | None = None

    @property
    def last_result(self) -> ControllerPipelineResult:
        """
        Возвращает последний успешный результат pipeline.

        Raises:
            PipelineNotExecutedError: если pipeline ещё ни разу не выполнялся.
        """
        if self._last_result is None:
            raise PipelineNotExecutedError(
                "Pipeline ещё не выполнялся. Сначала вызови run_pipeline(...)."
            )
        return self._last_result

    @property
    def last_config(self) -> ControllerPipelineConfig:
        """
        Возвращает конфигурацию последнего успешного запуска pipeline.

        Raises:
            PipelineNotExecutedError: если pipeline ещё ни разу не выполнялся.
        """
        if self._last_config is None:
            raise PipelineNotExecutedError(
                "Конфигурация отсутствует: pipeline ещё не выполнялся."
            )
        return self._last_config

    @property
    def has_result(self) -> bool:
        """Показывает, был ли успешно выполнен pipeline хотя бы один раз."""
        return self._last_result is not None

    def reset(self) -> None:
        """
        Сбрасывает сохранённое состояние контроллера.

        Полезно:
        - при повторной загрузке нового файла;
        - перед новой пользовательской сессией;
        - в тестах.
        """
        self._last_result = None
        self._last_config = None

    def run_pipeline(
        self,
        file_path: str | Path,
        target_column: str,
        *,
        prediction_scope: PredictionScope = "test",
        evaluation_average: EvaluationAverage = "weighted",
        zero_division: int = 0,
    ) -> ControllerPipelineResult:
        """
        Выполняет полный сценарий работы системы.

        Этапы:
            1. Загрузка данных
            2. Предварительная обработка
            3. Построение дерева решений
            4. Прогнозирование
            5. Оценка качества

        Args:
            file_path: Путь к исходному файлу данных.
            target_column: Имя целевого столбца.
            prediction_scope: train / test / full.
            evaluation_average: Стратегия усреднения метрик.
            zero_division: Поведение метрик при делении на ноль.

        Returns:
            ControllerPipelineResult: полный набор артефактов pipeline.

        Raises:
            ScenarioControllerError:
                если произошла ошибка на любом этапе сценария.
        """
        config = ControllerPipelineConfig(
            target_column=target_column,
            prediction_scope=prediction_scope,
            evaluation_average=evaluation_average,
            zero_division=zero_division,
        )

        try:
            dataset = self.load_dataset(file_path)
            dataset_info = self.analyze_dataset(dataset, config.target_column)
            processed_dataset = self.preprocess_dataset(dataset, config.target_column)
            model = self.build_model(processed_dataset)
            prediction_result = self.make_prediction(
                model=model,
                processed_dataset=processed_dataset,
                scope=config.prediction_scope,
            )
            evaluation_metrics = self.evaluate_prediction(
                prediction_result=prediction_result,
                average=config.evaluation_average,
                zero_division=config.zero_division,
            )
        except Exception as exc:
            raise ScenarioControllerError(
                f"Ошибка выполнения сценария анализа данных: {exc}"
            ) from exc

        result = ControllerPipelineResult(
            dataset=dataset,
            dataset_info=dataset_info,
            processed_dataset=processed_dataset,
            model=model,
            prediction_result=prediction_result,
            evaluation_metrics=evaluation_metrics,
        )
        self._last_result = result
        self._last_config = config
        return result

    def load_dataset(self, file_path: str | Path) -> Dataset:
        """
        Выполняет только этап загрузки данных.

        Полезно для:
        - UI-сценариев с пошаговой обработкой;
        - предварительного просмотра файла;
        - будущего подключения модуля анализа данных.
        """
        try:
            return self._data_loader.load(file_path)
        except Exception as exc:
            raise ScenarioControllerError(
                f"Ошибка на этапе загрузки данных: {exc}"
            ) from exc

    def analyze_dataset(self, dataset: Dataset, target_column: str) -> DatasetInfo:
        try:
            return self._analyzer.analyze(dataset, target_column)
        except Exception as exc:
            raise ScenarioControllerError(
                f"Ошибка на этапе анализа данных: {exc}"
            ) from exc

    def preprocess_dataset(
        self, dataset: Dataset, target_column: str
    ) -> ProcessedDataset:
        """
        Выполняет только этап предварительной обработки данных.
        """
        try:
            return self._preprocessor.preprocess(dataset, target_column)
        except Exception as exc:
            raise ScenarioControllerError(
                f"Ошибка на этапе предобработки данных: {exc}"
            ) from exc

    def build_model(self, processed_dataset: ProcessedDataset) -> DecisionTreeModel:
        """
        Выполняет только этап обучения дерева решений.
        """
        try:
            return self._tree_builder.build(processed_dataset)
        except Exception as exc:
            raise ScenarioControllerError(
                f"Ошибка на этапе построения дерева решений: {exc}"
            ) from exc

    def make_prediction(
        self,
        *,
        model: DecisionTreeModel,
        processed_dataset: ProcessedDataset,
        scope: PredictionScope = "test",
    ) -> PredictionResult:
        """
        Выполняет только этап прогнозирования.
        """
        try:
            return self._predictor.predict(model, processed_dataset, on=scope)
        except Exception as exc:
            raise ScenarioControllerError(
                f"Ошибка на этапе прогнозирования: {exc}"
            ) from exc

    def evaluate_prediction(
        self,
        *,
        prediction_result: PredictionResult,
        average: EvaluationAverage = "weighted",
        zero_division: int = 0,
    ) -> EvaluationMetrics:
        """
        Выполняет только этап оценки качества.
        """
        try:
            return self._evaluator.evaluate(
                prediction_result,
                average=average,
                zero_division=zero_division,
            )
        except Exception as exc:
            raise ScenarioControllerError(
                f"Ошибка на этапе оценки качества: {exc}"
            ) from exc

    def get_metrics_summary(self) -> dict[str, float]:
        return self.last_result.evaluation_metrics.score_summary

    def get_model_summary(self) -> dict[str, int | str]:
        """
        Возвращает краткую сводку по обученной модели.

        Удобно для:
        - карточки модели в UI;
        - текстового отчёта;
        - логирования.
        """
        result = self.last_result
        model = result.model

        return {
            "dataset_name": result.source_dataset_name,
            "target_column": result.target_column,
            "feature_count": result.feature_count,
            "class_count": result.class_count,
            "train_size": result.train_size,
            "test_size": result.test_size,
            "node_count": model.node_count,
            "depth": model.depth,
            "leaf_count": model.leaf_count,
        }

    def get_feature_importances(self) -> dict[str, float]:
        """
        Возвращает важности признаков последней обученной модели.
        """
        return self.last_result.model.feature_importances

    def get_dataset_summary(self) -> dict[str, int | str]:
        return self.last_result.dataset_info.summary
