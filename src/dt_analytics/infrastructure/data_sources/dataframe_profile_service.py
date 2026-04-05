"""Инфраструктура профилирования DataFrame."""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

import pandas as pd
from pandas import DataFrame
from pandas.api.types import (
    is_bool_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
)

from dt_analytics.domain.entities import DatasetProfile, FeatureDefinition
from dt_analytics.domain.enums import FeatureRole, LogicalFeatureType
from dt_analytics.domain.services import (
    DatasetProfileResult,
    DatasetProfileService,
    DatasetStructureSnapshot,
    FeatureSnapshot,
)
from dt_analytics.shared import Result
from dt_analytics.shared.types import JsonDict


@dataclass(frozen=True, slots=True)
class DataFrameAnalysisResult:
    """
    Промежуточный результат профилирования, основанный напрямую на DataFrame.

    Этот объект полезен внутри инфраструктуры перед конвертацией
    во внутренние доменные сущности.
    """

    snapshot: DatasetStructureSnapshot
    preview_summary: JsonDict


class DataFrameProfileService(DatasetProfileService):
    """
    Построение профилированных доменных объектов из экземпляров pandas DataFrame.

    Этот класс служит мостом между pandas‑инфраструктурой
    и контрактом доменного профилирования.
    """

    def analyze_dataframe(self, dataframe: DataFrame) -> Result[DataFrameAnalysisResult]:
        """
        Проанализировать DataFrame и создать структуру-снапшот, удобную для домена.
        """
        if dataframe.empty and len(dataframe.columns) == 0:
            return Result.fail(
                code="dataframe_empty",
                message="Набор данных не содержит ни столбцов, ни строк.",
            )

        try:
            row_count = len(dataframe.index)
            column_count = len(dataframe.columns)

            missing_total = int(dataframe.isna().sum().sum())
            duplicate_count = int(dataframe.duplicated().sum()) if row_count > 0 else 0
            memory_usage_bytes = int(dataframe.memory_usage(deep=True).sum())

            feature_snapshots: list[FeatureSnapshot] = []
            for ordinal_position, column_name in enumerate(dataframe.columns):
                series = dataframe[column_name]
                feature_snapshots.append(
                    FeatureSnapshot(
                        name=str(column_name),
                        physical_dtype=str(series.dtype),
                        logical_type=self._infer_logical_type(series),  # pyright: ignore[reportArgumentType]
                        nullable=bool(series.isna().any()),
                        missing_count=int(series.isna().sum()),  # pyright: ignore[reportArgumentType]
                        unique_count=int(series.nunique(dropna=True)),  # pyright: ignore[reportArgumentType]
                        ordinal_position=ordinal_position,
                    )
                )

            preview_summary: JsonDict = {
                "row_count": row_count,
                "column_count": column_count,
                "missing_total": missing_total,
                "duplicate_count": duplicate_count,
                "memory_usage_bytes": memory_usage_bytes,
                "columns": [str(column) for column in dataframe.columns],
                "dtypes": {
                    str(key): str(value)
                    for key, value in dataframe.dtypes.astype(str).to_dict().items()
                },
            }

            snapshot = DatasetStructureSnapshot(
                row_count=row_count,
                column_count=column_count,
                missing_total=missing_total,
                duplicate_count=duplicate_count,
                memory_usage_bytes=memory_usage_bytes,
                features=tuple(feature_snapshots),
            )

            return Result.ok(
                DataFrameAnalysisResult(
                    snapshot=snapshot,
                    preview_summary=preview_summary,
                )
            )
        except Exception as exc:
            return Result.fail(
                code="dataframe_profile_failed",
                message="Не удалось профилировать набор данных.",
                details=str(exc),
            )

    def profile(self, snapshot: DatasetStructureSnapshot) -> Result[DatasetProfileResult]:
        """
        Построить доменные сущности из снапшота структуры набора данных.
        """
        if snapshot.row_count < 0:
            return Result.fail(
                code="invalid_snapshot_row_count",
                message="Снапшот набора данных содержит некорректное число строк.",
            )

        if snapshot.column_count < 0:
            return Result.fail(
                code="invalid_snapshot_column_count",
                message="Снапшот набора данных содержит некорректное число столбцов.",
            )

        if len(snapshot.features) != snapshot.column_count:
            return Result.fail(
                code="snapshot_column_mismatch",
                message="Количество признаков не совпадает с числом столбцов.",
                details=(
                    f"column_count={snapshot.column_count}, features={len(snapshot.features)}"
                ),
            )

        feature_names = [feature.name for feature in snapshot.features]
        if len(feature_names) != len(set(feature_names)):
            return Result.fail(
                code="duplicate_feature_names",
                message="Набор данных содержит дублирующиеся имена признаков.",
                details=str(feature_names),
            )

        try:
            features = tuple(
                FeatureDefinition.create(
                    name=feature.name,
                    physical_dtype=feature.physical_dtype,
                    logical_type=feature.logical_type,
                    role=FeatureRole.FEATURE,
                    nullable=feature.nullable,
                    missing_count=feature.missing_count,
                    unique_count=feature.unique_count,
                    ordinal_position=feature.ordinal_position,
                )
                for feature in snapshot.features
            )

            profile_summary = self._build_profile_summary(snapshot)

            profile = DatasetProfile.create(
                missing_total=snapshot.missing_total,
                duplicate_count=snapshot.duplicate_count,
                memory_usage_bytes=snapshot.memory_usage_bytes,
                summary=profile_summary,
            )

            return Result.ok(
                DatasetProfileResult(
                    features=features,
                    profile=profile,
                )
            )
        except ValueError as exc:
            return Result.fail(
                code="dataset_profile_build_failed",
                message="Не удалось создать объекты профилей набора данных.",
                details=str(exc),
            )

    def profile_dataframe(self, dataframe: DataFrame) -> Result[DatasetProfileResult]:
        """
        Удобный метод: проанализировать DataFrame и сразу вернуть
        доменные объекты профилирования.
        """
        analysis_result = self.analyze_dataframe(dataframe)
        if analysis_result.is_failure:
            return Result.fail(
                code=analysis_result.error.code if analysis_result.error else "profile_failed",
                message=analysis_result.error.message
                if analysis_result.error
                else "Профилирование не удалось.",
                details=analysis_result.error.details if analysis_result.error else None,
                warnings=list(analysis_result.warnings),
            )

        analysis = analysis_result.unwrap()
        return self.profile(analysis.snapshot)

    @staticmethod
    def _infer_logical_type(series: pd.Series) -> LogicalFeatureType:
        """
        Определить доменный логический тип на основе pandas dtype и простых эвристик.
        """
        if is_bool_dtype(series):
            return LogicalFeatureType.BOOLEAN

        if is_numeric_dtype(series):
            return LogicalFeatureType.NUMERIC

        if is_datetime64_any_dtype(series):
            return LogicalFeatureType.DATETIME

        if series.dtype == "object":
            non_null = series.dropna()
            unique_count = int(non_null.nunique(dropna=True))
            sample_size = len(non_null.index)

            if sample_size == 0:
                return LogicalFeatureType.UNKNOWN

            # Эвристика MVP:
            # столбцы object с низким числом уникальных значений считаются категориальными,
            # иначе — текстовыми.
            if unique_count <= 50 or unique_count <= max(5, sample_size // 5):
                return LogicalFeatureType.CATEGORICAL

            return LogicalFeatureType.TEXT

        return LogicalFeatureType.UNKNOWN

    @staticmethod
    def _build_profile_summary(snapshot: DatasetStructureSnapshot) -> JsonDict:
        """
        Построить компактный JSON‑сериализуемый профиль‑сводку.
        """
        logical_type_counts: dict[str, int] = {}
        nullable_columns = 0

        for feature in snapshot.features:
            logical_type_counts[feature.logical_type.value] = (
                logical_type_counts.get(feature.logical_type.value, 0) + 1
            )
            if feature.nullable:
                nullable_columns += 1

        return cast(
            JsonDict,
            {
                "row_count": snapshot.row_count,
                "column_count": snapshot.column_count,
                "missing_total": snapshot.missing_total,
                "duplicate_count": snapshot.duplicate_count,
                "memory_usage_bytes": snapshot.memory_usage_bytes,
                "nullable_column_count": nullable_columns,
                "logical_type_counts": logical_type_counts,
            },
        )
