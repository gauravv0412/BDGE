"""Stub engine: placeholder output must satisfy the public JSON Schema."""

from __future__ import annotations

from typing import Any

import pytest

from app.core.validator import validate_against_output_schema
from app.engine.analyzer import analyze_dilemma
from app.engine.factory import build_placeholder_response
from app.semantic.scorer import semantic_scorer


@pytest.fixture
def force_semantic_stub(monkeypatch: Any) -> None:
    """Force analyzer Stage 1 to use semantic scorer stub payload."""

    def _semantic_stub(dilemma: str) -> dict[str, Any]:
        return semantic_scorer(dilemma, use_stub=True)

    monkeypatch.setattr("app.engine.analyzer.semantic_scorer", _semantic_stub)


def test_build_placeholder_response_validates(force_semantic_stub: None) -> None:
    dilemma = (
        "Synthetic dilemma text for unit test; must be at least twenty characters."
    )
    model = build_placeholder_response(dilemma, dilemma_id="stub-test-id-01")
    payload = model.model_dump(mode="json")
    ok, errors = validate_against_output_schema(payload)
    assert ok, errors


def test_analyze_dilemma_stub_validates(force_semantic_stub: None) -> None:
    out = analyze_dilemma(
        "Another synthetic dilemma for the analyzer stub path, long enough for schema."
    )
    ok, errors = validate_against_output_schema(out)
    assert ok, errors


def test_analyzer_uses_semantic_scorer(monkeypatch: Any) -> None:
    calls: list[str] = []

    def _fake_semantic_scorer(dilemma: str, *, use_stub: bool = True) -> dict[str, Any]:
        calls.append(dilemma)
        return {
            "verdict_sentence": "The apparent fix secures image first and leaves the duty ledger ethically unstable.",
            "ethical_dimensions": {
                "dharma_duty": {"score": 1, "note": "fake note one."},
                "satya_truth": {"score": 1, "note": "fake note two."},
                "ahimsa_nonharm": {"score": 1, "note": "fake note three."},
                "nishkama_detachment": {"score": 1, "note": "fake note four."},
                "shaucha_intent": {"score": 1, "note": "fake note five."},
                "sanyama_restraint": {"score": 1, "note": "fake note six."},
                "lokasangraha_welfare": {"score": 1, "note": "fake note seven."},
                "viveka_discernment": {"score": 1, "note": "fake note eight."},
            },
            "internal_driver": {
                "primary": "Fake semantic primary driver for test verification.",
                "hidden_risk": "Fake semantic hidden risk for test verification.",
            },
            "core_reading": (
                "Fake semantic core reading that is intentionally long enough to satisfy "
                "the minimum length requirement in the schema."
            ),
            "gita_analysis": "Fake semantic gita analysis string exceeding forty characters.",
            "higher_path": "Fake semantic higher path text that exceeds thirty characters.",
            "missing_facts": [],
            "ambiguity_flag": False,
            "if_you_continue": {
                "short_term": "Fake semantic short-term consequence for the analyzer test.",
                "long_term": "Fake semantic long-term consequence for the analyzer test.",
            },
            "counterfactuals": {
                "clearly_adharmic_version": {
                    "assumed_context": "Fake semantic adharmic context that is over thirty characters long.",
                    "decision": "Fake adharmic decision.",
                    "why": "Fake adharmic rationale with enough characters.",
                },
                "clearly_dharmic_version": {
                    "assumed_context": "Fake semantic dharmic context that is over thirty characters long.",
                    "decision": "Fake dharmic decision.",
                    "why": "Fake dharmic rationale with enough characters.",
                },
            },
            "share_layer": {
                "anonymous_share_title": "Fake semantic share title for analyzer test.",
                "card_quote": "Fake semantic card quote for analyzer verification.",
                "reflective_question": "Fake semantic reflective question?",
            },
        }

    monkeypatch.setattr("app.engine.analyzer.semantic_scorer", _fake_semantic_scorer)
    out = analyze_dilemma(
        "Synthetic dilemma to verify analyzer stage one uses semantic scorer."
    )

    assert calls, "semantic_scorer should be called by analyzer"
    assert out["internal_driver"]["primary"] == "Fake semantic primary driver for test verification."
    ok, errors = validate_against_output_schema(out)
    assert ok, errors


def test_analyzer_ships_semantic_authored_verdict_sentence(monkeypatch: Any) -> None:
    sentence = "The draft response protects calm now but quietly weakens the ethical core of the decision."

    def _semantic_stub(dilemma: str) -> dict[str, Any]:
        payload = semantic_scorer(dilemma, use_stub=True)
        payload["verdict_sentence"] = sentence
        return payload

    monkeypatch.setattr("app.engine.analyzer.semantic_scorer", _semantic_stub)
    out = analyze_dilemma("A long enough dilemma text to keep schema validation satisfied.")
    assert out["verdict_sentence"] == sentence


def test_analyzer_sanitizes_invalid_semantic_verdict_sentence(monkeypatch: Any) -> None:
    def _semantic_stub(dilemma: str) -> dict[str, Any]:
        payload = semantic_scorer(dilemma, use_stub=True)
        payload["verdict_sentence"] = "You should do this immediately."
        return payload

    monkeypatch.setattr("app.engine.analyzer.semantic_scorer", _semantic_stub)
    out = analyze_dilemma("A long enough dilemma text to keep schema validation satisfied.")
    assert "you should" not in out["verdict_sentence"].lower()
