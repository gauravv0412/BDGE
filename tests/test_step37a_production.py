"""Infrastructure hardening regressions — Step 37A (deploy settings, readiness, health)."""

from __future__ import annotations

import json
import os
import subprocess
import sys

import django
from django.test import Client

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.django_test_settings")
django.setup()


def test_health_endpoint_public_json() -> None:
    client = Client()
    response = client.get("/healthz/")
    assert response.status_code == 200
    data = json.loads(response.content.decode("utf-8"))
    assert data == {"ok": True, "service": "wisdomize"}
    assert "SECRET_KEY" not in response.content.decode("utf-8")


def test_health_rejects_non_get() -> None:
    client = Client()
    assert client.post("/healthz/").status_code == 405


def test_health_for_anonymous_even_if_session_present() -> None:
    client = Client()
    assert client.get("/healthz/", HTTP_ORIGIN="https://evil.test").status_code == 200


def test_env_csv_splits_csrf_hosts() -> None:
    from app.deploy.env_helpers import env_csv_list

    assert env_csv_list("https://a.com,https://b.com") == ["https://a.com", "https://b.com"]


def test_readiness_relaxed_mode_skips_blocking() -> None:
    from app.deploy.readiness import collect_readiness, read_debug_os, should_enforce_production

    enforce = should_enforce_production(assume_production=False)
    report = collect_readiness(read_debug_os(), enforce_production_checks=enforce)
    assert enforce is False
    assert report.blocking_count == 0


def test_readiness_strict_mode_blocks_placeholder_secret(monkeypatch) -> None:
    monkeypatch.setenv("DJANGO_DEBUG", "false")
    monkeypatch.setenv("DJANGO_SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("DJANGO_ALLOWED_HOSTS", "example.com")
    monkeypatch.setenv("DJANGO_CSRF_TRUSTED_ORIGINS", "https://example.com")
    monkeypatch.setenv("PRESENTATION_LLM_PROVIDER", "none")

    from app.deploy.readiness import collect_readiness, read_debug_os, should_enforce_production

    report = collect_readiness(read_debug_os(), enforce_production_checks=should_enforce_production(assume_production=True))
    assert report.blocking_count >= 1


def test_readiness_strict_good_fixture_passes(monkeypatch) -> None:
    monkeypatch.setenv("DJANGO_DEBUG", "false")
    monkeypatch.setenv("DJANGO_SECRET_KEY", "prod-" + "z" * 80)
    monkeypatch.setenv("DJANGO_ALLOWED_HOSTS", "example.com,app.example.com")
    monkeypatch.setenv("DJANGO_CSRF_TRUSTED_ORIGINS", "https://example.com,https://app.example.com")
    monkeypatch.setenv("DJANGO_SESSION_COOKIE_SECURE", "true")
    monkeypatch.setenv("DJANGO_CSRF_COOKIE_SECURE", "true")
    monkeypatch.setenv("PRESENTATION_LLM_PROVIDER", "none")
    monkeypatch.setenv("DATABASE_URL", "postgresql://ci_user:ci_secret_value@db.internal:5432/wisdemo")

    from app.deploy.readiness import collect_readiness, read_debug_os, should_enforce_production

    report = collect_readiness(read_debug_os(), enforce_production_checks=should_enforce_production(assume_production=True))
    assert report.blocking_count == 0


def test_readiness_blocks_missing_llm_key_when_provider_active(monkeypatch) -> None:
    monkeypatch.setenv("DJANGO_DEBUG", "false")
    monkeypatch.setenv("DJANGO_SECRET_KEY", "prod-" + "z" * 80)
    monkeypatch.setenv("DJANGO_ALLOWED_HOSTS", "example.com")
    monkeypatch.setenv("DJANGO_CSRF_TRUSTED_ORIGINS", "https://example.com")
    monkeypatch.setenv("PRESENTATION_LLM_ENABLED", "true")
    monkeypatch.setenv("PRESENTATION_LLM_PROVIDER", "anthropic")
    monkeypatch.delenv("PRESENTATION_LLM_API_KEY", raising=False)

    from app.deploy.readiness import collect_readiness, read_debug_os, should_enforce_production

    report = collect_readiness(read_debug_os(), enforce_production_checks=should_enforce_production(assume_production=True))
    assert any(f.code == "PRESENTATION_LLM" and f.severity == "block" for f in report.findings)


def test_check_deploy_script_exits_clean_locally() -> None:
    env = dict(os.environ)
    proc = subprocess.run(
        [sys.executable, "-m", "app.scripts.check_deploy_readiness"],
        cwd=os.path.dirname(os.path.dirname(__file__)),
        capture_output=True,
        text=True,
        env={**env, "DJANGO_SECRET_KEY": "relax-local-suite-key-xxxxx-xxxxx-xxxxx-xxxx"},
        check=False,
    )
    assert proc.returncode == 0


def test_site_settings_raises_without_secret_when_debug_false_subprocess() -> None:
    env = {k: v for k, v in os.environ.items()}
    env.pop("DJANGO_SECRET_KEY", None)
    env.pop("SECRET_KEY", None)
    env["DJANGO_SETTINGS_MODULE"] = "app.deploy.site_settings"
    env["DJANGO_DEBUG"] = "false"
    env.setdefault("PYTHONPATH", ".")
    snippet = """import django, os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.deploy.site_settings')
try:
    django.setup()
except Exception:
    raise SystemExit(2)
raise SystemExit(99)
"""

    proc = subprocess.run([sys.executable, "-c", snippet], cwd=os.path.dirname(os.path.dirname(__file__)), env=env, capture_output=True, text=True)
    assert proc.returncode == 2
