"""Сущность ссылки‑артефакта."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from dt_analytics.domain.enums import ArtifactType
from dt_analytics.domain.value_objects import ArtifactId, FileReference
from dt_analytics.shared.types import JsonDict


@dataclass(slots=True)
class ArtifactReference:
    """Ссылка на артефакт, сгенерированный в ходе эксперимента."""

    id: ArtifactId
    artifact_type: ArtifactType
    file: FileReference
    metadata: JsonDict = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def create(
        cls,
        artifact_type: ArtifactType,
        file: FileReference,
        metadata: JsonDict | None = None,
    ) -> ArtifactReference:
        return cls(
            id=ArtifactId.new(),
            artifact_type=artifact_type,
            file=file,
            metadata=metadata or {},
        )
