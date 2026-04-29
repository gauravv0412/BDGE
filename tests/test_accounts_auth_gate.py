"""Account and product gate tests for Wisdomize (signup, verification, dashboards, APIs)."""

from __future__ import annotations

import json
import os

import django
from django.contrib import admin
from django.contrib.auth.models import User
from django.core import mail
from django.test import Client

from app.accounts.models import AccountProfile, AnalysisHistory
from app.accounts.services import (
    ensure_profile,
    provision_google_user,
    verification_token_for,
)
from app.core.models import EngineAnalyzeResponse, WisdomizeEngineOutput

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.django_test_settings")
django.setup()


def _create_user(username: str = "auth-user", password: str = "test-pass-12345") -> User:
    user = User.objects.create_user(username=username, email=f"{username}@example.com", password=password)
    ensure_profile(user, verified=True, provider="password")
    return user


def _logged_in_client(username: str = "auth-user") -> Client:
    _create_user(username=username)
    client = Client()
    assert client.login(username=username, password="test-pass-12345")
    return client


def _presentation_payload() -> dict[str, str]:
    return {
        "dilemma": "Another synthetic dilemma for the analyzer stub path, long enough for schema.",
        "contract_version": "1.0",
    }


def _sample_engine_response(*, dilemma_id: str = "auth-presentation-1") -> EngineAnalyzeResponse:
    output = WisdomizeEngineOutput.model_validate(
        {
            "dilemma_id": dilemma_id,
            "dilemma": _presentation_payload()["dilemma"],
            "verdict_sentence": "Choose truthful action with disciplined intent.",
            "classification": "Mixed",
            "alignment_score": 12,
            "confidence": 0.7,
            "internal_driver": {"primary": "Fear", "hidden_risk": "Self-justification"},
            "core_reading": "The conflict is between convenience and integrity.",
            "gita_analysis": "Duty and truth should remain aligned.",
            "verse_match": None,
            "closest_teaching": "Act from duty without clinging to outcomes.",
            "if_you_continue": {"short_term": "Relief with residue.", "long_term": "Compounded ethical debt."},
            "counterfactuals": {
                "clearly_adharmic_version": {"assumed_context": "Hide facts", "decision": "Conceal", "why": "Avoid blame"},
                "clearly_dharmic_version": {"assumed_context": "Disclose facts", "decision": "Report", "why": "Protect trust"},
            },
            "higher_path": "Choose transparent correction.",
            "ethical_dimensions": {
                "dharma_duty": {"score": 1, "note": "Partially aligned"},
                "satya_truth": {"score": 1, "note": "Truth under pressure"},
                "ahimsa_nonharm": {"score": 0, "note": "Harm depends on the next step"},
                "nishkama_detachment": {"score": 1, "note": "Outcome anxiety is present"},
                "shaucha_intent": {"score": 0, "note": "Motive is mixed"},
                "sanyama_restraint": {"score": 1, "note": "Restraint is still available"},
                "lokasangraha_welfare": {"score": 0, "note": "Wider impact is limited"},
                "viveka_discernment": {"score": 1, "note": "The facts support a careful step"},
            },
            "missing_facts": [],
            "share_layer": {
                "anonymous_share_title": "Duty vs convenience",
                "card_quote": "Shortcuts become chains.",
                "reflective_question": "What action survives daylight?",
            },
        }
    )
    return EngineAnalyzeResponse.model_validate(
        {"meta": {"contract_version": "1.0", "engine_version": "2.1", "semantic_mode_default": "stub_default"}, "output": output.model_dump(mode="json")}
    )


# --- Smoke / marketing pages ---------------------------------------------------------------

def test_signup_page_returns_200_for_anonymous_users() -> None:
    response = Client().get("/accounts/signup/")
    assert response.status_code == 200
    html = response.content.decode("utf-8")
    assert "Create your Wisdomize account" in html
    assert 'name="full_name"' in html


def test_password_signup_stores_name_email_and_requires_verification() -> None:
    client = Client()
    response = client.post(
        "/accounts/signup/?next=/analyze/",
        {
            "full_name": "Mira Dev",
            "email": "mira@example.com",
            "password1": "test-pass-12345",
            "password2": "test-pass-12345",
            "next": "/analyze/",
        },
    )

    assert response.status_code == 302
    assert response["Location"] == "/accounts/verify/sent/"
    user = User.objects.get(username="mira@example.com")
    assert user.first_name == "Mira"
    assert user.is_active is False
    assert AccountProfile.objects.get(user=user).email_verified is False


