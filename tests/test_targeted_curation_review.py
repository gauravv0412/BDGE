"""Tests for targeted reference-verse curation review artifacts."""

from __future__ import annotations

from app.evals.build_targeted_curation_review import (
    DEFAULT_SEED_PATH,
    build_targeted_curation_review,
    render_markdown_review,
    write_targeted_curation_review,
)


def _review_by_id() -> dict[str, dict]:
    report = build_targeted_curation_review()
    return {case["dilemma_id"]: case for case in report["cases"]}


def test_review_artifact_builds() -> None:
    report = build_targeted_curation_review()

    assert report["artifact_version"] == "targeted-reference-verse-review-v1"
    assert report["policy"]["benchmark_is_reference_not_gold"] is True
    assert report["policy"]["active_seed_unchanged"] is True


def test_exactly_seven_cases_included() -> None:
    report = build_targeted_curation_review()

    assert report["summary"]["total_cases"] == 7
    assert {case["dilemma_id"] for case in report["cases"]} == {
        "W021",
        "W028",
        "W029",
        "W031",
        "W033",
        "W036",
        "W044",
    }


def test_w044_classified_as_fixture_precision() -> None:
    cases = _review_by_id()
    w044 = cases["W044"]

    assert w044["diagnosis"] == "fixture_precision"
    assert w044["recommended_action"] == "update_allowed_verse_refs"
    assert w044["equivalent_active_range_exists"] is True
    assert w044["equivalent_active_range_ref"] == "16.1-3"


def test_accepted_disagreements_are_not_included() -> None:
    report = build_targeted_curation_review()
    included = {case["dilemma_id"] for case in report["cases"]}

    assert "W024" not in included
    assert "W050" not in included
    assert report["policy"]["accepted_disagreements_excluded"] == ["W024", "W050"]


def test_inactive_reference_verses_are_not_written_into_active_seed() -> None:
    before = DEFAULT_SEED_PATH.read_text(encoding="utf-8")

    build_targeted_curation_review()

    after = DEFAULT_SEED_PATH.read_text(encoding="utf-8")
    assert after == before


def test_recommendations_are_present_for_all_cases() -> None:
    report = build_targeted_curation_review()

    for case in report["cases"]:
        assert case["diagnosis"]
        assert case["recommended_action"]
        assert case["rationale"]


def test_specific_recommendation_groups_after_step_28e_decisions() -> None:
    cases = _review_by_id()

    for dilemma_id in ("W021", "W031", "W036"):
        assert cases[dilemma_id]["recommended_action"] == "keep_current_actual"
        assert cases[dilemma_id]["reference_verse_active_in_seed"] is True
        assert "current retrieval matches" in cases[dilemma_id]["rationale"]

    assert cases["W028"]["recommended_action"] == "consider_curated_addition"
    assert "add-later" in cases["W028"]["rationale"]

    assert cases["W029"]["recommended_action"] == "keep_current_actual"
    assert "review decision" in cases["W029"]["rationale"]

    assert cases["W033"]["recommended_action"] == "keep_current_actual"
    assert "better active match" in cases["W033"]["rationale"]


def test_markdown_and_json_outputs_are_written(tmp_path) -> None:
    report = build_targeted_curation_review()
    out_json = tmp_path / "review.json"
    out_md = tmp_path / "review.md"

    write_targeted_curation_review(report, out_json=out_json, out_md=out_md)

    assert out_json.exists()
    assert out_md.exists()
    assert "targeted-reference-verse-review-v1" in out_json.read_text(encoding="utf-8")
    assert "# Targeted Reference Verse Review W001-W050" in out_md.read_text(encoding="utf-8")


def test_no_scoring_schema_or_transport_dependency_required() -> None:
    md = render_markdown_review(build_targeted_curation_review())

    assert "retrieval scoring" not in md.lower()
    assert "django" not in md.lower()
