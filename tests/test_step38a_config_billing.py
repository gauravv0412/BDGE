"""Step 38A — runtime config, plans, verse threshold wiring, billing quota."""

from __future__ import annotations

import json
import os

import django
import pytest
from django.contrib.auth.models import User
from django.test import Client

from app.billing.models import MonthlyPresentationUsage
from app.billing.services import current_period_key, get_or_create_billing_profile, presentation_usage_count
from app.config.runtime_config import (
    clear_runtime_config_caches,
    get_feedback_comment_max_len,
    get_plan,
    get_plan_definitions,
    get_runtime_config,
    get_verse_match_score_threshold,
)
from app.core.models import DimensionScore, EthicalDimensions
from app.feedback.validation import FeedbackValidationError, validate_feedback_payload
from app.verses.retriever import retrieve_verse
from app.verses.scorer import RetrievalContext

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.django_test_settings")
django.setup()


def _dims() -> EthicalDimensions:
    return EthicalDimensions(
        dharma_duty=DimensionScore(score=3, note="duty"),
        satya_truth=DimensionScore(score=1, note="truth"),
        ahimsa_nonharm=DimensionScore(score=0, note="nonharm"),
        nishkama_detachment=DimensionScore(score=4, note="detachment"),
        shaucha_intent=DimensionScore(score=0, note="intent"),
        sanyama_restraint=DimensionScore(score=3, note="restraint"),
        lokasangraha_welfare=DimensionScore(score=0, note="welfare"),
        viveka_discernment=DimensionScore(score=2, note="discernment"),
    )


def _ctx247() -> RetrievalContext:
    return RetrievalContext(
        dilemma_id="WTEST",
        classification="Mixed",
        primary_driver="test",
        hidden_risk="test",
        dominant_dimensions=["nishkama_detachment"],
        theme_tags=["duty", "detachment", "action"],
        applies_signals=["outcome-anxiety", "duty-conflict"],
        blocker_signals=[],
        missing_facts=[],
    )


def test_default_runtime_config_loads() -> None:
    cfg = get_runtime_config()
    assert cfg.verse_match_score_threshold == 6
    assert cfg.max_missing_facts == 6
    assert cfg.feedback_comment_max_len == 500
    assert cfg.dashboard_history_page_size == 20


def test_plan_definitions_include_free_plus_pro() -> None:
    plans = get_plan_definitions()
    assert set(plans) >= {"free", "plus", "pro"}
    assert get_plan("free").monthly_analysis_limit == 5


def test_plan_limits_override_via_env_json(monkeypatch) -> None:
    clear_runtime_config_caches()
    monkeypatch.setenv(
        "WISDOMIZE_PLANS_JSON",
        json.dumps({"free": {"monthly_analysis_limit": 12, "price_display": "₹0 (test)"}}),
    )
    assert get_plan("free").monthly_analysis_limit == 12
    clear_runtime_config_caches()
    monkeypatch.delenv("WISDOMIZE_PLANS_JSON", raising=False)


def test_invalid_plans_json_raises(monkeypatch) -> None:
    clear_runtime_config_caches()
    monkeypatch.setenv("WISDOMIZE_PLANS_JSON", "{not json")
    with pytest.raises(ValueError, match="WISDOMIZE_PLANS_JSON"):
        get_plan_definitions()
    monkeypatch.delenv("WISDOMIZE_PLANS_JSON", raising=False)
    clear_runtime_config_caches()


def test_pricing_and_billing_share_plan_labels() -> None:
    u = User.objects.create_user("billing-plan-user", "billing-plan-user@example.com", "pw12345")
    c = Client()
    c.force_login(u)
    phtml = c.get("/pricing/").content.decode("utf-8")
    bhtml = c.get("/billing/").content.decode("utf-8")
    assert "Free" in phtml and "Free" in bhtml
    assert "Plus" in phtml and "Plus" in bhtml
    assert u.username in bhtml or "Free plan" in bhtml or "plan" in bhtml.lower()


def test_verse_threshold_default_preserves_247_attachment(monkeypatch) -> None:
    monkeypatch.delenv("WISDOMIZE_VERSE_MATCH_SCORE_THRESHOLD", raising=False)
    r = retrieve_verse("I feel anxious about outcome and duty conflict.", _dims(), context_override=_ctx247())
    assert r["verse_match"] is not None
    assert r["verse_match"].verse_ref == "2.47"


