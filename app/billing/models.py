"""User plan and monthly presentation usage."""

from __future__ import annotations

from django.conf import settings
from django.db import models


class BillingProfile(models.Model):
    """Current subscription tier key (plans defined in config, not here)."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="billing_profile")
    plan_key = models.CharField(max_length=32, default="free", db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Billing profile"
        verbose_name_plural = "Billing profiles"

    def __str__(self) -> str:
        return f"BillingProfile(user_id={self.user_id}, plan={self.plan_key})"


class MonthlyPresentationUsage(models.Model):
    """Successful authenticated /api/v1/analyze/presentation completions per calendar month."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="monthly_presentation_usage"
    )
    year_month = models.CharField(max_length=7, db_index=True)
    presentation_count = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "year_month"], name="billing_monthlyusage_user_period_uniq")
        ]
        ordering = ["-year_month"]
        verbose_name = "Monthly presentation usage"
        verbose_name_plural = "Monthly presentation usages"

    def __str__(self) -> str:
        return f"MonthlyUsage(user_id={self.user_id}, {self.year_month}={self.presentation_count})"
