"""Tests for Step 25 full-corpus 10-batch curation workflow."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.verses.curation_batches import (
    BATCHES_DIR,
    assert_ten_batch_coverage,
    build_batch_artifact,
    dumps_batch_artifact,
    export_all_batches,
    export_batch,
    import_batch_to_prep,
    load_batch_artifact,
    merge_batch_into_curation_prep,
    validate_ai_filled_batch,
    write_merged_prep_artifact,
)
from app.verses.curation_prep import (
    CurationPrepEntry,
    build_curation_prep_artifact,
)
from app.verses.curation_promotion import build_promotion_plan


def _filled_entry(entry: CurationPrepEntry) -> CurationPrepEntry:
    return entry.model_copy(
        update={
            "promotion_requested": True,
            "placeholders": entry.placeholders.model_copy(
                update={
                    "core_teaching": "Act from duty without clinging to outcomes.",
                    "themes": ["duty"],
                    "applies_when": ["duty-conflict"],
                    "does_not_apply_when": ["active-harm"],
                    "priority": 4,
                    "status": "draft",
                }
            ),
        }
    )


def test_ten_batch_plan_covers_canonical_exactly_once() -> None:
    report = assert_ten_batch_coverage()
    assert report.total_canonical_verses == report.total_planned_verses
    assert report.missing_verse_refs == []
    assert report.duplicate_verse_refs == []


def test_batch_export_deterministic() -> None:
    a = build_batch_artifact("B03")
    b = build_batch_artifact("b03")
    assert dumps_batch_artifact(a) == dumps_batch_artifact(b)


def test_batch_export_refuses_invalid_batch_id() -> None:
    with pytest.raises(ValueError, match="Unknown batch_id"):
        build_batch_artifact("B99")


def test_batch_export_and_load_roundtrip(tmp_path: Path) -> None:
    out = tmp_path / "batch_b01.json"
    p = export_batch("B01", path=out)
    assert p == out
    loaded = load_batch_artifact(out)
    assert loaded.header.batch_id == "B01"
    assert loaded.header.verse_entry_count == len(loaded.entries)
    assert all(e.promotion_requested is False for e in loaded.entries)


def test_export_all_batches_requires_explicit_flag() -> None:
    with pytest.raises(ValueError, match="allow_all"):
        export_all_batches()


def test_validate_ai_batch_rejects_scripture_modification() -> None:
    batch = build_batch_artifact("B01")
    first = batch.entries[0]
    tampered = first.model_copy(
        update={
            "scripture": first.scripture.model_copy(
                update={
                    "english_translation": first.scripture.english_translation + " altered",
                    "source": first.scripture.source.model_copy(update={"english": "Other source"}),
                }
            )
        }
    )
    payload = batch.model_copy(update={"entries": [tampered, *batch.entries[1:]]})
    with pytest.raises(ValueError, match="scripture identity/text/source modified"):
        validate_ai_filled_batch(payload)


def test_promotable_rows_require_complete_and_non_generic_metadata() -> None:
    batch = build_batch_artifact("B01")
    first = batch.entries[0].model_copy(
        update={
            "promotion_requested": True,
            "placeholders": batch.entries[0].placeholders.model_copy(
                update={
                    "core_teaching": "todo",
                    "themes": ["misc"],
                    "applies_when": [],
                    "does_not_apply_when": ["active-harm"],
                    "priority": None,
                    "status": None,
                }
            ),
        }
    )
    candidate = batch.model_copy(update={"entries": [first, *batch.entries[1:]]})
    with pytest.raises(ValueError, match="generic placeholder"):
        validate_ai_filled_batch(candidate)


def test_non_promoted_incomplete_rows_are_allowed() -> None:
    batch = build_batch_artifact("B01")
    validate_ai_filled_batch(batch)


def test_import_merge_writes_only_to_curation_prep_paths(tmp_path: Path) -> None:
    batch = build_batch_artifact("B01")
    first_filled = _filled_entry(batch.entries[0])
    batch2 = batch.model_copy(update={"entries": [first_filled, *batch.entries[1:]]})

    batch_path = tmp_path / "batch.json"
    batch_path.write_text(dumps_batch_artifact(batch2), encoding="utf-8")

    out = tmp_path / "merged.json"
    merged_path = import_batch_to_prep(batch_path, out_path=out)
    assert merged_path == out

    from app.verses.curation_batches import _CURATED_DIR
    curated_like = _CURATED_DIR / "verses_seed.json"
    with pytest.raises(ValueError, match="Refusing curated output path"):
        write_merged_prep_artifact(build_curation_prep_artifact(), batch_id="B01", path=curated_like)


def test_merge_batch_into_prep_updates_only_batch_rows() -> None:
    base = build_curation_prep_artifact()
    batch = build_batch_artifact("B02")
    updated_first = _filled_entry(batch.entries[0])
    merged = merge_batch_into_curation_prep(batch.model_copy(update={"entries": [updated_first, *batch.entries[1:]]}), base_prep=base)

    changed = next(e for e in merged.entries if e.scripture.verse_ref == updated_first.scripture.verse_ref)
    unchanged = next(e for e in merged.entries if e.scripture.verse_ref == "1.1")
    assert changed.promotion_requested is True
    assert unchanged.promotion_requested is False


def test_promotion_workflow_stays_explicit_for_batch_exports() -> None:
    batch = build_batch_artifact("B03")
    prep = build_curation_prep_artifact().model_copy(update={"entries": batch.entries})
    plan = build_promotion_plan(prep, existing_entries=())
    assert plan.promotion_requested_count == 0
    assert plan.promoted == ()


def test_batch_directory_constant_under_curation_prep() -> None:
    assert BATCHES_DIR.name == "batches"
    assert BATCHES_DIR.parent.name == "curation_prep"
