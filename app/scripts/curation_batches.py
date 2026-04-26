"""CLI helper for 10-batch full-corpus curation workflow."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.verses.curation_batches import (
    assert_ten_batch_coverage,
    export_all_batches,
    export_batch,
    import_batch_to_prep,
    load_batch_artifact,
    validate_ai_filled_batch,
)


def _cmd_export(args: argparse.Namespace) -> int:
    if args.batch.lower() == "all":
        try:
            paths = export_all_batches(allow_all=bool(args.allow_all))
        except ValueError as exc:
            print(exc, file=sys.stderr)
            return 1
        for p in paths:
            print(p)
        return 0

    try:
        out = export_batch(args.batch, path=args.out)
    except Exception as exc:  # noqa: BLE001
        print(exc, file=sys.stderr)
        return 1
    print(out)
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    try:
        batch = load_batch_artifact(args.batch_path)
        validate_ai_filled_batch(batch)
    except Exception as exc:  # noqa: BLE001
        print(exc, file=sys.stderr)
        return 1
    print(f"Batch {batch.header.batch_id} is valid for merge/promotion planning.")
    return 0


def _cmd_import(args: argparse.Namespace) -> int:
    try:
        out = import_batch_to_prep(
            args.batch_path,
            base_prep_path=args.base_prep,
            out_path=args.out,
        )
    except Exception as exc:  # noqa: BLE001
        print(exc, file=sys.stderr)
        return 1
    print(out)
    return 0


def _cmd_report(_args: argparse.Namespace) -> int:
    try:
        report = assert_ten_batch_coverage()
    except Exception as exc:  # noqa: BLE001
        print(exc, file=sys.stderr)
        return 1
    print(
        json.dumps(
            report.model_dump(mode="json"),
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="10-batch curation workflow helper")
    sub = parser.add_subparsers(dest="command", required=True)

    p_export = sub.add_parser("export", help="Export one batch artifact (or all with explicit flag)")
    p_export.add_argument("batch", help="Batch id (B01..B10) or 'all'")
    p_export.add_argument("--out", type=Path, default=None)
    p_export.add_argument("--allow-all", action="store_true", help="Required when batch='all'")
    p_export.set_defaults(func=_cmd_export)

    p_validate = sub.add_parser("validate", help="Validate AI-filled batch artifact")
    p_validate.add_argument("batch_path", type=Path)
    p_validate.set_defaults(func=_cmd_validate)

    p_import = sub.add_parser("import", help="Merge validated batch back into curation prep")
    p_import.add_argument("batch_path", type=Path)
    p_import.add_argument("--base-prep", type=Path, default=None)
    p_import.add_argument("--out", type=Path, default=None)
    p_import.set_defaults(func=_cmd_import)

    p_report = sub.add_parser("report", help="Print coverage report for 10-batch plan")
    p_report.set_defaults(func=_cmd_report)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