def test_unverified_password_user_cannot_access_analyze() -> None:
    user = User.objects.create_user(username="unverified@example.com", email="unverified@example.com", password="test-pass-12345", is_active=False)
    ensure_profile(user, verified=False, provider="password")
    assert Client().login(username="unverified@example.com", password="test-pass-12345") is False
    response = Client().get("/analyze/")
    assert response.status_code == 302


def test_verification_link_marks_user_verified_and_logs_in() -> None:
    user = User.objects.create_user(username="verify@example.com", email="verify@example.com", password="test-pass-12345", is_active=False)
    ensure_profile(user, verified=False, provider="password")
    uid, token = verification_token_for(user)
    client = Client()
    session = client.session
    session["verification_next_url"] = "/analyze/"
    session.save()

    response = client.get(f"/accounts/verify/{uid}/{token}/")

    assert response.status_code == 302
    assert response["Location"] == "/analyze/"
    user.refresh_from_db()
    assert user.is_active is True
    assert AccountProfile.objects.get(user=user).email_verified is True


def test_login_works_and_redirects_to_safe_next() -> None:
    _create_user(username="login-user")
    client = Client()
    response = client.post(
        "/accounts/login/?next=/dashboard/",
        {"username": "login-user", "password": "test-pass-12345", "next": "/dashboard/"},
    )
    assert response.status_code == 302
    assert response["Location"] == "/dashboard/"
    assert "_auth_user_id" in client.session


def test_login_page_renders_improved_ui() -> None:
    html = Client().get("/accounts/login/").content.decode("utf-8")
    assert "Continue your Wisdomize journey" in html


def test_logout_ends_session() -> None:
    client = _logged_in_client("logout-user")
    response = client.post("/accounts/logout/")
    assert response.status_code == 302
    assert "_auth_user_id" not in client.session


def test_dashboard_redirects_anonymous_users_to_login() -> None:
    response = Client().get("/dashboard/")
    assert response.status_code == 302
    assert response["Location"].startswith("/accounts/login/")


def test_dashboard_returns_200_for_logged_in_users() -> None:
    html = _logged_in_client("dashboard-user").get("/dashboard/").content.decode("utf-8")
    assert "Your Wisdomize history will appear here." in html


def test_analyze_redirects_anonymous_users_to_login() -> None:
    response = Client().get("/analyze/")
    assert response.status_code == 302


def test_analyze_returns_200_for_logged_in_users() -> None:
    response = _logged_in_client("analyze-user").get("/analyze/")
    assert response.status_code == 200
    assert 'textarea id="dilemma"' in response.content.decode("utf-8")


def test_email_uniqueness_is_enforced() -> None:
    _create_user(username="dup@example.com")
    response = Client().post(
        "/accounts/signup/",
        {"full_name": "Duplicate User", "email": "dup@example.com", "password1": "test-pass-12345", "password2": "test-pass-12345"},
    )
    assert response.status_code == 200
    assert "already exists." in response.content.decode("utf-8")


def test_public_pages_remain_accessible_anonymously() -> None:
    for path in ["/", "/faq/", "/about/", "/pricing/", "/contact/"]:
        assert Client().get(path).status_code == 200


def test_unsafe_next_redirects_are_ignored() -> None:
    _create_user(username="safe-next-user")
    response = Client().post(
        "/accounts/login/?next=https://evil.example/analyze/",
        {"username": "safe-next-user", "password": "test-pass-12345", "next": "https://evil.example/analyze/"},
    )
    assert response.status_code == 302
    assert response["Location"] == "/analyze/"


def test_presentation_api_rejects_anonymous_requests() -> None:
    response = Client().post("/api/v1/analyze/presentation", data=json.dumps(_presentation_payload()), content_type="application/json")
    assert response.status_code == 401


def test_presentation_api_still_works_for_authenticated_users(monkeypatch) -> None:
    monkeypatch.setattr("app.transport.django_api.handle_engine_request", lambda payload: _sample_engine_response())
    response = _logged_in_client("presentation-user").post(
        "/api/v1/analyze/presentation",
        data=json.dumps(_presentation_payload()),
        content_type="application/json",
    )
    assert response.status_code == 200
    body = response.json()
    assert list(body.keys()) == ["meta", "output", "presentation"]
    assert body["output"]["dilemma_id"] == "auth-presentation-1"


def test_presentation_api_creates_history_for_authenticated_user(monkeypatch) -> None:
    monkeypatch.setattr("app.transport.django_api.handle_engine_request", lambda payload: _sample_engine_response())
    client = _logged_in_client("history-user")
    response = client.post("/api/v1/analyze/presentation", data=json.dumps(_presentation_payload()), content_type="application/json")
    assert response.status_code == 200
    user = User.objects.get(username="history-user")
    record = AnalysisHistory.objects.get(user=user)
    assert record.dilemma_id == "auth-presentation-1"
    assert record.classification == "Mixed"
    assert record.share_card_quote == "Shortcuts become chains."


