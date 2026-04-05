"""Вспомогательные утилиты оркестрации обучения sklearn‑моделей."""

from __future__ import annotations

from dataclasses import dataclass

from pandas import DataFrame, Series
from sklearn.base import ClassifierMixin
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from dt_analytics.domain import PreprocessingConfig
from dt_analytics.shared import Result


@dataclass(frozen=True, slots=True)
class TrainingArtifacts:
    """Артефакты, создаваемые тренировочным помощником до оценки."""

    pipeline: Pipeline
    x_train: DataFrame
    x_test: DataFrame
    y_train: Series
    y_test: Series
    train_score: float | None


class SklearnDecisionTreeTrainer:
    """Обучение sklearn‑pipeline из предобработки и модели для задачи классификации."""

    def train(
        self,
        dataframe: DataFrame,
        preprocessing_config: PreprocessingConfig,
        transformer: ColumnTransformer,
        model: ClassifierMixin,
    ) -> Result[TrainingArtifacts]:
        """Подготовить данные, разбить их, обучить pipeline и вернуть артефакты обучения."""
        try:
            working_frame = dataframe.copy()
        except Exception as exc:  # noqa: BLE001
            return Result.fail(
                code="training_dataframe_copy_failed",
                message="Не удалось создать рабочую копию фрейма данных.",
                details=str(exc),
            )

        if preprocessing_config.drop_duplicates:
            working_frame = working_frame.drop_duplicates()

        if preprocessing_config.missing_strategy.value == "drop_rows":
            involved_columns = [
                preprocessing_config.target_column,
                *preprocessing_config.feature_columns,
            ]
            working_frame = working_frame.dropna(subset=involved_columns)

        if working_frame.empty:
            return Result.fail(
                code="training_dataframe_empty",
                message="Набор данных стал пустым после предобработки.",
            )

        x = working_frame.loc[:, list(preprocessing_config.feature_columns)]
        y = working_frame.loc[:, preprocessing_config.target_column]

        if y.nunique(dropna=True) < 2:
            return Result.fail(
                code="training_single_class_target",
                message=(
                    "Целевая колонка должна содержать как минимум два "
                    "класса для задачи классификации."
                ),
            )

        stratify = y if preprocessing_config.stratify_enabled else None

        try:
            x_train, x_test, y_train, y_test = train_test_split(
                x,
                y,
                test_size=preprocessing_config.test_size,
                random_state=preprocessing_config.random_state,
                stratify=stratify,
            )
        except ValueError as exc:
            return Result.fail(
                code="train_test_split_failed",
                message="Не удалось разделить данные на обучающую и тестовую выборки.",
                details=str(exc),
            )

        pipeline = Pipeline(
            steps=[
                ("preprocessing", transformer),
                ("model", model),
            ]
        )

        try:
            pipeline.fit(x_train, y_train)
            train_score = float(pipeline.score(x_train, y_train))
        except Exception as exc:  # noqa: BLE001
            return Result.fail(
                code="model_training_failed",
                message="Не удалось обучить конвейер дерева решений.",
                details=str(exc),
            )

        return Result.ok(
            TrainingArtifacts(
                pipeline=pipeline,
                x_train=x_train,
                x_test=x_test,
                y_train=y_train,
                y_test=y_test,
                train_score=train_score,
            )
        )
