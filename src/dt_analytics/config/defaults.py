"""Значения конфигурации по умолчанию для DT Analytics."""

from __future__ import annotations

from pathlib import Path

APP_NAME = "DT Analytics"
APP_ORGANIZATION_NAME = "DT Analytics"
APP_ORGANIZATION_DOMAIN = "local.dt-analytics"
APP_VERSION = "0.1.0"

DEFAULT_WINDOW_TITLE = "DT Analytics"
DEFAULT_WINDOW_WIDTH = 1440
DEFAULT_WINDOW_HEIGHT = 900
DEFAULT_MIN_WINDOW_WIDTH = 1024
DEFAULT_MIN_WINDOW_HEIGHT = 720

DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_DEBUG = False

DEFAULT_RANDOM_STATE = 42
DEFAULT_TEST_SIZE = 0.2

DEFAULT_PROJECTS_DIR = Path.home() / "DTAnalyticsProjects"