def test_dashboard_shows_recent_history_and_is_user_scoped() -> None:
    owner = _create_user("owner")
    other = _create_user("other")
    AnalysisHistory.objects.create(
        user=owner,
        dilemma_text="Owner dilemma visible.",
        dilemma_id="owner-1",
        classification="Mixed",
        alignment_score=12,
        verdict_sentence="Owner verdict.",
    )
    AnalysisHistory.objects.create(
        user=other,
        dilemma_text="Other secret dilemma.",
        dilemma_id="other-1",
        classification="Dharmic",
        alignment_score=50,
        verdict_sentence="Other verdict.",
    )
    oc = Client()
    assert oc.login(username="owner", password="test-pass-12345")
    html = oc.get("/dashboard/").content.decode("utf-8")
    assert "Owner dilemma visible" in html
    assert "Other secret dilemma" not in html


def test_history_save_failure_does_not_break_analyze_response(monkeypatch) -> None:
    monkeypatch.setattr("app.transport.django_api.handle_engine_request", lambda payload: _sample_engine_response())
    monkeypatch.setattr("app.billing.services.save_analysis_history", lambda **_: (_ for _ in ()).throw(RuntimeError("history down")))
    response = _logged_in_client("history-failure").post(
        "/api/v1/analyze/presentation",
        data=json.dumps(_presentation_payload()),
        content_type="application/json",
    )
    assert response.status_code == 200


def test_history_does_not_store_provider_or_debug_payloads(monkeypatch) -> None:
    monkeypatch.setattr("app.transport.django_api.handle_engine_request", lambda payload: _sample_engine_response())
    client = _logged_in_client("history-privacy")
    client.post("/api/v1/analyze/presentation", data=json.dumps(_presentation_payload()), content_type="application/json")
    record = AnalysisHistory.objects.get(user__username="history-privacy")
    serialized = json.dumps({"dilemma_text": record.dilemma_text, "verdict_sentence": record.verdict_sentence})
    lowered = serialized.lower()
    assert "provider" not in lowered
    assert "prompt" not in lowered


def test_google_config_missing_does_not_crash() -> None:
    response = Client().get("/accounts/google/")
    assert response.status_code == 503
    assert "Google sign-in is not active yet." in response.content.decode("utf-8")


def test_google_provisioned_user_is_verified() -> None:
    user = provision_google_user(email="google@example.com", full_name="Google User", email_verified=True)
    assert AccountProfile.objects.get(user=user).email_verified is True


def test_public_api_analyze_smoke_behavior_remains_unchanged(monkeypatch) -> None:
    monkeypatch.setattr("app.transport.django_api.handle_engine_request", lambda payload: _sample_engine_response())
    response = Client().post("/api/v1/analyze", data=json.dumps(_presentation_payload()), content_type="application/json")
    assert response.status_code == 200
    assert list(response.json().keys()) == ["meta", "output"]


# --- Django admin ---------------------------------------------------------------

def test_django_admin_registers_account_models() -> None:
    import app.accounts.admin  # noqa: F401 — registers models with admin.site
    import app.billing.admin  # noqa: F401

    assert admin.site.is_registered(AccountProfile)
    assert admin.site.is_registered(AnalysisHistory)
    from app.billing.models import BillingProfile, MonthlyPresentationUsage

    assert admin.site.is_registered(BillingProfile)
    assert admin.site.is_registered(MonthlyPresentationUsage)


# --- History UX (step 36C) ---------------------------------------------------------------


def test_history_detail_requires_login() -> None:
    response = Client().get("/dashboard/history/99/")
    assert response.status_code == 302
    assert "login" in response["Location"]


def test_history_detail_owner_allowed_and_foreign_user_gets_404() -> None:
    owner = _create_user("hist-owner-x")
    other = _create_user("hist-other-x")
    record = AnalysisHistory.objects.create(
        user=owner,
        dilemma_text="Owner-only dilemma text.",
        dilemma_id="hist-99",
        classification="Mixed",
        alignment_score=5,
        verdict_sentence="Verdict ninety-nine.",
    )
    oc = Client()
    assert oc.login(username="hist-owner-x", password="test-pass-12345")
    ok_body = oc.get(f"/dashboard/history/{record.pk}/").content.decode("utf-8")
    assert "Owner-only dilemma" in ok_body
    assert "provider" not in ok_body.lower()

    bc = Client()
    assert bc.login(username="hist-other-x", password="test-pass-12345")
    assert bc.get(f"/dashboard/history/{record.pk}/").status_code == 404


