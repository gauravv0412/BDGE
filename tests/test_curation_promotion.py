"""Tests for editor-prep → curated promotion workflow."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from app.verses.curation_prep import (
    CANONICAL_RAW_CORPUS_FILENAME,
    CurationPrepArtifact,
    CurationPrepEntry,
    CurationPrepHeader,
    CurationPrepPlaceholders,
    build_curation_prep_artifact,
)
from app.verses.curation_promotion import (
    PromotionError,
    build_promotion_plan,
    merge_promoted_into_seed_json,
    prep_entry_to_curated_dict,
    validate_promotion_review_payload,
    write_promotion_review_artifact,
)
from app.verses.loader import (
    curated_verses_seed_path,
    load_curated_verses,
    validate_curated_seed_payload,
)
from app.verses.types import CuratedVerseEntry, VerseStatus


def _filled_placeholders(
    *,
    core_teaching: str = "One-line teaching for tests.",
    themes: list[str] | None = None,
    applies_when: list[str] | None = None,
    does_not_apply_when: list[str] | None = None,
    dimension_affinity: dict[str, int] | None = None,
    priority: int = 3,
    status: VerseStatus = "draft",
) -> CurationPrepPlaceholders:
    return CurationPrepPlaceholders(
        core_teaching=core_teaching,
        themes=themes or ["duty"],
        applies_when=applies_when or ["duty-conflict"],
        does_not_apply_when=does_not_apply_when or ["active-harm"],
        dimension_affinity=dimension_affinity or {"dharma_duty": 3},
        priority=priority,
        status=status,
    )


def _artifact_two_entries(
    first: CurationPrepEntry,
    second: CurationPrepEntry,
) -> CurationPrepArtifact:
    return CurationPrepArtifact(
        header=CurationPrepHeader(
            canonical_raw_filename=CANONICAL_RAW_CORPUS_FILENAME,
            verse_entry_count=2,
        ),
        entries=[first, second],
    )


def test_skips_rows_without_promotion_requested() -> None:
    full = build_curation_prep_artifact()
    a = full.entries[0]
    b = full.entries[1]
    prep = _artifact_two_entries(
        CurationPrepEntry(scripture=a.scripture, placeholders=a.placeholders),
        CurationPrepEntry(scripture=b.scripture, placeholders=b.placeholders),
    )
    plan = build_promotion_plan(prep, existing_entries=())
    assert plan.promoted == ()
    assert plan.skipped_not_requested == 2
    assert plan.promotion_requested_count == 0


def test_valid_promoted_row_becomes_curated_entry() -> None:
    full = build_curation_prep_artifact()
    v = full.entries[0]
    prep = _artifact_two_entries(
        CurationPrepEntry(
            promotion_requested=True,
            scripture=v.scripture,
            placeholders=_filled_placeholders(),
        ),
        CurationPrepEntry(scripture=full.entries[1].scripture, placeholders=full.entries[1].placeholders),
    )
    plan = build_promotion_plan(prep, existing_entries=())
    assert len(plan.promoted) == 1
    assert plan.skipped_not_requested == 1
    assert isinstance(plan.promoted[0], CuratedVerseEntry)
    assert plan.promoted[0].verse_ref == v.scripture.verse_ref
    assert plan.promoted[0].core_teaching.startswith("One-line")


def test_requested_but_incomplete_metadata_fails() -> None:
    full = build_curation_prep_artifact()
    v = full.entries[0]
    bad_ph = _filled_placeholders().model_copy(update={"themes": []})
    prep = _artifact_two_entries(
        CurationPrepEntry(
            promotion_requested=True,
            scripture=v.scripture,
            placeholders=bad_ph,
        ),
        CurationPrepEntry(scripture=full.entries[1].scripture, placeholders=full.entries[1].placeholders),
    )
    with pytest.raises(PromotionError, match="themes is empty"):
        build_promotion_plan(prep, existing_entries=())


def test_duplicate_verse_ref_within_batch_fails() -> None:
    full = build_curation_prep_artifact()
    v = full.entries[0]
    ph = _filled_placeholders()
    prep = _artifact_two_entries(
        CurationPrepEntry(promotion_requested=True, scripture=v.scripture, placeholders=ph),
        CurationPrepEntry(promotion_requested=True, scripture=v.scripture, placeholders=ph),
    )
    with pytest.raises(PromotionError, match="duplicate verse_ref"):
        build_promotion_plan(prep, existing_entries=())


def test_duplicate_verse_ref_against_existing_seed_fails() -> None:
    full = build_curation_prep_artifact()
    e247 = next(e for e in full.entries if e.scripture.verse_ref == "2.47")
    prep = CurationPrepArtifact(
        header=CurationPrepHeader(
            canonical_raw_filename=CANONICAL_RAW_CORPUS_FILENAME,
            verse_entry_count=1,
        ),
        entries=[
            CurationPrepEntry(
                promotion_requested=True,
                scripture=e247.scripture,
                placeholders=_filled_placeholders(),
            )
        ],
    )
    existing = load_curated_verses()
    with pytest.raises(PromotionError, match="conflicts with existing curated verse_ref"):
        build_promotion_plan(prep, existing_entries=existing)


def test_max_batch_guard() -> None:
    full = build_curation_prep_artifact()
    entries: list[CurationPrepEntry] = []
    for i in range(3):
        v = full.entries[i]
        entries.append(
            CurationPrepEntry(
                promotion_requested=True,
                scripture=v.scripture,
                placeholders=_filled_placeholders(
                    core_teaching=f"Teaching {i}",
                    themes=["duty"],
                ),
            )
        )
    prep = CurationPrepArtifact(
        header=CurationPrepHeader(
            canonical_raw_filename=CANONICAL_RAW_CORPUS_FILENAME,
            verse_entry_count=3,
        ),
        entries=entries,
    )
    with pytest.raises(PromotionError, match="bulk promotion guard"):
        build_promotion_plan(prep, existing_entries=(), max_promotions=2)
    plan = build_promotion_plan(prep, existing_entries=(), max_promotions=2, allow_large_batch=True)
    assert len(plan.promoted) == 3


def test_merge_write_false_does_not_modify_production_seed() -> None:
    path = curated_verses_seed_path()
    before = path.read_bytes()
    merge_promoted_into_seed_json(path, [], write=False)
    assert path.read_bytes() == before


def test_loader_unchanged_after_promotion_helpers(tmp_path: Path) -> None:
    n = len(load_curated_verses())
    full = build_curation_prep_artifact()
    v = full.entries[0]
    prep = CurationPrepArtifact(
        header=CurationPrepHeader(
            canonical_raw_filename=CANONICAL_RAW_CORPUS_FILENAME,
            verse_entry_count=1,
        ),
        entries=[
            CurationPrepEntry(
                promotion_requested=True,
                scripture=v.scripture,
                placeholders=_filled_placeholders(),
            )
        ],
    )
    plan = build_promotion_plan(prep, existing_entries=load_curated_verses())
    assert len(plan.promoted) == 1
    out = tmp_path / "review.json"
    write_promotion_review_artifact(plan, path=out)
    assert out.is_file()
    assert len(load_curated_verses()) == n


def test_merge_into_tmp_seed_append_write(tmp_path: Path) -> None:
    seed_src = curated_verses_seed_path()
    seed_copy = tmp_path / "verses_seed.json"
    shutil.copy(seed_src, seed_copy)
    n0 = len(validate_curated_seed_payload(json.loads(seed_copy.read_text(encoding="utf-8"))))

    full = build_curation_prep_artifact()
    v = full.entries[0]
    prep = CurationPrepArtifact(
        header=CurationPrepHeader(
            canonical_raw_filename=CANONICAL_RAW_CORPUS_FILENAME,
            verse_entry_count=1,
        ),
        entries=[
            CurationPrepEntry(
                promotion_requested=True,
                scripture=v.scripture,
                placeholders=_filled_placeholders(),
            )
        ],
    )
    plan = build_promotion_plan(prep, existing_entries=load_curated_verses(seed_copy))
    merge_promoted_into_seed_json(seed_copy, plan.promoted, write=True)
    n1 = len(validate_curated_seed_payload(json.loads(seed_copy.read_text(encoding="utf-8"))))
    assert n1 == n0 + 1


def test_production_seed_write_requires_confirm() -> None:
    full = build_curation_prep_artifact()
    v = full.entries[0]
    prep = CurationPrepArtifact(
        header=CurationPrepHeader(
            canonical_raw_filename=CANONICAL_RAW_CORPUS_FILENAME,
            verse_entry_count=1,
        ),
        entries=[
            CurationPrepEntry(
                promotion_requested=True,
                scripture=v.scripture,
                placeholders=_filled_placeholders(),
            )
        ],
    )
    plan = build_promotion_plan(prep, existing_entries=load_curated_verses())
    with pytest.raises(ValueError, match="confirm_production_curated_write"):
        merge_promoted_into_seed_json(
            curated_verses_seed_path(),
            plan.promoted,
            write=True,
            confirm_production_curated_write=False,
        )


def test_prep_dict_roundtrips_through_promotion_dict() -> None:
    full = build_curation_prep_artifact()
    entry = CurationPrepEntry(
        promotion_requested=True,
        scripture=full.entries[0].scripture,
        placeholders=_filled_placeholders(),
    )
    d = prep_entry_to_curated_dict(entry)
    assert d["verse_ref"] == full.entries[0].scripture.verse_ref
    assert "core_teaching" in d


def test_promotion_review_payload_validates(tmp_path: Path) -> None:
    full = build_curation_prep_artifact()
    v = full.entries[0]
    prep = CurationPrepArtifact(
        header=CurationPrepHeader(
            canonical_raw_filename=CANONICAL_RAW_CORPUS_FILENAME,
            verse_entry_count=1,
        ),
        entries=[
            CurationPrepEntry(
                promotion_requested=True,
                scripture=v.scripture,
                placeholders=_filled_placeholders(),
            )
        ],
    )
    plan = build_promotion_plan(prep, existing_entries=load_curated_verses())
    path = tmp_path / "review.json"
    write_promotion_review_artifact(plan, path=path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    review = validate_promotion_review_payload(payload)
    assert review.promoted_entry_count == len(review.promoted_entries)
