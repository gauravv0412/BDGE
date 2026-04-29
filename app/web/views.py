"""Static public web views for the Wisdomize launch foundation."""

from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def landing_view(request: HttpRequest) -> HttpResponse:
    return render(request, "web/landing.html", {"active_page": "landing"})


def faq_view(request: HttpRequest) -> HttpResponse:
    return render(request, "web/faq.html", {"active_page": "faq"})


def about_view(request: HttpRequest) -> HttpResponse:
    return render(request, "web/about.html", {"active_page": "about"})


def pricing_view(request: HttpRequest) -> HttpResponse:
    return render(request, "web/pricing.html", {"active_page": "pricing"})


def contact_view(request: HttpRequest) -> HttpResponse:
    return render(request, "web/contact.html", {"active_page": "contact"})
