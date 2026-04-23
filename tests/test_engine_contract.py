"""Public engine contract tests for API boundary prep (Step 9.5)."""

from __future__ import annotations

from typing import Any

import pytest

from app.core.models import EngineAnalyzeErrorResponse, EngineAnalyzeRequest, EngineAnalyzeResponse
from app.engine.analyzer import analyze_dilemma_request, handle_engine_request
from app.semantic.scorer import semantic_scorer


def test_engine_request_shape_forbids_unknown_fields() -> None:
    with pytest.raises(Exception):
        EngineAnalyzeRequest.model_validate(
            {
                "dilemma": "Synthetic dilemma text for unit test; must be at least twenty characters.",
                "unexpected": True,
            }
        )


def test_engine_request_rejects_short_dilemma() -> None:
    with pytest.raises(Exception):
        EngineAnalyzeRequest.model_validate({"dilemma": "too short"})


def test_engine_response_contract_contains_meta_and_output(monkeypatch: Any) -> None:
    def _semantic_stub(dilemma: str) -> dict[str, Any]:
        payload = semantic_scorer(dilemma, use_stub=True)
        payload["verdict_sentence"] = (
            "The stated approach carries ethical friction that remains unresolved at execution level."
        )
        return payload

    monkeypatch.setattr("app.engine.analyzer.semantic_scorer", _semantic_stub)
    req = EngineAnalyzeRequest(
        dilemma="Another synthetic dilemma for the analyzer stub path, long enough for schema.",
        dilemma_id="contract-test-01",
    )
    resp = analyze_dilemma_request(req)
    dumped = resp.model_dump(mode="json")
    assert "meta" in dumped
    assert "output" in dumped
    assert dumped["meta"]["contract_version"] == "1.0"
    assert dumped["meta"]["engine_version"] == "2.1"
    assert dumped["meta"]["semantic_mode_default"] in {"stub_default", "live_default"}
    assert dumped["output"]["dilemma_id"] == "contract-test-01"
    assert dumped["output"]["verdict_sentence"].startswith("The stated approach")


def test_handle_engine_request_returns_validation_error_envelope() -> None:
    resp = handle_engine_request({"dilemma": "short"})
    assert isinstance(resp, EngineAnalyzeErrorResponse)
    dumped = resp.model_dump(mode="json")
    assert dumped["meta"]["contract_version"] == "1.0"
    assert dumped["error"]["code"] == "request_validation_failed"
    assert dumped["error"]["message"]


def test_handle_engine_request_success_envelope_stable(monkeypatch: Any) -> None:
    def _semantic_stub(dilemma: str) -> dict[str, Any]:
        payload = semantic_scorer(dilemma, use_stub=True)
        payload["verdict_sentence"] = (
            "The stated approach carries ethical friction that remains unresolved at execution level."
        )
        return payload

    monkeypatch.setattr("app.engine.analyzer.semantic_scorer", _semantic_stub)
    resp = handle_engine_request(
        {
            "dilemma": "Another synthetic dilemma for the analyzer stub path, long enough for schema.",
            "dilemma_id": "contract-test-02",
        }
    )
    assert isinstance(resp, EngineAnalyzeResponse)
    dumped = resp.model_dump(mode="json")
    assert list(dumped.keys()) == ["meta", "output"]
    assert dumped["meta"]["contract_version"] == "1.0"
    assert dumped["output"]["dilemma_id"] == "contract-test-02"


def test_handle_engine_request_sanitizes_long_internal_exception(monkeypatch: Any) -> None:
    long_exception_text = "x" * 1200

    def _raise_long_exception(dilemma: str) -> dict[str, Any]:
        raise RuntimeError(long_exception_text)

    monkeypatch.setattr("app.engine.analyzer.semantic_scorer", _raise_long_exception)
    resp = handle_engine_request(
        {
            "dilemma": "Another synthetic dilemma for the analyzer stub path, long enough for schema.",
            "dilemma_id": "contract-test-03",
            "contract_version": "1.0",
        }
    )
    assert isinstance(resp, EngineAnalyzeErrorResponse)
    dumped = resp.model_dump(mode="json")
    assert dumped["error"]["code"] == "engine_execution_failed"
    assert dumped["error"]["message"] == "Internal engine failure."
    assert len(dumped["error"]["message"]) <= 500
    assert long_exception_text not in dumped["error"]["message"]
