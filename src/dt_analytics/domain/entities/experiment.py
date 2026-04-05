"""Сущность эксперимента."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from dt_analytics.domain.entities.artifact_reference import ArtifactReference
from dt_analytics.domain.entities.evaluation_result import EvaluationResult
from dt_analytics.domain.entities.model_config import ModelConfig
from dt_analytics.domain.entities.preprocessing_config import PreprocessingConfig
from dt_analytics.domain.entities.training_result import TrainingResult
from dt_analytics.domain.enums import ExperimentStatus
from dt_analytics.domain.value_objects import DatasetId, ExperimentId


@dataclass(slots=True)
class Experiment:
    """Агрегат эксперимента, представляющий одну попытку обучения."""

    id: ExperimentId
    dataset_id: DatasetId
    preprocessing_config: PreprocessingConfig
    model_config: ModelConfig
    name: str
    status: ExperimentStatus = ExperimentStatus.DRAFT
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error_message: str | None = None
    notes: str | None = None
    training_result: TrainingResult | None = None
    evaluation_result: EvaluationResult | None = None
    artifacts: list[ArtifactReference] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        dataset_id: DatasetId,
        preprocessing_config: PreprocessingConfig,
        model_config: ModelConfig,
        name: str,
        notes: str | None = None,
    ) -> Experiment:
        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError("Имя эксперимента не может быть пустым.")

        return cls(
            id=ExperimentId.new(),
            dataset_id=dataset_id,
            preprocessing_config=preprocessing_config,
            model_config=model_config,
            name=normalized_name,
            status=ExperimentStatus.CONFIGURED,
            notes=notes.strip() if notes else None,
        )

    def start(self) -> None:
        """Перевести эксперимент в состояние выполнения."""
        if self.status not in {ExperimentStatus.CONFIGURED, ExperimentStatus.DRAFT}:
            raise ValueError(f"Эксперимент нельзя запустить из статуса {self.status!s}.")

        self.status = ExperimentStatus.RUNNING
        self.started_at = datetime.now(UTC)
        self.finished_at = None
        self.error_message = None

    def mark_trained(self, training_result: TrainingResult) -> None:
        """Присоединить результат обучения и установить статус TRAINED."""
        if self.status is not ExperimentStatus.RUNNING:
            raise ValueError(
                "Эксперимент должен выполняться перед тем, как его можно пометить как обученный."
            )

        self.training_result = training_result
        self.status = ExperimentStatus.TRAINED

    def mark_evaluated(self, evaluation_result: EvaluationResult) -> None:
        """Присоединить результат оценки и установить статус EVALUATED."""
        if self.status not in {ExperimentStatus.RUNNING, ExperimentStatus.TRAINED}:
            raise ValueError("Эксперимент должен быть running или trained перед оценкой.")

        self.evaluation_result = evaluation_result
        self.status = ExperimentStatus.EVALUATED
        self.finished_at = datetime.now(UTC)

    def mark_failed(self, message: str) -> None:
        """Перевести эксперимент в статус FAILED."""
        normalized_message = message.strip()
        if not normalized_message:
            raise ValueError("Сообщение об ошибке не может быть пустым.")

        self.status = ExperimentStatus.FAILED
        self.error_message = normalized_message
        self.finished_at = datetime.now(UTC)

    def archive(self) -> None:
        """Заархивировать эксперимент."""
        if self.status is ExperimentStatus.RUNNING:
            raise ValueError("Запущенный эксперимент нельзя архивировать.")

        self.status = ExperimentStatus.ARCHIVED

    def add_artifact(self, artifact: ArtifactReference) -> None:
        """Присоединить ссылку на артефакт к эксперименту."""
        self.artifacts.append(artifact)

    @property
    def is_finished(self) -> bool:
        """Вернуть True, если эксперимент находится в финальном состоянии."""
        return self.status in {
            ExperimentStatus.EVALUATED,
            ExperimentStatus.FAILED,
            ExperimentStatus.ARCHIVED,
        }
