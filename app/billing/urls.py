"""Billing routes."""

from __future__ import annotations

from django.urls import path

from app.billing import views

app_name = "billing"

urlpatterns = [
    path("", views.billing_home_view, name="home"),
]
