"""Audit live-style sparse-input retrieval through the public engine boundary."""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any
from unittest import mock

from app.core.benchmark_loader import DEFAULT_BENCHMARK_PATH, load_dilemmas
from app.core.models import EngineAnalyzeErrorResponse, EthicalDimensions
from app.engine import analyzer as engine_analyzer
from app.evals.run_retrieval_audit import (
    _actual_label,
    _candidate_row,
    _expected_label,
    _pct,
    _theme_signature,
    run_retrieval_audit,
)
from app.evals.run_verse_retrieval_benchmarks import _expected_retrieval_verse_ref
from app.semantic.scorer import semantic_scorer
from app.verses.catalog import VerseCatalog
from app.verses.context_extractor import extract_live_retrieval_context_signals
from app.verses.loader import load_curated_verses
from app.verses.scorer import RetrievalContext, rank_candidates

EngineHandler = Callable[[dict[str, Any]], Any]
SemanticScorer = Callable[[str], dict[str, Any]]


def _load_audit_items(path: Path) -> tuple[list[dict[str, Any]], str]:
    """Load either a full benchmark JSON or a retrieval-only audit fixture."""
    with path.open(encoding="utf-8") as f:
        raw = json.load(f)
    if isinstance(raw, dict) and isinstance(raw.get("cases"), list):
        return [dict(item) for item in raw["cases"] if isinstance(item, dict)], "retrieval_fixture"
    if isinstance(raw, dict) and isinstance(raw.get("dilemmas"), list):
        return load_dilemmas(path=path), "benchmark"
    raise ValueError(f"Unsupported live retrieval audit input shape: {path}")


def _context_row(context: RetrievalContext | None) -> dict[str, Any] | None:
    if context is None:
        return None
    return {
        "classification": context.classification,
        "primary_driver": context.primary_driver,
        "hidden_risk": context.hidden_risk,
        "dominant_dimensions": context.dominant_dimensions,
        "theme_tags": context.theme_tags,
        "applies_signals": context.applies_signals,
        "blocker_signals": context.blocker_signals,
        "missing_facts": context.missing_facts,
        "theme_signature": list(_theme_signature(context)),
    }


def _as_str_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _dominant_dimensions_from_dimensions(dimensions: EthicalDimensions | None) -> list[str]:
    if dimensions is None:
        return []
    pairs = [
        ("dharma_duty", dimensions.dharma_duty.score),
        ("satya_truth", dimensions.satya_truth.score),
        ("ahimsa_nonharm", dimensions.ahimsa_nonharm.score),
        ("nishkama_detachment", dimensions.nishkama_detachment.score),
        ("shaucha_intent", dimensions.shaucha_intent.score),
        ("sanyama_restraint", dimensions.sanyama_restraint.score),
        ("lokasangraha_welfare", dimensions.lokasangraha_welfare.score),
        ("viveka_discernment", dimensions.viveka_discernment.score),
    ]
    ranked = sorted(pairs, key=lambda item: item[1], reverse=True)
    return [name for name, score in ranked if score >= 2]


def _semantic_signal_row(
    semantic_payload: dict[str, Any] | None,
    dimensions: EthicalDimensions | None,
) -> dict[str, list[str]]:
    semantic_payload = semantic_payload or {}
    return {
        "theme_tags": _as_str_list(semantic_payload.get("theme_tags")),
        "applies_signals": _as_str_list(semantic_payload.get("applies_signals")),
        "blocker_signals": _as_str_list(semantic_payload.get("blocker_signals")),
        "dominant_dimensions": _dominant_dimensions_from_dimensions(dimensions),
    }


def _deterministic_signal_row(dilemma: str) -> dict[str, list[str]]:
    extracted = extract_live_retrieval_context_signals(dilemma)
    return {
        "theme_tags": _as_str_list(extracted.get("theme_tags")),
        "applies_signals": _as_str_list(extracted.get("applies_signals")),
        "blocker_signals": _as_str_list(extracted.get("blocker_signals")),
        "dominant_dimensions": _as_str_list(extracted.get("dominant_dimensions")),
    }


