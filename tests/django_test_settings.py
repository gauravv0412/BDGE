"""Minimal Django settings for transport-layer tests."""

SECRET_KEY = "test-secret-key"
DEBUG = True
ROOT_URLCONF = "app.transport.urls"
ALLOWED_HOSTS = ["testserver", "localhost"]
MIDDLEWARE = []
INSTALLED_APPS = []
TEMPLATES = []
USE_TZ = True
