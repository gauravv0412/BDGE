"""URL routes for public Wisdomize web pages."""

from __future__ import annotations

from django.urls import path

from app.web import views

app_name = "web"

urlpatterns = [
    path("", views.landing_view, name="landing"),
    path("faq/", views.faq_view, name="faq"),
    path("about/", views.about_view, name="about"),
    path("pricing/", views.pricing_view, name="pricing"),
    path("contact/", views.contact_view, name="contact"),
]
