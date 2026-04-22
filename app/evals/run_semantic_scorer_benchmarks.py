"""
Run semantic-scorer quality checks over the benchmark dilemmas.

This harness evaluates only ``app/semantic/scorer.py`` outputs against the
semantic scorer schema and ontology checks. It does not call the deterministic
verdict layer and does not use ``docs/output_schema.json``.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from app.core.benchmark_loader import load_dilemmas
from app.semantic.guards import check_no_fake_scripture
from app.semantic.scorer import semantic_scorer, validate_semantic_payload

_FIXED_DIMENSION_KEYS = {
    "dharma_duty",
    "satya_truth",
    "ahimsa_nonharm",
    "nishkama_detachment",
    "shaucha_intent",
    "sanyama_restraint",
    "lokasangraha_welfare",
    "viveka_discernment",
}
_CHAPTER_VERSE_RE = re.compile(r"\b\d+\.\d+(?:-\d+)?\b")


@dataclass(frozen=True)
class SemanticBenchResult:
    dilemma_id: str
    valid_semantic_schema: bool
    exact_dimension_keys: bool
    ambiguity_matches_gold_context_dependent: bool
    missing_facts_len_le_6: bool
    reflective_question_nested_and_question_mark: bool
    fake_scripture_leak_free: bool
    passed_all_checks: bool
    errors: list[str]


def _schema_error_category(error: str) -> str:
    """Return a compact category label for a schema validation error."""
    if ":" in error:
        return error.split(":", maxsplit=1)[0].strip() or "(root)"
    return "(schema)"


def _has_fake_scripture_leak(payload: dict[str, Any]) -> bool:
    """Detect scripture leakage via guard markers or chapter.verse patterns."""
    guard_issues = check_no_fake_scripture(payload)
    if guard_issues:
        return True

    text_fields = [
        str(payload.get("core_reading", "")),
        str(payload.get("gita_analysis", "")),
        str(payload.get("higher_path", "")),
        str(payload.get("share_layer", {}).get("card_quote", "")),
        str(payload.get("share_layer", {}).get("reflective_question", "")),
    ]
    return any(_CHAPTER_VERSE_RE.search(text) for text in text_fields)


def _evaluate_one(
    item: dict[str, Any],
    *,
    use_stub: bool | None,
) -> SemanticBenchResult:
    dilemma_id = str(item.get("dilemma_id", "unknown"))
    dilemma = str(item.get("dilemma", ""))
    gold_is_context = item.get("classification") == "Context-dependent"

    errors: list[str] = []
    try:
        out = semantic_scorer(dilemma, use_stub=use_stub)
    except Exception as exc:  # noqa: BLE001
        return SemanticBenchResult(
            dilemma_id=dilemma_id,
            valid_semantic_schema=False,
            exact_dimension_keys=False,
            ambiguity_matches_gold_context_dependent=False,
            missing_facts_len_le_6=False,
            reflective_question_nested_and_question_mark=False,
            fake_scripture_leak_free=False,
            passed_all_checks=False,
            errors=[f"semantic_call_failed: {exc}"],
        )

    schema_ok, schema_errors = validate_semantic_payload(out)
    if not schema_ok:
        errors.extend(f"schema:{err}" for err in schema_errors)

    dims = out.get("ethical_dimensions")
    exact_dimension_keys = isinstance(dims, dict) and set(dims.keys()) == _FIXED_DIMENSION_KEYS
    if not exact_dimension_keys:
        errors.append("ontology:ethical_dimensions must be object with exact fixed 8 keys")

    ambiguity_flag = out.get("ambiguity_flag")
    ambiguity_matches = isinstance(ambiguity_flag, bool) and (ambiguity_flag == gold_is_context)
    if not ambiguity_matches:
        errors.append(
            "consistency:ambiguity_flag mismatch vs gold Context-dependent classification"
        )

    missing_facts = out.get("missing_facts", [])
    missing_len_ok = isinstance(missing_facts, list) and len(missing_facts) <= 6
    if not missing_len_ok:
        errors.append("contract:missing_facts length must be <= 6")

    share = out.get("share_layer")
    reflective = share.get("reflective_question") if isinstance(share, dict) else None
    reflective_ok = isinstance(reflective, str) and reflective.endswith("?")
    if not reflective_ok:
        errors.append("contract:share_layer.reflective_question missing or not ending with '?'")

    no_fake_scripture = not _has_fake_scripture_leak(out)
    if not no_fake_scripture:
        errors.append("safety:fake scripture or chapter.verse leak detected")

    passed = (
        schema_ok
        and exact_dimension_keys
        and ambiguity_matches
        and missing_len_ok
        and reflective_ok
        and no_fake_scripture
    )
    return SemanticBenchResult(
        dilemma_id=dilemma_id,
        valid_semantic_schema=schema_ok,
        exact_dimension_keys=exact_dimension_keys,
        ambiguity_matches_gold_context_dependent=ambiguity_matches,
        missing_facts_len_le_6=missing_len_ok,
        reflective_question_nested_and_question_mark=reflective_ok,
        fake_scripture_leak_free=no_fake_scripture,
        passed_all_checks=passed,
        errors=errors,
    )


def run_semantic_scorer_benchmarks(
    *,
    benchmark_path: Path | None = None,
    use_stub: bool | None = None,
    selected_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Run semantic scorer benchmark checks and return structured report data."""
    dilemmas = load_dilemmas(path=benchmark_path)
    if selected_ids:
        wanted = {d.strip() for d in selected_ids if d.strip()}
        present = {str(item.get("dilemma_id", "")) for item in dilemmas}
        unknown = sorted(wanted - present)
        if unknown:
            raise ValueError(
                "Unknown dilemma_id values requested: " + ", ".join(unknown)
            )
        dilemmas = [item for item in dilemmas if str(item.get("dilemma_id", "")) in wanted]
    results = [_evaluate_one(item, use_stub=use_stub) for item in dilemmas]

    passed = sum(1 for r in results if r.passed_all_checks)
    total = len(results)
    failed_ids = [r.dilemma_id for r in results if not r.passed_all_checks]

    categories = Counter()
    for r in results:
        for err in r.errors:
            categories[_schema_error_category(err)] += 1

    return {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "selected_dilemma_ids": selected_ids or [],
        "failed_dilemma_ids": failed_ids,
        "top_error_categories": categories.most_common(10),
        "results": [asdict(r) for r in results],
    }


