"""Исключения домена, связанные с машинным обучением."""

from __future__ import annotations

from dt_analytics.shared import DtAnalyticsError


class MlError(DtAnalyticsError):
    """Базовый класс для ошибок, связанных с машинным обучением."""


class MlValidationError(MlError):
    """Возникает, когда входные данные эксперимента ML некорректны."""


class DataPreparationError(MlError):
    """Возникает, когда подготовка набора данных для ML завершается с ошибкой."""


class ModelTrainingError(MlError):
    """Возникает, когда обучение модели завершается с ошибкой."""


class EvaluationError(MlError):
    """Возникает, когда оценка модели завершается с ошибкой."""


class ModelSerializationError(MlError):
    """Возникает, когда обученную модель невозможно сериализовать или сохранить."""
