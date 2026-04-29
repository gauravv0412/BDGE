"""Read-only deterministic audit for curated verse retrieval quality."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from app.config.runtime_config import get_verse_match_score_threshold
from app.core.benchmark_loader import DEFAULT_BENCHMARK_PATH, load_dilemmas
from app.core.models import EthicalDimensions
from app.evals.run_verse_retrieval_benchmarks import (
    _build_context,
    _expected_retrieval_verse_ref,
    _expects_closest_teaching_only,
)
from app.verses.catalog import VerseCatalog
from app.verses.loader import load_curated_verses
from app.verses.retriever import _SEVERE_BLOCKERS, retrieve_verse
from app.verses.scorer import RetrievalContext, VerseScoreResult, rank_candidates

_LOW_MARGIN_MAX = 1
_NEAR_THRESHOLD_DELTA = 1
_CONCENTRATION_WARNING_SHARE = 35.0
_CONCENTRATION_WARNING_DISTINCT_CLUSTERS = 3


def _case_ref(item: dict[str, Any]) -> str:
    return str(item.get("dilemma_id", "unknown"))


def _pct(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round((numerator / denominator) * 100, 2)


def _candidate_row(result: VerseScoreResult, rank: int) -> dict[str, Any]:
    """Serialize all score breakdown fields exposed by the retriever scorer."""
    return {
        "rank": rank,
        "verse_ref": result.verse_ref,
        "total_score": result.total_score,
        "theme_overlap": result.theme_overlap,
        "theme_overlap_count": len(result.theme_overlap),
        "applies_when_hits": result.applies_overlap,
        "applies_when_hits_count": len(result.applies_overlap),
        "blocker_hits": result.blocker_overlap,
        "blocker_hits_count": len(result.blocker_overlap),
        "dominant_dimension_alignment": result.dominant_dimension_hit,
        "priority_used": result.priority_used,
        "rejected": result.rejected,
        "rejection_reason": result.rejection_reason,
    }


def _actual_ref(out: dict[str, Any]) -> str | None:
    verse = out["verse_match"]
    return verse.verse_ref if verse is not None else None


def _winner_from_top_candidates(candidates: list[dict[str, Any]], actual_ref: str | None) -> dict[str, Any] | None:
    if actual_ref is None:
        return candidates[0] if candidates else None
    for candidate in candidates:
        if candidate["verse_ref"] == actual_ref:
            return candidate
    return candidates[0] if candidates else None


def _expected_label(expected_ref: str | None) -> str:
    return expected_ref if expected_ref is not None else "fallback"


def _actual_label(actual_ref: str | None) -> str:
    return actual_ref if actual_ref is not None else "fallback"


def _theme_signature(context: RetrievalContext) -> tuple[str, ...]:
    return tuple(sorted(context.theme_tags))


def _case_flags(
    *,
    expected_ref: str | None,
    actual_ref: str | None,
    context: RetrievalContext,
    candidates: list[dict[str, Any]],
    winner_score: int | None,
    runner_up_score: int | None,
) -> list[str]:
    flags: list[str] = []
    winner = _winner_from_top_candidates(candidates, actual_ref)
    score_margin = (
        None
        if winner_score is None or runner_up_score is None
        else winner_score - runner_up_score
    )

    if actual_ref is not None and winner is not None:
        if winner["theme_overlap_count"] < 2 or winner["applies_when_hits_count"] == 0:
            flags.append("weak verse match")
        if winner["blocker_hits_count"] > 0 or set(context.blocker_signals) & _SEVERE_BLOCKERS:
            flags.append("blocker ignored")

    if expected_ref != actual_ref:
        runner_up_refs = {candidate["verse_ref"] for candidate in candidates[1:]}
        if expected_ref is not None and expected_ref in runner_up_refs:
            flags.append("wrong verse beating better runner-up")
        else:
            flags.append("expected/actual mismatch")

    if score_margin is not None and score_margin <= _LOW_MARGIN_MAX:
        flags.append("low-margin win")

    if actual_ref is None and candidates:
        top = candidates[0]
        thr = get_verse_match_score_threshold()
        if (
            not top["rejected"]
            and thr - _NEAR_THRESHOLD_DELTA <= top["total_score"] < thr
        ):
            flags.append("fallback despite near-threshold strong candidate")

    if not context.theme_tags and not context.applies_signals and not context.blocker_signals:
        flags.append("semantic context missing obvious signals")

    return flags


def _aggregate_concentration_flags(
    cases: list[dict[str, Any]],
    *,
    total_cases: int,
) -> list[dict[str, Any]]:
    by_ref: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for case in cases:
        actual_ref = case["actual"]["verse_ref"]
        if actual_ref is not None:
            by_ref[actual_ref].append(case)

    warnings: list[dict[str, Any]] = []
    for verse_ref, rows in sorted(by_ref.items()):
        share = _pct(len(rows), total_cases)
        signatures = {
            tuple(case["context"]["theme_tags"])
            for case in rows
        }
        if share >= _CONCENTRATION_WARNING_SHARE and len(signatures) >= _CONCENTRATION_WARNING_DISTINCT_CLUSTERS:
            warnings.append(
                {
                    "verse_ref": verse_ref,
                    "case_count": len(rows),
                    "share_pct": share,
                    "distinct_theme_clusters": len(signatures),
                    "case_ids": [case["dilemma_id"] for case in rows],
                    "flag": "repeated verse dominating unrelated clusters",
                }
            )
            for case in rows:
                if "repeated verse dominating unrelated clusters" not in case["flags"]:
                    case["flags"].append("repeated verse dominating unrelated clusters")
                if "generic verse dominance" not in case["flags"]:
                    case["flags"].append("generic verse dominance")
    return warnings


def _expected_mismatches(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "dilemma_id": case["dilemma_id"],
            "expected": case["expected"]["label"],
            "actual": case["actual"]["label"],
            "flags": case["flags"],
        }
        for case in cases
        if case["expected"]["label"] != case["actual"]["label"]
    ]


def _flagged_case_ids(cases: list[dict[str, Any]], flag: str) -> list[str]:
    return [case["dilemma_id"] for case in cases if flag in case["flags"]]


def _blocker_failure_cases(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "dilemma_id": case["dilemma_id"],
            "actual": case["actual"]["label"],
            "blocker_signals": case["context"]["blocker_signals"],
            "winner_blocker_hits": case["winner"]["blocker_hits"] if case["winner"] else [],
        }
        for case in cases
        if "blocker ignored" in case["flags"]
    ]


def _near_threshold_fallback_cases(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in cases:
        if "fallback despite near-threshold strong candidate" not in case["flags"]:
            continue
        top = case["top_candidates"][0] if case["top_candidates"] else None
        rows.append(
            {
                "dilemma_id": case["dilemma_id"],
                "top_candidate": top["verse_ref"] if top else None,
                "top_candidate_score": top["total_score"] if top else None,
                "threshold": get_verse_match_score_threshold(),
            }
        )
    return rows


def _summary(cases: list[dict[str, Any]], concentration_warnings: list[dict[str, Any]]) -> dict[str, Any]:
    total_cases = len(cases)
    verse_usage = Counter(
        case["actual"]["verse_ref"] for case in cases if case["actual"]["verse_ref"] is not None
    )
    attach_count = sum(1 for case in cases if case["actual"]["verse_ref"] is not None)
    top_counts = sorted(verse_usage.values(), reverse=True)
    top_1_count = top_counts[0] if top_counts else 0
    top_5_count = sum(top_counts[:5])

    low_margin_cases = [
        {
            "dilemma_id": case["dilemma_id"],
            "actual": case["actual"]["label"],
            "winner_score": case["winner_score"],
            "runner_up_score": case["runner_up_score"],
            "score_margin": case["score_margin"],
        }
        for case in cases
        if "low-margin win" in case["flags"]
    ]
    weak_match_cases = [
        {
            "dilemma_id": case["dilemma_id"],
            "actual": case["actual"]["label"],
            "theme_overlap_count": case["winner"]["theme_overlap_count"] if case["winner"] else 0,
            "applies_when_hits_count": case["winner"]["applies_when_hits_count"] if case["winner"] else 0,
        }
        for case in cases
        if "weak verse match" in case["flags"]
    ]

    return {
        "total_cases": total_cases,
        "verse_attach_rate": _pct(attach_count, total_cases),
        "fallback_rate": _pct(total_cases - attach_count, total_cases),
        "verse_usage": dict(sorted(verse_usage.items())),
        "top_1_verse_share_pct": _pct(top_1_count, total_cases),
        "top_5_verse_share_pct": _pct(top_5_count, total_cases),
        "low_margin_cases": low_margin_cases,
        "weak_match_cases": weak_match_cases,
        "blocker_failure_cases": _blocker_failure_cases(cases),
        "near_threshold_fallback_cases": _near_threshold_fallback_cases(cases),
        "expected_vs_actual_mismatches": _expected_mismatches(cases),
        "concentration_warnings": concentration_warnings,
    }


def _risk_sort_key(case: dict[str, Any]) -> tuple[int, str]:
    flags = case["flags"]
    order = (
        "blocker ignored",
        "wrong verse beating better runner-up",
        "expected/actual mismatch",
        "low-margin win",
        "weak verse match",
        "fallback despite near-threshold strong candidate",
        "repeated verse dominating unrelated clusters",
        "generic verse dominance",
    )
    for idx, flag in enumerate(order):
        if flag in flags:
            return (idx, case["dilemma_id"])
    return (len(order), case["dilemma_id"])


def run_retrieval_audit(*, input_path: Path | None = None) -> dict[str, Any]:
    """Run retrieval over benchmark rows and return machine-readable diagnostics."""
    resolved_path = input_path or DEFAULT_BENCHMARK_PATH
    dilemmas = load_dilemmas(path=resolved_path)
    entries = load_curated_verses()
    active_entries = VerseCatalog(entries).list_active()

    cases: list[dict[str, Any]] = []
    for item in dilemmas:
        dilemma_id = _case_ref(item)
        context = _build_context(item)
        dimensions = EthicalDimensions.model_validate(item["ethical_dimensions"])
        ranked = rank_candidates(active_entries, context)
        top_candidates = [_candidate_row(candidate, idx + 1) for idx, candidate in enumerate(ranked[:5])]
        out = retrieve_verse(str(item.get("dilemma", "")), dimensions, context_override=context)

        expected_ref = _expected_retrieval_verse_ref(item)
        actual_ref = _actual_ref(out)
        winner_score = top_candidates[0]["total_score"] if top_candidates else None
        runner_up_score = top_candidates[1]["total_score"] if len(top_candidates) > 1 else None
        score_margin = (
            None
            if winner_score is None or runner_up_score is None
            else winner_score - runner_up_score
        )
        winner = _winner_from_top_candidates(top_candidates, actual_ref)
        flags = _case_flags(
            expected_ref=expected_ref,
            actual_ref=actual_ref,
            context=context,
            candidates=top_candidates,
            winner_score=winner_score,
            runner_up_score=runner_up_score,
        )

        case = {
            "dilemma_id": dilemma_id,
            "dilemma": str(item.get("dilemma", "")),
            "expected": {
                "verse_ref": expected_ref,
                "label": _expected_label(expected_ref),
                "expects_fallback": _expects_closest_teaching_only(item),
            },
            "actual": {
                "verse_ref": actual_ref,
                "label": _actual_label(actual_ref),
                "is_fallback": actual_ref is None,
            },
            "winner_score": winner_score,
            "runner_up_score": runner_up_score,
            "score_margin": score_margin,
            "theme_overlaps": winner["theme_overlap"] if winner else [],
            "applies_when_hits": winner["applies_when_hits"] if winner else [],
            "blocker_hits": winner["blocker_hits"] if winner else [],
            "dominant_dimension_alignment": (
                winner["dominant_dimension_alignment"] if winner else False
            ),
            "winner": winner,
            "top_candidates": top_candidates,
            "context": {
                "classification": context.classification,
                "primary_driver": context.primary_driver,
                "hidden_risk": context.hidden_risk,
                "dominant_dimensions": context.dominant_dimensions,
                "theme_tags": context.theme_tags,
                "applies_signals": context.applies_signals,
                "blocker_signals": context.blocker_signals,
                "missing_facts": context.missing_facts,
                "theme_signature": list(_theme_signature(context)),
            },
            "flags": flags,
        }
        cases.append(case)

    concentration_warnings = _aggregate_concentration_flags(cases, total_cases=len(cases))
    report = {
        "audit_version": "retrieval-audit-v1",
        "benchmark_source_path": str(resolved_path),
        "retrieval_threshold": get_verse_match_score_threshold(),
        "summary": _summary(cases, concentration_warnings),
        "cases": sorted(cases, key=_risk_sort_key),
    }
    return report


def _section(title: str, rows: list[str]) -> list[str]:
    if not rows:
        return [f"## {title}", "None."]
    return [f"## {title}", *rows]


def render_markdown_report(report: dict[str, Any]) -> str:
    """Render the audit in risk-first order for human review."""
    summary = report["summary"]
    cases = report["cases"]

    lines = [
        "# Retrieval Audit",
        "",
        f"- Source: `{report['benchmark_source_path']}`",
        f"- Total cases: {summary['total_cases']}",
        f"- Verse attach rate: {summary['verse_attach_rate']}%",
        f"- Fallback rate: {summary['fallback_rate']}%",
        f"- Top 1 verse share: {summary['top_1_verse_share_pct']}%",
        f"- Top 5 verse share: {summary['top_5_verse_share_pct']}%",
        "",
    ]

    def case_lines(flag: str) -> list[str]:
        return [
            (
                f"- `{case['dilemma_id']}` expected `{case['expected']['label']}`, "
                f"actual `{case['actual']['label']}`, score `{case['winner_score']}`, "
                f"margin `{case['score_margin']}`, flags: {', '.join(case['flags'])}"
            )
            for case in cases
            if flag in case["flags"]
        ]

    sections = [
        ("Blocker Failures", case_lines("blocker ignored")),
        ("Expected/Actual Mismatches", [
            (
                f"- `{row['dilemma_id']}` expected `{row['expected']}`, "
                f"actual `{row['actual']}`, flags: {', '.join(row['flags'])}"
            )
            for row in summary["expected_vs_actual_mismatches"]
        ]),
        ("Low-Margin Wins", case_lines("low-margin win")),
        ("Weak Matches", case_lines("weak verse match")),
        ("Near-Threshold Fallbacks", case_lines("fallback despite near-threshold strong candidate")),
        ("Concentration Warnings", [
            (
                f"- `{row['verse_ref']}` appears in {row['case_count']} cases "
                f"({row['share_pct']}%) across {row['distinct_theme_clusters']} theme clusters: "
                f"{', '.join(row['case_ids'])}"
            )
            for row in summary["concentration_warnings"]
        ]),
    ]

    for title, rows in sections:
        lines.extend(_section(title, rows))
        lines.append("")

    lines.extend(
        [
            "## Verse Usage",
            *[
                f"- `{verse_ref}`: {count}"
                for verse_ref, count in sorted(summary["verse_usage"].items())
            ],
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def write_audit_outputs(report: dict[str, Any], *, out_json: Path, out_md: Path) -> None:
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    out_md.write_text(render_markdown_report(report), encoding="utf-8")


def _default_output_paths(input_path: Path) -> tuple[Path, Path]:
    batch = input_path.stem
    artifacts = Path("artifacts")
    return (
        artifacts / f"retrieval_audit_{batch}.json",
        artifacts / f"retrieval_audit_{batch}.md",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run read-only deterministic retrieval quality audit."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_BENCHMARK_PATH,
        help="Benchmark JSON path.",
    )
    parser.add_argument(
        "--out-json",
        type=Path,
        default=None,
        help="Output JSON path.",
    )
    parser.add_argument(
        "--out-md",
        type=Path,
        default=None,
        help="Output Markdown path.",
    )
    args = parser.parse_args()

    default_json, default_md = _default_output_paths(args.input)
    out_json = args.out_json or default_json
    out_md = args.out_md or default_md

    report = run_retrieval_audit(input_path=args.input)
    write_audit_outputs(report, out_json=out_json, out_md=out_md)
    print(
        "Retrieval audit:"
        f" total_cases={report['summary']['total_cases']},"
        f" verse_attach_rate={report['summary']['verse_attach_rate']}%,"
        f" fallback_rate={report['summary']['fallback_rate']}%,"
        f" mismatches={len(report['summary']['expected_vs_actual_mismatches'])}"
    )
    print(f"Saved JSON report to: {out_json}")
    print(f"Saved Markdown report to: {out_md}")


if __name__ == "__main__":
    main()
