"""Пакет конфигурации для DT Analytics."""

from dt_analytics.config.schemas import AppSettings
from dt_analytics.config.settings import load_settings

__all__ = ["AppSettings", "load_settings"]
