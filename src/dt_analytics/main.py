"""Точка входа приложения для DT Analytics."""

from __future__ import annotations

import sys
from collections.abc import Sequence

from dt_analytics.bootstrap import build_container, create_application, initialize_runtime
from dt_analytics.config import load_settings


def main(argv: Sequence[str] | None = None) -> int:
    """
    Запустить приложение DT Analytics.

    Параметры
    ----------
    argv:
        Необязательные аргументы командной строки. Если не указаны,
        используется ``sys.argv``.

    Возвращает
    -------
    int
        Код завершения процесса.
    """
    args = list(argv) if argv is not None else list(sys.argv)

    settings = load_settings()
    runtime = initialize_runtime(settings)
    container = build_container(settings=settings, runtime=runtime)
    app_instance = create_application(argv=args, container=container)

    app_instance.main_window.show()
    return app_instance.qt_app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