def test_history_delete_post_only_owner() -> None:
    owner = _create_user("del-owner-x")
    other = _create_user("del-other-x")
    item = AnalysisHistory.objects.create(
        user=owner,
        dilemma_text="Delete me.",
        dilemma_id="hist-del-1",
        classification="Mixed",
        alignment_score=1,
        verdict_sentence="Verdict.",
    )
    oc = Client()
    assert oc.login(username="del-owner-x", password="test-pass-12345")
    assert oc.get(f"/dashboard/history/{item.pk}/delete/").status_code == 405

    bc = Client()
    assert bc.login(username="del-other-x", password="test-pass-12345")
    assert bc.post(f"/dashboard/history/{item.pk}/delete/").status_code == 404
    assert AnalysisHistory.objects.filter(pk=item.pk).exists()

    oc.post(f"/dashboard/history/{item.pk}/delete/")
    assert AnalysisHistory.objects.filter(pk=item.pk).count() == 0


def test_history_clear_requires_post_and_is_scoped() -> None:
    alice = _create_user("clear-alice-x")
    bob = _create_user("clear-bob-x")
    AnalysisHistory.objects.create(
        user=alice,
        dilemma_text="A",
        dilemma_id="clear-a",
        classification="Mixed",
        alignment_score=0,
        verdict_sentence="V",
    )
    AnalysisHistory.objects.create(
        user=bob,
        dilemma_text="B",
        dilemma_id="clear-b",
        classification="Mixed",
        alignment_score=1,
        verdict_sentence="V",
    )

    alice_client = Client()
    assert alice_client.login(username="clear-alice-x", password="test-pass-12345")
    assert alice_client.get("/dashboard/history/clear/").status_code == 405
    alice_client.post("/dashboard/history/clear/")
    assert AnalysisHistory.objects.filter(user=alice).count() == 0
    assert AnalysisHistory.objects.filter(user=bob).count() == 1


def test_account_settings_requires_login() -> None:
    assert Client().get("/accounts/settings/").status_code == 302


def test_account_settings_displays_identity_and_updates_name() -> None:
    user = _create_user("settings-user-x")
    user.first_name = "Original"
    user.save()
    client = Client()
    assert client.login(username="settings-user-x", password="test-pass-12345")
    body = client.get("/accounts/settings/").content.decode("utf-8")
    assert user.email in body

    resp = client.post("/accounts/settings/", {"full_name": "Updated Display"})
    assert resp.status_code == 302
    user.refresh_from_db()
    assert user.first_name == "Updated"


def test_account_settings_post_email_field_is_ignored() -> None:
    user = _create_user("email-lock-x")
    orig = user.email
    client = Client()
    assert client.login(username="email-lock-x", password="test-pass-12345")
    client.post("/accounts/settings/", {"full_name": "Same", "email": "evil@evil.test"})
    user.refresh_from_db()
    assert user.email == orig


def test_active_unverified_profile_redirected_from_analyze() -> None:
    user = User.objects.create_user(
        username="limbo@example.com",
        email="limbo@example.com",
        password="test-pass-12345",
        is_active=True,
    )
    ensure_profile(user, verified=False, provider="password")

    client = Client()
    assert client.login(username="limbo@example.com", password="test-pass-12345")
    response = client.get("/analyze/")
    assert response.status_code == 302
    assert "/accounts/verify/required/" in response["Location"]


def test_login_with_unverified_inactive_credentials_reaches_verify_flow() -> None:
    pending = User.objects.create_user(
        username="pending@example.com",
        email="pending@example.com",
        password="test-pass-12345",
        is_active=False,
    )
    ensure_profile(pending, verified=False, provider="password")
    resp = Client().post("/accounts/login/", {"username": "pending@example.com", "password": "test-pass-12345"})
    assert resp.status_code == 302
    assert resp["Location"].endswith("/accounts/verify/required/")


def test_verification_resend_sends_when_session_pending(monkeypatch) -> None:
    mail.outbox.clear()
    pending = User.objects.create_user(
        username="pend2@example.com",
        email="pend2@example.com",
        password="test-pass-12345",
        is_active=False,
    )
    ensure_profile(pending, verified=False, provider="password")

    client = Client()
    session = client.session
    session["verification_pending_email"] = "pend2@example.com"
    session.save()

    client.post("/accounts/verify/resend/")
    assert len(mail.outbox) == 1


def test_verification_resend_no_leak_for_unknown_email() -> None:
    mail.outbox.clear()
    client = Client()
    session = client.session
    session["verification_pending_email"] = "ghost@example.com"
    session.save()
    client.post("/accounts/verify/resend/")
    assert len(mail.outbox) == 0
