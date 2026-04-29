"""Shared Django test setup for the lightweight transport test suite."""

from __future__ import annotations

import os

import django
import pytest
from django.core.management import call_command

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.django_test_settings")
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")
django.setup()


@pytest.fixture(scope="session", autouse=True)
def _migrate_django_auth_tables() -> None:
    call_command("migrate", verbosity=0, interactive=False)


@pytest.fixture(autouse=True)
def _clean_django_auth_state(request: pytest.FixtureRequest) -> None:
    django_test_files = {
        "test_accounts_auth_gate.py",
        "test_django_transport.py",
        "test_feedback_endpoint.py",
        "test_frontend_shell.py",
        "test_frontend_shell_browser.py",
        "test_step38a_config_billing.py",
        "test_web_pages.py",
    }
    if request.node.path.name not in django_test_files:
        return
    call_command("flush", verbosity=0, interactive=False)
