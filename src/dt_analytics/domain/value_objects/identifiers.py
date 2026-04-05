"""Доменные идентификаторы‑объекты значений."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class ProjectId:
    """Сильно типизированный идентификатор проекта."""

    value: str

    @classmethod
    def new(cls) -> ProjectId:
        return cls(value=str(uuid4()))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class DatasetId:
    """Сильно типизированный идентификатор набора данных."""

    value: str

    @classmethod
    def new(cls) -> DatasetId:
        return cls(value=str(uuid4()))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class FeatureId:
    """Сильно типизированный идентификатор определения признака."""

    value: str

    @classmethod
    def new(cls) -> FeatureId:
        return cls(value=str(uuid4()))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class ProfileId:
    """Сильно типизированный идентификатор профиля набора данных."""

    value: str

    @classmethod
    def new(cls) -> ProfileId:
        return cls(value=str(uuid4()))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class PreprocessingConfigId:
    """Сильно типизированный идентификатор конфигурации предобработки."""

    value: str

    @classmethod
    def new(cls) -> PreprocessingConfigId:
        return cls(value=str(uuid4()))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class ModelConfigId:
    """Сильно типизированный идентификатор конфигурации модели."""

    value: str

    @classmethod
    def new(cls) -> ModelConfigId:
        return cls(value=str(uuid4()))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class ExperimentId:
    """Сильно типизированный идентификатор эксперимента."""

    value: str

    @classmethod
    def new(cls) -> ExperimentId:
        return cls(value=str(uuid4()))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class TrainingResultId:
    """Сильно типизированный идентификатор результата обучения."""

    value: str

    @classmethod
    def new(cls) -> TrainingResultId:
        return cls(value=str(uuid4()))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class EvaluationResultId:
    """Сильно типизированный идентификатор результата оценки."""

    value: str

    @classmethod
    def new(cls) -> EvaluationResultId:
        return cls(value=str(uuid4()))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class ArtifactId:
    """Сильно типизированный идентификатор артефакта."""

    value: str

    @classmethod
    def new(cls) -> ArtifactId:
        return cls(value=str(uuid4()))

    def __str__(self) -> str:
        return self.value
