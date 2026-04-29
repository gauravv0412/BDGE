"""Django URL routes for thin transport layer."""

from __future__ import annotations

from django.urls import include, path

from app.transport.django_api import analyze_presentation_view, analyze_view, feedback_view
from app.transport.frontend_shell import shell_view

urlpatterns = [
    path("api/v1/feedback", feedback_view, name="feedback"),
    path("api/v1/analyze/presentation", analyze_presentation_view, name="engine-analyze-presentation"),
    path("api/v1/analyze", analyze_view, name="engine-analyze"),
    path("analyze/", shell_view, name="frontend-shell"),
    path("", include("app.web.urls")),
]
