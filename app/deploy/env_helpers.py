"""Environment parsing for Django deployment settings and readiness scripts."""

from __future__ import annotations

import hashlib
from urllib.parse import urlparse


def env_bool(raw: str | None, default: bool = False) -> bool:
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def env_csv_list(raw: str | None) -> list[str]:
    if raw is None or not raw.strip():
        return []
    return [p.strip() for p in raw.replace("\n", ",").split(",") if p.strip()]


def env_int(raw: str | None, default: int) -> int:
    if raw is None or raw.strip() == "":
        return default
    try:
        value = int(raw.strip())
        return max(0, value)
    except ValueError:
        return default


# Placeholder secret keys blocked in strict production readiness
_DEV_SECRET_SENTINELS = frozenset(
    {
        "test-secret-key",
        "dev-secret-key-change-me",
        "django-insecure",
        "",
    }
)


def is_placeholder_secret(secret_key: str) -> bool:
    if not secret_key or len(secret_key) < 20:
        return True
    s = secret_key.strip()
    if s.lower() in _DEV_SECRET_SENTINELS:
        return True
    if len(s) < 32:
        # Short secrets are dubious in production checks
        return True
    if "change" in s.lower() and ("me" in s.lower() or "this" in s.lower()):
        return True
    return False


def secret_fingerprint(secret_key: str) -> str:
    """Fingerprint for logs/readiness — never echoes raw secret."""
    if not secret_key:
        return "empty"
    h = hashlib.sha256(secret_key.encode("utf-8")).hexdigest()
    return f"sha256:{h[:16]}..."


def mask_database_url(url: str) -> str:
    """Redact credentials from DATABASE_URL for readiness logs (passwords never printed)."""
    s = url.strip()
    if not s:
        return "(empty)"
    parsed = urlparse(s)
    if not parsed.scheme:
        return "***"
    host = parsed.hostname or ""
    port = f":{parsed.port}" if parsed.port else ""
    user = parsed.username or ""
    if user or parsed.password:
        auth = f"{user}:***@" if user else "***@"
    else:
        auth = ""
    path = parsed.path or ""
    q = f"?{parsed.query}" if parsed.query else ""
    return f"{parsed.scheme}://{auth}{host}{port}{path}{q}"

