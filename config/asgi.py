"""ASGI entrypoint (no Channels dependency). Compatible with::

    uvicorn config.asgi:application
"""

from __future__ import annotations

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.deploy.site_settings")

application = get_asgi_application()
