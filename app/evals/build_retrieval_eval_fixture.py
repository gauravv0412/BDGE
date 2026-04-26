"""Build retrieval-eval fixture from reference benchmark outputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE_PATH = (
    _ROOT
    / "tests"
    / "fixtures"
    / "benchmarks"
    / "reference"
    / "benchmarks_v2_complete_W001-W050.json"
)
DEFAULT_OUTPUT_PATH = (
    _ROOT
    / "tests"
    / "fixtures"
    / "benchmarks"
    / "retrieval_eval"
    / "retrieval_eval_W001-W050.json"
)

_POLICY = {
    "benchmark_is_reference_not_gold": True,
    "verse_null_is_not_strict": True,
    "different_valid_verse_allowed": True,
    "higher_verse_coverage_allowed": True,
}
_REFERENCE_RANGE_EQUIVALENTS = {
    "16.3": "16.1-3",
}


def _load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        payload = json.load(f)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected object payload in {path}")
    return payload


def _reference_verse_ref(item: dict[str, Any]) -> str | None:
    verse_match = item.get("verse_match")
    if isinstance(verse_match, dict):
        ref = verse_match.get("verse_ref")
        if isinstance(ref, str) and ref.strip():
            return ref.strip()
    return None


def _build_case(item: dict[str, Any]) -> dict[str, Any]:
    dilemma_id = str(item.get("dilemma_id", "")).strip()
    dilemma = str(item.get("dilemma", "")).strip()
    classification = str(item.get("classification", "")).strip()
    if not dilemma_id or not dilemma or not classification:
        raise ValueError(f"Benchmark case missing required reference fields: {dilemma_id!r}")

    verse_ref = _reference_verse_ref(item)
    if verse_ref is not None:
        reference_shape = "verse"
        allowed_verse_refs = [verse_ref]
        equivalent_ref = _REFERENCE_RANGE_EQUIVALENTS.get(verse_ref)
        if equivalent_ref is not None:
            allowed_verse_refs.append(equivalent_ref)
    else:
        reference_shape = "fallback"
        allowed_verse_refs = []
    notes = "Reference verse/fallback is advisory, not gold."
    if verse_ref in _REFERENCE_RANGE_EQUIVALENTS:
        notes += (
            f" Active seed uses range {_REFERENCE_RANGE_EQUIVALENTS[verse_ref]}, "
            f"which contains {verse_ref}."
        )

    return {
        "dilemma_id": dilemma_id,
        "dilemma": dilemma,
        "reference_classification": classification,
        "reference_shape": reference_shape,
        "reference_verse_ref": verse_ref,
        "allowed_verse_refs": allowed_verse_refs,
        "allow_different_valid_verse": True,
        "allow_fallback": True,
        "notes": notes,
    }


def build_retrieval_eval_fixture(*, source_path: Path = DEFAULT_SOURCE_PATH) -> dict[str, Any]:
    """Return derived retrieval-eval fixture from complete W001-W050 reference benchmark."""
    source = _load_json(source_path)
    raw_cases = source.get("dilemmas")
    if not isinstance(raw_cases, list):
        raise ValueError("Reference benchmark must contain a dilemmas array.")
    if len(raw_cases) != 50:
        raise ValueError(f"Expected 50 reference cases, found {len(raw_cases)}.")

    cases = [_build_case(item) for item in raw_cases if isinstance(item, dict)]
    if len(cases) != 50:
        raise ValueError("Reference dilemmas array contains non-object cases.")

    return {
        "benchmark_version": "wisdomize-v2-reference-derived-retrieval-eval",
        "source": source_path.name,
        "policy": dict(_POLICY),
        "cases": cases,
    }


def write_retrieval_eval_fixture(
    *,
    source_path: Path = DEFAULT_SOURCE_PATH,
    output_path: Path = DEFAULT_OUTPUT_PATH,
) -> dict[str, Any]:
    fixture = build_retrieval_eval_fixture(source_path=source_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(fixture, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return fixture


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build reference-derived retrieval eval fixture for W001-W050."
    )
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args()

    fixture = write_retrieval_eval_fixture(source_path=args.source, output_path=args.output)
    verse_cases = sum(1 for case in fixture["cases"] if case["reference_shape"] == "verse")
    fallback_cases = sum(1 for case in fixture["cases"] if case["reference_shape"] == "fallback")
    print(
        "Built retrieval eval fixture:"
        f" total={len(fixture['cases'])},"
        f" reference_verse_cases={verse_cases},"
        f" reference_fallback_cases={fallback_cases},"
        f" output={args.output}"
    )


if __name__ == "__main__":
    main()
