"""Tests for reference benchmark comparison runner."""

from __future__ import annotations

import json
from pathlib import Path

from app.evals.run_reference_benchmark_comparison import (
    DEFAULT_RETRIEVAL_EVAL_PATH,
    render_markdown_report,
    run_reference_benchmark_comparison,
    write_comparison_outputs,
)


def _default_case_by_id() -> dict[str, dict]:
    report = run_reference_benchmark_comparison()
    return {case["dilemma_id"]: case for case in report["cases"]}


def _write_fixture(tmp_path: Path, cases: list[dict]) -> Path:
    payload = {
        "benchmark_version": "test-reference-derived-retrieval-eval",
        "source": "test.json",
        "policy": {
            "benchmark_is_reference_not_gold": True,
            "verse_null_is_not_strict": True,
            "different_valid_verse_allowed": True,
            "higher_verse_coverage_allowed": True,
        },
        "cases": cases,
    }
    path = tmp_path / "retrieval_eval.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _case(
    *,
    dilemma_id: str,
    dilemma: str,
    reference_shape: str,
    reference_verse_ref: str | None,
    allowed_verse_refs: list[str] | None = None,
) -> dict:
    return {
        "dilemma_id": dilemma_id,
        "dilemma": dilemma,
        "reference_classification": "Mixed",
        "reference_shape": reference_shape,
        "reference_verse_ref": reference_verse_ref,
        "allowed_verse_refs": (
            allowed_verse_refs
            if allowed_verse_refs is not None
            else ([reference_verse_ref] if reference_verse_ref else [])
        ),
        "allow_different_valid_verse": True,
        "allow_fallback": True,
        "notes": "Reference verse/fallback is advisory, not gold.",
    }


def test_comparison_runner_loads_derived_fixture() -> None:
    report = run_reference_benchmark_comparison()

    assert report["fixture_path"] == str(DEFAULT_RETRIEVAL_EVAL_PATH)
    assert report["policy"]["benchmark_is_reference_not_gold"] is True
    assert report["summary"]["total_cases"] == 50


def test_comparison_runner_produces_json_summary() -> None:
    report = run_reference_benchmark_comparison()
    summary = report["summary"]

    assert "reference_verse_cases" in summary
    assert "actual_verse_cases" in summary
    assert "same_reference_verse_count" in summary
    assert "upgraded_fallback_to_verse_count" in summary
    assert "accepted_reference_disagreement_count" in summary
    assert "needs_review_extractor_count" in summary
    assert "needs_review_metadata_or_scoring_count" in summary
    assert "raw_downgraded_verse_to_fallback_count" in summary
    assert summary["reference_verse_cases"] + summary["reference_fallback_cases"] == 50
    assert summary["actual_verse_cases"] + summary["actual_fallback_cases"] == 50


def test_step_28e_reference_comparison_expected_cases() -> None:
    cases = _default_case_by_id()

    assert cases["W021"]["category"] == "same_reference_verse"
    assert cases["W021"]["actual_verse_ref"] == "3.20"
    assert cases["W031"]["category"] == "same_reference_verse"
    assert cases["W031"]["actual_verse_ref"] == "6.16"
    assert cases["W036"]["category"] == "same_reference_verse"
    assert cases["W036"]["actual_verse_ref"] == "2.70"
    assert cases["W044"]["category"] == "same_reference_verse"
    assert cases["W044"]["actual_verse_ref"] == "16.1-3"


def test_w044_fixture_allows_active_range_without_changing_reference_ref() -> None:
    fixture = json.loads(DEFAULT_RETRIEVAL_EVAL_PATH.read_text(encoding="utf-8"))
    w044 = next(case for case in fixture["cases"] if case["dilemma_id"] == "W044")

    assert w044["reference_verse_ref"] == "16.3"
    assert "16.1-3" in w044["allowed_verse_refs"]
    assert "contains 16.3" in w044["notes"]


def test_comparison_runner_produces_markdown_report() -> None:
    report = run_reference_benchmark_comparison()
    md = render_markdown_report(report)

    assert "# Reference Benchmark Comparison" in md
    assert "## Summary" in md
    assert "## Needs Human Review" in md


def test_fallback_to_verse_upgrade_is_review_not_failure(tmp_path: Path) -> None:
    path = _write_fixture(
        tmp_path,
        [
            _case(
                dilemma_id="UPGRADE",
                dilemma="My manager takes credit for my work. Should I publicly correct him in the next meeting?",
                reference_shape="fallback",
                reference_verse_ref=None,
                allowed_verse_refs=[],
            )
        ],
    )

    report = run_reference_benchmark_comparison(fixture_path=path)
    case = report["cases"][0]

    assert case["category"] == "upgraded_fallback_to_verse"
    assert case["needs_human_review"] is True
    assert report["policy"]["verse_null_is_not_strict"] is True
    assert report["summary"]["upgraded_fallback_to_verse_count"] == 1


