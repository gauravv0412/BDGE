"""Account verification, Google foundation, and history helpers."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.http import HttpRequest
from django.urls import reverse
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes

from app.accounts.models import AccountProfile, AnalysisHistory

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class GoogleOAuthConfig:
    client_id: str
    client_secret: str

    @property
    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret)


def google_oauth_config() -> GoogleOAuthConfig:
    return GoogleOAuthConfig(
        client_id=getattr(settings, "GOOGLE_OAUTH_CLIENT_ID", ""),
        client_secret=getattr(settings, "GOOGLE_OAUTH_CLIENT_SECRET", ""),
    )


def ensure_profile(user: User, *, verified: bool | None = None, provider: str | None = None) -> AccountProfile:
    profile, _created = AccountProfile.objects.get_or_create(user=user)
    changed_fields: list[str] = []
    if verified is not None and profile.email_verified != verified:
        profile.email_verified = verified
        changed_fields.append("email_verified")
    if provider and profile.auth_provider != provider:
        profile.auth_provider = provider
        changed_fields.append("auth_provider")
    if changed_fields:
        profile.save(update_fields=changed_fields + ["updated_at"])
    return profile


def create_password_user(*, full_name: str, email: str, password: str) -> User:
    normalized_email = User.objects.normalize_email(email).strip().lower()
    first_name, last_name = split_full_name(full_name)
    user = User.objects.create_user(
        username=normalized_email,
        email=normalized_email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        is_active=False,
    )
    ensure_profile(user, verified=False, provider="password")
    return user


def split_full_name(full_name: str) -> tuple[str, str]:
    parts = full_name.strip().split()
    if not parts:
        return "", ""
    first_name = parts[0][:150]
    last_name = " ".join(parts[1:])[:150]
    return first_name, last_name


def user_is_verified(user: User) -> bool:
    if not user.is_authenticated:
        return False
    try:
        return bool(user.account_profile.email_verified)
    except AccountProfile.DoesNotExist:
        return user.is_active


def verification_token_for(user: User) -> tuple[str, str]:
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    return uid, token


def send_verification_email(request: HttpRequest, user: User) -> str:
    uid, token = verification_token_for(user)
    path = reverse("accounts:verify-email", kwargs={"uidb64": uid, "token": token})
    url = request.build_absolute_uri(path)
    subject = "Verify your Wisdomize account"
    body = (
        "Welcome to Wisdomize.\n\n"
        "Verify your email to start using the analyze workspace:\n"
        f"{url}\n\n"
        "If you did not create this account, you can ignore this email."
    )
    send_mail(
        subject,
        body,
        getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@wisdomize.local"),
        [user.email],
        fail_silently=True,
    )
    return url


def verify_email_token(*, uidb64: str, token: str) -> User | None:
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return None
    if not default_token_generator.check_token(user, token):
        return None
    user.is_active = True
    user.save(update_fields=["is_active"])
    ensure_profile(user, verified=True, provider="password")
    return user


def provision_google_user(*, email: str, full_name: str, email_verified: bool) -> User:
    normalized_email = User.objects.normalize_email(email).strip().lower()
    first_name, last_name = split_full_name(full_name or normalized_email)
    user, created = User.objects.get_or_create(
        username=normalized_email,
        defaults={
            "email": normalized_email,
            "first_name": first_name,
            "last_name": last_name,
            "is_active": bool(email_verified),
        },
    )
    update_fields: list[str] = []
    if not created:
        for field_name, value in {
            "email": normalized_email,
            "first_name": first_name,
            "last_name": last_name,
            "is_active": bool(email_verified),
        }.items():
            if getattr(user, field_name) != value:
                setattr(user, field_name, value)
                update_fields.append(field_name)
        if update_fields:
            user.save(update_fields=update_fields)
    ensure_profile(user, verified=bool(email_verified), provider="google")
    return user


def save_analysis_history(*, user: User, response_body: dict[str, Any]) -> AnalysisHistory | None:
    presentation = response_body.get("presentation")
    if isinstance(presentation, dict) and presentation.get("presentation_mode") == "crisis_safe":
        return None
    output = response_body.get("output")
    if not isinstance(output, dict):
        return None
    verse = output.get("verse_match") if isinstance(output.get("verse_match"), dict) else None
    share_layer = output.get("share_layer") if isinstance(output.get("share_layer"), dict) else {}
    return AnalysisHistory.objects.create(
        user=user,
        dilemma_text=str(output.get("dilemma", "")),
        dilemma_id=str(output.get("dilemma_id", "")),
        classification=str(output.get("classification", "")),
        alignment_score=int(output.get("alignment_score", 0)),
        verdict_sentence=str(output.get("verdict_sentence", ""))[:200],
        share_card_quote=str(share_layer.get("card_quote", ""))[:200],
        has_verse_match=verse is not None,
        verse_ref=str(verse.get("verse_ref", ""))[:32] if verse else "",
    )
