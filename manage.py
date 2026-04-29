#!/usr/bin/env python
"""Django management entrypoint — defaults to ``tests.django_test_settings`` (matches pytest).

Production deploys typically set::
    export DJANGO_SETTINGS_MODULE=app.deploy.site_settings
before invoking manage.py for migrate/collectstatic, or export once in the shell.
"""

from __future__ import annotations

import os
import sys


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.django_test_settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "Django must be installed: pip install django"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
