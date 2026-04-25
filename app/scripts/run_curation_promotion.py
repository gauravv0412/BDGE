"""
Plan curation promotion from an editor-prep file and write a review artifact.

Does **not** modify ``verses_seed.json``. Use ``merge_promoted_into_seed_json`` in
a controlled environment when merging is intentional.

Usage::

    PYTHONPATH=. .venv/bin/python -m app.scripts.run_curation_promotion \\
        --prep app/verses/data/curation_prep/verses_editor_prep.json \\
        --out app/verses/data/curation_prep/verses_promotion_review.json
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.verses.curation_prep import load_curation_prep_artifact
from app.verses.curation_promotion import (
    PromotionError,
    build_promotion_plan,
    write_promotion_review_artifact,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build curation promotion review artifact.")
    parser.add_argument(
        "--prep",
        type=Path,
        required=True,
        help="Path to verses_editor_prep.json (or compatible prep artifact).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Review JSON output path (default: verses_promotion_review.json under curation_prep/).",
    )
    parser.add_argument(
        "--allow-large-batch",
        action="store_true",
        help=f"Disable default max promotion batch size guard.",
    )
    args = parser.parse_args(argv)

    try:
        prep = load_curation_prep_artifact(args.prep)
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        return 1
    try:
        plan = build_promotion_plan(
            prep,
            allow_large_batch=bool(args.allow_large_batch),
        )
    except PromotionError as exc:
        print(exc, file=sys.stderr)
        return 1

    path = write_promotion_review_artifact(plan, path=args.out)
    print(
        f"Wrote {path}: {len(plan.promoted)} promoted, "
        f"{plan.skipped_not_requested} skipped (not requested), "
        f"{plan.promotion_requested_count} requested."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
