"""Tests for semantic benchmark runner filtering behavior."""

from __future__ import annotations

from typing import Any

import pytest

from app.evals import run_semantic_scorer_benchmarks as runner


def _stub_semantic_output() -> dict[str, Any]:
    return {
        "ethical_dimensions": {
            "dharma_duty": {"score": 1, "note": "note one is long enough."},
            "satya_truth": {"score": 1, "note": "note two is long enough."},
            "ahimsa_nonharm": {"score": 1, "note": "note three is long enough."},
            "nishkama_detachment": {"score": 1, "note": "note four is long enough."},
            "shaucha_intent": {"score": 1, "note": "note five is long enough."},
            "sanyama_restraint": {"score": 1, "note": "note six is long enough."},
            "lokasangraha_welfare": {"score": 1, "note": "note seven is long enough."},
            "viveka_discernment": {"score": 1, "note": "note eight is long enough."},
        },
        "internal_driver": {
            "primary": "Primary driver text long enough.",
            "hidden_risk": "Hidden risk text long enough.",
        },
        "core_reading": "Core reading text that is long enough to satisfy schema minimum lengths for tests.",
        "gita_analysis": "Gita analysis text that also exceeds the schema minimum length.",
        "higher_path": "Higher path text that exceeds the schema minimum and remains concise.",
        "missing_facts": [],
        "ambiguity_flag": False,
        "if_you_continue": {
            "short_term": "Short term consequence text is long enough.",
            "long_term": "Long term consequence text is long enough.",
        },
        "counterfactuals": {
            "clearly_adharmic_version": {
                "assumed_context": "Adharmic assumed context with enough length for schema checks.",
                "decision": "Adharmic decision text.",
                "why": "Adharmic why text that is sufficiently long.",
            },
            "clearly_dharmic_version": {
                "assumed_context": "Dharmic assumed context with enough length for schema checks.",
                "decision": "Dharmic decision text.",
                "why": "Dharmic why text that is sufficiently long.",
            },
        },
        "share_layer": {
            "anonymous_share_title": "The app said method matters most.",
            "card_quote": "Clarity and restraint together outperform dramatic certainty.",
            "reflective_question": "What fact would most change your decision?",
        },
    }


def test_filtering_to_valid_ids(monkeypatch: Any) -> None:
    monkeypatch.setattr(runner, "semantic_scorer", lambda _d, use_stub=True: _stub_semantic_output())
    report = runner.run_semantic_scorer_benchmarks(
        use_stub=True,
        selected_ids=["W003", "W007"],
    )
    ids = [row["dilemma_id"] for row in report["results"]]
    assert set(ids) == {"W003", "W007"}
    assert report["total"] == 2
    assert report["selected_dilemma_ids"] == ["W003", "W007"]


def test_unknown_id_error() -> None:
    with pytest.raises(ValueError, match="Unknown dilemma_id values requested: BAD999"):
        runner.run_semantic_scorer_benchmarks(
            use_stub=True,
            selected_ids=["W003", "BAD999"],
        )


def test_filtered_summary_total_matches_filtered_count(monkeypatch: Any) -> None:
    monkeypatch.setattr(runner, "semantic_scorer", lambda _d, use_stub=True: _stub_semantic_output())
    report = runner.run_semantic_scorer_benchmarks(
        use_stub=True,
        selected_ids=["W001", "W002", "W003"],
    )
    assert report["total"] == 3
    assert len(report["results"]) == 3
    assert report["passed"] + report["failed"] == 3

