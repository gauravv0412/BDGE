"""Tests for full curated catalog activation dry-run auditing."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.evals.run_full_activation_dry_run import (
    _diagnostic_row,
    _safety_risk_reasons,
    _shape_lock_regressions,
    render_markdown_report,
    run_full_activation_dry_run,
    write_dry_run_outputs,
)
from app.verses.loader import curated_verses_seed_path, load_curated_verses

_ROOT = Path(__file__).resolve().parents[1]
_BLOCKERS_REVIEW_JSON = (
    _ROOT
    / "app"
    / "verses"
    / "data"
    / "curation_prep"
    / "targeted_reviews"
    / "full_activation_blockers_review.json"
)
_BLOCKERS_REVIEW_MD = _BLOCKERS_REVIEW_JSON.with_suffix(".md")


@pytest.fixture(scope="module")
def dry_run_report() -> dict:
    return run_full_activation_dry_run()


def test_dry_run_loader_does_not_mutate_verses_seed() -> None:
    seed_path = curated_verses_seed_path()
    before = seed_path.read_text(encoding="utf-8")

    current_entries = load_curated_verses()
    dry_run_entries = load_curated_verses(dry_run_all_active=True)

    after = seed_path.read_text(encoding="utf-8")
    assert after == before
    assert sum(1 for entry in dry_run_entries if entry.status == "active") >= sum(
        1 for entry in current_entries if entry.status == "active"
    )


def test_dry_run_summary_contains_before_after_coverage(dry_run_report: dict) -> None:
    summary = dry_run_report["summary"]

    assert summary["total_curated_entries"] >= summary["currently_active_entries"]
    assert summary["dry_run_active_entries"] >= summary["currently_active_entries"]
    assert "actual_verse_coverage_before" in summary
    assert "actual_verse_coverage_dry_run" in summary
    assert isinstance(summary["actual_verse_coverage_before"], float)
    assert isinstance(summary["actual_verse_coverage_dry_run"], float)


def test_full_activation_blockers_are_cleared_under_dry_run(dry_run_report: dict) -> None:
    summary = dry_run_report["summary"]

    assert summary["shape_lock_regressions_count"] == 0
    assert summary["forced_match_warning_count"] == 0
    assert summary["blocker_failure_count"] == 0
    assert summary["overtrigger_warning_count"] == 0
    assert dry_run_report["shape_lock_regressions"] == []
    assert dry_run_report["changed_cases"] == []
    assert summary["should_block_full_activation"] is False


def test_full_activation_dry_run_preserves_reviewed_case_outputs(dry_run_report: dict) -> None:
    cases = {
        case["dilemma_id"]: case
        for case in dry_run_report["runs"]["reference_dry_run_W001_W050"]["cases"]
    }

    assert cases["W012"]["actual_verse_ref"] == "2.47"
    assert cases["W018"]["actual_shape"] == "fallback"
    assert cases["W031"]["actual_verse_ref"] == "6.16"
    assert cases["W044"]["actual_verse_ref"] == "16.1-3"


def test_changed_winners_are_reported_with_required_diagnostics(dry_run_report: dict) -> None:
    summary = dry_run_report["summary"]
    changed_cases = dry_run_report["changed_cases"]

    assert summary["changed_winner_count"] == len(changed_cases)
    for case in changed_cases:
        assert {
            "dilemma_id",
            "dilemma",
            "current",
            "dry_run",
            "reference",
            "top_5_candidates_current",
            "top_5_candidates_dry_run",
            "score_breakdown",
            "why_dry_run_winner_won",
            "risk_label",
        }.issubset(case)
        assert case["risk_label"] in {
            "better_specific_match",
            "acceptable_alternative",
            "possible_noise",
            "safety_risk",
            "shape_lock_regression",
            "needs_human_review",
        }


def test_severe_blocker_case_is_flagged_if_it_retrieves_verse() -> None:
    case = {
        "dilemma_id": "SAFETY",
        "dilemma": "I want to attack someone because I am angry.",
        "actual_verse_ref": "2.31",
        "actual_shape": "verse",
        "reference_shape": "fallback",
        "retrieval_context": {"blocker_signals": ["active-harm"]},
        "score_breakdown": {
            "verse_ref": "2.31",
            "total_score": 8,
            "theme_overlap": ["action", "duty"],
            "applies_when_hits": ["duty-conflict"],
            "theme_overlap_count": 2,
            "applies_when_hits_count": 1,
            "blocker_hits_count": 0,
            "rejected": False,
        },
    }

    reasons = _safety_risk_reasons(case)

    assert any("severe blocker" in reason for reason in reasons)
    assert any("action-justifying verse" in reason for reason in reasons)


def test_w001_w020_shape_regressions_are_detected() -> None:
    current = {
        "cases": [
            {"dilemma_id": "W001", "actual": {"label": "17.15"}},
            {"dilemma_id": "W002", "actual": {"label": "6.5"}},
        ]
    }
    dry = {
        "cases": [
            {"dilemma_id": "W001", "actual": {"label": "2.47"}, "expected": {"label": "17.15"}, "flags": []},
            {"dilemma_id": "W002", "actual": {"label": "6.5"}, "expected": {"label": "6.5"}, "flags": []},
        ]
    }

    regressions = _shape_lock_regressions(current, dry)

    assert regressions == [
        {
            "dilemma_id": "W001",
            "current": "17.15",
            "dry_run": "2.47",
            "expected": "17.15",
            "flags": [],
        }
    ]


def test_shape_lock_regression_risk_label_is_reported() -> None:
    current_case = {
        "dilemma_id": "W001",
        "dilemma": "Should I publicly correct my manager?",
        "actual_shape": "verse",
        "actual_verse_ref": "17.15",
        "top_5_candidates": [],
    }
    dry_case = {
        "dilemma_id": "W001",
        "dilemma": "Should I publicly correct my manager?",
        "actual_shape": "verse",
        "actual_verse_ref": "2.47",
        "reference_shape": "verse",
        "reference_verse_ref": "17.15",
        "allowed_verse_refs": ["17.15"],
        "retrieval_context": {"blocker_signals": []},
        "top_5_candidates": [],
        "score_breakdown": None,
    }

    row = _diagnostic_row(
        current_case=current_case,
        dry_case=dry_case,
        shape_lock_regression_ids={"W001"},
    )

    assert row["risk_label"] == "shape_lock_regression"


def test_dry_run_outputs_json_and_markdown(tmp_path, dry_run_report: dict) -> None:
    out_json = tmp_path / "full_activation_dry_run.json"
    out_md = tmp_path / "full_activation_dry_run.md"

    write_dry_run_outputs(dry_run_report, out_json=out_json, out_md=out_md)

    assert out_json.exists()
    assert out_md.exists()
    assert '"mutates_seed": false' in out_json.read_text(encoding="utf-8")
    md = out_md.read_text(encoding="utf-8")
    assert "# Full Activation Dry-Run Audit" in md
    assert "## Changed Winners" in md


def test_markdown_contains_recommendation(dry_run_report: dict) -> None:
    md = render_markdown_report(dry_run_report)

    assert "Recommendation:" in md


def test_full_activation_blocker_review_artifact_has_decisions() -> None:
    assert _BLOCKERS_REVIEW_JSON.exists()
    assert _BLOCKERS_REVIEW_MD.exists()
    payload = json.loads(_BLOCKERS_REVIEW_JSON.read_text(encoding="utf-8"))
    decisions = {row["verse_ref"]: row for row in payload["decisions"]}

    for verse_ref in ("18.26", "2.63", "2.58", "16.2"):
        assert decisions[verse_ref]["decision"] == "REPAIR_METADATA"
        assert decisions[verse_ref]["rationale"]

    assert payload["summary"]["quarantine_for_now_count"] == 0
    assert payload["summary"]["repair_metadata_count"] >= 4
