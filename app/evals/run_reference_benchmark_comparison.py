"""Compare current retrieval behavior against reference benchmark outputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from app.core.models import EngineAnalyzeErrorResponse
from app.engine import analyzer as engine_analyzer
from app.evals.run_live_retrieval_audit import (
    EngineHandler,
    SemanticScorer,
    _actual_label,
    _context_row,
    _deterministic_signal_row,
    _run_one_live_case,
    _semantic_signal_row,
    _source_row,
    _top_candidates,
)
from app.evals.run_retrieval_audit import _pct
from app.verses.catalog import VerseCatalog
from app.verses.loader import load_curated_verses
from app.verses.scorer import RetrievalContext

_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RETRIEVAL_EVAL_PATH = (
    _ROOT
    / "tests"
    / "fixtures"
    / "benchmarks"
    / "retrieval_eval"
    / "retrieval_eval_W001-W050.json"
)
DEFAULT_OUT_JSON = _ROOT / "artifacts" / "benchmark_comparison_W001-W050.json"
DEFAULT_OUT_MD = _ROOT / "artifacts" / "benchmark_comparison_W001-W050.md"
_ACCEPTED_FALLBACK_BLOCKERS = {
    "abuse-context",
    "active-harm",
    "self-harm",
    "scripture-as-weapon",
}


def _load_retrieval_eval_fixture(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        payload = json.load(f)
    if not isinstance(payload, dict) or not isinstance(payload.get("cases"), list):
        raise ValueError(f"Expected retrieval eval fixture with cases array: {path}")
    return payload


def _actual_shape(actual_ref: str | None) -> str:
    return "verse" if actual_ref is not None else "fallback"


def _weak_retrieval_diagnostics(actual_label: str, top_candidates: list[dict[str, Any]]) -> bool:
    if actual_label == "fallback" or not top_candidates:
        return False
    winner = top_candidates[0]
    return (
        winner["theme_overlap_count"] < 2
        or winner["applies_when_hits_count"] == 0
        or winner["blocker_hits_count"] > 0
        or bool(winner["rejected"])
    )


def _raw_category(
    *,
    reference_shape: str,
    reference_verse_ref: str | None,
    allowed_verse_refs: list[str],
    actual_label: str,
    engine_error: Any,
) -> str:
    if engine_error is not None:
        return "unexpected_error"
    if reference_shape == "verse" and actual_label == reference_verse_ref:
        return "same_reference_verse"
    if reference_shape == "fallback" and actual_label == "fallback":
        return "same_reference_fallback"
    if reference_shape == "fallback" and actual_label != "fallback":
        return "upgraded_fallback_to_verse"
    if reference_shape == "verse" and actual_label == "fallback":
        return "downgraded_verse_to_fallback"
    if reference_shape == "verse" and actual_label != reference_verse_ref:
        if actual_label in allowed_verse_refs:
            return "same_reference_verse"
        return "different_verse_from_reference"
    return "unexpected_error"


def _active_verse_refs() -> set[str]:
    return {entry.verse_ref for entry in VerseCatalog(load_curated_verses()).list_active()}


def _diagnosed_category(
    *,
    raw_category: str,
    reference_verse_ref: str | None,
    actual_label: str,
    context: RetrievalContext | None,
    curated_refs: set[str],
    top_candidates: list[dict[str, Any]],
) -> tuple[str, str | None]:
    if raw_category != "downgraded_verse_to_fallback":
        if raw_category == "different_verse_from_reference" and reference_verse_ref not in curated_refs:
            return (
                "needs_review_metadata_or_scoring",
                f"Reference verse {reference_verse_ref} is not active in the curated retrieval catalog.",
            )
        return raw_category, None
    blocker_signals = set(context.blocker_signals if context is not None else [])
    if blocker_signals & _ACCEPTED_FALLBACK_BLOCKERS:
        blockers = sorted(blocker_signals & _ACCEPTED_FALLBACK_BLOCKERS)
        return (
            "accepted_reference_disagreement",
            f"Fallback preserved because context includes severe blocker(s): {', '.join(blockers)}.",
        )
    if reference_verse_ref not in curated_refs:
        return (
            "needs_review_metadata_or_scoring",
            f"Reference verse {reference_verse_ref} is not active in the curated retrieval catalog.",
        )
    if context is None or not (context.theme_tags or context.applies_signals or context.blocker_signals):
        return (
            "needs_review_extractor",
            "Live context has no deterministic theme/apply/blocker signals for a reference verse case.",
        )
    if top_candidates and top_candidates[0]["total_score"] < 6:
        return (
            "needs_review_metadata_or_scoring",
            "Signals exist, but the top candidate remains below the retrieval threshold.",
        )
    return (
        "downgraded_verse_to_fallback",
        "Reference had a verse but current retrieval fell back; diagnosis is unresolved.",
    )


def _review_reason(
    *,
    category: str,
    reference_verse_ref: str | None,
    actual_label: str,
    top_candidates: list[dict[str, Any]],
    diagnostic_reason: str | None = None,
) -> str | None:
    weak = _weak_retrieval_diagnostics(actual_label, top_candidates)
    if category == "unexpected_error":
        return "Engine or retrieval returned an error."
    if category == "accepted_reference_disagreement":
        return diagnostic_reason
    if category in {"needs_review_extractor", "needs_review_metadata_or_scoring"}:
        return diagnostic_reason
    if category == "downgraded_verse_to_fallback":
        return "Reference had a verse but current retrieval fell back; possible regression."
    if category == "different_verse_from_reference":
        return (
            f"Reference verse was {reference_verse_ref}, current retrieval chose {actual_label}; "
            "different valid verses are allowed but need review."
        )
    if category == "upgraded_fallback_to_verse":
        if weak:
            return "Reference fallback became verse, but retrieval diagnostics look weak; review for forced match."
        return "Reference fallback became verse; higher coverage is allowed, but review the fit."
    return None


def _needs_human_review(category: str, review_reason: str | None) -> bool:
    return category in {
        "unexpected_error",
        "downgraded_verse_to_fallback",
        "needs_review_extractor",
        "needs_review_metadata_or_scoring",
        "different_verse_from_reference",
        "upgraded_fallback_to_verse",
    } and review_reason is not None


def _summary(cases: list[dict[str, Any]]) -> dict[str, Any]:
    total_cases = len(cases)
    reference_verse_cases = sum(1 for case in cases if case["reference_shape"] == "verse")
    actual_verse_cases = sum(1 for case in cases if case["actual_shape"] == "verse")
    categories = {
        "same_reference_verse_count": "same_reference_verse",
        "same_reference_fallback_count": "same_reference_fallback",
        "upgraded_fallback_to_verse_count": "upgraded_fallback_to_verse",
        "downgraded_verse_to_fallback_count": "downgraded_verse_to_fallback",
        "accepted_reference_disagreement_count": "accepted_reference_disagreement",
        "needs_review_extractor_count": "needs_review_extractor",
        "needs_review_metadata_or_scoring_count": "needs_review_metadata_or_scoring",
        "different_verse_from_reference_count": "different_verse_from_reference",
        "unexpected_error_count": "unexpected_error",
    }
    summary = {
        "total_cases": total_cases,
        "reference_verse_cases": reference_verse_cases,
        "reference_fallback_cases": total_cases - reference_verse_cases,
        "actual_verse_cases": actual_verse_cases,
        "actual_fallback_cases": total_cases - actual_verse_cases,
        "actual_verse_coverage_pct": _pct(actual_verse_cases, total_cases),
        "reference_verse_coverage_pct": _pct(reference_verse_cases, total_cases),
        "needs_human_review_count": sum(1 for case in cases if case["needs_human_review"]),
        "raw_downgraded_verse_to_fallback_count": sum(
            1 for case in cases if case["raw_category"] == "downgraded_verse_to_fallback"
        ),
    }
    for key, category in categories.items():
        summary[key] = sum(1 for case in cases if case["category"] == category)
    return summary


def run_reference_benchmark_comparison(
    *,
    fixture_path: Path = DEFAULT_RETRIEVAL_EVAL_PATH,
    handler: EngineHandler | None = None,
    semantic_scorer_override: SemanticScorer | None = None,
) -> dict[str, Any]:
    fixture = _load_retrieval_eval_fixture(fixture_path)
    engine_handler = handler or engine_analyzer.handle_engine_request
    curated_refs = _active_verse_refs()
    cases: list[dict[str, Any]] = []

    for item in fixture["cases"]:
        response, context, captured_dimensions, semantic_payload = _run_one_live_case(
            item,
            handler=engine_handler,
            semantic_scorer_override=semantic_scorer_override,
        )
        output = response.get("output") if isinstance(response.get("output"), dict) else {}
        engine_error = response.get("error")
        if isinstance(response, EngineAnalyzeErrorResponse):
            engine_error = response.model_dump(mode="json")["error"]

        verse_match = output.get("verse_match") if isinstance(output, dict) else None
        actual_ref = verse_match.get("verse_ref") if isinstance(verse_match, dict) else None
        actual_label = _actual_label(actual_ref)
        top_candidates = _top_candidates(context)
        reference_shape = str(item["reference_shape"])
        reference_verse_ref = item.get("reference_verse_ref")
        allowed_verse_refs = [
            str(ref).strip()
            for ref in item.get("allowed_verse_refs", [])
            if str(ref).strip()
        ]
        raw_category = _raw_category(
            reference_shape=reference_shape,
            reference_verse_ref=reference_verse_ref,
            allowed_verse_refs=allowed_verse_refs,
            actual_label=actual_label,
            engine_error=engine_error,
        )
        category, diagnostic_reason = _diagnosed_category(
            raw_category=raw_category,
            reference_verse_ref=reference_verse_ref,
            actual_label=actual_label,
            context=context,
            curated_refs=curated_refs,
            top_candidates=top_candidates,
        )
        review_reason = _review_reason(
            category=category,
            reference_verse_ref=reference_verse_ref,
            actual_label=actual_label,
            top_candidates=top_candidates,
            diagnostic_reason=diagnostic_reason,
        )
        semantic_signals = _semantic_signal_row(semantic_payload, captured_dimensions)
        deterministic_signals = _deterministic_signal_row(str(item.get("dilemma", "")))
        signal_sources = _source_row(
            final_context=context,
            semantic_signals=semantic_signals,
            deterministic_signals=deterministic_signals,
        )
        winner = top_candidates[0] if top_candidates else None

        cases.append(
            {
                "dilemma_id": str(item["dilemma_id"]),
                "dilemma": str(item["dilemma"]),
                "reference_classification": item.get("reference_classification"),
                "actual_classification": output.get("classification") if isinstance(output, dict) else None,
                "reference_shape": reference_shape,
                "reference_verse_ref": reference_verse_ref,
                "actual_shape": _actual_shape(actual_ref),
                "actual_verse_ref": actual_ref,
                "allowed_verse_refs": allowed_verse_refs,
                "raw_category": raw_category,
                "category": category,
                "diagnostic_reason": diagnostic_reason,
                "needs_human_review": _needs_human_review(category, review_reason),
                "review_reason": review_reason,
                "top_5_candidates": top_candidates,
                "score_breakdown": winner,
                "theme_overlaps": winner["theme_overlap"] if winner else [],
                "applies_when_hits": winner["applies_when_hits"] if winner else [],
                "blocker_hits": winner["blocker_hits"] if winner else [],
                "deterministic_extractor_signals": deterministic_signals,
                "semantic_context_signals": semantic_signals,
                "signal_sources": signal_sources,
                "retrieval_context": _context_row(context),
                "engine_error": engine_error,
            }
        )

    return {
        "comparison_version": "reference-benchmark-comparison-v1",
        "fixture_path": str(fixture_path),
        "source": fixture.get("source"),
        "policy": fixture.get("policy", {}),
        "summary": _summary(cases),
        "cases": sorted(cases, key=_risk_sort_key),
    }


def _risk_sort_key(case: dict[str, Any]) -> tuple[int, str]:
    order = {
        "unexpected_error": 0,
        "downgraded_verse_to_fallback": 1,
        "needs_review_extractor": 2,
        "needs_review_metadata_or_scoring": 3,
        "different_verse_from_reference": 4,
        "accepted_reference_disagreement": 5,
        "upgraded_fallback_to_verse": 6,
        "same_reference_fallback": 7,
        "same_reference_verse": 8,
    }
    return (order.get(case["category"], 99), case["dilemma_id"])


def _answer_label(shape: str, verse_ref: str | None) -> str:
    return verse_ref if shape == "verse" and verse_ref is not None else "fallback"


def render_markdown_report(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Reference Benchmark Comparison",
        "",
        f"- Fixture: `{report['fixture_path']}`",
        f"- Total cases: {summary['total_cases']}",
        f"- Reference verse coverage: {summary['reference_verse_coverage_pct']}%",
        f"- Actual verse coverage: {summary['actual_verse_coverage_pct']}%",
        f"- Needs human review: {summary['needs_human_review_count']}",
        "",
        "## Summary",
    ]
    for key in (
        "same_reference_verse_count",
        "same_reference_fallback_count",
        "upgraded_fallback_to_verse_count",
        "downgraded_verse_to_fallback_count",
        "accepted_reference_disagreement_count",
        "needs_review_extractor_count",
        "needs_review_metadata_or_scoring_count",
        "different_verse_from_reference_count",
        "unexpected_error_count",
        "raw_downgraded_verse_to_fallback_count",
    ):
        lines.append(f"- `{key}`: {summary[key]}")

    lines.append("")
    lines.append("## Needs Human Review")
    review_cases = [case for case in report["cases"] if case["needs_human_review"]]
    if not review_cases:
        lines.append("None.")
    else:
        for case in review_cases:
            top = case["top_5_candidates"][0] if case["top_5_candidates"] else None
            top_explanation = (
                f"{top['verse_ref']} score={top['total_score']} "
                f"themes={top['theme_overlap']} applies={top['applies_when_hits']} "
                f"blockers={top['blocker_hits']}"
                if top
                else "No candidates captured."
            )
            lines.extend(
                [
                    f"### `{case['dilemma_id']}` {case['category']}",
                    (
                        "- Reference answer: "
                        f"`{_answer_label(case['reference_shape'], case['reference_verse_ref'])}`"
                    ),
                    (
                        "- Actual answer: "
                        f"`{_answer_label(case['actual_shape'], case['actual_verse_ref'])}`"
                    ),
                    f"- Top candidate: {top_explanation}",
                    f"- Review reason: {case['review_reason']}",
                    "",
                ]
            )

    lines.append("## All Cases By Risk")
    for case in report["cases"]:
        lines.append(
            f"- `{case['dilemma_id']}` {case['category']}: "
            f"reference `{_answer_label(case['reference_shape'], case['reference_verse_ref'])}`, "
            f"actual `{_answer_label(case['actual_shape'], case['actual_verse_ref'])}`"
        )
    return "\n".join(lines).rstrip() + "\n"


def write_comparison_outputs(report: dict[str, Any], *, out_json: Path, out_md: Path) -> None:
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    out_md.write_text(render_markdown_report(report), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare current retrieval behavior against W001-W050 reference benchmark."
    )
    parser.add_argument("--fixture", type=Path, default=DEFAULT_RETRIEVAL_EVAL_PATH)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    args = parser.parse_args()

    report = run_reference_benchmark_comparison(fixture_path=args.fixture)
    write_comparison_outputs(report, out_json=args.out_json, out_md=args.out_md)
    summary = report["summary"]
    print(
        "Reference benchmark comparison:"
        f" total_cases={summary['total_cases']},"
        f" actual_verse_cases={summary['actual_verse_cases']},"
        f" reference_verse_cases={summary['reference_verse_cases']},"
        f" unresolved_downgrades={summary['downgraded_verse_to_fallback_count']},"
        f" needs_human_review={summary['needs_human_review_count']}"
    )
    print(f"Saved JSON report to: {args.out_json}")
    print(f"Saved Markdown report to: {args.out_md}")


if __name__ == "__main__":
    main()
