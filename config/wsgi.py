"""WSGI entrypoint — use::

    gunicorn config.wsgi:application --bind 0.0.0.0:8000

Set ``DJANGO_SETTINGS_MODULE`` to ``app.deploy.site_settings`` in production."""

from __future__ import annotations

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.deploy.site_settings")

application = get_wsgi_application()
