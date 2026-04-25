"""Tests for raw → editor-prep (curation prep) workflow."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from app.verses.curation_prep import (
    ARTIFACT_ROLE,
    CANONICAL_RAW_CORPUS_FILENAME,
    CURATION_PREP_DATA_DIR,
    DEFAULT_EDITOR_PREP_PATH,
    EDITOR_PREP_ARTIFACT_FILENAME,
    SCHEMA_ID,
    build_curation_prep_artifact,
    dumps_curation_prep_artifact,
    load_curation_prep_artifact,
    validate_curation_prep_payload,
    write_curation_prep_artifact,
)
from app.verses.loader import load_curated_verses
from app.verses.raw_corpus import CANONICAL_RAW_CORPUS_PATH, load_canonical_raw_corpus


def test_build_declares_canonical_raw_source() -> None:
    artifact = build_curation_prep_artifact()
    assert artifact.header.schema_id == SCHEMA_ID
    assert artifact.header.artifact_role == ARTIFACT_ROLE
    assert artifact.header.canonical_raw_filename == CANONICAL_RAW_CORPUS_FILENAME
    assert artifact.header.verse_entry_count == len(artifact.entries)
    assert artifact.header.verse_entry_count == 701


def test_build_uses_canonical_raw_loader_by_default() -> None:
    with patch(
        "app.verses.curation_prep.load_canonical_raw_corpus",
        wraps=load_canonical_raw_corpus,
    ) as spy:
        artifact = build_curation_prep_artifact()
        spy.assert_called_once_with()
    assert len(artifact.entries) == 701


def test_serialization_is_deterministic() -> None:
    a = build_curation_prep_artifact()
    b = build_curation_prep_artifact()
    assert dumps_curation_prep_artifact(a) == dumps_curation_prep_artifact(b)


def test_roundtrip_json_validate(tmp_path: Path) -> None:
    path = tmp_path / "prep.json"
    artifact = build_curation_prep_artifact()
    path.write_text(dumps_curation_prep_artifact(artifact), encoding="utf-8")
    loaded = load_curation_prep_artifact(path)
    assert loaded.model_dump() == artifact.model_dump()


def test_validate_rejects_wrong_entry_count() -> None:
    artifact = build_curation_prep_artifact()
    payload = json.loads(dumps_curation_prep_artifact(artifact))
    payload["header"]["verse_entry_count"] = 1
    with pytest.raises(ValueError, match="verse_entry_count"):
        validate_curation_prep_payload(payload)


def test_validate_rejects_wrong_canonical_filename() -> None:
    artifact = build_curation_prep_artifact()
    payload = json.loads(dumps_curation_prep_artifact(artifact))
    payload["header"]["canonical_raw_filename"] = "other.json"
    with pytest.raises(ValueError, match="canonical_raw_filename"):
        validate_curation_prep_payload(payload)


def test_write_refuses_active_verses_seed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    curated = tmp_path / "curated"
    curated.mkdir()
    monkeypatch.setattr("app.verses.curation_prep._CURATED_DIR", curated)
    bad = curated / "verses_seed.json"
    artifact = build_curation_prep_artifact()
    with pytest.raises(ValueError, match="Refusing to write"):
        write_curation_prep_artifact(artifact, bad)


def test_write_refuses_other_guarded_curated_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    curated = tmp_path / "curated"
    curated.mkdir()
    monkeypatch.setattr("app.verses.curation_prep._CURATED_DIR", curated)
    artifact = build_curation_prep_artifact()
    for name in ("themes.json", "applies_when.json", "blockers.json"):
        target = curated / name
        with pytest.raises(ValueError, match="Refusing to write"):
            write_curation_prep_artifact(artifact, target)


def test_default_prep_path_is_not_curated_seed() -> None:
    assert DEFAULT_EDITOR_PREP_PATH.parent.resolve() == CURATION_PREP_DATA_DIR.resolve()
    assert DEFAULT_EDITOR_PREP_PATH.name == EDITOR_PREP_ARTIFACT_FILENAME
    assert DEFAULT_EDITOR_PREP_PATH.parent.name == "curation_prep"
    assert DEFAULT_EDITOR_PREP_PATH.parent.parent.name == "data"
    assert CANONICAL_RAW_CORPUS_PATH.name == CANONICAL_RAW_CORPUS_FILENAME


def test_loader_still_loads_production_seed_only() -> None:
    entries = load_curated_verses()
    assert len(entries) > 0
    assert all(e.status in ("draft", "active", "archived") for e in entries)


def test_prep_placeholders_start_empty() -> None:
    artifact = build_curation_prep_artifact()
    first = artifact.entries[0]
    assert first.entry_kind == "curation_prep"
    assert first.promotion_requested is False
    assert first.placeholders.core_teaching == ""
    assert first.placeholders.themes == []
    assert first.placeholders.priority is None
    assert first.placeholders.status is None


def test_validate_rejects_bad_placeholder_dimension_score() -> None:
    artifact = build_curation_prep_artifact()
    payload = json.loads(dumps_curation_prep_artifact(artifact))
    entry = payload["entries"][0]
    entry["placeholders"]["dimension_affinity"] = {"dharma_duty": 99}
    with pytest.raises(ValueError, match="dimension_affinity"):
        validate_curation_prep_payload(payload)


def test_prep_scripture_matches_raw_for_first_verse() -> None:
    corpus = load_canonical_raw_corpus()
    artifact = build_curation_prep_artifact(corpus=corpus)
    raw_first = corpus.chapters[0].verses[0]
    prep_first = artifact.entries[0].scripture
    assert prep_first.verse_id == raw_first.verse_id
    assert prep_first.verse_ref == raw_first.verse_ref
    assert prep_first.hindi_translation == raw_first.hindi_translation
