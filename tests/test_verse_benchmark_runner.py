"""Tests for verse retrieval benchmark evaluation harness."""

from __future__ import annotations

from app.core.benchmark_loader import OOD_VERSE_RETRIEVAL_BATCH1_PATH, load_benchmark_file
from app.evals.run_verse_retrieval_benchmarks import (
    _expected_retrieval_verse_ref,
    _expects_closest_teaching_only,
    run_verse_retrieval_benchmarks,
)


def test_benchmark_report_shape() -> None:
    report = run_verse_retrieval_benchmarks()
    required_keys = {
        "benchmark_source_path",
        "evaluation_label",
        "total_dilemmas",
        "verse_present_count",
        "closest_teaching_count",
        "top1_exact_match_count",
        "null_match_agreement_count",
        "per_verse_usage_counts",
        "max_single_verse_reuse",
        "max_single_verse_reuse_pct",
        "blocker_suppressed_cases",
        "false_positive_cases",
        "false_positive_count",
        "differs_from_benchmark_cases",
        "style_check_failures",
        "obvious_case_results",
        "obvious_case_agreement_count",
        "cases",
    }
    assert required_keys.issubset(report.keys())
    assert report["total_dilemmas"] == 20
    assert report["verse_present_count"] + report["closest_teaching_count"] == 20
    assert "benchmarks_v2_batch1" in report["benchmark_source_path"]


def test_obvious_case_agreement_reporting() -> None:
    report = run_verse_retrieval_benchmarks()
    obvious_refs = {"2.47", "3.37", "5.18", "17.15", "17.20", "16.21", "18.47"}
    case_refs = {
        row["benchmark_verse_ref"]
        for row in report["obvious_case_results"]
        if row["benchmark_verse_ref"] is not None
    }
    assert obvious_refs.issuperset(case_refs)
    assert report["obvious_case_agreement_count"] >= 2


def test_null_match_agreement_on_known_benchmark_cases() -> None:
    report = run_verse_retrieval_benchmarks()
    null_agreed_ids = {
        row["dilemma_id"]
        for row in report["cases"]
        if row["benchmark_verse_ref"] is None and row["retrieved_verse_ref"] is None
    }
    assert {"W007", "W010", "W011"}.issubset(null_agreed_ids)


def test_false_positive_tracking() -> None:
    """Cases where benchmark expects no verse but retrieval returned one are visible."""
    report = run_verse_retrieval_benchmarks()
    fp_ids = {row["dilemma_id"] for row in report["false_positive_cases"]}
    assert report["false_positive_count"] == len(report["false_positive_cases"])
    # W015 (public shaming) must be suppressed — public-shaming-intent is now a severe blocker
    assert "W015" not in fp_ids
    for row in report["false_positive_cases"]:
        assert "false_positive_reason" in row


def test_diff_rows_include_deterministic_diagnosis_keys() -> None:
    report = run_verse_retrieval_benchmarks()
    for row in report["differs_from_benchmark_cases"]:
        assert "mismatch_reason" in row
        assert "likely_fix_type" in row


def test_ood_verse_retrieval_eval_file_loads() -> None:
    meta = load_benchmark_file(OOD_VERSE_RETRIEVAL_BATCH1_PATH)
    assert len(meta.dilemmas) == 20
    first = meta.dilemmas[0]
    assert first.get("dilemma_id", "").startswith("OOD-")


def test_ood_runner_report_compatible_with_batch1_shape() -> None:
    report = run_verse_retrieval_benchmarks(benchmark_path=OOD_VERSE_RETRIEVAL_BATCH1_PATH)
    assert report["total_dilemmas"] == 20
    assert report["evaluation_label"] == "verse_retrieval_ood_batch1"
    assert report["verse_present_count"] + report["closest_teaching_count"] == 20
    for row in report["cases"]:
        assert "expect_closest_teaching_only" in row


def test_expected_retrieval_fields_precedence() -> None:
    item = {
        "verse_match": {"verse_ref": "2.47"},
        "retrieval_golden_verse_ref": "17.15",
        "retrieval_expect_closest_teaching": False,
    }
    assert _expected_retrieval_verse_ref(item) == "17.15"
    assert not _expects_closest_teaching_only(item)
    ct_item = {
        "verse_match": {"verse_ref": "17.15"},
        "retrieval_expect_closest_teaching": True,
    }
    assert _expected_retrieval_verse_ref(ct_item) is None
    assert _expects_closest_teaching_only(ct_item)

