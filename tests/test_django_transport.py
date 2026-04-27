"""Thin Django transport-layer contract tests (Step 12)."""

from __future__ import annotations

import json
import logging
import os
import re

import django
from django.test import Client
import pytest

from app.core.models import EngineAnalyzeErrorResponse, EngineAnalyzeResponse, WisdomizeEngineOutput
from app.core.validator import validate_against_output_schema, validate_against_schema
from app.engine.analyzer import build_engine_error_response

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.django_test_settings")
django.setup()


def _success_request_payload() -> dict[str, str]:
    return {
        "dilemma": "Another synthetic dilemma for the analyzer stub path, long enough for schema.",
        "dilemma_id": "dj-transport-01",
        "contract_version": "1.0",
    }


def _assert_key_order(body: dict[str, object], expected_order: list[str]) -> None:
    assert list(body.keys()) == expected_order


def _json_logs(caplog: pytest.LogCaptureFixture, *, event: str) -> list[dict[str, object]]:
    payloads: list[dict[str, object]] = []
    for record in caplog.records:
        if not isinstance(record.msg, str):
            continue
        try:
            payload = json.loads(record.msg)
        except json.JSONDecodeError:
            continue
        if payload.get("event") == event:
            payloads.append(payload)
    return payloads


def _sample_success_response() -> EngineAnalyzeResponse:
    output = WisdomizeEngineOutput.model_validate(
        {
            "dilemma_id": "dj-transport-01",
            "dilemma": "Another synthetic dilemma for the analyzer stub path, long enough for schema.",
            "verdict_sentence": "This option appears practical but carries unresolved ethical instability.",
            "classification": "Mixed",
            "alignment_score": 10,
            "confidence": 0.7,
            "internal_driver": {
                "primary": "Fear of short-term reputational loss",
                "hidden_risk": "Normalizing convenience over truth",
            },
            "core_reading": "There is awareness of right action, but pressure skews execution.",
            "gita_analysis": "The action is mixed because intention and method are not fully aligned.",
            "verse_match": None,
            "closest_teaching": "Act from duty and truth without clinging to immediate outcomes.",
            "if_you_continue": {
                "short_term": "Immediate tension may reduce, but ethical ambiguity remains active.",
                "long_term": "Repeated compromises can weaken trust and inner clarity.",
            },
            "counterfactuals": {
                "clearly_adharmic_version": {
                    "assumed_context": "Facts are hidden to protect image and avoid scrutiny.",
                    "decision": "Conceal material details.",
                    "why": "This prioritizes self-protection over duty and truth.",
                },
                "clearly_dharmic_version": {
                    "assumed_context": "Facts are disclosed with accountability and corrective action.",
                    "decision": "Report the issue transparently.",
                    "why": "This aligns duty with truth while reducing future harm.",
                },
            },
            "higher_path": "Choose transparent correction now to preserve integrity over time.",
            "ethical_dimensions": {
                "dharma_duty": {"score": 1, "note": "Duty is partially acknowledged."},
                "satya_truth": {"score": 1, "note": "Truth is constrained by fear."},
                "ahimsa_nonharm": {"score": 1, "note": "Near-term harm is reduced, long-term risk grows."},
                "nishkama_detachment": {"score": 0, "note": "Outcome-anxiety still drives choice."},
                "shaucha_intent": {"score": 0, "note": "Intent is mixed between care and protection."},
                "sanyama_restraint": {"score": 1, "note": "Some restraint appears under pressure."},
                "lokasangraha_welfare": {"score": 1, "note": "Collective trust remains vulnerable."},
                "viveka_discernment": {"score": 1, "note": "Discernment is present but not decisive."},
            },
            "missing_facts": [],
            "share_layer": {
                "anonymous_share_title": "Pressure, truth, and duty",
                "card_quote": "Short-term ease can become long-term ethical debt.",
                "reflective_question": "What choice preserves truth after the pressure passes?",
            },
        }
    )
    return EngineAnalyzeResponse.model_validate(
        {
            "meta": {
                "contract_version": "1.0",
                "engine_version": "2.1",
                "semantic_mode_default": "stub_default",
            },
            "output": output.model_dump(mode="json"),
        }
    )


