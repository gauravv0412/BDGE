"""Run deterministic curated verse retrieval over benchmark dilemmas."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from app.core.benchmark_loader import DEFAULT_BENCHMARK_PATH, load_dilemmas
from app.core.models import EthicalDimensions
from app.verses.retriever import (
    _infer_applies_signals,
    _infer_blocker_signals,
    _infer_theme_tags,
    retrieve_verse,
)
from app.verses.scorer import RetrievalContext
from app.verses.style_guards import (
    evaluate_closest_teaching_style,
    evaluate_why_it_applies_style,
)
from app.verses.types import DimensionKey


def _dominant_dimensions_from_item(item: dict[str, Any]) -> list[DimensionKey]:
    dims = item.get("ethical_dimensions", {})
    if not isinstance(dims, dict):
        return []
    pairs: list[tuple[DimensionKey, int]] = []
    for key in (
        "dharma_duty",
        "satya_truth",
        "ahimsa_nonharm",
        "nishkama_detachment",
        "shaucha_intent",
        "sanyama_restraint",
        "lokasangraha_welfare",
        "viveka_discernment",
    ):
        value = dims.get(key, {})
        score = value.get("score") if isinstance(value, dict) else None
        if isinstance(score, int):
            pairs.append((key, abs(score)))
    ranked = sorted(pairs, key=lambda item: item[1], reverse=True)
    return [name for name, magnitude in ranked if magnitude >= 2][:4]


def _diagnose_top1_mismatch(
    *,
    expected_ref: str | None,
    retrieved_ref: str | None,
) -> tuple[str, str]:
    """Deterministic (expected_ref, retrieved_ref) → (reason, likely_fix_type)."""
    if expected_ref is None or retrieved_ref is None:
        return ("n/a", "n/a")
    if expected_ref == retrieved_ref:
        return ("n/a", "n/a")
    return (
        f"expected_{expected_ref}_got_{retrieved_ref}",
        "inference_gap_or_scoring_bias",
    )


def _diagnose_false_positive(*, retrieved_ref: str | None) -> str:
    if not retrieved_ref:
        return "n/a"
    return f"retrieval_emitted_{retrieved_ref}_while_eval_expects_closest_teaching_only"


def _diagnose_miss(
    *,
    expected_ref: str | None,
    retrieved_ref: str | None,
) -> tuple[str, str]:
    if expected_ref is None or retrieved_ref is not None:
        return ("n/a", "n/a")
    return ("expected_verse_but_no_match_above_threshold", "inference_gap_or_scoring_bias")


def _expected_retrieval_verse_ref(item: dict[str, Any]) -> str | None:
    """
    Expected top-1 verse_ref for eval agreement.

    Precedence: explicit ``retrieval_expect_closest_teaching`` (no verse) →
    ``retrieval_golden_verse_ref`` → golden ``verse_match.verse_ref``.
    """
    if item.get("retrieval_expect_closest_teaching") is True:
        return None
    rg = item.get("retrieval_golden_verse_ref")
    if isinstance(rg, str) and rg.strip():
        return rg.strip()
    vm = item.get("verse_match")
    if isinstance(vm, dict):
        ref = vm.get("verse_ref")
        if isinstance(ref, str) and ref.strip():
            return ref.strip()
    return None


def _expects_closest_teaching_only(item: dict[str, Any]) -> bool:
    if item.get("retrieval_expect_closest_teaching") is True:
        return True
    rg = item.get("retrieval_golden_verse_ref")
    if isinstance(rg, str) and rg.strip():
        return False
    vm = item.get("verse_match")
    if isinstance(vm, dict) and isinstance(vm.get("verse_ref"), str) and vm["verse_ref"].strip():
        return False
    return True


def _resolved_benchmark_path(benchmark_path: Path | None) -> Path:
    return benchmark_path if benchmark_path is not None else DEFAULT_BENCHMARK_PATH


def _evaluation_label(path: Path) -> str:
    return path.stem


def _track_obvious_case_rows(path: Path) -> bool:
    return path.resolve() == DEFAULT_BENCHMARK_PATH.resolve()


def _build_context(item: dict[str, Any]) -> RetrievalContext:
    internal_driver = item.get("internal_driver", {})
    primary = internal_driver.get("primary", "") if isinstance(internal_driver, dict) else ""
    hidden = internal_driver.get("hidden_risk", "") if isinstance(internal_driver, dict) else ""
    combined_text = " ".join(
        [
            str(item.get("dilemma", "")),
            str(item.get("core_reading", "")),
            str(item.get("gita_analysis", "")),
            str(primary),
            str(hidden),
        ]
    ).lower()
    return RetrievalContext(
        dilemma_id=str(item.get("dilemma_id", "unknown")),
        classification=str(item.get("classification", "Unknown")),
        primary_driver=str(primary),
        hidden_risk=str(hidden),
        dominant_dimensions=_dominant_dimensions_from_item(item),
        theme_tags=_infer_theme_tags(combined_text),
        applies_signals=_infer_applies_signals(combined_text),
        blocker_signals=_infer_blocker_signals(combined_text),
        missing_facts=[str(x) for x in item.get("missing_facts", []) if isinstance(x, str)],
    )


def run_verse_retrieval_benchmarks(*, benchmark_path: Path | None = None) -> dict[str, Any]:
    """Run deterministic retrieval against benchmark dilemmas and return JSON report."""
    obvious_refs = {"2.47", "3.37", "5.18", "17.15", "17.20", "16.21", "18.47"}
    obvious_case_results: list[dict[str, Any]] = []
    resolved_path = _resolved_benchmark_path(benchmark_path)
    track_obvious = _track_obvious_case_rows(resolved_path)
    dilemmas = load_dilemmas(path=benchmark_path)
    per_verse_usage: Counter[str] = Counter()
    differs: list[dict[str, Any]] = []
    false_positives: list[dict[str, Any]] = []
    blocker_suppressed_cases: list[str] = []
    style_failures: list[dict[str, Any]] = []
    top1_exact = 0
    null_agreement = 0
    verse_present = 0
    closest_teaching_count = 0
    by_case: list[dict[str, Any]] = []

    for item in dilemmas:
        dilemma_id = str(item.get("dilemma_id", "unknown"))
        context = _build_context(item)
        dimensions = EthicalDimensions.model_validate(item["ethical_dimensions"])
        out = retrieve_verse(str(item.get("dilemma", "")), dimensions, context_override=context)

        got_match = out["verse_match"] is not None
        expect_ct_only = _expects_closest_teaching_only(item)
        expected_ref = _expected_retrieval_verse_ref(item)
        benchmark_has_match = expected_ref is not None
        retrieved_ref = out["verse_match"].verse_ref if out["verse_match"] else None

        if got_match:
            verse_present += 1
            per_verse_usage[retrieved_ref or "unknown"] += 1
        else:
            closest_teaching_count += 1

        if benchmark_has_match and got_match and expected_ref == retrieved_ref:
            top1_exact += 1
        if expect_ct_only and (not got_match):
            null_agreement += 1

        if benchmark_has_match and expected_ref != retrieved_ref:
            if retrieved_ref is None:
                m_reason, fix_type = _diagnose_miss(
                    expected_ref=expected_ref, retrieved_ref=retrieved_ref
                )
            else:
                m_reason, fix_type = _diagnose_top1_mismatch(
                    expected_ref=expected_ref, retrieved_ref=retrieved_ref
                )
            differs.append(
                {
                    "dilemma_id": dilemma_id,
                    "benchmark_verse_ref": expected_ref,
                    "retrieved_verse_ref": retrieved_ref,
                    "mismatch_reason": m_reason,
                    "likely_fix_type": fix_type,
                }
            )

        if expect_ct_only and got_match:
            false_positives.append(
                {
                    "dilemma_id": dilemma_id,
                    "retrieved_verse_ref": retrieved_ref,
                    "false_positive_reason": _diagnose_false_positive(retrieved_ref=retrieved_ref),
                }
            )

        if track_obvious and expected_ref in obvious_refs:
            obvious_case_results.append(
                {
                    "dilemma_id": dilemma_id,
                    "benchmark_verse_ref": expected_ref,
                    "retrieved_verse_ref": retrieved_ref,
                    "agrees": expected_ref == retrieved_ref,
                }
            )

        if not got_match and context.blocker_signals:
            blocker_suppressed_cases.append(dilemma_id)

        if out["verse_match"] is not None:
            issues = evaluate_why_it_applies_style(out["verse_match"].why_it_applies)
            if issues:
                style_failures.append(
                    {"dilemma_id": dilemma_id, "field": "why_it_applies", "issues": issues}
                )
        else:
            fallback_text = out["closest_teaching"] or ""
            issues = evaluate_closest_teaching_style(fallback_text)
            if issues:
                style_failures.append(
                    {"dilemma_id": dilemma_id, "field": "closest_teaching", "issues": issues}
                )

        by_case.append(
            {
                "dilemma_id": dilemma_id,
                "benchmark_verse_ref": expected_ref,
                "expect_closest_teaching_only": expect_ct_only,
                "retrieved_verse_ref": retrieved_ref,
                "has_blocker_signals": bool(context.blocker_signals),
            }
        )

    max_single_verse_reuse = max(per_verse_usage.values(), default=0)
    max_single_verse_reuse_pct = round(
        (max_single_verse_reuse / max(1, verse_present)) * 100, 2
    )

    return {
        "benchmark_source_path": str(resolved_path),
        "evaluation_label": _evaluation_label(resolved_path),
        "total_dilemmas": len(dilemmas),
        "verse_present_count": verse_present,
        "closest_teaching_count": closest_teaching_count,
        "top1_exact_match_count": top1_exact,
        "null_match_agreement_count": null_agreement,
        "per_verse_usage_counts": dict(per_verse_usage),
        "max_single_verse_reuse": max_single_verse_reuse,
        "max_single_verse_reuse_pct": max_single_verse_reuse_pct,
        "blocker_suppressed_cases": blocker_suppressed_cases,
        "false_positive_cases": false_positives,
        "false_positive_count": len(false_positives),
        "differs_from_benchmark_cases": differs,
        "style_check_failures": style_failures,
        "obvious_case_results": obvious_case_results,
        "obvious_case_agreement_count": sum(1 for item in obvious_case_results if item["agrees"]),
        "cases": by_case,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run deterministic verse retrieval benchmark checks."
    )
    parser.add_argument(
        "--benchmark",
        type=Path,
        default=None,
        help=(
            "Path to benchmark-style JSON (default: batch1 W001–W020). "
            "Use docs/evals/verse_retrieval_ood_batch1.json for held-out retrieval eval."
        ),
    )
    parser.add_argument(
        "--report-json",
        type=Path,
        default=None,
        help="Optional path to save full JSON report.",
    )
    args = parser.parse_args()

    report = run_verse_retrieval_benchmarks(benchmark_path=args.benchmark)
    print(
        "Verse retrieval benchmark:"
        f" top1_exact={report['top1_exact_match_count']},"
        f" null_agreement={report['null_match_agreement_count']},"
        f" style_failures={len(report['style_check_failures'])}"
    )

    if args.report_json is not None:
        args.report_json.parent.mkdir(parents=True, exist_ok=True)
        with args.report_json.open("w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"Saved JSON report to: {args.report_json}")


if __name__ == "__main__":
    main()

