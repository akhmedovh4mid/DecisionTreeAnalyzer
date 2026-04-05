"""Общие низкоуровневые псевдонимы типов, используемые по всему проекту."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

type JsonPrimitive = str | int | float | bool | None
type JsonValue = JsonPrimitive | list["JsonValue"] | dict[str, "JsonValue"]
type JsonDict = dict[str, JsonValue]
type ReadonlyMapping = Mapping[str, Any]

type PathLike = str | Path
type Identifier = str