def test_django_analyze_success_snapshot_200(monkeypatch) -> None:
    monkeypatch.setattr("app.transport.django_api.handle_engine_request", lambda payload: _sample_success_response())
    client = Client()
    response = client.post(
        "/api/v1/analyze",
        data=json.dumps(_success_request_payload()),
        content_type="application/json",
    )
    assert response.status_code == 200
    assert response["Content-Type"].startswith("application/json")
    assert response["X-Request-ID"]
    body = response.json()
    _assert_key_order(body, ["meta", "output"])
    _assert_key_order(body["meta"], ["contract_version", "engine_version", "semantic_mode_default"])
    assert body["meta"]["contract_version"] == "1.0"
    assert body["meta"]["engine_version"] == "2.1"
    assert body["meta"]["semantic_mode_default"] == "stub_default"
    assert body["output"]["dilemma_id"] == "dj-transport-01"
    assert body["output"]["dilemma"] == _success_request_payload()["dilemma"]
    assert body["output"]["classification"] in {
        "Dharmic",
        "Adharmic",
        "Mixed",
        "Context-dependent",
        "Insufficient information",
    }

    # Schema-aware: output payload must remain valid against the canonical output contract.
    output_ok, output_errors = validate_against_output_schema(body["output"])
    assert output_ok, output_errors

    # Schema-aware: success envelope shape remains stable for public transport.
    success_schema = {
        "type": "object",
        "required": ["meta", "output"],
        "additionalProperties": False,
        "properties": {
            "meta": {
                "type": "object",
                "required": ["contract_version", "engine_version", "semantic_mode_default"],
                "additionalProperties": False,
                "properties": {
                    "contract_version": {"type": "string"},
                    "engine_version": {"type": "string"},
                    "semantic_mode_default": {"type": "string"},
                },
            },
            "output": {"type": "object"},
        },
    }
    success_ok, success_errors = validate_against_schema(body, success_schema)
    assert success_ok, success_errors
    EngineAnalyzeResponse.model_validate(body)


def test_django_analyze_presentation_success_adds_internal_view_model(monkeypatch) -> None:
    monkeypatch.setattr("app.transport.django_api.handle_engine_request", lambda payload: _sample_success_response())
    client = Client()
    response = client.post(
        "/api/v1/analyze/presentation",
        data=json.dumps(_success_request_payload()),
        content_type="application/json",
    )
    assert response.status_code == 200
    assert response["X-Request-ID"]
    body = response.json()
    _assert_key_order(body, ["meta", "output", "presentation"])
    assert body["output"]["dilemma_id"] == "dj-transport-01"
    assert body["presentation"]["meta"]["public_schema_changed"] is False
    assert body["presentation"]["presentation_mode"] == "standard"
    assert body["presentation"]["verdict_card"]["primary_text"] == body["output"]["verdict_sentence"]
    assert body["presentation"]["guidance_card"]["title"] == "Closest Gita Lens"
    assert body["presentation"]["share_card"]["needs_copy_refinement"] is False

    output_ok, output_errors = validate_against_output_schema(body["output"])
    assert output_ok, output_errors
    EngineAnalyzeResponse.model_validate({"meta": body["meta"], "output": body["output"]})


