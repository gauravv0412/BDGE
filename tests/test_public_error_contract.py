"""Public error taxonomy and message policy contract tests (Step 14)."""

from __future__ import annotations

import json
import os
from pathlib import Path

import django
from django.test import Client

from app.engine.analyzer import build_engine_error_response
from app.engine.public_errors import (
    MAX_PUBLIC_ERROR_MESSAGE_LENGTH,
    PUBLIC_ERROR_CODES,
    PUBLIC_ERROR_CONTRACT_VERSION,
    PUBLIC_ERROR_FIXED_MESSAGES,
    PUBLIC_ERROR_HTTP_STATUS,
)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.django_test_settings")
django.setup()


def test_public_error_taxonomy_codes_and_status_mapping_locked() -> None:
    assert PUBLIC_ERROR_CODES == {"request_validation_failed", "engine_execution_failed", "usage_limit_reached"}
    assert PUBLIC_ERROR_HTTP_STATUS == {
        "request_validation_failed": 400,
        "engine_execution_failed": 500,
        "usage_limit_reached": 429,
    }


def test_public_error_contract_artifact_matches_runtime_contract() -> None:
    contract_path = Path(__file__).resolve().parents[1] / "docs" / "public_error_contract_v1.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    artifact_codes = {entry["code"] for entry in contract["errors"]}
    artifact_statuses = {entry["code"]: entry["http_status"] for entry in contract["errors"]}
    artifact_fixed_messages = {
        entry["code"]: entry["fixed_message"] for entry in contract["errors"] if "fixed_message" in entry
    }
    assert artifact_codes == PUBLIC_ERROR_CODES
    assert artifact_statuses == PUBLIC_ERROR_HTTP_STATUS
    assert artifact_fixed_messages == PUBLIC_ERROR_FIXED_MESSAGES
    assert contract["contract_version"] == PUBLIC_ERROR_CONTRACT_VERSION


def test_public_error_message_policy_engine_execution_failed_is_fixed() -> None:
    resp = build_engine_error_response(
        code="engine_execution_failed",
        message="do not leak this stack detail",
    )
    dumped = resp.model_dump(mode="json")
    assert dumped["error"]["code"] == "engine_execution_failed"
    assert dumped["error"]["message"] == PUBLIC_ERROR_FIXED_MESSAGES["engine_execution_failed"]


def test_public_error_message_policy_request_validation_is_descriptive_and_bounded() -> None:
    long_message = "v" * 800
    resp = build_engine_error_response(
        code="request_validation_failed",
        message=long_message,
    )
    dumped = resp.model_dump(mode="json")
    assert dumped["error"]["code"] == "request_validation_failed"
    assert dumped["error"]["message"] == long_message[:MAX_PUBLIC_ERROR_MESSAGE_LENGTH]
    assert len(dumped["error"]["message"]) <= MAX_PUBLIC_ERROR_MESSAGE_LENGTH


def test_transport_status_mapping_aligned_with_public_error_contract(monkeypatch) -> None:
    client = Client()
    response_400 = client.post(
        "/api/v1/analyze",
        data=json.dumps({"dilemma": "short", "contract_version": "1.0"}),
        content_type="application/json",
    )
    assert response_400.status_code == PUBLIC_ERROR_HTTP_STATUS["request_validation_failed"]
    assert response_400.json()["error"]["code"] == "request_validation_failed"

    monkeypatch.setattr(
        "app.transport.django_api.handle_engine_request",
        lambda payload: build_engine_error_response(
            code="engine_execution_failed",
            message="internal diagnostic text should not leak",
        ),
    )
    response_500 = client.post(
        "/api/v1/analyze",
        data=json.dumps(
            {
                "dilemma": "Another synthetic dilemma for the analyzer stub path, long enough for schema.",
                "contract_version": "1.0",
            }
        ),
        content_type="application/json",
    )
    assert response_500.status_code == PUBLIC_ERROR_HTTP_STATUS["engine_execution_failed"]
    assert response_500.json()["error"]["code"] == "engine_execution_failed"
    assert response_500.json()["error"]["message"] == PUBLIC_ERROR_FIXED_MESSAGES["engine_execution_failed"]
