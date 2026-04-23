"""Django URL routes for thin transport layer."""

from __future__ import annotations

from django.urls import path

from app.transport.django_api import analyze_view

urlpatterns = [
    path("api/v1/analyze", analyze_view, name="engine-analyze"),
]