def _source_row(
    *,
    final_context: RetrievalContext | None,
    semantic_signals: dict[str, list[str]],
    deterministic_signals: dict[str, list[str]],
) -> dict[str, dict[str, str]]:
    if final_context is None:
        return {
            "theme_tags": {},
            "applies_signals": {},
            "blocker_signals": {},
            "dominant_dimensions": {},
        }
    final_values = {
        "theme_tags": final_context.theme_tags,
        "applies_signals": final_context.applies_signals,
        "blocker_signals": final_context.blocker_signals,
        "dominant_dimensions": final_context.dominant_dimensions,
    }
    sources: dict[str, dict[str, str]] = {}
    for key, values in final_values.items():
        semantic_set = set(semantic_signals.get(key, []))
        deterministic_set = set(deterministic_signals.get(key, []))
        key_sources: dict[str, str] = {}
        for value in values:
            in_semantic = value in semantic_set
            in_deterministic = value in deterministic_set
            if in_semantic and in_deterministic:
                key_sources[value] = "both"
            elif in_semantic:
                key_sources[value] = "semantic"
            elif in_deterministic:
                key_sources[value] = "deterministic_extractor"
            else:
                key_sources[value] = "unknown"
        sources[key] = key_sources
    return sources


def _too_sparse_context(context: RetrievalContext | None) -> bool:
    if context is None:
        return True
    return not (context.theme_tags or context.applies_signals or context.blocker_signals)


def _top_candidates(context: RetrievalContext | None) -> list[dict[str, Any]]:
    if context is None:
        return []
    active_entries = VerseCatalog(load_curated_verses()).list_active()
    ranked = rank_candidates(active_entries, context)
    return [_candidate_row(candidate, idx + 1) for idx, candidate in enumerate(ranked[:5])]


def _case_flags(
    *,
    expected_shape: str,
    expected_allowed_verses: list[str],
    actual_label: str,
    rich_label: str | None,
    context: RetrievalContext | None,
    top_candidates: list[dict[str, Any]],
    missing_expected_signals: dict[str, list[str]],
) -> list[str]:
    flags: list[str] = []
    actual_is_verse = actual_label != "fallback"
    if expected_shape == "fallback" and actual_is_verse:
        flags.append("unexpected verse")
    if expected_shape == "verse" and not actual_is_verse:
        flags.append("unexpected fallback")
    if actual_is_verse and expected_allowed_verses and actual_label not in expected_allowed_verses:
        flags.append("disallowed verse")
    if (
        (expected_shape == "fallback" and actual_is_verse)
        or (expected_shape == "verse" and not actual_is_verse)
        or (actual_is_verse and expected_allowed_verses and actual_label not in expected_allowed_verses)
    ):
        flags.append("expected/actual live mismatch")
    if rich_label is not None and actual_label != rich_label:
        flags.append("live differs from rich context")
    if rich_label is not None and rich_label in (expected_allowed_verses or [expected_shape]) and "expected/actual live mismatch" in flags:
        flags.append("rich audit passes but live audit fails")
    if _too_sparse_context(context):
        flags.append("semantic/context extraction too sparse")
    if actual_label == "fallback" and expected_shape == "verse" and _too_sparse_context(context):
        flags.append("fallback due to missing live signals")
    if actual_label != "fallback" and expected_shape == "fallback":
        flags.append("live verse where rich benchmark expects fallback")
        flags.append("possible overtrigger")
    if actual_label != "fallback" and top_candidates:
        winner = top_candidates[0]
        if winner["theme_overlap_count"] < 2 or winner["applies_when_hits_count"] == 0:
            flags.append("weak live verse match")
            flags.append("possible forced match")
    if any(missing_expected_signals.values()):
        flags.append("missing expected signals")
    return flags


def _semantic_stub_only(dilemma: str) -> dict[str, Any]:
    return semantic_scorer(dilemma, use_stub=True)


