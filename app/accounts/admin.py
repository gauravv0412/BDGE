"""Django admin registration for account models."""

from __future__ import annotations

from django.contrib import admin

from app.accounts.models import AccountProfile, AnalysisHistory


@admin.register(AccountProfile)
class AccountProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "email_verified", "auth_provider", "created_at", "updated_at")
    search_fields = ("user__username", "user__email")
    readonly_fields = ("created_at", "updated_at")


@admin.register(AnalysisHistory)
class AnalysisHistoryAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "dilemma_id", "classification", "alignment_score", "created_at")
    search_fields = ("dilemma_id", "user__username", "user__email", "verdict_sentence")
    readonly_fields = (
        "created_at",
        "user",
        "dilemma_text",
        "dilemma_id",
        "classification",
        "alignment_score",
        "verdict_sentence",
        "share_card_quote",
        "has_verse_match",
        "verse_ref",
    )
