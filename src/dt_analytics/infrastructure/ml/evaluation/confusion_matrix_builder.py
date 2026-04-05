"""Вспомогательные функции для матрицы ошибок (confusion matrix)."""

from __future__ import annotations

from collections.abc import Sequence

from sklearn.metrics import confusion_matrix


def build_confusion_matrix(
    y_true: Sequence[object],
    y_pred: Sequence[object],
) -> list[list[int]]:
    """Построить матрицу ошибок в JSON‑сериализуемом виде."""
    matrix = confusion_matrix(y_true, y_pred)
    return [[int(cell) for cell in row] for row in matrix.tolist()]
