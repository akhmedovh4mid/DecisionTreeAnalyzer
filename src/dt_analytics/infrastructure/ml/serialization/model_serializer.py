"""Вспомогательные утилиты сериализации обученных ML‑моделей."""

from __future__ import annotations

from pathlib import Path

import joblib
from sklearn.pipeline import Pipeline

from dt_analytics.shared import Result


class ModelSerializer:
    """Сохранение и восстановление обученных sklearn‑pipeline."""

    def save(self, pipeline: Pipeline, file_path: Path) -> Result[Path]:
        """Сериализовать конвейер на диск."""
        try:
            destination = file_path.expanduser().resolve()
            destination.parent.mkdir(parents=True, exist_ok=True)
            joblib.dump(pipeline, destination)
        except Exception as exc:  # noqa: BLE001
            return Result.fail(
                code="model_serialize_failed",
                message="Не удалось сериализовать обученную модель.",
                details=str(exc),
            )

        return Result.ok(destination)

    def load(self, file_path: Path) -> Result[Pipeline]:
        """Загрузить сериализованный конвейер с диска."""
        try:
            source = file_path.expanduser().resolve()
            pipeline = joblib.load(source)
        except Exception as exc:  # noqa: BLE001
            return Result.fail(
                code="model_deserialize_failed",
                message="Не удалось десериализовать обученную модель.",
                details=str(exc),
            )

        return Result.ok(pipeline)