def test_verse_threshold_raise_suppresses_attachment(monkeypatch) -> None:
    monkeypatch.setenv("WISDOMIZE_VERSE_MATCH_SCORE_THRESHOLD", "20")
    try:
        r = retrieve_verse("I feel anxious about outcome and duty conflict.", _dims(), context_override=_ctx247())
        assert r["verse_match"] is None
        assert r["closest_teaching"]
    finally:
        monkeypatch.delenv("WISDOMIZE_VERSE_MATCH_SCORE_THRESHOLD", raising=False)


def test_feedback_respects_configured_comment_max(monkeypatch) -> None:
    monkeypatch.setenv("WISDOMIZE_FEEDBACK_COMMENT_MAX_LEN", "10")
    try:
        assert get_feedback_comment_max_len() == 10
        base = {
            "result_id": "x" * 10,
            "route": "presentation",
            "comment": "12345678901",
        }
        with pytest.raises(FeedbackValidationError):
            validate_feedback_payload(base)
    finally:
        monkeypatch.delenv("WISDOMIZE_FEEDBACK_COMMENT_MAX_LEN", raising=False)


def test_get_verse_match_score_threshold_matches_helper(monkeypatch) -> None:
    monkeypatch.setenv("WISDOMIZE_VERSE_MATCH_SCORE_THRESHOLD", "7")
    try:
        assert get_verse_match_score_threshold() == 7
    finally:
        monkeypatch.delenv("WISDOMIZE_VERSE_MATCH_SCORE_THRESHOLD", raising=False)


def test_new_user_gets_free_plan_and_zero_usage() -> None:
    u = User.objects.create_user("quota-new", "quota-new@example.com", "pw12345")
    p = get_or_create_billing_profile(u)
    assert p.plan_key == "free"
    assert presentation_usage_count(u, current_period_key()) == 0


def test_billing_page_requires_login() -> None:
    r = Client().get("/billing/")
    assert r.status_code == 302


def test_presentation_increments_usage_once_per_success(monkeypatch) -> None:
    from tests.test_accounts_auth_gate import _logged_in_client, _presentation_payload, _sample_engine_response

    clear_runtime_config_caches()
    monkeypatch.setenv(
        "WISDOMIZE_PLANS_JSON",
        json.dumps({"free": {"monthly_analysis_limit": 50, "price_display": "₹0"}}),
    )
    monkeypatch.setattr("app.transport.django_api.handle_engine_request", lambda payload: _sample_engine_response())
    client = _logged_in_client("usage-counter-user")
    u = User.objects.get(username="usage-counter-user")
    period = current_period_key()
    assert presentation_usage_count(u, period) == 0
    r = client.post("/api/v1/analyze/presentation", data=json.dumps(_presentation_payload()), content_type="application/json")
    assert r.status_code == 200
    assert presentation_usage_count(u, period) == 1
    clear_runtime_config_caches()
    monkeypatch.delenv("WISDOMIZE_PLANS_JSON", raising=False)


def test_analyze_endpoint_does_not_increment_usage(monkeypatch) -> None:
    from tests.test_accounts_auth_gate import _logged_in_client, _presentation_payload, _sample_engine_response

    monkeypatch.setattr("app.transport.django_api.handle_engine_request", lambda payload: _sample_engine_response())
    client = _logged_in_client("usage-analyze-only")
    u = User.objects.get(username="usage-analyze-only")
    period = current_period_key()
    before = presentation_usage_count(u, period)
    r = client.post("/api/v1/analyze", data=json.dumps(_presentation_payload()), content_type="application/json")
    assert r.status_code == 200
    assert presentation_usage_count(u, period) == before


