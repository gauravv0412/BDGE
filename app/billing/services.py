"""Plan + quota helpers (config-driven)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from app.accounts.services import save_analysis_history
from app.config.runtime_config import PlanDefinition, get_plan, get_plan_definitions
from app.billing.models import BillingProfile, MonthlyPresentationUsage

if TYPE_CHECKING:
    from django.contrib.auth.models import User


@dataclass(frozen=True)
class QuotaStatus:
    allowed: bool
    used: int
    limit: int
    plan_key: str
    plan_label: str
    user_message: str


def current_period_key() -> str:
    """UTC month bucket (YYYY-MM) aligned with Django USE_TZ."""
    now = timezone.now()
    return f"{now.year:04d}-{now.month:02d}"


def get_or_create_billing_profile(user: User) -> BillingProfile:
    profile, _created = BillingProfile.objects.get_or_create(user=user, defaults={"plan_key": "free"})
    return profile


def presentation_usage_count(user: User, period: str) -> int:
    row = MonthlyPresentationUsage.objects.filter(user=user, year_month=period).first()
    return int(row.presentation_count) if row else 0


def check_presentation_quota(user: User) -> QuotaStatus:
    profile = get_or_create_billing_profile(user)
    plan = get_plan(profile.plan_key)
    if not plan.enabled:
        return QuotaStatus(
            allowed=False,
            used=0,
            limit=plan.monthly_analysis_limit,
            plan_key=plan.key,
            plan_label=plan.label,
            user_message="This plan is not available. Please contact support.",
        )
    period = current_period_key()
    used = presentation_usage_count(user, period)
    limit = plan.monthly_analysis_limit
    if limit <= 0:
        allowed = True
    else:
        allowed = used < limit
    msg = ""
    if not allowed:
        msg = (
            f"You have used all {limit} included analyses on the {plan.label} plan for this month. "
            "Upgrade options are coming soon — visit Billing for details."
        )
    return QuotaStatus(
        allowed=allowed,
        used=used,
        limit=limit,
        plan_key=plan.key,
        plan_label=plan.label,
        user_message=msg,
    )


def record_presentation_success(*, user: User, response_body: dict) -> None:
    """Persist history + increment monthly usage in one transaction."""
    presentation = response_body.get("presentation")
    if isinstance(presentation, dict) and presentation.get("presentation_mode") == "crisis_safe":
        return
    period = current_period_key()
    with transaction.atomic():
        saved = save_analysis_history(user=user, response_body=response_body)
        if saved is None:
            return
        row, _created = MonthlyPresentationUsage.objects.select_for_update().get_or_create(
            user=user,
            year_month=period,
            defaults={"presentation_count": 0},
        )
        MonthlyPresentationUsage.objects.filter(pk=row.pk).update(presentation_count=F("presentation_count") + 1)


def ordered_plan_definitions() -> list[PlanDefinition]:
    """Ordered free → plus → pro, then any additional configured plan keys."""
    defs = get_plan_definitions()
    order = ["free", "plus", "pro"]
    out: list = []
    for key in order:
        if key in defs:
            out.append(defs[key])
    for key, plan in defs.items():
        if key not in order:
            out.append(plan)
    return out
