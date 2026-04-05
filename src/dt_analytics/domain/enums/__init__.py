"""Доменные перечисления."""

from dt_analytics.domain.enums.artifact_type import ArtifactType
from dt_analytics.domain.enums.categorical_encoding_strategy import (
    CategoricalEncodingStrategy,
)
from dt_analytics.domain.enums.experiment_status import ExperimentStatus
from dt_analytics.domain.enums.feature_role import FeatureRole
from dt_analytics.domain.enums.logical_feature_type import LogicalFeatureType
from dt_analytics.domain.enums.missing_strategy import MissingStrategy
from dt_analytics.domain.enums.task_type import TaskType

__all__ = [
    "ArtifactType",
    "CategoricalEncodingStrategy",
    "ExperimentStatus",
    "FeatureRole",
    "LogicalFeatureType",
    "MissingStrategy",
    "TaskType",
]
