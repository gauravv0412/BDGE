"""Build targeted curation review artifact for reference-verse mismatches."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_COMPARISON_PATH = _ROOT / "artifacts" / "benchmark_comparison_W001-W050.json"
DEFAULT_REFERENCE_BENCHMARK_PATH = (
    _ROOT
    / "tests"
    / "fixtures"
    / "benchmarks"
    / "reference"
    / "benchmarks_v2_complete_W001-W050.json"
)
DEFAULT_SEED_PATH = _ROOT / "app" / "verses" / "data" / "curated" / "verses_seed.json"
DEFAULT_OUT_JSON = (
    _ROOT
    / "app"
    / "verses"
    / "data"
    / "curation_prep"
    / "targeted_reviews"
    / "reference_verse_review_W001-W050.json"
)
DEFAULT_OUT_MD = DEFAULT_OUT_JSON.with_suffix(".md")

_TARGET_DILEMMA_IDS = {"W021", "W028", "W029", "W031", "W033", "W036", "W044"}
_APPLIED_CURATED_REFERENCES = {"W021", "W031", "W036"}
_ADD_LATER_REFERENCES = {"W028"}
_DO_NOT_ADD_REFERENCES = {"W029"}
_CURRENT_ACTUAL_BETTER = {"W033"}


def _load_json(path: Path) -> dict[str, Any] | list[Any]:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _case_by_id(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    cases = payload.get("cases")
    if not isinstance(cases, list):
        raise ValueError("Comparison payload must contain a cases array.")
    return {str(case.get("dilemma_id")): case for case in cases if isinstance(case, dict)}


def _reference_by_id(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    dilemmas = payload.get("dilemmas")
    if not isinstance(dilemmas, list):
        raise ValueError("Reference benchmark payload must contain a dilemmas array.")
    return {str(item.get("dilemma_id")): item for item in dilemmas if isinstance(item, dict)}


def _seed_entries_by_ref(seed_payload: list[Any]) -> dict[str, list[dict[str, Any]]]:
    entries: dict[str, list[dict[str, Any]]] = {}
    for item in seed_payload:
        if not isinstance(item, dict):
            continue
        ref = item.get("verse_ref")
        if isinstance(ref, str) and ref.strip():
            entries.setdefault(ref.strip(), []).append(item)
    return entries


def _active_seed_refs(seed_payload: list[Any]) -> set[str]:
    return {
        str(item.get("verse_ref")).strip()
        for item in seed_payload
        if isinstance(item, dict)
        and str(item.get("verse_ref", "")).strip()
        and item.get("status") == "active"
    }


def _parse_ref(ref: str) -> tuple[int, int, int] | None:
    if "." not in ref:
        return None
    chapter_s, verse_s = ref.split(".", 1)
    if not chapter_s.isdigit():
        return None
    if "-" in verse_s:
        start_s, end_s = verse_s.split("-", 1)
    else:
        start_s = verse_s
        end_s = verse_s
    if not start_s.isdigit() or not end_s.isdigit():
        return None
    return int(chapter_s), int(start_s), int(end_s)


def _equivalent_active_range(ref: str, active_refs: set[str]) -> str | None:
    parsed = _parse_ref(ref)
    if parsed is None:
        return None
    chapter, start, end = parsed
    for active_ref in sorted(active_refs):
        active_parsed = _parse_ref(active_ref)
        if active_parsed is None:
            continue
        active_chapter, active_start, active_end = active_parsed
        if active_chapter == chapter and active_start <= start and end <= active_end and active_ref != ref:
            return active_ref
    return None


def _actual_label(case: dict[str, Any]) -> str:
    actual_ref = case.get("actual_verse_ref")
    return str(actual_ref).strip() if isinstance(actual_ref, str) and actual_ref.strip() else "fallback"


def _reference_verse_text(reference_case: dict[str, Any]) -> dict[str, Any] | None:
    verse_match = reference_case.get("verse_match")
    return verse_match if isinstance(verse_match, dict) else None


def _diagnosis_and_action(
    *,
    dilemma_id: str,
    reference_ref: str,
    actual_label: str,
    reference_active: bool,
    equivalent_range: str | None,
) -> tuple[str, str, str]:
    if dilemma_id == "W044" and equivalent_range:
        return (
            "fixture_precision",
            "update_allowed_verse_refs",
            f"Reference {reference_ref} is contained in active range {equivalent_range}; update eval allowance before metadata work.",
        )
    if dilemma_id in _APPLIED_CURATED_REFERENCES and reference_active and actual_label == reference_ref:
        return (
            "current_actual_acceptable",
            "keep_current_actual",
            f"Approved reference {reference_ref} is now active and current retrieval matches it.",
        )
    if dilemma_id in _CURRENT_ACTUAL_BETTER and actual_label != "fallback":
        return (
            "current_actual_acceptable",
            "keep_current_actual",
            f"Reference {reference_ref} remains inactive; current {actual_label} was approved as the better active match.",
        )
    if dilemma_id in _DO_NOT_ADD_REFERENCES:
        return (
            "current_actual_acceptable",
            "keep_current_actual",
            f"Reference {reference_ref} remains inactive by review decision; keep the current fallback.",
        )
    if dilemma_id in _ADD_LATER_REFERENCES:
        return (
            "inactive_reference_verse_candidate",
            "consider_curated_addition",
            f"Reference {reference_ref} remains inactive and is marked add-later for a future curation batch.",
        )
    if actual_label == "fallback":
        return (
            "inactive_reference_verse_candidate",
            "consider_curated_addition",
            f"Reference {reference_ref} is inactive and current retrieval falls back, suggesting this topic may be underserved.",
        )
    if reference_active:
        return (
            "current_actual_acceptable",
            "keep_current_actual",
            f"Reference {reference_ref} is active, but current {actual_label} may be a valid reference-not-gold disagreement.",
        )
    return (
        "needs_human_curation_review",
        "needs_claude_metadata_review",
        f"Reference {reference_ref} is inactive and no narrow automated recommendation applies.",
    )


def _build_review_case(
    *,
    dilemma_id: str,
    comparison_case: dict[str, Any],
    reference_case: dict[str, Any],
    seed_by_ref: dict[str, list[dict[str, Any]]],
    active_refs: set[str],
) -> dict[str, Any]:
    reference_ref = str(comparison_case.get("reference_verse_ref", "")).strip()
    actual_label = _actual_label(comparison_case)
    reference_entries = seed_by_ref.get(reference_ref, [])
    reference_active = reference_ref in active_refs
    equivalent_range = _equivalent_active_range(reference_ref, active_refs)
    diagnosis, recommended_action, rationale = _diagnosis_and_action(
        dilemma_id=dilemma_id,
        reference_ref=reference_ref,
        actual_label=actual_label,
        reference_active=reference_active,
        equivalent_range=equivalent_range,
    )

    return {
        "dilemma_id": dilemma_id,
        "dilemma": comparison_case.get("dilemma"),
        "reference_verse_ref": reference_ref,
        "current_actual_verse_or_fallback": actual_label,
        "current_category": comparison_case.get("category"),
        "reference_verse_active_in_seed": reference_active,
        "reference_verse_seed_statuses": sorted(
            {str(entry.get("status", "unknown")) for entry in reference_entries}
        ),
        "equivalent_active_range_exists": equivalent_range is not None,
        "equivalent_active_range_ref": equivalent_range,
        "current_top_5_candidates": comparison_case.get("top_5_candidates", []),
        "diagnosis": diagnosis,
        "recommended_action": recommended_action,
        "rationale": rationale,
        "reference_verse_match": _reference_verse_text(reference_case),
    }


def build_targeted_curation_review(
    *,
    comparison_path: Path = DEFAULT_COMPARISON_PATH,
    reference_benchmark_path: Path = DEFAULT_REFERENCE_BENCHMARK_PATH,
    seed_path: Path = DEFAULT_SEED_PATH,
) -> dict[str, Any]:
    comparison_payload = _load_json(comparison_path)
    reference_payload = _load_json(reference_benchmark_path)
    seed_payload = _load_json(seed_path)
    if not isinstance(comparison_payload, dict):
        raise ValueError("Comparison artifact must be a JSON object.")
    if not isinstance(reference_payload, dict):
        raise ValueError("Reference benchmark must be a JSON object.")
    if not isinstance(seed_payload, list):
        raise ValueError("Verse seed must be a JSON array.")

    comparison_by_id = _case_by_id(comparison_payload)
    reference_by_id = _reference_by_id(reference_payload)
    seed_by_ref = _seed_entries_by_ref(seed_payload)
    active_refs = _active_seed_refs(seed_payload)

    cases = [
        _build_review_case(
            dilemma_id=dilemma_id,
            comparison_case=comparison_by_id[dilemma_id],
            reference_case=reference_by_id[dilemma_id],
            seed_by_ref=seed_by_ref,
            active_refs=active_refs,
        )
        for dilemma_id in sorted(_TARGET_DILEMMA_IDS)
    ]

    return {
        "artifact_version": "targeted-reference-verse-review-v1",
        "scope": "W001-W050 metadata/scoring review cases from reference benchmark comparison",
        "source_paths": {
            "comparison": str(comparison_path),
            "reference_benchmark": str(reference_benchmark_path),
            "verses_seed": str(seed_path),
        },
        "policy": {
            "benchmark_is_reference_not_gold": True,
            "do_not_promote_blindly": True,
            "active_seed_unchanged": True,
            "accepted_disagreements_excluded": ["W024", "W050"],
        },
        "summary": {
            "total_cases": len(cases),
            "fixture_precision_cases": [
                case["dilemma_id"] for case in cases if case["diagnosis"] == "fixture_precision"
            ],
            "curated_addition_candidates": [
                case["dilemma_id"]
                for case in cases
                if case["recommended_action"] == "consider_curated_addition"
            ],
            "current_actual_may_be_acceptable": [
                case["dilemma_id"]
                for case in cases
                if case["recommended_action"] == "keep_current_actual"
            ],
        },
        "cases": cases,
    }


def render_markdown_review(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Targeted Reference Verse Review W001-W050",
        "",
        f"- Total cases: {summary['total_cases']}",
        f"- Fixture precision cases: {', '.join(summary['fixture_precision_cases']) or 'None'}",
        f"- Curated addition candidates: {', '.join(summary['curated_addition_candidates']) or 'None'}",
        (
            "- Current actual may be acceptable: "
            f"{', '.join(summary['current_actual_may_be_acceptable']) or 'None'}"
        ),
        "",
        "## Cases",
    ]
    for case in report["cases"]:
        top = case["current_top_5_candidates"][0] if case["current_top_5_candidates"] else None
        top_text = (
            f"{top['verse_ref']} score={top['total_score']} themes={top['theme_overlap']} "
            f"applies={top['applies_when_hits']}"
            if top
            else "No candidate captured"
        )
        lines.extend(
            [
                f"### `{case['dilemma_id']}`",
                f"- Reference: `{case['reference_verse_ref']}`",
                f"- Current actual: `{case['current_actual_verse_or_fallback']}`",
                f"- Current category: `{case['current_category']}`",
                f"- Active in seed: `{case['reference_verse_active_in_seed']}`",
                f"- Equivalent active range: `{case['equivalent_active_range_ref']}`",
                f"- Diagnosis: `{case['diagnosis']}`",
                f"- Recommended action: `{case['recommended_action']}`",
                f"- Top candidate: {top_text}",
                f"- Rationale: {case['rationale']}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def write_targeted_curation_review(report: dict[str, Any], *, out_json: Path, out_md: Path) -> None:
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    out_md.write_text(render_markdown_review(report), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build targeted curation review for W001-W050 references.")
    parser.add_argument("--comparison", type=Path, default=DEFAULT_COMPARISON_PATH)
    parser.add_argument("--reference-benchmark", type=Path, default=DEFAULT_REFERENCE_BENCHMARK_PATH)
    parser.add_argument("--seed", type=Path, default=DEFAULT_SEED_PATH)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    args = parser.parse_args()

    report = build_targeted_curation_review(
        comparison_path=args.comparison,
        reference_benchmark_path=args.reference_benchmark,
        seed_path=args.seed,
    )
    write_targeted_curation_review(report, out_json=args.out_json, out_md=args.out_md)
    print(
        "Targeted curation review:"
        f" total_cases={report['summary']['total_cases']},"
        f" fixture_precision={len(report['summary']['fixture_precision_cases'])},"
        f" curated_addition_candidates={len(report['summary']['curated_addition_candidates'])}"
    )
    print(f"Saved JSON review to: {args.out_json}")
    print(f"Saved Markdown review to: {args.out_md}")


if __name__ == "__main__":
    main()
