"""Thin Django transport-layer tests (Step 11)."""

from __future__ import annotations

import json
import os
from typing import Any

import django
from django.test import Client

from app.engine.analyzer import build_engine_error_response
from app.semantic.scorer import semantic_scorer

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.django_test_settings")
django.setup()


def test_django_analyze_success_200(monkeypatch: Any) -> None:
    def _semantic_stub(dilemma: str) -> dict[str, Any]:
        payload = semantic_scorer(dilemma, use_stub=True)
        payload["verdict_sentence"] = (
            "The proposed move appears coherent at first glance but remains ethically unstable in execution."
        )
        return payload

    monkeypatch.setattr("app.engine.analyzer.semantic_scorer", _semantic_stub)
    client = Client()
    response = client.post(
        "/api/v1/analyze",
        data=json.dumps(
            {
                "dilemma": "Another synthetic dilemma for the analyzer stub path, long enough for schema.",
                "dilemma_id": "dj-transport-01",
            }
        ),
        content_type="application/json",
    )
    assert response.status_code == 200
    assert response["Content-Type"].startswith("application/json")
    body = response.json()
    assert sorted(body.keys()) == ["meta", "output"]
    assert body["meta"]["contract_version"] == "1.0"
    assert body["output"]["dilemma_id"] == "dj-transport-01"


def test_django_analyze_invalid_request_400() -> None:
    client = Client()
    response = client.post(
        "/api/v1/analyze",
        data=json.dumps({"dilemma": "too short"}),
        content_type="application/json",
    )
    assert response.status_code == 400
    body = response.json()
    assert sorted(body.keys()) == ["error", "meta"]
    assert body["error"]["code"] == "request_validation_failed"
    assert body["meta"]["contract_version"] == "1.0"


def test_django_analyze_internal_failure_500(monkeypatch: Any) -> None:
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
                "dilemma": "Another synthetic dilemma for the analyzer stub path, long enough for schema.",
                "dilemma_id": "dj-transport-02",
            }
        ),
        content_type="application/json",
    )
    assert response.status_code == 500
    assert response["Content-Type"].startswith("application/json")
    body = response.json()
    assert body["error"]["code"] == "engine_execution_failed"
    assert body["meta"]["engine_version"] == "2.1"


def test_django_analyze_malformed_json_400() -> None:
    client = Client()
    response = client.post(
        "/api/v1/analyze",
        data="{not-json",
        content_type="application/json",
    )
    assert response.status_code == 400
    body = response.json()
    assert body["error"]["code"] == "request_validation_failed"
