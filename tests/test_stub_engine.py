"""Stub engine: placeholder output must satisfy the public JSON Schema."""

from __future__ import annotations

from app.core.validator import validate_against_output_schema
from app.engine.analyzer import analyze_dilemma
from app.engine.factory import build_placeholder_response


def test_build_placeholder_response_validates() -> None:
    dilemma = (
        "Synthetic dilemma text for unit test; must be at least twenty characters."
    )
    model = build_placeholder_response(dilemma, dilemma_id="stub-test-id-01")
    payload = model.model_dump(mode="json")
    ok, errors = validate_against_output_schema(payload)
    assert ok, errors


def test_analyze_dilemma_stub_validates() -> None:
    out = analyze_dilemma(
        "Another synthetic dilemma for the analyzer stub path, long enough for schema."
    )
    ok, errors = validate_against_output_schema(out)
    assert ok, errors
