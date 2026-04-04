# DT Analytics

Desktop-информационная система для анализа табличных данных с применением методов построения деревьев решений.

## Текущий статус

Проект находится на этапе поэтапной реализации production-oriented MVP.

На текущем шаге реализован базовый каркас проекта:
- Python package с `src`-layout;
- единая конфигурация через `pyproject.toml`;
- базовая точка входа приложения;
- подготовка к следующему этапу: bootstrap и конфигурация приложения.

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
        └── main.py
```
