"""Traceability checks for Step 29D full-activation repair review artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from app.evals.run_full_activation_dry_run import run_full_activation_dry_run
from app.verses.catalog import VerseCatalog
from app.verses.loader import load_curated_verses

_ROOT = Path(__file__).resolve().parents[1]
_REVIEW_JSON = (
    _ROOT
    / "app"
    / "verses"
    / "data"
    / "curation_prep"
    / "targeted_reviews"
    / "full_activation_blockers_review.json"
)
_REVIEW_MD = _REVIEW_JSON.with_suffix(".md")
_REQUIRED_RISKS = {
    "shape_lock_regression",
    "forced_match",
    "overtrigger",
    "cluster_saturation",
    "weak_match",
    "generic_overlap_noise",
}


def _review_payload() -> dict:
    return json.loads(_REVIEW_JSON.read_text(encoding="utf-8"))


def test_follow_on_repairs_include_required_traceability_fields() -> None:
    payload = _review_payload()
    repairs = payload["follow_on_repairs"]

    assert len(repairs) == payload["summary"]["follow_on_repair_count"] == 26
    for repair in repairs:
        assert repair["verse_ref"]
        assert repair["repair_type"] == "follow_on_metadata_narrowing"
        assert repair["metadata_before"]
        assert {"themes", "applies_when", "does_not_apply_when", "priority", "status"}.issubset(
            repair["metadata_after"]
        )
        assert repair["narrowed_fields"]
        assert repair["risk_prevented"] in _REQUIRED_RISKS
        assert repair["behavior_status"] == "verified_clean_after_step_29c"
        assert repair["evidence"]["full_activation_dry_run"]["shape_lock_regressions_count"] == 0
        assert repair["evidence"]["full_activation_dry_run"]["blocker_failure_count"] == 0
        assert repair["evidence"]["full_activation_dry_run"]["forced_match_warning_count"] == 0
        assert repair["evidence"]["full_activation_dry_run"]["overtrigger_warning_count"] == 0
        assert repair["evidence"]["full_activation_dry_run"]["changed_winner_count"] == 0


def test_metadata_before_unavailable_cases_are_explicitly_counted() -> None:
    payload = _review_payload()
    unavailable = [
        repair
        for repair in payload["follow_on_repairs"]
        if repair["metadata_before"] == "not captured during original run"
    ]

    assert len(unavailable) == 26
    assert payload["summary"]["metadata_before_unavailable_count"] == 26


def test_review_artifact_confirms_all_curated_entries_remain_active() -> None:
    payload = _review_payload()
    entries = load_curated_verses()

    assert payload["summary"]["all_curated_entries_active_after_step_29c"] is True
    assert len(entries) == 109
    assert len(VerseCatalog(entries).list_active()) == 109


def test_full_activation_dry_run_metrics_remain_clean() -> None:
    report = run_full_activation_dry_run()
    summary = report["summary"]

    assert summary["currently_active_entries"] == 109
    assert summary["dry_run_active_entries"] == 109
    assert summary["shape_lock_regressions_count"] == 0
    assert summary["blocker_failure_count"] == 0
    assert summary["forced_match_warning_count"] == 0
    assert summary["overtrigger_warning_count"] == 0
    assert summary["changed_winner_count"] == 0
    assert summary["should_block_full_activation"] is False


def test_step_29d_is_documented_as_traceability_only() -> None:
    payload = _review_payload()
    md = _REVIEW_MD.read_text(encoding="utf-8")

    assert payload["summary"]["step_29d_retrieval_behavior_changed"] is False
    assert "Step 29D is traceability-only" in md
    assert "did not change retrieval scoring" in md
    assert "All 109 curated entries remain active" in md
