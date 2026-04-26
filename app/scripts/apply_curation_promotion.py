"""
Apply a reviewed curation-promotion artifact into a curated seed path.

Default mode is dry-run (no file mutation). Writing requires --write and follows
existing production guardrails in merge_promoted_into_seed_json.

Usage::

    PYTHONPATH=. .venv/bin/python -m app.scripts.apply_curation_promotion \
      --review app/verses/data/curation_prep/verses_promotion_review.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.verses.curation_promotion import (
    load_promotion_review_artifact,
    merge_promoted_into_seed_json,
    promoted_entries_from_review,
)
from app.verses.loader import curated_verses_seed_path, validate_curated_seed_payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Dry-run or apply reviewed promotion entries into curated seed."
    )
    parser.add_argument("--review", type=Path, required=True, help="Promotion review JSON path.")
    parser.add_argument(
        "--seed",
        type=Path,
        default=None,
        help="Curated seed JSON path (default: production verses_seed.json).",
    )
    parser.add_argument("--write", action="store_true", help="Actually write merged seed file.")
    parser.add_argument(
        "--confirm-production-curated-write",
        action="store_true",
        help="Required to write production verses_seed.json.",
    )
    args = parser.parse_args(argv)

    seed_path = args.seed or curated_verses_seed_path()
    write_mode = bool(args.write)

    try:
        review = load_promotion_review_artifact(args.review)
        promoted = promoted_entries_from_review(review)

        before_payload = seed_path.read_text(encoding="utf-8")
        before_count = len(validate_curated_seed_payload(json.loads(before_payload)))

        merged = merge_promoted_into_seed_json(
            seed_path,
            promoted,
            write=write_mode,
            confirm_production_curated_write=bool(args.confirm_production_curated_write),
        )
    except Exception as exc:  # noqa: BLE001
        print(f"Apply promotion failed: {exc}", file=sys.stderr)
        return 1

    promoted_refs = [entry.verse_ref for entry in promoted]
    after_count = len(merged)

    print(f"mode={'write' if write_mode else 'dry-run'}")
    print(f"seed_path={seed_path}")
    print(f"review_path={args.review}")
    print(f"before_count={before_count}")
    print(f"promoted_count={len(promoted)}")
    print(f"after_count={after_count}")
    print(f"promoted_verse_refs={','.join(promoted_refs)}")
    print(f"write_occurred={'yes' if write_mode else 'no'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
