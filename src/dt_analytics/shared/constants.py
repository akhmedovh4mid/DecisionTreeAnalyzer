"""Общие технические константы для DT Analytics."""

from __future__ import annotations

APP_PACKAGE_NAME = "dt_analytics"

PROJECT_DB_FILENAME = "project.db"

DATASETS_DIRNAME = "datasets"
DATASETS_IMPORTED_DIRNAME = "imported"
DATASETS_PROCESSED_DIRNAME = "processed"

ARTIFACTS_DIRNAME = "artifacts"
ARTIFACTS_MODELS_DIRNAME = "models"
ARTIFACTS_PLOTS_DIRNAME = "plots"
ARTIFACTS_REPORTS_DIRNAME = "reports"

EXPORTS_DIRNAME = "exports"
LOGS_DIRNAME = "logs"
TMP_DIRNAME = "tmp"
RUNTIME_DIRNAME = ".runtime"

DEFAULT_ENCODING = "utf-8"

ERROR_CODE_UNKNOWN = "unknown_error"
ERROR_CODE_VALIDATION = "validation_error"
ERROR_CODE_NOT_FOUND = "not_found"
ERROR_CODE_PERSISTENCE = "persistence_error"
ERROR_CODE_CONFIGURATION = "configuration_error"
