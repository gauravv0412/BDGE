"""Guarded production activation for every curated verse entry."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.evals.run_full_activation_dry_run import (
    DEFAULT_OUT_JSON as DEFAULT_DRY_RUN_JSON,
    DEFAULT_OUT_MD as DEFAULT_DRY_RUN_MD,
    run_full_activation_dry_run,
    write_dry_run_outputs,
)
from app.evals.run_live_retrieval_audit import (
    DEFAULT_BENCHMARK_PATH,
    write_audit_outputs as write_live_audit_outputs,
    run_live_retrieval_audit,
)
from app.evals.run_reference_benchmark_comparison import (
    DEFAULT_OUT_JSON as DEFAULT_COMPARISON_JSON,
    DEFAULT_OUT_MD as DEFAULT_COMPARISON_MD,
    DEFAULT_RETRIEVAL_EVAL_PATH,
    run_reference_benchmark_comparison,
    write_comparison_outputs,
)
from app.verses.loader import curated_verses_seed_path, validate_curated_seed_payload

ActivationAuditRunner = Callable[[], dict[str, Any]]

_BLOCKING_SUMMARY_KEYS = (
    "shape_lock_regressions_count",
    "blocker_failure_count",
    "forced_match_warning_count",
    "overtrigger_warning_count",
)


@dataclass(frozen=True)
class ActivationResult:
    seed_path: Path
    total_curated_entries: int
    active_before: int
    active_after: int
    would_activate_refs: tuple[str, ...]
    already_active_refs: tuple[str, ...]
    wrote: bool
    audit_summary: dict[str, Any]


def _load_seed_payload(seed_path: Path) -> list[dict[str, Any]]:
    payload = json.loads(seed_path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"Expected list payload in {seed_path}.")
    validate_curated_seed_payload(payload)
    return payload


def _activation_counts(payload: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    already_active: list[str] = []
    would_activate: list[str] = []
    for entry in payload:
        ref = str(entry.get("verse_ref", "unknown"))
        if entry.get("status") == "active":
            already_active.append(ref)
        else:
            would_activate.append(ref)
    return already_active, would_activate


def _blocking_reasons(summary: dict[str, Any]) -> list[str]:
    reasons = []
    for key in _BLOCKING_SUMMARY_KEYS:
        value = int(summary.get(key, 0))
        if value > 0:
            reasons.append(f"{key}={value}")
    if bool(summary.get("should_block_full_activation")):
        reasons.append("should_block_full_activation=true")
    return reasons


def _write_all_active(seed_path: Path, payload: list[dict[str, Any]]) -> int:
    activated = [{**entry, "status": "active"} for entry in payload]
    validated = validate_curated_seed_payload(activated)
    seed_path.write_text(
        json.dumps([entry.model_dump(mode="json") for entry in validated], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return sum(1 for entry in validated if entry.status == "active")


def refresh_activation_artifacts() -> dict[str, Path]:
    """Regenerate audit artifacts expected after production activation."""
    dry_run_report = run_full_activation_dry_run()
    write_dry_run_outputs(dry_run_report, out_json=DEFAULT_DRY_RUN_JSON, out_md=DEFAULT_DRY_RUN_MD)

    comparison = run_reference_benchmark_comparison(fixture_path=DEFAULT_RETRIEVAL_EVAL_PATH)
    write_comparison_outputs(comparison, out_json=DEFAULT_COMPARISON_JSON, out_md=DEFAULT_COMPARISON_MD)

    live_w001_w020 = run_live_retrieval_audit(input_path=DEFAULT_BENCHMARK_PATH)
    live_w001_json = Path("artifacts/live_retrieval_audit_W001-W020.json")
    live_w001_md = Path("artifacts/live_retrieval_audit_W001-W020.md")
    write_live_audit_outputs(live_w001_w020, out_json=live_w001_json, out_md=live_w001_md)

    live_ood_path = Path("tests/fixtures/live_retrieval_ood_W021-W050.json")
    live_w021_w050 = run_live_retrieval_audit(input_path=live_ood_path)
    live_w021_json = Path("artifacts/live_retrieval_audit_W021-W050.json")
    live_w021_md = Path("artifacts/live_retrieval_audit_W021-W050.md")
    write_live_audit_outputs(live_w021_w050, out_json=live_w021_json, out_md=live_w021_md)

    return {
        "full_activation_dry_run_json": DEFAULT_DRY_RUN_JSON,
        "full_activation_dry_run_md": DEFAULT_DRY_RUN_MD,
        "benchmark_comparison_json": DEFAULT_COMPARISON_JSON,
        "benchmark_comparison_md": DEFAULT_COMPARISON_MD,
        "live_retrieval_audit_w001_w020_json": live_w001_json,
        "live_retrieval_audit_w001_w020_md": live_w001_md,
        "live_retrieval_audit_w021_w050_json": live_w021_json,
        "live_retrieval_audit_w021_w050_md": live_w021_md,
    }


def activate_all_curated_verses(
    *,
    seed_path: Path,
    write: bool = False,
    confirm_production_curated_write: bool = False,
    audit_runner: ActivationAuditRunner | None = None,
) -> ActivationResult:
    payload = _load_seed_payload(seed_path)
    already_active, would_activate = _activation_counts(payload)
    audit = audit_runner() if audit_runner is not None else run_full_activation_dry_run()
    summary = dict(audit.get("summary", {}))
    blocking_reasons = _blocking_reasons(summary)
    if blocking_reasons:
        raise RuntimeError(
            "Refusing activation because full-activation audit is not clean: "
            + ", ".join(blocking_reasons)
        )

    if write and not confirm_production_curated_write:
        raise PermissionError(
            "Refusing to write curated seed without "
            "--confirm-production-curated-write."
        )

    active_after = len(already_active)
    if write:
        active_after = _write_all_active(seed_path, payload)

    return ActivationResult(
        seed_path=seed_path,
        total_curated_entries=len(payload),
        active_before=len(already_active),
        active_after=active_after,
        would_activate_refs=tuple(would_activate),
        already_active_refs=tuple(already_active),
        wrote=write,
        audit_summary=summary,
    )


def _print_result(result: ActivationResult) -> None:
    print("Curated activation plan:")
    print(f"  seed_path={result.seed_path}")
    print(f"  total_curated_entries={result.total_curated_entries}")
    print(f"  currently_active_count={result.active_before}")
    print(f"  entries_that_would_be_activated={len(result.would_activate_refs)}")
    print(f"  already_active_entries={len(result.already_active_refs)}")
    print(f"  wrote={result.wrote}")
    if result.wrote:
        print(f"  active_count_after={result.active_after}")
    print("Full activation audit gate:")
    for key in _BLOCKING_SUMMARY_KEYS:
        print(f"  {key}={result.audit_summary.get(key, 0)}")
    print(f"  should_block_full_activation={result.audit_summary.get('should_block_full_activation')}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Guardedly activate all curated verses in verses_seed.json."
    )
    parser.add_argument("--seed", type=Path, default=curated_verses_seed_path())
    parser.add_argument("--write", action="store_true", help="Write status=active to every seed entry.")
    parser.add_argument(
        "--confirm-production-curated-write",
        action="store_true",
        help="Required with --write when targeting production verses_seed.json.",
    )
    parser.add_argument(
        "--skip-artifact-refresh",
        action="store_true",
        help="Do not regenerate audit artifacts after a successful write.",
    )
    args = parser.parse_args(argv)

    try:
        result = activate_all_curated_verses(
            seed_path=args.seed,
            write=bool(args.write),
            confirm_production_curated_write=bool(args.confirm_production_curated_write),
        )
    except (PermissionError, RuntimeError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 1

    _print_result(result)
    if result.wrote and not args.skip_artifact_refresh:
        paths = refresh_activation_artifacts()
        print("Refreshed artifacts:")
        for label, path in paths.items():
            print(f"  {label}={path}")
    elif not result.wrote:
        print("Dry-run only. Use --write --confirm-production-curated-write to activate production seed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
