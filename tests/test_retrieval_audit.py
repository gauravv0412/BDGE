"""Tests for deterministic post-expansion retrieval audit reporting."""

from __future__ import annotations

from pathlib import Path

from app.evals.run_retrieval_audit import (
    render_markdown_report,
    run_retrieval_audit,
    write_audit_outputs,
)

EXPECTED_W001_W020_RETRIEVAL_SHAPE = {
    "W001": "17.15",
    "W002": "6.5",
    "W003": "3.35",
    "W004": "17.15",
    "W005": "18.47",
    "W006": "16.21",
    "W007": "fallback",
    "W008": "5.18",
    "W009": "16.1-3",
    "W010": "fallback",
    "W011": "fallback",
    "W012": "2.47",
    "W013": "3.37",
    "W014": "17.20",
    "W015": "fallback",
    "W016": "fallback",
    "W017": "fallback",
    "W018": "fallback",
    "W019": "fallback",
    "W020": "2.27",
}


def test_audit_runner_creates_summary_metrics() -> None:
    report = run_retrieval_audit()
    summary = report["summary"]

    assert summary["total_cases"] == 20
    assert "verse_attach_rate" in summary
    assert "fallback_rate" in summary
    assert summary["verse_attach_rate"] + summary["fallback_rate"] == 100.0
    assert isinstance(summary["verse_usage"], dict)
    assert "top_1_verse_share_pct" in summary
    assert "top_5_verse_share_pct" in summary


def test_current_w001_w020_audit_state_has_no_regressions() -> None:
    report = run_retrieval_audit()
    summary = report["summary"]

    assert summary["total_cases"] == 20
    assert summary["expected_vs_actual_mismatches"] == []
    assert summary["blocker_failure_cases"] == []
    assert summary["weak_match_cases"] == []
    assert summary["near_threshold_fallback_cases"] == []


def test_w001_w020_expected_retrieval_shape_is_locked() -> None:
    report = run_retrieval_audit()
    actual_shape = {
        case["dilemma_id"]: case["actual"]["label"]
        for case in report["cases"]
    }

    assert actual_shape == EXPECTED_W001_W020_RETRIEVAL_SHAPE


def test_audit_runner_creates_per_case_diagnostics() -> None:
    report = run_retrieval_audit()
    case = report["cases"][0]

    assert {
        "dilemma_id",
        "expected",
        "actual",
        "winner_score",
        "runner_up_score",
        "score_margin",
        "theme_overlaps",
        "applies_when_hits",
        "blocker_hits",
        "dominant_dimension_alignment",
        "top_candidates",
        "context",
        "flags",
    }.issubset(case.keys())
    assert len(case["top_candidates"]) <= 5
    assert {"verse_ref", "total_score", "theme_overlap_count"}.issubset(
        case["top_candidates"][0].keys()
    )


def test_rates_are_computed_from_cases_not_hardcoded() -> None:
    report = run_retrieval_audit()
    cases = report["cases"]
    summary = report["summary"]

    attached = sum(1 for case in cases if case["actual"]["verse_ref"] is not None)
    fallback = len(cases) - attached
    assert summary["verse_attach_rate"] == round((attached / len(cases)) * 100, 2)
    assert summary["fallback_rate"] == round((fallback / len(cases)) * 100, 2)


def test_verse_reuse_is_reported_but_not_failure() -> None:
    report = run_retrieval_audit()
    summary = report["summary"]

    assert "verse_usage" in summary
    assert "top_1_verse_share_pct" in summary
    assert "top_5_verse_share_pct" in summary
    assert isinstance(summary["verse_usage"], dict)
    assert isinstance(summary["top_1_verse_share_pct"], float)
    assert isinstance(summary["top_5_verse_share_pct"], float)
    assert sum(summary["verse_usage"].values()) == sum(
        1 for case in report["cases"] if case["actual"]["verse_ref"] is not None
    )
    assert "concentration_warnings" in summary
    assert isinstance(summary["concentration_warnings"], list)


def test_low_margin_weak_match_and_blocker_flags_are_deterministic() -> None:
    first = run_retrieval_audit()
    second = run_retrieval_audit()

    for key in (
        "low_margin_cases",
        "weak_match_cases",
        "blocker_failure_cases",
        "near_threshold_fallback_cases",
        "expected_vs_actual_mismatches",
    ):
        assert first["summary"][key] == second["summary"][key]

    first_flags = {case["dilemma_id"]: case["flags"] for case in first["cases"]}
    second_flags = {case["dilemma_id"]: case["flags"] for case in second["cases"]}
    assert first_flags == second_flags


def test_audit_outputs_json_and_markdown(tmp_path: Path) -> None:
    report = run_retrieval_audit()
    out_json = tmp_path / "retrieval_audit_test.json"
    out_md = tmp_path / "retrieval_audit_test.md"

    write_audit_outputs(report, out_json=out_json, out_md=out_md)

    assert out_json.exists()
    assert out_md.exists()
    assert '"total_cases": 20' in out_json.read_text(encoding="utf-8")
    md = out_md.read_text(encoding="utf-8")
    assert "# Retrieval Audit" in md
    assert "## Blocker Failures" in md


def test_markdown_report_is_risk_sorted() -> None:
    report = run_retrieval_audit()
    md = render_markdown_report(report)

    assert md.index("## Blocker Failures") < md.index("## Expected/Actual Mismatches")
    assert md.index("## Expected/Actual Mismatches") < md.index("## Low-Margin Wins")
    assert md.index("## Low-Margin Wins") < md.index("## Weak Matches")
    assert md.index("## Weak Matches") < md.index("## Near-Threshold Fallbacks")
    assert md.index("## Near-Threshold Fallbacks") < md.index("## Concentration Warnings")
