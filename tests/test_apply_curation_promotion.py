"""Tests for guarded apply curation promotion CLI."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from app.scripts.apply_curation_promotion import main
from app.verses.curation_prep import (
    CANONICAL_RAW_CORPUS_FILENAME,
    CurationPrepArtifact,
    CurationPrepEntry,
    CurationPrepHeader,
    CurationPrepPlaceholders,
    build_curation_prep_artifact,
)
from app.verses.curation_promotion import build_promotion_plan, write_promotion_review_artifact
from app.verses.loader import curated_verses_seed_path, load_curated_verses, validate_curated_seed_payload


def _filled_placeholders() -> CurationPrepPlaceholders:
    return CurationPrepPlaceholders(
        core_teaching="Act from duty without fixation.",
        themes=["duty"],
        applies_when=["duty-conflict"],
        does_not_apply_when=["active-harm"],
        priority=4,
        status="draft",
    )


def _review_for_new_verse(tmp_path: Path) -> Path:
    full = build_curation_prep_artifact()
    target = next(e for e in full.entries if e.scripture.verse_ref == "1.1")
    prep = CurationPrepArtifact(
        header=CurationPrepHeader(
            canonical_raw_filename=CANONICAL_RAW_CORPUS_FILENAME,
            verse_entry_count=1,
        ),
        entries=[
            CurationPrepEntry(
                promotion_requested=True,
                scripture=target.scripture,
                placeholders=_filled_placeholders(),
            )
        ],
    )
    plan = build_promotion_plan(prep, existing_entries=load_curated_verses())
    out = tmp_path / "review.json"
    write_promotion_review_artifact(plan, path=out)
    return out



def test_dry_run_does_not_mutate_seed_file(tmp_path: Path) -> None:
    review = _review_for_new_verse(tmp_path)
    seed_src = curated_verses_seed_path()
    seed_copy = tmp_path / "seed.json"
    shutil.copy(seed_src, seed_copy)
    before = seed_copy.read_bytes()

    rc = main(["--review", str(review), "--seed", str(seed_copy)])
    assert rc == 0
    assert seed_copy.read_bytes() == before


def test_write_without_confirm_fails_for_production_seed(tmp_path: Path) -> None:
    review = _review_for_new_verse(tmp_path)
    rc = main([
        "--review",
        str(review),
        "--seed",
        str(curated_verses_seed_path()),
        "--write",
    ])
    assert rc == 1


def test_write_with_confirm_succeeds_with_monkeypatched_production(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    review = _review_for_new_verse(tmp_path)
    production_like = tmp_path / "production_seed.json"
    shutil.copy(curated_verses_seed_path(), production_like)

    monkeypatch.setattr(
        "app.scripts.apply_curation_promotion.curated_verses_seed_path",
        lambda: production_like,
    )

    before_count = len(validate_curated_seed_payload(json.loads(production_like.read_text(encoding="utf-8"))))
    rc = main([
        "--review",
        str(review),
        "--write",
        "--confirm-production-curated-write",
    ])
    assert rc == 0
    after_count = len(validate_curated_seed_payload(json.loads(production_like.read_text(encoding="utf-8"))))
    assert after_count == before_count + 1


def test_duplicate_conflict_fails_clearly(tmp_path: Path) -> None:
    review = _review_for_new_verse(tmp_path)
    seed_copy = tmp_path / "seed.json"
    shutil.copy(curated_verses_seed_path(), seed_copy)

    rc_first = main(["--review", str(review), "--seed", str(seed_copy), "--write"])
    assert rc_first == 0

    rc_second = main(["--review", str(review), "--seed", str(seed_copy), "--write"])
    assert rc_second == 1


def test_malformed_review_artifact_fails_clearly(tmp_path: Path) -> None:
    bad = tmp_path / "bad_review.json"
    bad.write_text(json.dumps({"schema_id": "bdge.curation_promotion_review.v1"}), encoding="utf-8")

    rc = main(["--review", str(bad), "--seed", str(curated_verses_seed_path())])
    assert rc == 1
