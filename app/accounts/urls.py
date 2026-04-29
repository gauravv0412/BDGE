"""URL routes for Wisdomize account pages."""

from __future__ import annotations

from django.urls import path

from app.accounts import views

app_name = "accounts"

urlpatterns = [
    path("signup/", views.signup_view, name="signup"),
    path("login/", views.login_view, name="login"),
    path("settings/", views.account_settings_view, name="settings"),
    path("verify/sent/", views.verification_sent_view, name="verification-sent"),
    path("verify/required/", views.verification_required_view, name="verification-required"),
    path("verify/resend/", views.verification_resend_view, name="verification-resend"),
    path("verify/<uidb64>/<token>/", views.verify_email_view, name="verify-email"),
    path("google/", views.google_login_view, name="google-login"),
    path("logout/", views.logout_view, name="logout"),
]
