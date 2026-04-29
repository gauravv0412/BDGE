"""Django settings for Wisdomize deployments (HTTPS-aware, env-driven).

Use::
    export DJANGO_SETTINGS_MODULE=app.deploy.site_settings

Tests and CI keep using ``tests.django_test_settings``.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

try:
    from whitenoise.middleware import WhiteNoiseMiddleware  # noqa: F401

    _HAS_WHITENOISE = True
except ImportError:  # pragma: no cover
    _HAS_WHITENOISE = False

from django.core.exceptions import ImproperlyConfigured

from app.deploy.db_settings import databases_from_environ
from app.deploy.env_helpers import env_bool, env_csv_list, env_int


_REPO_ROOT = Path(__file__).resolve().parents[2]

# --- Debug (default True when unset; local dev ergonomics)


def _read_debug() -> bool:
    raw = os.environ.get("DJANGO_DEBUG")
    if raw is None:
        return True
    return env_bool(raw, True)


DEBUG = _read_debug()

# --- Secrets

_SECRET_KEY_RAW = (
    (os.environ.get("DJANGO_SECRET_KEY") or os.environ.get("SECRET_KEY") or "").strip()
)
if not _SECRET_KEY_RAW:
    _placeholder = ("unsafe-local-development-only-setting-" + "x" * 16)[:50]
    if DEBUG:
        SECRET_KEY = _placeholder
    else:
        raise ImproperlyConfigured(
            "DJANGO_SECRET_KEY must be set to a secure value when DJANGO_DEBUG is false."
        )
else:
    SECRET_KEY = _SECRET_KEY_RAW


# --- Host / CSRF

_hosts = env_csv_list(os.environ.get("DJANGO_ALLOWED_HOSTS"))
ALLOWED_HOSTS = _hosts or (
    ["localhost", "127.0.0.1", "testserver"] + (["*"] if DEBUG else [])
)

CSRF_TRUSTED_ORIGINS = env_csv_list(os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS"))

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env_bool(os.environ.get("DJANGO_SECURE_SSL_REDIRECT"), False)
SESSION_COOKIE_SECURE = env_bool(os.environ.get("DJANGO_SESSION_COOKIE_SECURE"), False)
CSRF_COOKIE_SECURE = env_bool(os.environ.get("DJANGO_CSRF_COOKIE_SECURE"), False)
SECURE_HSTS_SECONDS = env_int(os.environ.get("DJANGO_SECURE_HSTS_SECONDS"), 0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool(os.environ.get("DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS"), False)
SECURE_HSTS_PRELOAD = env_bool(os.environ.get("DJANGO_SECURE_HSTS_PRELOAD"), False)

SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
SECURE_REFERRER_POLICY = "same-origin"

# --- Paths / DB / templates

ROOT_URLCONF = "app.transport.urls"


def _middleware() -> list[str]:
    mw = [
        "django.middleware.security.SecurityMiddleware",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.middleware.common.CommonMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "django.contrib.messages.middleware.MessageMiddleware",
        "django.middleware.clickjacking.XFrameOptionsMiddleware",
    ]
    if _HAS_WHITENOISE:
        mw.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
    return mw


MIDDLEWARE = _middleware()

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "app.accounts",
    "app.billing",
    "app.web",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "DIRS": [],
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

DATABASES = databases_from_environ(_REPO_ROOT)


_email_backend_override = os.environ.get("DJANGO_EMAIL_BACKEND") or ""
if _email_backend_override.strip():
    EMAIL_BACKEND = _email_backend_override.strip()
elif DEBUG:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
else:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

DEFAULT_FROM_EMAIL = (
    os.environ.get("DJANGO_DEFAULT_FROM_EMAIL") or os.environ.get("DEFAULT_FROM_EMAIL") or "no-reply@wisdomize.local"
)
EMAIL_HOST = os.environ.get("DJANGO_EMAIL_HOST") or ""
EMAIL_PORT = env_int(os.environ.get("DJANGO_EMAIL_PORT"), 587)
EMAIL_USE_TLS = env_bool(os.environ.get("DJANGO_EMAIL_USE_TLS"), True)
EMAIL_HOST_USER = os.environ.get("DJANGO_EMAIL_HOST_USER") or ""
EMAIL_HOST_PASSWORD = os.environ.get("DJANGO_EMAIL_HOST_PASSWORD") or ""

GOOGLE_OAUTH_CLIENT_ID = (
    os.environ.get("DJANGO_GOOGLE_OAUTH_CLIENT_ID") or os.environ.get("GOOGLE_OAUTH_CLIENT_ID") or ""
)
GOOGLE_OAUTH_CLIENT_SECRET = (
    os.environ.get("DJANGO_GOOGLE_OAUTH_CLIENT_SECRET") or os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET") or ""
)


STATIC_URL = "/static/"
_static_root_env = os.environ.get("DJANGO_STATIC_ROOT", "").strip()
STATIC_ROOT = str(Path(_static_root_env).resolve()) if _static_root_env else str(_REPO_ROOT / "static_collected")

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": (
        {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"}
        if _HAS_WHITENOISE
        else {"BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"}
    ),
}

USE_TZ = True
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/analyze/"
LOGOUT_REDIRECT_URL = "/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]

STATICFILES_DIRS = []


# Logging: no payloads, dilemma text, prompts, OAuth secrets, or verification tokens in standard config.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "structured": {"format": '%(levelname)s %(name)s %(message)s'},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "structured"},
    },
    "root": {"level": os.environ.get("DJANGO_ROOT_LOG_LEVEL", "INFO").upper(), "handlers": ["console"]},
    "loggers": {
        "django.request": {"handlers": ["console"], "level": "ERROR", "propagate": False},
        "django.security": {"handlers": ["console"], "level": "WARNING", "propagate": False},
    },
}

if not DEBUG:
    logging.getLogger("django.db.backends").setLevel(logging.WARNING)