def _run_one_live_case(
    item: dict[str, Any],
    *,
    handler: EngineHandler,
    semantic_scorer_override: SemanticScorer | None,
) -> tuple[dict[str, Any], RetrievalContext | None, EthicalDimensions | None, dict[str, Any] | None]:
    captured: dict[str, Any] = {"context": None, "dimensions": None, "semantic": None}
    original_retrieve = engine_analyzer.retrieve_verse

    def _capturing_retrieve(
        dilemma: str,
        dimensions: EthicalDimensions,
        context_override: RetrievalContext | None = None,
    ) -> dict[str, Any]:
        captured["context"] = context_override
        captured["dimensions"] = dimensions
        return original_retrieve(dilemma, dimensions, context_override=context_override)

    scorer = semantic_scorer_override or _semantic_stub_only

    def _capturing_semantic_scorer(dilemma: str) -> dict[str, Any]:
        payload = scorer(dilemma)
        captured["semantic"] = payload
        return payload

    payload = {"dilemma": str(item.get("dilemma", ""))}
    with (
        mock.patch("app.engine.analyzer.retrieve_verse", _capturing_retrieve),
        mock.patch("app.engine.analyzer.semantic_scorer", _capturing_semantic_scorer),
    ):
        response = handler(payload)

    if isinstance(response, EngineAnalyzeErrorResponse):
        return (
            {
                "error": response.model_dump(mode="json")["error"],
            },
            captured["context"],
            captured["dimensions"],
            captured["semantic"],
        )
    return response.model_dump(mode="json"), captured["context"], captured["dimensions"], captured["semantic"]


