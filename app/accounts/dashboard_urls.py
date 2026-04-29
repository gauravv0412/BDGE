"""URL routes for the account dashboard and history."""

from __future__ import annotations

from django.urls import path

from app.accounts import views

app_name = "dashboard"

urlpatterns = [
    path("", views.dashboard_view, name="index"),
    path("history/<int:pk>/", views.history_detail_view, name="history-detail"),
    path("history/<int:pk>/delete/", views.history_delete_view, name="history-delete"),
    path("history/clear/confirm/", views.history_clear_confirm_view, name="history-clear-confirm"),
    path("history/clear/", views.history_clear_view, name="history-clear"),
]
