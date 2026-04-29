"""Build Django DATABASES from environment (PostgreSQL vs SQLite fallback)."""

from __future__ import annotations

import os
from pathlib import Path

from app.deploy.env_helpers import env_int

try:
    import dj_database_url as _dj_db_url

    _HAS_DB_URL = True
except ImportError:  # pragma: no cover
    _HAS_DB_URL = False
    _dj_db_url = None  # type: ignore[misc, assignment]


def databases_from_environ(repo_root: Path) -> dict[str, dict]:
    raw = os.environ.get("DATABASE_URL", "").strip()
    if raw:
        if not _HAS_DB_URL:
            raise RuntimeError("DATABASE_URL requires the dj-database-url package.")  # noqa: TRY003
        conn_max_age = env_int(os.environ.get("DJANGO_DATABASE_CONN_MAX_AGE"), 600)
        return {"default": _dj_db_url.parse(raw, conn_max_age=conn_max_age)}
    sqlite_override = os.environ.get("DJANGO_SQLITE_PATH", "").strip()
    sqlite_file = Path(sqlite_override).resolve() if sqlite_override else (repo_root / "var" / "wisdomize.sqlite3").resolve()
    sqlite_file.parent.mkdir(parents=True, exist_ok=True)
    return {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": sqlite_file.as_posix(),
        }
    }


def try_parse_database_url(raw: str) -> tuple[bool, str]:
    """Return (success, error_or_empty). Does not connect to the database."""
    if not raw.strip():
        return False, "empty DATABASE_URL"
    if not _HAS_DB_URL:
        return False, "dj-database-url not installed"
    try:
        _dj_db_url.parse(raw)
    except Exception as exc:  # noqa: BLE001 — surface parse failures to readiness
        return False, str(exc)
    return True, ""