def _summary(cases: list[dict[str, Any]]) -> dict[str, Any]:
    total_cases = len(cases)
    attach_count = sum(1 for case in cases if case["actual"]["label"] != "fallback")
    expected_mismatches = [
        {
            "dilemma_id": case["dilemma_id"],
            "expected": case["expected"]["label"],
            "actual": case["actual"]["label"],
            "flags": case["flags"],
        }
        for case in cases
        if "expected/actual live mismatch" in case["flags"]
    ]
    expected_shape_mismatches = [
        {
            "dilemma_id": case["dilemma_id"],
            "expected_shape": case["expected"]["shape"],
            "actual": case["actual"]["label"],
            "flags": case["flags"],
        }
        for case in cases
        if "unexpected verse" in case["flags"] or "unexpected fallback" in case["flags"]
    ]
    unexpected_verse_cases = [
        {
            "dilemma_id": case["dilemma_id"],
            "actual": case["actual"]["label"],
            "expected_shape": case["expected"]["shape"],
        }
        for case in cases
        if "unexpected verse" in case["flags"]
    ]
    unexpected_fallback_cases = [
        {
            "dilemma_id": case["dilemma_id"],
            "expected_allowed_verses": case["expected"]["allowed_verses"],
        }
        for case in cases
        if "unexpected fallback" in case["flags"]
    ]
    disallowed_verse_cases = [
        {
            "dilemma_id": case["dilemma_id"],
            "actual": case["actual"]["label"],
            "expected_allowed_verses": case["expected"]["allowed_verses"],
        }
        for case in cases
        if "disallowed verse" in case["flags"]
    ]
    live_vs_rich = [
        {
            "dilemma_id": case["dilemma_id"],
            "rich": case["rich_context_actual"]["label"],
            "live": case["actual"]["label"],
            "flags": case["flags"],
        }
        for case in cases
        if "live differs from rich context" in case["flags"]
    ]
    rich_pass_live_fail = [
        {
            "dilemma_id": case["dilemma_id"],
            "expected": case["expected"]["label"],
            "live": case["actual"]["label"],
            "flags": case["flags"],
        }
        for case in cases
        if "rich audit passes but live audit fails" in case["flags"]
    ]
    sparse_cases = [
        {
            "dilemma_id": case["dilemma_id"],
            "actual": case["actual"]["label"],
            "expected": case["expected"]["label"],
        }
        for case in cases
        if "semantic/context extraction too sparse" in case["flags"]
    ]
    fallback_missing_signals = [
        {
            "dilemma_id": case["dilemma_id"],
            "expected": case["expected"]["label"],
            "top_candidate": case["top_candidates"][0]["verse_ref"] if case["top_candidates"] else None,
            "top_candidate_score": case["top_candidates"][0]["total_score"] if case["top_candidates"] else None,
        }
        for case in cases
        if "fallback due to missing live signals" in case["flags"]
    ]
    live_false_positive_verses = [
        {
            "dilemma_id": case["dilemma_id"],
            "actual": case["actual"]["label"],
        }
        for case in cases
        if "live verse where rich benchmark expects fallback" in case["flags"]
    ]
    missing_expected_signal_cases = [
        {
            "dilemma_id": case["dilemma_id"],
            "missing_expected_signals": case["missing_expected_signals"],
        }
        for case in cases
        if "missing expected signals" in case["flags"]
    ]
    possible_forced_match_cases = [
        {
            "dilemma_id": case["dilemma_id"],
            "actual": case["actual"]["label"],
            "winner": case["top_candidates"][0] if case["top_candidates"] else None,
            "flags": case["flags"],
        }
        for case in cases
        if "possible forced match" in case["flags"]
    ]
    possible_overtrigger_cases = [
        {
            "dilemma_id": case["dilemma_id"],
            "actual": case["actual"]["label"],
            "flags": case["flags"],
        }
        for case in cases
        if "possible overtrigger" in case["flags"]
    ]

    return {
        "total_cases": total_cases,
        "expected_vs_actual_live_mismatches": expected_mismatches,
        "expected_shape_mismatches": expected_shape_mismatches,
        "unexpected_verse_cases": unexpected_verse_cases,
        "unexpected_fallback_cases": unexpected_fallback_cases,
        "disallowed_verse_cases": disallowed_verse_cases,
        "missing_expected_signal_cases": missing_expected_signal_cases,
        "possible_forced_match_cases": possible_forced_match_cases,
        "possible_overtrigger_cases": possible_overtrigger_cases,
        "live_verse_attach_rate": _pct(attach_count, total_cases),
        "live_fallback_rate": _pct(total_cases - attach_count, total_cases),
        "live_vs_rich_context_diff_count": len(live_vs_rich),
        "live_vs_rich_context_differences": live_vs_rich,
        "rich_pass_live_fail_cases": rich_pass_live_fail,
        "too_sparse_context_cases": sparse_cases,
        "fallback_due_to_missing_live_signals_cases": fallback_missing_signals,
        "live_verse_where_rich_expected_fallback_cases": live_false_positive_verses,
    }


def _expected_from_item(item: dict[str, Any]) -> tuple[str, list[str], str | None]:
    if "expected_shape" in item:
        shape = str(item.get("expected_shape", "fallback")).strip()
        if shape not in {"verse", "fallback"}:
            raise ValueError(f"{item.get('dilemma_id', 'unknown')}: invalid expected_shape {shape!r}")
        allowed = _as_str_list(item.get("expected_allowed_verses"))
        expected_ref = allowed[0] if shape == "verse" and allowed else None
        return shape, allowed, expected_ref
    expected_ref = _expected_retrieval_verse_ref(item)
    if expected_ref is None:
        return "fallback", [], None
    return "verse", [expected_ref], expected_ref


def _expected_signal_hints(item: dict[str, Any]) -> dict[str, list[str]]:
    raw = item.get("expected_signal_hints")
    if not isinstance(raw, dict):
        return {"themes": [], "applies": [], "blockers": []}
    return {
        "themes": _as_str_list(raw.get("themes")),
        "applies": _as_str_list(raw.get("applies")),
        "blockers": _as_str_list(raw.get("blockers")),
    }


