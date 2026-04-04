# DT Analytics

Desktop-информационная система для анализа табличных данных с применением методов построения деревьев решений.

## Текущий статус

Проект находится на этапе реализации production-oriented MVP.

На текущем шаге реализованы:
- базовый каркас проекта;
- bootstrap-слой;
- централизованная типизированная конфигурация;
- composition root;
- создание `QApplication`;
- минимальное главное окно.

## Технологический стек

- Python 3.12+
- PySide6
- pandas
- numpy
- scikit-learn
- matplotlib
- SQLite
- pytest

## Структура проекта

```text
decision_tree_analytics/
├── pyproject.toml
├── README.md
├── .gitignore
├── .editorconfig
├── pytest.ini
└── src/
    └── dt_analytics/
        ├── __init__.py
        ├── main.py
        ├── bootstrap/
        ├── config/
        └── presentation/
```
