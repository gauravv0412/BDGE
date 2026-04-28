"""Tests for presentation narrator shadow evaluation harness."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.presentation.config import PresentationLLMConfig
from app.scripts import run_presentation_narrator_shadow_eval as shadow_eval
from app.scripts.run_presentation_narrator_shadow_eval import run_shadow_eval, write_outputs


def _benchmark_fixture(path: Path) -> Path:
    payload = {
        "benchmark_version": "test-shadow-eval-v1",
        "schema_version": "1.0",
        "batch": "test",
        "tone_directive": "test",
        "distribution": {},
        "dilemmas": [
            {"dilemma_id": "W001", "dilemma": "I found a wallet with cash and an ID and feel tempted to keep the cash."},
            {"dilemma_id": "W002", "dilemma": "My manager took credit for my work and I want to publicly expose him."},
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_shadow_eval_writes_json_and_markdown_with_mock_provider(tmp_path: Path) -> None:
    benchmark = _benchmark_fixture(tmp_path / "bench.json")
    report = run_shadow_eval(
        benchmark_path=benchmark,
        include_ood=False,
        mock_provider_mode="repair_success",
    )
    out_json = tmp_path / "shadow_eval.json"
    out_md = tmp_path / "shadow_eval.md"
    write_outputs(report, out_json=out_json, out_md=out_md)

    assert out_json.exists()
    assert out_md.exists()
    parsed = json.loads(out_json.read_text(encoding="utf-8"))
    assert parsed["metrics"]["total_cases"] == 2
    assert parsed["metrics"]["provider_called_count"] == 2
    assert parsed["cases"][0]["accepted_llm_preview"]["simple.headline"]
    assert "Accepted LLM Preview Snippets" in out_md.read_text(encoding="utf-8")
    assert "# Presentation Narrator Shadow Eval" in out_md.read_text(encoding="utf-8")


def test_shadow_eval_metrics_computed_correctly(tmp_path: Path) -> None:
    benchmark = _benchmark_fixture(tmp_path / "bench.json")
    report = run_shadow_eval(
        benchmark_path=benchmark,
        include_ood=False,
        mock_provider_mode="always_valid",
    )
    metrics = report["metrics"]
    assert metrics["total_cases"] == 2
    assert metrics["provider_called_count"] == 2
    assert metrics["initial_attempt_valid_count"] == 2
    assert metrics["repair_attempted_count"] == 0
    assert metrics["final_source_distribution"]["shadow_fallback"] == 2
    assert metrics["style_profile_distribution"]


def test_default_benchmark_classification_breakdown_not_all_mixed() -> None:
    report = run_shadow_eval(
        benchmark_path=shadow_eval.DEFAULT_BENCHMARK_PATH,
        include_ood=False,
        mock_provider_mode="always_valid",
    )
    breakdown = report["metrics"]["per_classification_acceptance_breakdown"]

    assert breakdown["Dharmic"]["total"] == 5
    assert breakdown["Adharmic"]["total"] == 6
    assert breakdown["Mixed"]["total"] == 6
    assert breakdown["Context-dependent"]["total"] == 3
    assert set(breakdown) != {"Mixed"}
    assert len(report["metrics"]["style_profile_distribution"]) >= 3


def test_shadow_eval_reports_soft_style_repetition_warnings() -> None:
    rows = [
        {
            "classification": "Mixed",
            "presentation_mode": "standard",
            "style_profile": "blunt_confrontational",
            "narrator_meta": {"provider_called": True, "final_source": "shadow_fallback", "fallback_returned": True, "rejection_reasons": []},
            "accepted_llm_preview": {"simple.headline": "The real test isn't whether this stings."},
        },
        {
            "classification": "Mixed",
            "presentation_mode": "standard",
            "style_profile": "reflective_calm",
            "narrator_meta": {"provider_called": True, "final_source": "shadow_fallback", "fallback_returned": True, "rejection_reasons": []},
            "accepted_llm_preview": {"simple.headline": "The real question isn't whether you are angry."},
        },
    ]

    metrics = shadow_eval._compute_metrics(rows)

    warnings = {warning["warning"] for warning in metrics["style_repetition_warnings"]}
    assert "repeated template: the real test isn't" in warnings
    assert "repeated template: the real question isn't" in warnings


def test_no_prompt_or_key_leakage_in_artifacts(tmp_path: Path, monkeypatch) -> None:
    benchmark = _benchmark_fixture(tmp_path / "bench.json")
    monkeypatch.setenv("PRESENTATION_LLM_API_KEY", "super-secret-key")
    report = run_shadow_eval(
        benchmark_path=benchmark,
        include_ood=False,
        mock_provider_mode="always_valid",
    )
    out_json = tmp_path / "shadow_eval.json"
    out_md = tmp_path / "shadow_eval.md"
    write_outputs(report, out_json=out_json, out_md=out_md)

    blob = out_json.read_text(encoding="utf-8") + "\n" + out_md.read_text(encoding="utf-8")
    assert "super-secret-key" not in blob
    assert "engine_output" not in blob
    assert "rejected_narrator_output" not in blob
    assert "simple.headline" in blob


def test_provider_unavailable_fails_cleanly_without_mock(tmp_path: Path, monkeypatch) -> None:
    benchmark = _benchmark_fixture(tmp_path / "bench.json")
    monkeypatch.setattr(
        shadow_eval,
        "load_presentation_llm_config",
        lambda: PresentationLLMConfig(provider="none"),
    )
    with pytest.raises(RuntimeError, match="Provider is not configured for shadow eval"):
        run_shadow_eval(
            benchmark_path=benchmark,
            include_ood=False,
            mock_provider_mode="none",
        )