def _missing_expected_signals(
    *,
    hints: dict[str, list[str]],
    context: RetrievalContext | None,
) -> dict[str, list[str]]:
    if context is None:
        return {key: values for key, values in hints.items() if values}
    actual = {
        "themes": set(context.theme_tags),
        "applies": set(context.applies_signals),
        "blockers": set(context.blocker_signals),
    }
    return {
        key: [value for value in expected_values if value not in actual[key]]
        for key, expected_values in hints.items()
    }


def run_live_retrieval_audit(
    *,
    input_path: Path | None = None,
    handler: EngineHandler | None = None,
    semantic_scorer_override: SemanticScorer | None = None,
) -> dict[str, Any]:
    """Run sparse live-style dilemmas through the engine boundary and audit retrieval."""
    resolved_path = input_path or DEFAULT_BENCHMARK_PATH
    dilemmas, input_kind = _load_audit_items(resolved_path)
    engine_handler = handler or engine_analyzer.handle_engine_request
    rich_by_id: dict[str, dict[str, Any]] = {}
    if input_kind == "benchmark":
        rich_report = run_retrieval_audit(input_path=resolved_path)
        rich_by_id = {case["dilemma_id"]: case for case in rich_report["cases"]}

    cases: list[dict[str, Any]] = []
    for item in dilemmas:
        dilemma_id = str(item.get("dilemma_id", "unknown"))
        expected_shape, expected_allowed_verses, expected_ref = _expected_from_item(item)
        expected_label = (
            _expected_label(expected_ref)
            if expected_shape == "verse" and expected_ref is not None
            else expected_shape
        )
        response, context, captured_dimensions, semantic_payload = _run_one_live_case(
            item,
            handler=engine_handler,
            semantic_scorer_override=semantic_scorer_override,
        )
        output = response.get("output") if isinstance(response.get("output"), dict) else {}
        error = response.get("error")

        verse_match = output.get("verse_match") if isinstance(output, dict) else None
        actual_ref = verse_match.get("verse_ref") if isinstance(verse_match, dict) else None
        actual_label = _actual_label(actual_ref)
        rich_case = rich_by_id.get(dilemma_id, {})
        rich_label = rich_case.get("actual", {}).get("label") if isinstance(rich_case, dict) else None
        top_candidates = _top_candidates(context)
        semantic_signals = _semantic_signal_row(semantic_payload, captured_dimensions)
        deterministic_signals = _deterministic_signal_row(str(item.get("dilemma", "")))
        signal_sources = _source_row(
            final_context=context,
            semantic_signals=semantic_signals,
            deterministic_signals=deterministic_signals,
        )
        expected_signal_hints = _expected_signal_hints(item)
        missing_expected_signals = _missing_expected_signals(
            hints=expected_signal_hints,
            context=context,
        )
        flags = _case_flags(
            expected_shape=expected_shape,
            expected_allowed_verses=expected_allowed_verses,
            actual_label=actual_label,
            rich_label=rich_label,
            context=context,
            top_candidates=top_candidates,
            missing_expected_signals=missing_expected_signals,
        )

        case = {
            "dilemma_id": dilemma_id,
            "dilemma": str(item.get("dilemma", "")),
            "payload": {"dilemma": str(item.get("dilemma", ""))},
            "expected": {
                "verse_ref": expected_ref,
                "label": expected_label,
                "shape": expected_shape,
                "allowed_verses": expected_allowed_verses,
            },
            "actual": {
                "verse_ref": actual_ref,
                "label": actual_label,
                "is_fallback": actual_ref is None,
            },
            "rich_context_actual": {
                "label": rich_label,
            },
            "engine_error": error,
            "generated_internal_driver": output.get("internal_driver") if isinstance(output, dict) else None,
            "generated_ethical_dimensions": output.get("ethical_dimensions") if isinstance(output, dict) else None,
            "generated_missing_facts": output.get("missing_facts") if isinstance(output, dict) else None,
            "captured_dimensions": captured_dimensions.model_dump(mode="json") if captured_dimensions else None,
            "semantic_context_signals": semantic_signals,
            "deterministic_extractor_signals": deterministic_signals,
            "signal_sources": signal_sources,
            "expected_signal_hints": expected_signal_hints,
            "missing_expected_signals": missing_expected_signals,
            "retrieval_context": _context_row(context),
            "top_candidates": top_candidates,
            "flags": flags,
        }
        cases.append(case)

    return {
        "audit_version": "live-retrieval-audit-v1",
        "benchmark_source_path": str(resolved_path),
        "input_kind": input_kind,
        "semantic_mode": "stubbed_deterministic",
        "input_style": "live_sparse_dilemma_only",
        "summary": _summary(cases),
        "cases": cases,
    }