def test_disabled_free_plan_blocks_presentation_without_calling_engine(monkeypatch) -> None:
    from tests.test_accounts_auth_gate import _logged_in_client, _presentation_payload

    clear_runtime_config_caches()
    monkeypatch.setenv(
        "WISDOMIZE_PLANS_JSON",
        json.dumps({"free": {"enabled": False, "label": "Free", "monthly_analysis_limit": 50, "price_display": "₹0"}}),
    )
    called: list[str] = []

    def _stub_engine(payload):  # noqa: ANN001
        called.append("engine")
        from tests.test_accounts_auth_gate import _sample_engine_response

        return _sample_engine_response(dilemma_id="should-not-run")

    monkeypatch.setattr("app.transport.django_api.handle_engine_request", _stub_engine)
    client = _logged_in_client("disabled-plan-presentation-user")
    r = client.post("/api/v1/analyze/presentation", data=json.dumps(_presentation_payload()), content_type="application/json")
    assert r.status_code == 429
    assert called == []
    body = r.json()
    assert body["error"]["code"] == "usage_limit_reached"
    msg = body["error"]["message"]
    assert "support" in msg.lower() or "not available" in msg.lower()
    assert "traceback" not in msg.lower()
    assert "keyerror" not in msg.lower()
    clear_runtime_config_caches()
    monkeypatch.delenv("WISDOMIZE_PLANS_JSON", raising=False)


def test_over_quota_blocks_before_engine(monkeypatch) -> None:
    from tests.test_accounts_auth_gate import _logged_in_client, _presentation_payload

    clear_runtime_config_caches()
    monkeypatch.setenv(
        "WISDOMIZE_PLANS_JSON",
        json.dumps({"free": {"monthly_analysis_limit": 1, "price_display": "₹0"}}),
    )
    called: list[str] = []

    def _boom(payload):  # noqa: ANN001
        called.append("engine")
        from tests.test_accounts_auth_gate import _sample_engine_response

        return _sample_engine_response()

    monkeypatch.setattr("app.transport.django_api.handle_engine_request", _boom)
    client = _logged_in_client("quota-block-user")
    assert client.post("/api/v1/analyze/presentation", data=json.dumps(_presentation_payload()), content_type="application/json").status_code == 200
    assert called == ["engine"]
    r2 = client.post("/api/v1/analyze/presentation", data=json.dumps(_presentation_payload()), content_type="application/json")
    assert r2.status_code == 429
    body = r2.json()
    assert body["error"]["code"] == "usage_limit_reached"
    assert "billing" in body["error"]["message"].lower() or "month" in body["error"]["message"].lower()
    assert len(called) == 1
    u = User.objects.get(username="quota-block-user")
    assert MonthlyPresentationUsage.objects.filter(user=u, year_month=current_period_key()).count() == 1
    clear_runtime_config_caches()
    monkeypatch.delenv("WISDOMIZE_PLANS_JSON", raising=False)


def test_over_quota_does_not_create_second_history_row(monkeypatch) -> None:
    from app.accounts.models import AnalysisHistory
    from tests.test_accounts_auth_gate import _logged_in_client, _presentation_payload, _sample_engine_response

    clear_runtime_config_caches()
    monkeypatch.setenv(
        "WISDOMIZE_PLANS_JSON",
        json.dumps({"free": {"monthly_analysis_limit": 1, "price_display": "₹0"}}),
    )
    monkeypatch.setattr("app.transport.django_api.handle_engine_request", lambda payload: _sample_engine_response())
    client = _logged_in_client("quota-history-user")
    client.post("/api/v1/analyze/presentation", data=json.dumps(_presentation_payload()), content_type="application/json")
    first_count = AnalysisHistory.objects.filter(user__username="quota-history-user").count()
    client.post("/api/v1/analyze/presentation", data=json.dumps(_presentation_payload()), content_type="application/json")
    assert AnalysisHistory.objects.filter(user__username="quota-history-user").count() == first_count
    clear_runtime_config_caches()
    monkeypatch.delenv("WISDOMIZE_PLANS_JSON", raising=False)


def test_failed_presentation_does_not_increment_usage(monkeypatch) -> None:
    from tests.test_accounts_auth_gate import _logged_in_client, _presentation_payload

    monkeypatch.setattr(
        "app.transport.django_api.handle_engine_request",
        lambda payload: __import__("app.engine.analyzer", fromlist=["build_engine_error_response"]).build_engine_error_response(
            code="request_validation_failed", message="bad"
        ),
    )
    client = _logged_in_client("usage-fail-user")
    u = User.objects.get(username="usage-fail-user")
    period = current_period_key()
    before = presentation_usage_count(u, period)
    r = client.post("/api/v1/analyze/presentation", data=json.dumps(_presentation_payload()), content_type="application/json")
    assert r.status_code == 400
    assert presentation_usage_count(u, period) == before
