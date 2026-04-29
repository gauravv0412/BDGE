"""Billing shell (read-only; no checkout)."""

from __future__ import annotations

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from app.billing.services import (
    check_presentation_quota,
    current_period_key,
    get_or_create_billing_profile,
    ordered_plan_definitions,
)
from app.config.runtime_config import get_plan


@login_required(login_url=settings.LOGIN_URL)
def billing_home_view(request: HttpRequest) -> HttpResponse:
    profile = get_or_create_billing_profile(request.user)
    plan = get_plan(profile.plan_key)
    quota = check_presentation_quota(request.user)
    return render(
        request,
        "billing/billing_home.html",
        {
            "active_page": "billing",
            "current_plan": plan,
            "quota": quota,
            "period": current_period_key(),
            "all_plans": ordered_plan_definitions(),
        },
    )