def render_markdown_report(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Live Retrieval Audit",
        "",
        f"- Source: `{report['benchmark_source_path']}`",
        f"- Input style: `{report['input_style']}`",
        f"- Semantic mode: `{report['semantic_mode']}`",
        f"- Total cases: {summary['total_cases']}",
        f"- Live verse attach rate: {summary['live_verse_attach_rate']}%",
        f"- Live fallback rate: {summary['live_fallback_rate']}%",
        f"- Live vs rich diff count: {summary['live_vs_rich_context_diff_count']}",
        "",
        "## Expected/Actual Live Mismatches",
    ]
    mismatches = summary["expected_vs_actual_live_mismatches"]
    if not mismatches:
        lines.append("None.")
    else:
        lines.extend(
            f"- `{row['dilemma_id']}` expected `{row['expected']}`, actual `{row['actual']}`"
            for row in mismatches
        )

    sections = [
        ("Rich Pass, Live Fail", summary["rich_pass_live_fail_cases"]),
        ("Too Sparse Context", summary["too_sparse_context_cases"]),
        ("Fallback Due To Missing Live Signals", summary["fallback_due_to_missing_live_signals_cases"]),
        ("Live Verse Where Rich Expected Fallback", summary["live_verse_where_rich_expected_fallback_cases"]),
        ("Expected Shape Mismatches", summary["expected_shape_mismatches"]),
        ("Unexpected Verse Cases", summary["unexpected_verse_cases"]),
        ("Unexpected Fallback Cases", summary["unexpected_fallback_cases"]),
        ("Disallowed Verse Cases", summary["disallowed_verse_cases"]),
        ("Missing Expected Signal Cases", summary["missing_expected_signal_cases"]),
        ("Possible Forced Match Cases", summary["possible_forced_match_cases"]),
        ("Possible Overtrigger Cases", summary["possible_overtrigger_cases"]),
    ]
    for title, rows in sections:
        lines.extend(["", f"## {title}"])
        if not rows:
            lines.append("None.")
            continue
        for row in rows:
            details = ", ".join(f"{key}=`{value}`" for key, value in row.items() if key != "flags")
            lines.append(f"- {details}")

    return "\n".join(lines).rstrip() + "\n"


def write_audit_outputs(report: dict[str, Any], *, out_json: Path, out_md: Path) -> None:
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    out_md.write_text(render_markdown_report(report), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run deterministic live-style sparse-input retrieval audit."
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
        default=Path("artifacts/live_retrieval_audit_W001-W020.json"),
        help="Output JSON path.",
    )
    parser.add_argument(
        "--out-md",
        type=Path,
        default=Path("artifacts/live_retrieval_audit_W001-W020.md"),
        help="Output Markdown path.",
    )
    args = parser.parse_args()

    report = run_live_retrieval_audit(input_path=args.input)
    write_audit_outputs(report, out_json=args.out_json, out_md=args.out_md)
    print(
        "Live retrieval audit:"
        f" total_cases={report['summary']['total_cases']},"
        f" live_verse_attach_rate={report['summary']['live_verse_attach_rate']}%,"
        f" live_fallback_rate={report['summary']['live_fallback_rate']}%,"
        f" live_vs_rich_diff_count={report['summary']['live_vs_rich_context_diff_count']}"
    )
    print(f"Saved JSON report to: {args.out_json}")
    print(f"Saved Markdown report to: {args.out_md}")


if __name__ == "__main__":
    main()
