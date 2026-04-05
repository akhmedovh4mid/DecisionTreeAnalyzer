"""Доменные сущности."""

from dt_analytics.domain.entities.artifact_reference import ArtifactReference
from dt_analytics.domain.entities.dataset import Dataset
from dt_analytics.domain.entities.dataset_profile import DatasetProfile
from dt_analytics.domain.entities.evaluation_result import EvaluationResult
from dt_analytics.domain.entities.experiment import Experiment
from dt_analytics.domain.entities.feature_definition import FeatureDefinition
from dt_analytics.domain.entities.model_config import ModelConfig
from dt_analytics.domain.entities.preprocessing_config import PreprocessingConfig
from dt_analytics.domain.entities.project import Project
from dt_analytics.domain.entities.training_result import TrainingResult

__all__ = [
    "ArtifactReference",
    "Dataset",
    "DatasetProfile",
    "EvaluationResult",
    "Experiment",
    "FeatureDefinition",
    "ModelConfig",
    "PreprocessingConfig",
    "Project",
    "TrainingResult",
]
