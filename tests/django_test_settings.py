"""Minimal Django settings for transport-layer tests."""

SECRET_KEY = "test-secret-key"
DEBUG = True
ROOT_URLCONF = "app.transport.urls"
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]
MIDDLEWARE = []
INSTALLED_APPS = ["django.contrib.staticfiles", "app.web"]
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "DIRS": [],
        "OPTIONS": {},
    }
]
STATIC_URL = "/static/"
USE_TZ = True
