"""Утилиты подключения к SQLite."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from dt_analytics.shared import PersistenceError


def create_connection(db_path: Path) -> sqlite3.Connection:
    """
    Создать и настроить подключение к SQLite.

    Параметры
    ----------
    db_path:
        Путь к файлу базы данных SQLite.

    Возвращает
    -------
    sqlite3.Connection
        Настроенное подключение к SQLite.
    """
    try:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(str(db_path))
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON;")
        return connection
    except sqlite3.Error as exc:
        raise PersistenceError(f"Не удалось создать подключение к SQLite: {exc}") from exc