def _print_summary(report: dict[str, Any]) -> None:
    selected = report.get("selected_dilemma_ids") or []
    if selected:
        print("Selected dilemma IDs:", ", ".join(selected))
    total = report["total"]
    passed = report["passed"]
    failed = report["failed"]
    print(f"Semantic scorer benchmark: {passed}/{total} passed, {failed}/{total} failed")
    if report["failed_dilemma_ids"]:
        print("Failed dilemma IDs:", ", ".join(report["failed_dilemma_ids"]))
    else:
        print("Failed dilemma IDs: none")

    if report["top_error_categories"]:
        print("Top error categories:")
        for cat, count in report["top_error_categories"]:
            print(f"  - {cat}: {count}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run semantic scorer benchmark checks over docs benchmark dilemmas."
    )
    parser.add_argument(
        "--benchmark",
        type=Path,
        default=None,
        help="Path to benchmark JSON (default: docs/benchmarks_v2_batch1_W001-W020.json)",
    )
    parser.add_argument(
        "--ids",
        type=str,
        default="",
        help="Comma-separated dilemma IDs to run (e.g. W003,W007).",
    )
    parser.add_argument(
        "--id",
        dest="ids_list",
        action="append",
        default=[],
        help="Repeatable dilemma ID filter (e.g. --id W003 --id W007).",
    )
    parser.add_argument(
        "--mode",
        choices=("default", "stub", "live"),
        default="default",
        help=(
            "semantic_scorer mode: default=use config use_stub_default; "
            "stub=force stub; live=force Anthropic live"
        ),
    )
    parser.add_argument(
        "--report-json",
        type=Path,
        default=None,
        help="Optional path to write full JSON report (e.g. app/evals/semantic_report.json)",
    )
    args = parser.parse_args()

    use_stub = None
    if args.mode == "stub":
        use_stub = True
    elif args.mode == "live":
        use_stub = False

    selected_ids: list[str] = []
    if args.ids:
        selected_ids.extend([chunk.strip() for chunk in args.ids.split(",") if chunk.strip()])
    if args.ids_list:
        selected_ids.extend([chunk.strip() for chunk in args.ids_list if chunk.strip()])

    deduped_selected_ids: list[str] = []
    for did in selected_ids:
        if did not in deduped_selected_ids:
            deduped_selected_ids.append(did)

    report = run_semantic_scorer_benchmarks(
        benchmark_path=args.benchmark,
        use_stub=use_stub,
        selected_ids=deduped_selected_ids or None,
    )
    _print_summary(report)

    if args.report_json is not None:
        args.report_json.parent.mkdir(parents=True, exist_ok=True)
        with args.report_json.open("w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"Saved JSON report to: {args.report_json}")


if __name__ == "__main__":
    main()

