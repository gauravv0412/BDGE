"""In-process deploy surface smoke (no HTTP server, no LLM, no browser auth flow)."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.django_test_settings")

    import django

    django.setup()

    from django.conf import settings as django_settings
    from django.urls import Resolver404, resolve

    from app.deploy.db_settings import databases_from_environ, try_parse_database_url

    required = [
        ("/healthz/", "health endpoint"),
        ("/", "web root"),
        ("/analyze/", "analyze shell"),
        ("/billing/", "billing shell"),
        ("/api/v1/analyze", "analyze api"),
        ("/api/v1/analyze/presentation", "analyze presentation api"),
    ]
    for path, hint in required:
        try:
            match = resolve(path)
        except Resolver404 as exc:
            print(f"[XX] resolve {path!r} failed ({hint}): {exc}", file=sys.stderr)
            return 2
        if match.func is None:
            print(f"[XX] empty resolver for {path!r}", file=sys.stderr)
            return 2

    if "django.contrib.auth" not in django_settings.INSTALLED_APPS:
        print("[XX] django.contrib.auth missing from INSTALLED_APPS", file=sys.stderr)
        return 3
    if "django.contrib.auth.middleware.AuthenticationMiddleware" not in django_settings.MIDDLEWARE:
        print("[XX] AuthenticationMiddleware missing", file=sys.stderr)
        return 3

    static_url = getattr(django_settings, "STATIC_URL", "") or ""
    if not static_url.strip("/"):
        print("[XX] STATIC_URL missing", file=sys.stderr)
        return 4

    probe_database_url = os.environ.get("DATABASE_URL", "").strip()
    if probe_database_url:
        ok_parse, parse_err = try_parse_database_url(probe_database_url)
        if not ok_parse:
            print(f"[XX] DATABASE_URL not parseable: {parse_err}", file=sys.stderr)
            return 5

    databases = databases_from_environ(repo_root=repo_root)
    cfg = databases.get("default") or {}
    if not cfg.get("ENGINE"):
        print("[XX] DATABASES['default'].ENGINE missing", file=sys.stderr)
        return 5

    print("[OK] smoke_deploy_surface: URLs, auth stack, DB config, static basics")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
