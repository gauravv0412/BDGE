"""Tests for OOD sparse-input live retrieval audit fixtures."""

from __future__ import annotations

import json
from pathlib import Path

from app.evals.run_live_retrieval_audit import run_live_retrieval_audit

OOD_FIXTURE = Path("tests/fixtures/live_retrieval_ood_W021-W050.json")


def _load_fixture(path: Path = OOD_FIXTURE) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_ood_fixture_loads() -> None:
    payload = _load_fixture()

    assert payload["fixture_version"] == "live-retrieval-ood-v1"
    assert len(payload["cases"]) == 30


def test_ood_fixture_cases_have_required_fields() -> None:
    payload = _load_fixture()
    required = {
        "dilemma_id",
        "dilemma",
        "expected_shape",
        "expected_allowed_verses",
        "expected_signal_hints",
        "notes",
    }

    for case in payload["cases"]:
        assert required.issubset(case.keys())
        assert case["dilemma_id"].startswith("W0")
        assert case["expected_shape"] in {"verse", "fallback"}
        assert isinstance(case["expected_allowed_verses"], list)
        assert isinstance(case["expected_signal_hints"], dict)
        assert {"themes", "applies", "blockers"}.issubset(case["expected_signal_hints"].keys())


def test_ood_live_audit_runs_without_llm_network() -> None:
    report = run_live_retrieval_audit(input_path=OOD_FIXTURE)

    assert report["input_kind"] == "retrieval_fixture"
    assert report["semantic_mode"] == "stubbed_deterministic"
    assert report["summary"]["total_cases"] == 30
    assert report["cases"][0]["payload"] == {"dilemma": report["cases"][0]["dilemma"]}


def test_ood_summary_includes_mismatch_categories() -> None:
    report = run_live_retrieval_audit(input_path=OOD_FIXTURE)
    summary = report["summary"]

    for key in (
        "expected_shape_mismatches",
        "unexpected_verse_cases",
        "unexpected_fallback_cases",
        "disallowed_verse_cases",
        "missing_expected_signal_cases",
        "possible_forced_match_cases",
        "possible_overtrigger_cases",
    ):
        assert key in summary
        assert isinstance(summary[key], list)


def test_ood_live_audit_has_no_forced_or_overtrigger_warnings() -> None:
    report = run_live_retrieval_audit(input_path=OOD_FIXTURE)
    summary = report["summary"]

    assert summary["unexpected_verse_cases"] == []
    assert summary["possible_forced_match_cases"] == []
    assert summary["possible_overtrigger_cases"] == []


def test_expected_allowed_verses_are_enforced(tmp_path: Path) -> None:
    fixture = {
        "cases": [
            {
                "dilemma_id": "OOD-DISALLOWED",
                "dilemma": "My manager takes credit for my work. Should I publicly correct him in the next meeting?",
                "expected_shape": "verse",
                "expected_allowed_verses": ["2.47"],
                "expected_signal_hints": {"themes": ["speech"], "applies": ["ethical-speech"], "blockers": []},
                "notes": "Actual live retrieval should not be in the allowed list.",
            }
        ]
    }
    path = tmp_path / "fixture.json"
    path.write_text(json.dumps(fixture), encoding="utf-8")

    report = run_live_retrieval_audit(input_path=path)

    assert report["summary"]["disallowed_verse_cases"]
    assert report["summary"]["expected_vs_actual_live_mismatches"]


def test_expected_fallback_cases_do_not_pass_with_random_verse(tmp_path: Path) -> None:
    fixture = {
        "cases": [
            {
                "dilemma_id": "OOD-FALLBACK",
                "dilemma": "My manager takes credit for my work. Should I publicly correct him in the next meeting?",
                "expected_shape": "fallback",
                "expected_allowed_verses": [],
                "expected_signal_hints": {"themes": ["speech"], "applies": ["ethical-speech"], "blockers": []},
                "notes": "Expected fallback fixture should fail if a verse attaches.",
            }
        ]
    }
    path = tmp_path / "fixture.json"
    path.write_text(json.dumps(fixture), encoding="utf-8")

    report = run_live_retrieval_audit(input_path=path)

    assert report["summary"]["unexpected_verse_cases"]
    assert report["summary"]["possible_overtrigger_cases"]


def test_expected_signal_hints_are_checked(tmp_path: Path) -> None:
    fixture = {
        "cases": [
            {
                "dilemma_id": "OOD-MISSING-SIGNAL",
                "dilemma": "Something feels off but I cannot explain why.",
                "expected_shape": "fallback",
                "expected_allowed_verses": [],
                "expected_signal_hints": {
                    "themes": ["right-livelihood"],
                    "applies": ["whistleblowing-risk"],
                    "blockers": ["active-harm"],
                },
                "notes": "Impossible hints should be reported as missing.",
            }
        ]
    }
    path = tmp_path / "fixture.json"
    path.write_text(json.dumps(fixture), encoding="utf-8")

    report = run_live_retrieval_audit(input_path=path)

    missing = report["summary"]["missing_expected_signal_cases"]
    assert missing
    assert missing[0]["missing_expected_signals"]["themes"] == ["right-livelihood"]
