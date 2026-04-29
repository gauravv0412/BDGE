"""Account views for signup, login, logout, dashboard, settings, and verification."""

from __future__ import annotations

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods, require_POST

from app.accounts.forms import AccountSettingsForm, WisdomizeLoginForm, WisdomizeSignupForm
from app.accounts.models import AnalysisHistory
from app.accounts.services import (
    google_oauth_config,
    send_verification_email,
    split_full_name,
    user_is_verified,
    verify_email_token,
)
from app.billing.services import (
    current_period_key,
    get_or_create_billing_profile,
    presentation_usage_count,
)
from app.config.runtime_config import get_plan, get_runtime_config


def _safe_next_url(request: HttpRequest, fallback: str = "/analyze/") -> str:
    candidate = request.POST.get("next") or request.GET.get("next")
    if candidate and url_has_allowed_host_and_scheme(
        url=candidate,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return candidate
    return fallback


def _safe_next_candidate(request: HttpRequest, candidate: str) -> bool:
    return url_has_allowed_host_and_scheme(
        url=candidate,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    )


def _apply_full_name(user: User, full_name: str) -> None:
    fn, ln = split_full_name(full_name)
    user.first_name = fn
    user.last_name = ln
    user.save(update_fields=["first_name", "last_name"])


def _display_full_name(user: User) -> str:
    return f"{user.first_name} {user.last_name}".strip() or user.get_username()


@require_http_methods(["GET", "POST"])
def signup_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect(_safe_next_url(request))

    if request.method == "POST":
        form = WisdomizeSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            verification_url = send_verification_email(request, user)
            request.session["verification_pending_email"] = user.email
            request.session["verification_next_url"] = _safe_next_url(request)
            if settings.DEBUG:
                request.session["last_verification_url"] = verification_url
            return redirect("accounts:verification-sent")
    else:
        form = WisdomizeSignupForm()

    return render(
        request,
        "accounts/signup.html",
        {
            "form": form,
            "next_url": _safe_next_url(request),
            "active_page": "signup",
            "google_configured": google_oauth_config().is_configured,
        },
    )


def _login_post_unverified_with_valid_password(request: HttpRequest) -> HttpResponse | None:
    """If credentials match an unverified account, send them to verification UX (no auth leak)."""
    email = (request.POST.get("username") or "").strip().lower()
    password = request.POST.get("password") or ""
    if not email or not password:
        return None
    try:
        candidate = User.objects.get(username__iexact=email)
    except User.DoesNotExist:
        return None
    if not candidate.check_password(password):
        return None
    if user_is_verified(candidate):
        return None
    request.session["verification_pending_email"] = candidate.email or candidate.username
    request.session["verification_next_url"] = _safe_next_url(request)
    messages.warning(request, "Please verify your email to continue.")
    return redirect("accounts:verification-required")


@require_http_methods(["GET", "POST"])
def login_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect(_safe_next_url(request))

    if request.method == "POST":
        form = WisdomizeLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if not user_is_verified(user):
                request.session["verification_pending_email"] = user.email or user.username
                request.session["verification_next_url"] = _safe_next_url(request)
                messages.warning(request, "Please verify your email to continue.")
                return redirect("accounts:verification-required")
            login(request, user)
            return redirect(_safe_next_url(request))
        alt = _login_post_unverified_with_valid_password(request)
        if alt is not None:
            return alt
    else:
        form = WisdomizeLoginForm(request)

    return render(
        request,
        "accounts/login.html",
        {
            "form": form,
            "next_url": _safe_next_url(request),
            "active_page": "login",
            "google_configured": google_oauth_config().is_configured,
        },
    )


@require_POST
def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    return redirect("/")


@login_required(login_url=settings.LOGIN_URL)
def dashboard_view(request: HttpRequest) -> HttpResponse:
    page_size = get_runtime_config().dashboard_history_page_size
    history = list(AnalysisHistory.objects.filter(user=request.user)[:page_size])
    profile = get_or_create_billing_profile(request.user)
    plan = get_plan(profile.plan_key)
    used = presentation_usage_count(request.user, current_period_key())
    return render(
        request,
        "accounts/dashboard.html",
        {
            "active_page": "dashboard",
            "history": history,
            "history_count": len(history),
            "usage_used": used,
            "usage_limit": plan.monthly_analysis_limit,
            "usage_plan_label": plan.label,
            "usage_period": current_period_key(),
        },
    )


@login_required(login_url=settings.LOGIN_URL)
def history_detail_view(request: HttpRequest, pk: int) -> HttpResponse:
    record = get_object_or_404(AnalysisHistory.objects.filter(user=request.user), pk=pk)
    return render(
        request,
        "accounts/history_detail.html",
        {
            "active_page": "dashboard",
            "record": record,
            "detail_title": "Analysis detail",
        },
    )


@login_required(login_url=settings.LOGIN_URL)
@require_POST
def history_delete_view(request: HttpRequest, pk: int) -> HttpResponse:
    record = AnalysisHistory.objects.filter(user=request.user, pk=pk).first()
    if record is None:
        raise Http404()
    record.delete()
    messages.success(request, "This analysis has been removed from your history.")
    return redirect("dashboard:index")


@login_required(login_url=settings.LOGIN_URL)
@require_http_methods(["GET"])
def history_clear_confirm_view(request: HttpRequest) -> HttpResponse:
    count = AnalysisHistory.objects.filter(user=request.user).count()
    return render(
        request,
        "accounts/history_clear_confirm.html",
        {
            "active_page": "dashboard",
            "count": count,
        },
    )


@login_required(login_url=settings.LOGIN_URL)
@require_POST
def history_clear_view(request: HttpRequest) -> HttpResponse:
    AnalysisHistory.objects.filter(user=request.user).delete()
    messages.success(request, "Your analysis history has been cleared.")
    return redirect("dashboard:index")


@login_required(login_url=settings.LOGIN_URL)
@require_http_methods(["GET", "POST"])
def account_settings_view(request: HttpRequest) -> HttpResponse:
    user = request.user
    initial_name = _display_full_name(user)
    if request.method == "POST":
        form = AccountSettingsForm(request.POST)
        if form.is_valid():
            _apply_full_name(user, form.cleaned_data["full_name"])
            messages.success(request, "Your name has been updated.")
            return redirect("accounts:settings")
    else:
        form = AccountSettingsForm(initial={"full_name": initial_name})

    verified = user_is_verified(user)
    return render(
        request,
        "accounts/settings.html",
        {
            "active_page": "settings",
            "form": form,
            "email": user.email,
            "email_verified": verified,
            "account_created": user.date_joined,
        },
    )


def verification_required_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        if user_is_verified(request.user):
            return redirect("/analyze/")
        pending_email = request.user.email or request.user.username
        request.session["verification_pending_email"] = pending_email
        return render(
            request,
            "accounts/verification_required.html",
            {
                "active_page": "login",
                "email": pending_email,
                "can_resend": True,
            },
        )

    pending = (request.session.get("verification_pending_email") or "").strip()
    if not pending:
        messages.info(request, "Log in to continue, or confirm your signup from the verification email.")
        return redirect(settings.LOGIN_URL)

    return render(
        request,
        "accounts/verification_required.html",
        {
            "active_page": "login",
            "email": pending,
            "can_resend": True,
        },
    )


@require_POST
def verification_resend_view(request: HttpRequest) -> HttpResponse:
    """Resend verification; same outcome message always (no email enumeration)."""
    user_to_mail: User | None = None
    if request.user.is_authenticated:
        if user_is_verified(request.user):
            return redirect("/analyze/")
        user_to_mail = request.user
    else:
        raw = (request.session.get("verification_pending_email") or "").strip().lower()
        if raw:
            user_to_mail = User.objects.filter(username__iexact=raw).first()
            if user_to_mail is None:
                user_to_mail = User.objects.filter(email__iexact=raw).first()

    if user_to_mail is not None and not user_is_verified(user_to_mail):
        send_verification_email(request, user_to_mail)
        request.session["verification_pending_email"] = user_to_mail.email or user_to_mail.username

    messages.success(
        request,
        "If there is an account pending verification for that email, we sent a new verification link.",
    )
    return redirect("accounts:verification-sent")


def verification_sent_view(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "accounts/verification_sent.html",
        {
            "active_page": "signup",
            "email": request.session.get("verification_pending_email", ""),
            "debug_verification_url": request.session.get("last_verification_url", "") if settings.DEBUG else "",
        },
    )


def verify_email_view(request: HttpRequest, uidb64: str, token: str) -> HttpResponse:
    user = verify_email_token(uidb64=uidb64, token=token)
    if user is None:
        return render(request, "accounts/verification_invalid.html", {"active_page": "login"}, status=400)
    next_url = request.session.pop("verification_next_url", "/analyze/")
    request.session.pop("verification_pending_email", None)
    request.session.pop("last_verification_url", None)
    login(request, user)
    return redirect(next_url if _safe_next_candidate(request, next_url) else "/analyze/")


def google_login_view(request: HttpRequest) -> HttpResponse:
    config = google_oauth_config()
    if not config.is_configured:
        return render(request, "accounts/google_unavailable.html", {"active_page": "login"}, status=503)
    return render(request, "accounts/google_unavailable.html", {"active_page": "login"}, status=501)
