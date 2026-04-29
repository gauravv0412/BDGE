from __future__ import annotations

from django.contrib import admin

from app.billing.models import BillingProfile, MonthlyPresentationUsage


@admin.register(BillingProfile)
class BillingProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "plan_key", "updated_at")
    list_filter = ("plan_key",)
    search_fields = ("user__username", "user__email", "plan_key")
    raw_id_fields = ("user",)


@admin.register(MonthlyPresentationUsage)
class MonthlyPresentationUsageAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "year_month", "presentation_count")
    list_filter = ("year_month",)
    search_fields = ("user__username", "user__email", "year_month")
    raw_id_fields = ("user",)
