"""Tests for live-style sparse-input retrieval audit."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.evals.run_live_retrieval_audit import (
    render_markdown_report,
    run_live_retrieval_audit,
    write_audit_outputs,
)
from app.semantic.scorer import semantic_scorer as real_semantic_scorer


def test_live_audit_runner_produces_summary() -> None:
    report = run_live_retrieval_audit()
    summary = report["summary"]

    assert report["input_style"] == "live_sparse_dilemma_only"
    assert report["semantic_mode"] == "stubbed_deterministic"
    assert summary["total_cases"] == 20
    assert "expected_vs_actual_live_mismatches" in summary
    assert "live_verse_attach_rate" in summary
    assert "live_fallback_rate" in summary


def test_live_audit_captures_semantic_and_context_fields() -> None:
    report = run_live_retrieval_audit()
    case = report["cases"][0]

    assert case["payload"] == {"dilemma": case["dilemma"]}
    assert isinstance(case["generated_internal_driver"], dict)
    assert isinstance(case["generated_ethical_dimensions"], dict)
    assert isinstance(case["generated_missing_facts"], list)
    assert isinstance(case["semantic_context_signals"], dict)
    assert isinstance(case["deterministic_extractor_signals"], dict)
    assert isinstance(case["signal_sources"], dict)
    assert isinstance(case["retrieval_context"], dict)
    assert {
        "dominant_dimensions",
        "theme_tags",
        "applies_signals",
        "blocker_signals",
        "missing_facts",
    }.issubset(case["retrieval_context"].keys())
    assert isinstance(case["top_candidates"], list)


def test_live_audit_compares_actual_vs_expected_shape() -> None:
    report = run_live_retrieval_audit()
    case = report["cases"][0]

    assert {"verse_ref", "label"}.issubset(case["expected"].keys())
    assert {"verse_ref", "label", "is_fallback"}.issubset(case["actual"].keys())
    assert isinstance(report["summary"]["expected_vs_actual_live_mismatches"], list)


def test_live_audit_identifies_rich_vs_live_differences() -> None:
    report = run_live_retrieval_audit()
    summary = report["summary"]

    assert "live_vs_rich_context_diff_count" in summary
    assert "live_vs_rich_context_differences" in summary
    assert summary["live_vs_rich_context_diff_count"] == len(
        summary["live_vs_rich_context_differences"]
    )
    assert summary["live_vs_rich_context_diff_count"] < 12


def test_live_audit_attach_rate_improves_from_zero() -> None:
    report = run_live_retrieval_audit()
    summary = report["summary"]

    assert summary["live_verse_attach_rate"] > 0.0
    assert summary["too_sparse_context_cases"] == []
    assert summary["fallback_due_to_missing_live_signals_cases"] == []


def test_live_audit_uses_stub_semantic_scorer_without_network(monkeypatch: Any) -> None:
    calls: list[bool | None] = []

    def _fake_semantic_scorer(dilemma: str, *, use_stub: bool | None = None) -> dict[str, Any]:
        calls.append(use_stub)
        if use_stub is not True:
            raise AssertionError("live retrieval audit must force stub semantic mode in tests")
        return real_semantic_scorer(dilemma, use_stub=True)

    monkeypatch.setattr("app.evals.run_live_retrieval_audit.semantic_scorer", _fake_semantic_scorer)

    report = run_live_retrieval_audit()

    assert report["summary"]["total_cases"] == 20
    assert calls
    assert set(calls) == {True}


def test_live_audit_outputs_json_and_markdown(tmp_path: Path) -> None:
    report = run_live_retrieval_audit()
    out_json = tmp_path / "live_retrieval_audit.json"
    out_md = tmp_path / "live_retrieval_audit.md"

    write_audit_outputs(report, out_json=out_json, out_md=out_md)

    assert out_json.exists()
    assert out_md.exists()
    assert '"audit_version": "live-retrieval-audit-v1"' in out_json.read_text(encoding="utf-8")
    md = out_md.read_text(encoding="utf-8")
    assert "# Live Retrieval Audit" in md
    assert "## Expected/Actual Live Mismatches" in md


def test_live_markdown_report_mentions_sparse_sections() -> None:
    report = run_live_retrieval_audit()
    md = render_markdown_report(report)

    assert "## Rich Pass, Live Fail" in md
    assert "## Too Sparse Context" in md
    assert "## Fallback Due To Missing Live Signals" in md