def test_django_analyze_invalid_request_snapshot_400() -> None:
    client = Client()
    response = client.post(
        "/api/v1/analyze",
        data=json.dumps(
            {
                "dilemma": "too short",
                "contract_version": "1.0",
            }
        ),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert response["X-Request-ID"]
    body = response.json()
    _assert_key_order(body, ["meta", "error"])
    _assert_key_order(body["meta"], ["contract_version", "engine_version", "semantic_mode_default"])
    _assert_key_order(body["error"], ["code", "message"])
    assert body["error"]["code"] == "request_validation_failed"
    assert body["meta"]["contract_version"] == "1.0"
    assert body["error"]["message"]
    EngineAnalyzeErrorResponse.model_validate(body)


def test_django_analyze_malformed_json_snapshot_400() -> None:
    client = Client()
    response = client.post(
        "/api/v1/analyze",
        data="{not-json",
        content_type="application/json",
    )
    assert response.status_code == 400
    assert response["X-Request-ID"]
    body = response.json()
    _assert_key_order(body, ["meta", "error"])
    _assert_key_order(body["meta"], ["contract_version", "engine_version", "semantic_mode_default"])
    _assert_key_order(body["error"], ["code", "message"])
    assert body["error"]["code"] == "request_validation_failed"
    assert body["error"]["message"] == "Malformed JSON payload."
    EngineAnalyzeErrorResponse.model_validate(body)


def test_django_analyze_internal_failure_snapshot_500(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.transport.django_api.handle_engine_request",
        lambda payload: build_engine_error_response(
            code="engine_execution_failed",
            message="Synthetic internal failure for transport test.",
        ),
    )
    client = Client()
    response = client.post(
        "/api/v1/analyze",
        data=json.dumps(
            {
                **_success_request_payload(),
                "dilemma_id": "dj-transport-02",
            }
        ),
        content_type="application/json",
    )
    assert response.status_code == 500
    assert response["Content-Type"].startswith("application/json")
    assert response["X-Request-ID"]
    body = response.json()
    _assert_key_order(body, ["meta", "error"])
    _assert_key_order(body["meta"], ["contract_version", "engine_version", "semantic_mode_default"])
    _assert_key_order(body["error"], ["code", "message"])
    assert body["error"]["code"] == "engine_execution_failed"
    assert body["error"]["message"] == "Internal engine failure."
    assert body["meta"]["contract_version"] == "1.0"
    assert body["meta"]["engine_version"] == "2.1"
    EngineAnalyzeErrorResponse.model_validate(body)


def test_django_analyze_unsupported_contract_version_snapshot_400() -> None:
    client = Client()
    response = client.post(
        "/api/v1/analyze",
        data=json.dumps(
            {
                **_success_request_payload(),
                "contract_version": "2.0",
            }
        ),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert response["X-Request-ID"]
    body = response.json()
    _assert_key_order(body, ["meta", "error"])
    _assert_key_order(body["meta"], ["contract_version", "engine_version", "semantic_mode_default"])
    _assert_key_order(body["error"], ["code", "message"])
    assert body["error"]["code"] == "request_validation_failed"
    assert "Unsupported contract_version" in body["error"]["message"]
    assert "'2.0'" in body["error"]["message"]
    EngineAnalyzeErrorResponse.model_validate(body)


def test_django_analyze_contract_version_missing_or_invalid_type_or_empty_400() -> None:
    client = Client()
    bad_payloads = [
        ({k: v for k, v in _success_request_payload().items() if k != "contract_version"}, "contract_version is required."),
        ({**_success_request_payload(), "contract_version": 1}, "contract_version must be a non-empty string."),
        ({**_success_request_payload(), "contract_version": ""}, "contract_version must be a non-empty string."),
        ({**_success_request_payload(), "contract_version": "   "}, "contract_version must be a non-empty string."),
    ]
    for payload, expected_message in bad_payloads:
        response = client.post("/api/v1/analyze", data=json.dumps(payload), content_type="application/json")
        assert response.status_code == 400
        body = response.json()
        assert body["error"]["code"] == "request_validation_failed"
        assert body["error"]["message"] == expected_message
        assert response["X-Request-ID"]
        EngineAnalyzeErrorResponse.model_validate(body)


def test_django_error_envelope_schema_stable_across_error_paths() -> None:
    client = Client()
    error_schema = {
        "type": "object",
        "required": ["meta", "error"],
        "additionalProperties": False,
        "properties": {
            "meta": {
                "type": "object",
                "required": ["contract_version", "engine_version", "semantic_mode_default"],
                "additionalProperties": False,
                "properties": {
                    "contract_version": {"type": "string"},
                    "engine_version": {"type": "string"},
                    "semantic_mode_default": {"type": "string"},
                },
            },
            "error": {
                "type": "object",
                "required": ["code", "message"],
                "additionalProperties": False,
                "properties": {
                    "code": {"type": "string"},
                    "message": {"type": "string"},
                },
            },
        },
    }
    responses = [
        client.post(
            "/api/v1/analyze",
            data=json.dumps({"dilemma": "too short", "contract_version": "1.0"}),
            content_type="application/json",
        ),
        client.post("/api/v1/analyze", data="{not-json", content_type="application/json"),
        client.post(
            "/api/v1/analyze",
            data=json.dumps({**_success_request_payload(), "contract_version": "2.0"}),
            content_type="application/json",
        ),
    ]
    for response in responses:
        body = response.json()
        ok, errors = validate_against_schema(body, error_schema)
        assert ok, errors


def test_django_analyze_escaped_internal_failure_is_json_500(monkeypatch) -> None:
    long_exception_text = "x" * 1200

    def _raise_unhandled(_payload):
        raise RuntimeError(long_exception_text)

    monkeypatch.setattr("app.transport.django_api.handle_engine_request", _raise_unhandled)
    client = Client()
    response = client.post(
        "/api/v1/analyze",
        data=json.dumps(_success_request_payload()),
        content_type="application/json",
    )
    assert response.status_code == 500
    assert response["Content-Type"].startswith("application/json")
    assert response["X-Request-ID"]
    body = response.json()
    _assert_key_order(body, ["meta", "error"])
    _assert_key_order(body["error"], ["code", "message"])
    assert body["error"]["code"] == "engine_execution_failed"
    assert body["error"]["message"] == "Internal engine failure."
    assert long_exception_text not in body["error"]["message"]
    assert len(body["error"]["message"]) <= 500
    EngineAnalyzeErrorResponse.model_validate(body)


def test_django_request_id_passthrough_header_success(monkeypatch) -> None:
    inbound_request_id = "client-provided-req-id_123"
    monkeypatch.setattr("app.transport.django_api.handle_engine_request", lambda payload: _sample_success_response())
    client = Client()
    response = client.post(
        "/api/v1/analyze",
        data=json.dumps(_success_request_payload()),
        content_type="application/json",
        HTTP_X_REQUEST_ID=inbound_request_id,
    )
    assert response.status_code == 200
    assert response["X-Request-ID"] == inbound_request_id


def test_django_request_id_generated_when_header_missing(monkeypatch) -> None:
    monkeypatch.setattr("app.transport.django_api.handle_engine_request", lambda payload: _sample_success_response())
    client = Client()
    response = client.post(
        "/api/v1/analyze",
        data=json.dumps(_success_request_payload()),
        content_type="application/json",
    )
    assert response.status_code == 200
    request_id = response["X-Request-ID"]
    assert bool(re.fullmatch(r"[a-f0-9]{32}", request_id))


def test_django_request_id_invalid_header_replaced_with_generated_id(monkeypatch) -> None:
    monkeypatch.setattr("app.transport.django_api.handle_engine_request", lambda payload: _sample_success_response())
    client = Client()
    response = client.post(
        "/api/v1/analyze",
        data=json.dumps(_success_request_payload()),
        content_type="application/json",
        HTTP_X_REQUEST_ID="bad request id with spaces",
    )
    assert response.status_code == 200
    request_id = response["X-Request-ID"]
    assert request_id != "bad request id with spaces"
    assert bool(re.fullmatch(r"[a-f0-9]{32}", request_id))


def test_django_request_id_header_stable_on_error_response() -> None:
    inbound_request_id = "req-for-error-path-001"
    client = Client()
    response = client.post(
        "/api/v1/analyze",
        data=json.dumps({"dilemma": "too short", "contract_version": "1.0"}),
        content_type="application/json",
        HTTP_X_REQUEST_ID=inbound_request_id,
    )
    assert response.status_code == 400
    assert response["X-Request-ID"] == inbound_request_id


def test_django_structured_access_log_emitted_on_success(monkeypatch, caplog: pytest.LogCaptureFixture) -> None:
    monkeypatch.setattr("app.transport.django_api.handle_engine_request", lambda payload: _sample_success_response())
    caplog.set_level(logging.INFO, logger="app.transport.django_api")
    client = Client()
    response = client.post(
        "/api/v1/analyze",
        data=json.dumps(_success_request_payload()),
        content_type="application/json",
        HTTP_X_REQUEST_ID="access-log-test-1",
    )
    assert response.status_code == 200
    access_logs = _json_logs(caplog, event="transport.access")
    assert access_logs
    access = access_logs[-1]
    assert access["request_id"] == "access-log-test-1"
    assert access["path"] == "/api/v1/analyze"
    assert access["method"] == "POST"
    assert access["status_code"] == 200
    assert access["outcome"] == "success"
    assert isinstance(access["duration_ms"], int)
    assert access["duration_ms"] >= 0
    assert access["contract_version"] == "1.0"


def test_django_structured_access_log_emitted_on_malformed_json_400(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger="app.transport.django_api")
    client = Client()
    response = client.post(
        "/api/v1/analyze",
        data="{not-json",
        content_type="application/json",
        HTTP_X_REQUEST_ID="access-log-400-test",
    )
    assert response.status_code == 400
    access_logs = _json_logs(caplog, event="transport.access")
    assert access_logs
    access = access_logs[-1]
    assert access["request_id"] == "access-log-400-test"
    assert access["path"] == "/api/v1/analyze"
    assert access["method"] == "POST"
    assert access["status_code"] == 400
    assert access["outcome"] == "request_validation_failed"
    assert access["contract_version"] is None


def test_django_structured_error_log_emitted_on_escaped_failure(
    monkeypatch, caplog: pytest.LogCaptureFixture
) -> None:
    long_exception_text = "z" * 1200

    def _raise_unhandled(_payload):
        raise RuntimeError(long_exception_text)

    monkeypatch.setattr("app.transport.django_api.handle_engine_request", _raise_unhandled)
    caplog.set_level(logging.INFO, logger="app.transport.django_api")
    client = Client()
    response = client.post(
        "/api/v1/analyze",
        data=json.dumps(_success_request_payload()),
        content_type="application/json",
        HTTP_X_REQUEST_ID="error-log-test-1",
    )
    assert response.status_code == 500
    assert response["X-Request-ID"] == "error-log-test-1"
    body = response.json()
    assert body["error"]["message"] == "Internal engine failure."
    assert long_exception_text not in body["error"]["message"]

    error_logs = _json_logs(caplog, event="transport.error")
    assert error_logs
    error_log = error_logs[-1]
    assert error_log["request_id"] == "error-log-test-1"
    assert error_log["path"] == "/api/v1/analyze"
    assert error_log["method"] == "POST"
    assert error_log["contract_version"] == "1.0"
    assert error_log["error_type"] == "RuntimeError"
    assert len(error_log["error_message"]) <= 500
    assert long_exception_text[:500] == error_log["error_message"]

    access_logs = _json_logs(caplog, event="transport.access")
    assert access_logs
    access_log = access_logs[-1]
    assert access_log["request_id"] == "error-log-test-1"
    assert access_log["status_code"] == 500
    assert access_log["outcome"] == "engine_execution_failed"
