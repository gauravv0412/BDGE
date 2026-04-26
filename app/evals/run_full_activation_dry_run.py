"""Dry-run audit for activating every curated verse entry in retrieval."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from unittest import mock

from app.core.benchmark_loader import DEFAULT_BENCHMARK_PATH
from app.evals.run_live_retrieval_audit import run_live_retrieval_audit
from app.evals.run_reference_benchmark_comparison import (
    DEFAULT_RETRIEVAL_EVAL_PATH,
    run_reference_benchmark_comparison,
)
from app.evals.run_retrieval_audit import _pct, run_retrieval_audit
from app.verses.loader import curated_verses_seed_path, load_curated_verses

_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LIVE_OOD_PATH = _ROOT / "tests" / "fixtures" / "live_retrieval_ood_W021-W050.json"
DEFAULT_OUT_JSON = _ROOT / "artifacts" / "full_activation_dry_run_W001-W050.json"
DEFAULT_OUT_MD = _ROOT / "artifacts" / "full_activation_dry_run_W001-W050.md"
DEFAULT_CURRENT_COMPARISON_PATH = _ROOT / "artifacts" / "benchmark_comparison_W001-W050.json"

_SEVERE_SAFETY_BLOCKERS = {
    "abuse-context",
    "active-harm",
    "imminent-violence",
    "scripture-as-weapon",
    "self-harm",
}
_VIOLENT_OR_CRISIS_TERMS = (
    "abuse",
    "assault",
    "attack",
    "beat",
    "crisis",
    "harm myself",
    "kill",
    "self harm",
    "self-harm",
    "suicide",
    "violent",
)
_ACTION_JUSTIFYING_REFS = {"2.3", "2.31", "2.33", "2.38", "2.47"}


@contextmanager
def _dry_run_all_active_loader() -> Iterator[None]:
    """Patch existing audit modules so they see an all-active in-memory catalog."""

    def _load_all_active(path: Path | None = None) -> Any:
        return load_curated_verses(path=path, dry_run_all_active=True)

    with (
        mock.patch("app.verses.retriever.load_curated_verses", _load_all_active),
        mock.patch("app.evals.run_retrieval_audit.load_curated_verses", _load_all_active),
        mock.patch("app.evals.run_live_retrieval_audit.load_curated_verses", _load_all_active),
        mock.patch("app.evals.run_reference_benchmark_comparison.load_curated_verses", _load_all_active),
    ):
        yield


def _entry_counts() -> dict[str, int]:
    current_entries = load_curated_verses()
    dry_run_entries = load_curated_verses(dry_run_all_active=True)
    currently_active = sum(1 for entry in current_entries if entry.status == "active")
    return {
        "total_curated_entries": len(current_entries),
        "currently_active_entries": currently_active,
        "dry_run_active_entries": sum(1 for entry in dry_run_entries if entry.status == "active"),
        "newly_eligible_entries_count": len(dry_run_entries) - currently_active,
    }


def _case_label(case: dict[str, Any], *, prefix: str = "actual") -> str:
    if prefix == "actual":
        return str(case.get("actual_verse_ref") or "fallback")
    verse_ref = case.get(f"{prefix}_verse_ref")
    shape = case.get(f"{prefix}_shape")
    return str(verse_ref) if shape == "verse" and verse_ref else "fallback"


def _shape_label_from_audit_case(case: dict[str, Any]) -> str:
    actual = case.get("actual", {})
    return str(actual.get("label", "fallback")) if isinstance(actual, dict) else "fallback"


def _context_blockers(case: dict[str, Any]) -> set[str]:
    context = case.get("retrieval_context")
    if not isinstance(context, dict):
        context = case.get("context")
    if not isinstance(context, dict):
        return set()
    blockers = context.get("blocker_signals")
    if not isinstance(blockers, list):
        return set()
    return {str(item) for item in blockers}


def _winner(case: dict[str, Any]) -> dict[str, Any] | None:
    score = case.get("score_breakdown")
    if isinstance(score, dict):
        return score
    top = case.get("top_5_candidates") or case.get("top_candidates")
    if isinstance(top, list) and top and isinstance(top[0], dict):
        return top[0]
    return None


def _weak_winner(case: dict[str, Any]) -> bool:
    winner = _winner(case)
    if winner is None:
        return False
    return (
        int(winner.get("theme_overlap_count", 0)) < 2
        or int(winner.get("applies_when_hits_count", 0)) == 0
        or int(winner.get("blocker_hits_count", 0)) > 0
        or bool(winner.get("rejected"))
    )


def _is_action_justifying(case: dict[str, Any], verse_ref: str) -> bool:
    if verse_ref in _ACTION_JUSTIFYING_REFS:
        return True
    winner = _winner(case) or {}
    overlaps = set(winner.get("theme_overlap", []))
    return bool(overlaps & {"action", "duty"})


def _safety_risk_reasons(case: dict[str, Any]) -> list[str]:
    actual_ref = case.get("actual_verse_ref")
    if not actual_ref:
        return []
    reasons: list[str] = []
    blockers = _context_blockers(case)
    severe_hits = sorted(blockers & _SEVERE_SAFETY_BLOCKERS)
    if severe_hits:
        reasons.append(f"severe blocker with verse: {', '.join(severe_hits)}")
    dilemma = str(case.get("dilemma", "")).lower()
    if any(term in dilemma for term in _VIOLENT_OR_CRISIS_TERMS) and _is_action_justifying(case, str(actual_ref)):
        reasons.append("violent/self-harm/crisis-like query received action-justifying verse")
    if case.get("reference_shape") == "fallback" and severe_hits:
        reasons.append("reference fallback with severe blocker became verse")
    return reasons


def _why_winner_won(case: dict[str, Any]) -> str:
    winner = _winner(case)
    if winner is None:
        return "Dry-run did not produce ranked candidates."
    parts = [
        f"ranked first with score {winner.get('total_score')}",
        f"themes={winner.get('theme_overlap', [])}",
        f"applies={winner.get('applies_when_hits', [])}",
    ]
    if winner.get("dominant_dimension_alignment"):
        parts.append("dominant dimension aligned")
    if winner.get("blocker_hits"):
        parts.append(f"blockers={winner.get('blocker_hits')}")
    return "; ".join(parts)


def _risk_label(
    *,
    dilemma_id: str,
    current_case: dict[str, Any],
    dry_case: dict[str, Any],
    shape_lock_regression: bool,
) -> str:
    if _safety_risk_reasons(dry_case):
        return "safety_risk"
    if shape_lock_regression:
        return "shape_lock_regression"
    current_label = _case_label(current_case)
    dry_label = _case_label(dry_case)
    reference_label = _case_label(dry_case, prefix="reference")
    allowed = {str(ref) for ref in dry_case.get("allowed_verse_refs", [])}
    if dry_label != "fallback" and (dry_label == reference_label or dry_label in allowed):
        return "better_specific_match" if current_label == "fallback" else "acceptable_alternative"
    if dry_label != "fallback" and _weak_winner(dry_case):
        return "possible_noise"
    if current_label == "fallback" and dry_label != "fallback":
        return "acceptable_alternative"
    if dilemma_id:
        return "needs_human_review"
    return "needs_human_review"


def _diagnostic_row(
    *,
    current_case: dict[str, Any],
    dry_case: dict[str, Any],
    shape_lock_regression_ids: set[str],
) -> dict[str, Any]:
    dilemma_id = str(dry_case["dilemma_id"])
    shape_lock_regression = dilemma_id in shape_lock_regression_ids
    dry_label = _case_label(dry_case)
    row = {
        "dilemma_id": dilemma_id,
        "dilemma": dry_case.get("dilemma"),
        "current": {
            "shape": current_case.get("actual_shape"),
            "verse_ref": current_case.get("actual_verse_ref"),
            "label": _case_label(current_case),
        },
        "dry_run": {
            "shape": dry_case.get("actual_shape"),
            "verse_ref": dry_case.get("actual_verse_ref"),
            "label": dry_label,
        },
        "reference": {
            "shape": dry_case.get("reference_shape"),
            "verse_ref": dry_case.get("reference_verse_ref"),
            "label": _case_label(dry_case, prefix="reference"),
            "allowed_verse_refs": dry_case.get("allowed_verse_refs", []),
        },
        "top_5_candidates_current": current_case.get("top_5_candidates", []),
        "top_5_candidates_dry_run": dry_case.get("top_5_candidates", []),
        "score_breakdown": _winner(dry_case),
        "why_dry_run_winner_won": _why_winner_won(dry_case),
        "safety_risk_reasons": _safety_risk_reasons(dry_case),
        "shape_lock_regression": shape_lock_regression,
        "risk_label": _risk_label(
            dilemma_id=dilemma_id,
            current_case=current_case,
            dry_case=dry_case,
            shape_lock_regression=shape_lock_regression,
        ),
    }
    return row


def _changed_case_diagnostics(
    *,
    current_reference_report: dict[str, Any],
    dry_reference_report: dict[str, Any],
    shape_lock_regression_ids: set[str],
) -> list[dict[str, Any]]:
    current_by_id = {case["dilemma_id"]: case for case in current_reference_report["cases"]}
    rows: list[dict[str, Any]] = []
    for dry_case in dry_reference_report["cases"]:
        current_case = current_by_id.get(dry_case["dilemma_id"])
        if current_case is None:
            continue
        if _case_label(current_case) == _case_label(dry_case):
            continue
        rows.append(
            _diagnostic_row(
                current_case=current_case,
                dry_case=dry_case,
                shape_lock_regression_ids=shape_lock_regression_ids,
            )
        )
    return sorted(rows, key=lambda row: (row["risk_label"], row["dilemma_id"]))


def _shape_lock_regressions(
    current_shape_report: dict[str, Any],
    dry_shape_report: dict[str, Any],
) -> list[dict[str, Any]]:
    current_by_id = {case["dilemma_id"]: case for case in current_shape_report["cases"]}
    rows: list[dict[str, Any]] = []
    for dry_case in dry_shape_report["cases"]:
        current_case = current_by_id.get(dry_case["dilemma_id"])
        if current_case is None:
            continue
        current_label = _shape_label_from_audit_case(current_case)
        dry_label = _shape_label_from_audit_case(dry_case)
        if current_label != dry_label:
            rows.append(
                {
                    "dilemma_id": dry_case["dilemma_id"],
                    "current": current_label,
                    "dry_run": dry_label,
                    "expected": dry_case.get("expected", {}).get("label"),
                    "flags": dry_case.get("flags", []),
                }
            )
    return sorted(rows, key=lambda row: row["dilemma_id"])


def _coverage(summary: dict[str, Any]) -> float:
    return float(summary.get("actual_verse_coverage_pct", 0.0))


def _concentration_warnings(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_ref: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for case in cases:
        ref = case.get("actual_verse_ref")
        if ref:
            by_ref[str(ref)].append(case)
    warnings: list[dict[str, Any]] = []
    total_cases = len(cases)
    for verse_ref, rows in sorted(by_ref.items()):
        signatures = {
            tuple((case.get("retrieval_context") or {}).get("theme_signature", []))
            for case in rows
        }
        share = _pct(len(rows), total_cases)
        if share >= 35.0 and len(signatures) >= 3:
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
    return warnings


def _noisy_verse_rows(changed_cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    noisy_cases = [
        row
        for row in changed_cases
        if row["dry_run"]["verse_ref"] and row["risk_label"] in {"possible_noise", "safety_risk", "needs_human_review"}
    ]
    counts = Counter(
        row["dry_run"]["verse_ref"] for row in noisy_cases
    )
    return [
        {
            "verse_ref": verse_ref,
            "changed_case_count": count,
            "case_ids": [
                row["dilemma_id"]
                for row in noisy_cases
                if row["dry_run"]["verse_ref"] == verse_ref
            ],
        }
        for verse_ref, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]


def _recommendation(summary: dict[str, Any], noisy_verses: list[dict[str, Any]]) -> str:
    if summary["blocker_failure_count"] or summary["shape_lock_regressions_count"]:
        return "Do not proceed to full activation yet; quarantine or fix blocker/shape-lock failures first."
    if noisy_verses:
        refs = ", ".join(row["verse_ref"] for row in noisy_verses[:5])
        return f"Proceed only after human review of noisy candidates, especially: {refs}."
    return "Proceed to full activation; no blocker failures or shape-lock regressions were detected."


def _summary(
    *,
    counts: dict[str, int],
    current_reference_report: dict[str, Any],
    dry_reference_report: dict[str, Any],
    changed_cases: list[dict[str, Any]],
    shape_lock_regressions: list[dict[str, Any]],
    concentration_warnings: list[dict[str, Any]],
) -> dict[str, Any]:
    current_summary = current_reference_report["summary"]
    dry_summary = dry_reference_report["summary"]
    blocker_failures = [row for row in changed_cases if row["risk_label"] == "safety_risk"]
    forced_match_warnings = [
        row for row in changed_cases if row["dry_run"]["verse_ref"] and _weak_winner({"score_breakdown": row["score_breakdown"]})
    ]
    overtrigger_warnings = [
        row
        for row in changed_cases
        if row["current"]["label"] == "fallback" and row["dry_run"]["label"] != "fallback"
    ]
    return {
        **counts,
        "actual_verse_coverage_before": _coverage(current_summary),
        "actual_verse_coverage_dry_run": _coverage(dry_summary),
        "same_reference_verse_before": current_summary["same_reference_verse_count"],
        "same_reference_verse_dry_run": dry_summary["same_reference_verse_count"],
        "same_reference_fallback_before": current_summary["same_reference_fallback_count"],
        "same_reference_fallback_dry_run": dry_summary["same_reference_fallback_count"],
        "upgraded_fallback_to_verse_count": dry_summary["upgraded_fallback_to_verse_count"],
        "changed_winner_count": len(changed_cases),
        "shape_lock_regressions_count": len(shape_lock_regressions),
        "blocker_failure_count": len(blocker_failures),
        "forced_match_warning_count": len(forced_match_warnings),
        "overtrigger_warning_count": len(overtrigger_warnings),
        "concentration_warnings": concentration_warnings,
    }


def run_full_activation_dry_run(
    *,
    retrieval_eval_path: Path = DEFAULT_RETRIEVAL_EVAL_PATH,
    shape_lock_benchmark_path: Path = DEFAULT_BENCHMARK_PATH,
    live_ood_path: Path = DEFAULT_LIVE_OOD_PATH,
    current_comparison_path: Path = DEFAULT_CURRENT_COMPARISON_PATH,
) -> dict[str, Any]:
    """Run current vs all-active dry-run retrieval audits without mutating seed data."""
    counts = _entry_counts()
    current_shape_report = run_retrieval_audit(input_path=shape_lock_benchmark_path)
    current_reference_report = run_reference_benchmark_comparison(fixture_path=retrieval_eval_path)

    with _dry_run_all_active_loader():
        dry_shape_report = run_retrieval_audit(input_path=shape_lock_benchmark_path)
        dry_reference_report = run_reference_benchmark_comparison(fixture_path=retrieval_eval_path)
        dry_live_ood_report = run_live_retrieval_audit(input_path=live_ood_path)

    shape_regressions = _shape_lock_regressions(current_shape_report, dry_shape_report)
    shape_regression_ids = {row["dilemma_id"] for row in shape_regressions}
    changed_cases = _changed_case_diagnostics(
        current_reference_report=current_reference_report,
        dry_reference_report=dry_reference_report,
        shape_lock_regression_ids=shape_regression_ids,
    )
    concentration_warnings = _concentration_warnings(dry_reference_report["cases"])
    summary = _summary(
        counts=counts,
        current_reference_report=current_reference_report,
        dry_reference_report=dry_reference_report,
        changed_cases=changed_cases,
        shape_lock_regressions=shape_regressions,
        concentration_warnings=concentration_warnings,
    )
    noisy_verses = _noisy_verse_rows(changed_cases)
    summary["recommendation"] = _recommendation(summary, noisy_verses)
    summary["should_block_full_activation"] = bool(
        summary["blocker_failure_count"] or summary["shape_lock_regressions_count"]
    )

    current_artifact_summary = None
    if current_comparison_path.exists():
        current_artifact_summary = json.loads(current_comparison_path.read_text(encoding="utf-8")).get("summary")

    return {
        "audit_version": "full-activation-dry-run-v1",
        "seed_path": str(curated_verses_seed_path()),
        "retrieval_eval_path": str(retrieval_eval_path),
        "shape_lock_benchmark_path": str(shape_lock_benchmark_path),
        "live_ood_path": str(live_ood_path),
        "current_comparison_artifact_path": str(current_comparison_path),
        "current_comparison_artifact_summary": current_artifact_summary,
        "dry_run_mode": "all_curated_entries_active_in_memory",
        "mutates_seed": False,
        "policy": {
            "higher_verse_coverage_allowed": True,
            "reference_fallback_to_verse_allowed": True,
            "different_valid_verse_allowed": True,
            "block_on_shape_lock_regression": True,
            "block_on_severe_blocker_returning_verse": True,
        },
        "summary": summary,
        "shape_lock_regressions": shape_regressions,
        "changed_cases": changed_cases,
        "blocker_failures": [row for row in changed_cases if row["risk_label"] == "safety_risk"],
        "forced_match_warnings": [
            row for row in changed_cases if row["dry_run"]["verse_ref"] and _weak_winner({"score_breakdown": row["score_breakdown"]})
        ],
        "overtrigger_warnings": [
            row for row in changed_cases if row["current"]["label"] == "fallback" and row["dry_run"]["label"] != "fallback"
        ],
        "noisy_verses": noisy_verses,
        "runs": {
            "shape_lock_current_W001_W020": current_shape_report,
            "shape_lock_dry_run_W001_W020": dry_shape_report,
            "reference_current_W001_W050": current_reference_report,
            "reference_dry_run_W001_W050": dry_reference_report,
            "live_ood_dry_run_W021_W050": dry_live_ood_report,
        },
    }


def render_markdown_report(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Full Activation Dry-Run Audit",
        "",
        f"- Seed: `{report['seed_path']}`",
        f"- Mode: `{report['dry_run_mode']}`",
        f"- Mutates seed: `{report['mutates_seed']}`",
        "",
        "## Summary",
    ]
    for key in (
        "total_curated_entries",
        "currently_active_entries",
        "dry_run_active_entries",
        "newly_eligible_entries_count",
        "actual_verse_coverage_before",
        "actual_verse_coverage_dry_run",
        "same_reference_verse_before",
        "same_reference_verse_dry_run",
        "same_reference_fallback_before",
        "same_reference_fallback_dry_run",
        "upgraded_fallback_to_verse_count",
        "changed_winner_count",
        "shape_lock_regressions_count",
        "blocker_failure_count",
        "forced_match_warning_count",
        "overtrigger_warning_count",
    ):
        lines.append(f"- `{key}`: {summary[key]}")
    lines.extend(
        [
            f"- `concentration_warnings`: {len(summary['concentration_warnings'])}",
            f"- Recommendation: {summary['recommendation']}",
            "",
            "## Blockers",
        ]
    )
    if not report["blocker_failures"] and not report["shape_lock_regressions"]:
        lines.append("None.")
    for row in report["shape_lock_regressions"]:
        lines.append(f"- `{row['dilemma_id']}` shape lock changed `{row['current']}` -> `{row['dry_run']}`")
    for row in report["blocker_failures"]:
        lines.append(
            f"- `{row['dilemma_id']}` safety risk: dry-run `{row['dry_run']['label']}`; "
            f"{'; '.join(row['safety_risk_reasons'])}"
        )

    lines.append("")
    lines.append("## Changed Winners")
    if not report["changed_cases"]:
        lines.append("None.")
    else:
        for row in report["changed_cases"][:50]:
            lines.append(
                f"- `{row['dilemma_id']}` {row['risk_label']}: "
                f"`{row['current']['label']}` -> `{row['dry_run']['label']}` "
                f"(reference `{row['reference']['label']}`)"
            )

    lines.append("")
    lines.append("## Noisy Verses")
    if not report["noisy_verses"]:
        lines.append("None.")
    else:
        for row in report["noisy_verses"]:
            lines.append(
                f"- `{row['verse_ref']}` in {row['changed_case_count']} changed cases: "
                f"{', '.join(row['case_ids'])}"
            )

    lines.append("")
    lines.append("## Concentration Warnings")
    if not summary["concentration_warnings"]:
        lines.append("None.")
    else:
        for row in summary["concentration_warnings"]:
            lines.append(
                f"- `{row['verse_ref']}` appears in {row['case_count']} cases "
                f"({row['share_pct']}%) across {row['distinct_theme_clusters']} theme clusters."
            )
    return "\n".join(lines).rstrip() + "\n"


def write_dry_run_outputs(report: dict[str, Any], *, out_json: Path, out_md: Path) -> None:
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    out_md.write_text(render_markdown_report(report), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Dry-run activating every curated verse entry for retrieval."
    )
    parser.add_argument("--retrieval-eval", type=Path, default=DEFAULT_RETRIEVAL_EVAL_PATH)
    parser.add_argument("--shape-lock-benchmark", type=Path, default=DEFAULT_BENCHMARK_PATH)
    parser.add_argument("--live-ood", type=Path, default=DEFAULT_LIVE_OOD_PATH)
    parser.add_argument("--current-comparison", type=Path, default=DEFAULT_CURRENT_COMPARISON_PATH)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    args = parser.parse_args()

    report = run_full_activation_dry_run(
        retrieval_eval_path=args.retrieval_eval,
        shape_lock_benchmark_path=args.shape_lock_benchmark,
        live_ood_path=args.live_ood,
        current_comparison_path=args.current_comparison,
    )
    write_dry_run_outputs(report, out_json=args.out_json, out_md=args.out_md)
    summary = report["summary"]
    print(
        "Full activation dry-run:"
        f" current_active={summary['currently_active_entries']},"
        f" dry_run_active={summary['dry_run_active_entries']},"
        f" coverage_before={summary['actual_verse_coverage_before']}%,"
        f" coverage_dry_run={summary['actual_verse_coverage_dry_run']}%,"
        f" shape_regressions={summary['shape_lock_regressions_count']},"
        f" blocker_failures={summary['blocker_failure_count']},"
        f" changed_winners={summary['changed_winner_count']}"
    )
    print(f"Recommendation: {summary['recommendation']}")
    print(f"Saved JSON report to: {args.out_json}")
    print(f"Saved Markdown report to: {args.out_md}")


if __name__ == "__main__":
    main()
