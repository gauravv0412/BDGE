"""Account profile and analysis history models."""

from __future__ import annotations

from django.conf import settings
from django.db import models


class AccountProfile(models.Model):
    """Small extension around Django's built-in User model."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="account_profile")
    email_verified = models.BooleanField(default=False)
    auth_provider = models.CharField(max_length=24, default="password")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"AccountProfile(user_id={self.user_id}, verified={self.email_verified})"


class AnalysisHistory(models.Model):
    """Minimal user-owned history for successful presentation analyses."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="analysis_history")
    created_at = models.DateTimeField(auto_now_add=True)
    dilemma_text = models.TextField()
    dilemma_id = models.CharField(max_length=64)
    classification = models.CharField(max_length=64)
    alignment_score = models.IntegerField()
    verdict_sentence = models.CharField(max_length=200)
    share_card_quote = models.CharField(max_length=200, blank=True)
    has_verse_match = models.BooleanField(default=False)
    verse_ref = models.CharField(max_length=32, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"AnalysisHistory(user_id={self.user_id}, dilemma_id={self.dilemma_id})"