def test_reference_fallback_is_not_prohibition_against_verse(tmp_path: Path) -> None:
    path = _write_fixture(
        tmp_path,
        [
            _case(
                dilemma_id="FALLBACK-NOT-GOLD",
                dilemma="I'm attracted to a married colleague who flirts with me. Should I keep meeting them alone after work?",
                reference_shape="fallback",
                reference_verse_ref=None,
                allowed_verse_refs=[],
            )
        ],
    )

    report = run_reference_benchmark_comparison(fixture_path=path)
    case = report["cases"][0]

    assert case["actual_shape"] == "verse"
    assert case["category"] == "upgraded_fallback_to_verse"
    assert "failure" not in (case["review_reason"] or "").lower()


def test_downgraded_reference_verse_cases_are_detected_and_diagnosed(tmp_path: Path) -> None:
    path = _write_fixture(
        tmp_path,
        [
            _case(
                dilemma_id="DOWNGRADE",
                dilemma="Something feels off about a business deal, but I cannot explain why.",
                reference_shape="verse",
                reference_verse_ref="17.15",
                allowed_verse_refs=["17.15"],
            )
        ],
    )

    report = run_reference_benchmark_comparison(fixture_path=path)
    case = report["cases"][0]

    assert case["raw_category"] == "downgraded_verse_to_fallback"
    assert case["category"] == "needs_review_metadata_or_scoring"
    assert case["needs_human_review"] is True
    assert report["summary"]["raw_downgraded_verse_to_fallback_count"] == 1
    assert report["summary"]["needs_review_metadata_or_scoring_count"] == 1


def test_accepted_reference_disagreement_is_separate_from_unresolved_downgrade(
    tmp_path: Path,
) -> None:
    path = _write_fixture(
        tmp_path,
        [
            _case(
                dilemma_id="ACCEPTED",
                dilemma="Is killing in self-defense adharmic?",
                reference_shape="verse",
                reference_verse_ref="2.31",
                allowed_verse_refs=["2.31"],
            )
        ],
    )

    report = run_reference_benchmark_comparison(fixture_path=path)
    case = report["cases"][0]

    assert case["raw_category"] == "downgraded_verse_to_fallback"
    assert case["category"] == "accepted_reference_disagreement"
    assert case["needs_human_review"] is False
    assert "active-harm" in case["deterministic_extractor_signals"]["blocker_signals"]
    assert report["summary"]["accepted_reference_disagreement_count"] == 1
    assert report["summary"]["downgraded_verse_to_fallback_count"] == 0


def test_different_verse_is_review_case(tmp_path: Path) -> None:
    path = _write_fixture(
        tmp_path,
        [
            _case(
                dilemma_id="DIFFERENT",
                dilemma="My manager takes credit for my work. Should I publicly correct him in the next meeting?",
                reference_shape="verse",
                reference_verse_ref="2.47",
                allowed_verse_refs=["2.47"],
            )
        ],
    )

    report = run_reference_benchmark_comparison(fixture_path=path)
    case = report["cases"][0]

    assert case["actual_verse_ref"] == "17.15"
    assert case["category"] == "different_verse_from_reference"
    assert case["needs_human_review"] is True
    assert report["summary"]["different_verse_from_reference_count"] == 1


def test_counts_actual_verse_and_fallback_separately_from_reference(tmp_path: Path) -> None:
    path = _write_fixture(
        tmp_path,
        [
            _case(
                dilemma_id="ACTUAL-VERSE",
                dilemma="My manager takes credit for my work. Should I publicly correct him in the next meeting?",
                reference_shape="fallback",
                reference_verse_ref=None,
                allowed_verse_refs=[],
            ),
            _case(
                dilemma_id="ACTUAL-FALLBACK",
                dilemma="Something feels off about a business deal, but I cannot explain why.",
                reference_shape="verse",
                reference_verse_ref="17.15",
                allowed_verse_refs=["17.15"],
            ),
        ],
    )

    summary = run_reference_benchmark_comparison(fixture_path=path)["summary"]

    assert summary["reference_verse_cases"] == 1
    assert summary["reference_fallback_cases"] == 1
    assert summary["actual_verse_cases"] == 1
    assert summary["actual_fallback_cases"] == 1


def test_no_llm_network_dependency_required() -> None:
    report = run_reference_benchmark_comparison()

    assert report["summary"]["total_cases"] == 50
    assert all(case["engine_error"] is None for case in report["cases"])


def test_comparison_outputs_json_and_markdown(tmp_path: Path) -> None:
    report = run_reference_benchmark_comparison()
    out_json = tmp_path / "comparison.json"
    out_md = tmp_path / "comparison.md"

    write_comparison_outputs(report, out_json=out_json, out_md=out_md)

    assert out_json.exists()
    assert out_md.exists()
    assert "reference-benchmark-comparison-v1" in out_json.read_text(encoding="utf-8")
    assert "# Reference Benchmark Comparison" in out_md.read_text(encoding="utf-8")
