"""Tests for reference-derived retrieval eval fixture builder."""

from __future__ import annotations

import json
from pathlib import Path

from app.evals.build_retrieval_eval_fixture import (
    DEFAULT_OUTPUT_PATH,
    DEFAULT_SOURCE_PATH,
    build_retrieval_eval_fixture,
    write_retrieval_eval_fixture,
)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_raw_complete_reference_benchmark_loads() -> None:
    payload = _load_json(DEFAULT_SOURCE_PATH)

    assert payload["benchmark_version"] == "wisdomize-v2.0-complete"
    assert isinstance(payload["dilemmas"], list)


def test_raw_complete_reference_has_exactly_50_cases() -> None:
    payload = _load_json(DEFAULT_SOURCE_PATH)

    assert len(payload["dilemmas"]) == 50


def test_derived_fixture_has_exactly_50_cases() -> None:
    fixture = build_retrieval_eval_fixture()

    assert fixture["benchmark_version"] == "wisdomize-v2-reference-derived-retrieval-eval"
    assert fixture["source"] == DEFAULT_SOURCE_PATH.name
    assert len(fixture["cases"]) == 50


def test_reference_verse_cases_are_marked_as_verse() -> None:
    fixture = build_retrieval_eval_fixture()
    verse_cases = [case for case in fixture["cases"] if case["reference_shape"] == "verse"]

    assert len(verse_cases) == 29
    for case in verse_cases:
        assert case["reference_verse_ref"]
        assert case["allowed_verse_refs"][0] == case["reference_verse_ref"]


def test_reference_fallback_cases_are_marked_as_fallback() -> None:
    fixture = build_retrieval_eval_fixture()
    fallback_cases = [case for case in fixture["cases"] if case["reference_shape"] == "fallback"]

    assert len(fallback_cases) == 21
    for case in fallback_cases:
        assert case["reference_verse_ref"] is None
        assert case["allowed_verse_refs"] == []


def test_all_cases_allow_different_valid_verse_and_fallback() -> None:
    fixture = build_retrieval_eval_fixture()

    for case in fixture["cases"]:
        assert case["allow_different_valid_verse"] is True
        assert case["allow_fallback"] is True


def test_fixture_policy_marks_benchmark_as_reference_not_gold() -> None:
    fixture = build_retrieval_eval_fixture()
    policy = fixture["policy"]

    assert policy["benchmark_is_reference_not_gold"] is True
    assert policy["verse_null_is_not_strict"] is True
    assert policy["different_valid_verse_allowed"] is True
    assert policy["higher_verse_coverage_allowed"] is True


def test_reference_fallback_is_not_strict_verse_prohibition() -> None:
    fixture = build_retrieval_eval_fixture()
    fallback_case = next(case for case in fixture["cases"] if case["reference_shape"] == "fallback")

    assert fallback_case["allowed_verse_refs"] == []
    assert fallback_case["allow_different_valid_verse"] is True
    assert fixture["policy"]["verse_null_is_not_strict"] is True
    assert fixture["policy"]["higher_verse_coverage_allowed"] is True


def test_w044_reference_precision_allows_active_range() -> None:
    fixture = build_retrieval_eval_fixture()
    w044 = next(case for case in fixture["cases"] if case["dilemma_id"] == "W044")

    assert w044["reference_verse_ref"] == "16.3"
    assert w044["allowed_verse_refs"] == ["16.3", "16.1-3"]
    assert "contains 16.3" in w044["notes"]


def test_write_retrieval_eval_fixture_outputs_expected_payload(tmp_path: Path) -> None:
    out = tmp_path / "retrieval_eval_W001-W050.json"

    fixture = write_retrieval_eval_fixture(source_path=DEFAULT_SOURCE_PATH, output_path=out)

    assert out.exists()
    written = _load_json(out)
    assert written == fixture
    assert len(written["cases"]) == 50


def test_committed_derived_fixture_matches_builder_output() -> None:
    expected = build_retrieval_eval_fixture()
    committed = _load_json(DEFAULT_OUTPUT_PATH)

    assert committed == expected
