"""Step 37B — Django ops entrypoint, DATABASE_URL, readiness extensions, deploy smoke."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.django_test_settings")
django.setup()


def test_manage_py_check_runs() -> None:
    repo = Path(__file__).resolve().parents[1]
    env = {**dict(os.environ), "PYTHONPATH": str(repo)}
    proc = subprocess.run(
        [sys.executable, str(repo / "manage.py"), "check"],
        cwd=str(repo),
        env=env,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr


def test_wsgi_application_importable() -> None:
    snippet = '''import django, os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.deploy.site_settings")
os.environ.setdefault("DJANGO_SECRET_KEY", "pytest-wsgi-" + "x" * 40)
os.environ.pop("DATABASE_URL", None)
os.environ.pop("DJANGO_SQLITE_PATH", None)
django.setup()
import config.wsgi
assert getattr(config.wsgi, "application", None) is not None
'''
    repo = Path(__file__).resolve().parents[1]
    clean = {**os.environ, "PYTHONPATH": "."}
    clean.pop("DATABASE_URL", None)
    clean.pop("DJANGO_SQLITE_PATH", None)
    proc = subprocess.run(
        [sys.executable, "-c", snippet],
        cwd=str(repo),
        capture_output=True,
        text=True,
        env=clean,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout


def test_asgi_application_importable() -> None:
    snippet = '''import django, os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.deploy.site_settings")
os.environ.setdefault("DJANGO_SECRET_KEY", "pytest-asgi-" + "y" * 40)
os.environ.pop("DATABASE_URL", None)
os.environ.pop("DJANGO_SQLITE_PATH", None)
django.setup()
import config.asgi
assert getattr(config.asgi, "application", None) is not None
'''
    repo = Path(__file__).resolve().parents[1]
    clean = {**os.environ, "PYTHONPATH": "."}
    clean.pop("DATABASE_URL", None)
    clean.pop("DJANGO_SQLITE_PATH", None)
    proc = subprocess.run(
        [sys.executable, "-c", snippet],
        cwd=str(repo),
        capture_output=True,
        text=True,
        env=clean,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout


def test_database_url_parses_to_postgresql_engine_via_dj_url() -> None:
    import dj_database_url

    parsed = dj_database_url.parse("postgresql://alice:bobpassword@pgsql.example.invalid:5432/wis_demo")
    assert "postgresql" in parsed["ENGINE"]
    assert parsed.get("HOST") == "pgsql.example.invalid"


def test_databases_from_environ_reflects_database_url(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://alice:bobpassword@pgsql.example.invalid:5432/wis_demo")
    from app.deploy.db_settings import databases_from_environ

    cfg = databases_from_environ(Path(__file__).resolve().parents[1])["default"]
    assert "postgresql" in cfg["ENGINE"]
    assert cfg.get("HOST") == "pgsql.example.invalid"


def test_default_sqlite_when_database_url_missing_subprocess(monkeypatch) -> None:
    snippet = '''import django, os
from pathlib import Path
os.environ.pop("DATABASE_URL", None)
repo = Path(".").resolve()
os.environ.setdefault("DJANGO_SQLITE_PATH", str(repo / "_tmp_verify_sqlite.sqlite3"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.deploy.site_settings")
os.environ.setdefault("DJANGO_SECRET_KEY", "sqlite-test-with-enough-characters-xx")
django.setup()
from django.conf import settings
cfg = settings.DATABASES["default"]
assert cfg["ENGINE"].endswith("sqlite3"), cfg["ENGINE"]
(Path(cfg["NAME"]).parent.mkdir(parents=True, exist_ok=True))
'''
    repo = Path(__file__).resolve().parents[1]
    monkeypatch.chdir(repo)
    proc = subprocess.run(
        [sys.executable, "-c", snippet],
        cwd=str(repo),
        capture_output=True,
        text=True,
        env={"PYTHONPATH": ".", **os.environ},
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout


def test_readiness_strict_warns_implicit_sqlite(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("DJANGO_ALLOW_SQLITE_IN_PRODUCTION", raising=False)
    monkeypatch.setenv("DJANGO_DEBUG", "false")
    monkeypatch.setenv("DJANGO_SECRET_KEY", "prod-" + "z" * 80)
    monkeypatch.setenv("DJANGO_ALLOWED_HOSTS", "example.com")
    monkeypatch.setenv("DJANGO_CSRF_TRUSTED_ORIGINS", "https://example.com")
    monkeypatch.setenv("PRESENTATION_LLM_PROVIDER", "none")

    from app.deploy.readiness import collect_readiness, read_debug_os, should_enforce_production

    report = collect_readiness(read_debug_os(), enforce_production_checks=should_enforce_production(assume_production=True))
    assert any(f.code == "DATABASE_BACKEND" and f.severity == "block" for f in report.findings)


def test_readiness_passes_strict_with_postgres_url_masked(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://alice:bobpassword123@pgsql.example.internal:5432/wdb")
    monkeypatch.setenv("DJANGO_DEBUG", "false")
    monkeypatch.setenv("DJANGO_SECRET_KEY", "prod-" + "z" * 80)
    monkeypatch.setenv("DJANGO_ALLOWED_HOSTS", "example.com")
    monkeypatch.setenv("DJANGO_CSRF_TRUSTED_ORIGINS", "https://example.com")
    monkeypatch.setenv("PRESENTATION_LLM_PROVIDER", "none")

    from app.deploy.readiness import collect_readiness, read_debug_os, should_enforce_production

    report = collect_readiness(read_debug_os(), enforce_production_checks=should_enforce_production(assume_production=True))
    blob = "\n".join(f.line() for f in report.findings)
    assert "bobpassword" not in blob
    assert "***" in blob or "postgresql://" in blob
    assert report.blocking_count == 0


def test_smoke_deploy_surface_zero_exit(monkeypatch) -> None:
    monkeypatch.chdir(Path(__file__).resolve().parents[1])
    proc = subprocess.run(
        [sys.executable, "-m", "app.scripts.smoke_deploy_surface"],
        capture_output=True,
        text=True,
        env={"PYTHONPATH": ".", **os.environ},
    )
    assert proc.returncode == 0
    assert proc.stdout.startswith("[OK] smoke_deploy_surface")


def test_mask_database_url_helpers() -> None:
    from app.deploy.env_helpers import mask_database_url

    m = mask_database_url("postgresql://user:sekret@localhost:5432/name")
    assert "sekret" not in m
    assert "***" in m


def test_env_example_has_placeholder_keys() -> None:
    root = Path(__file__).resolve().parents[1]
    txt = (root / ".env.example").read_text(encoding="utf-8")
    for needle in (
        "DJANGO_SECRET_KEY",
        "DJANGO_DEBUG",
        "DATABASE_URL",
        "DJANGO_CSRF_TRUSTED_ORIGINS",
    ):
        assert needle in txt


def test_collect_static_noinput_manage_py() -> None:
    repo = Path(__file__).resolve().parents[1]
    env = {"PYTHONPATH": str(repo), **dict(os.environ)}
    proc = subprocess.run(
        [sys.executable, str(repo / "manage.py"), "collectstatic", "--noinput"],
        cwd=str(repo),
        env=env,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
