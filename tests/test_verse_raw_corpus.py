"""Tests for canonical raw Bhagavad Gita corpus loading and validation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.verses.raw_corpus import (
    CANONICAL_RAW_CORPUS_FILENAME,
    CANONICAL_RAW_CORPUS_PATH,
    CanonicalRawCorpus,
    iter_canonical_verses,
    load_canonical_raw_corpus,
)


def _minimal_corpus_dict() -> dict:
    return {
        "text_id": "bg_test",
        "tradition": "test",
        "verse_count_convention": "701",
        "total_chapters": 1,
        "total_verses": 1,
        "sources": {
            "sanskrit": "SrcS",
            "transliteration": "SrcT",
            "english_translation": "SrcE",
            "hindi_translation": "SrcH",
        },
        "notes": [],
        "chapters": [
            {
                "chapter_number": 1,
                "chapter_title": "Test chapter",
                "verses": [
                    {
                        "verse_id": "BG-TEST-1-1",
                        "verse_ref": "1.1",
                        "chapter": 1,
                        "verse_start": 1,
                        "verse_end": 1,
                        "sanskrit_devanagari": "अ",
                        "sanskrit_iast": "a",
                        "english_translation": "English line",
                        "hindi_translation": "Hindi line",
                        "source": {
                            "sanskrit": "S",
                            "transliteration": "T",
                            "english": "E",
                            "hindi": "H",
                        },
                    }
                ],
            }
        ],
    }


def test_canonical_path_points_at_canonical_filename() -> None:
    assert CANONICAL_RAW_CORPUS_PATH.name == CANONICAL_RAW_CORPUS_FILENAME
    assert CANONICAL_RAW_CORPUS_FILENAME == "bhagavad_gita_corpus_canonical.json"


def test_default_load_uses_canonical_path_not_other_raw_files() -> None:
    raw_dir = CANONICAL_RAW_CORPUS_PATH.parent
    assert raw_dir.name == "raw"
    other_json = sorted(
        p.name
        for p in raw_dir.glob("*.json")
        if p.name != CANONICAL_RAW_CORPUS_FILENAME
    )
    assert other_json, "expected non-canonical raw JSON fixtures to exist for this check"
    assert CANONICAL_RAW_CORPUS_PATH.is_file()
    default_corpus = load_canonical_raw_corpus()
    explicit_corpus = load_canonical_raw_corpus(CANONICAL_RAW_CORPUS_PATH)
    assert default_corpus.model_dump() == explicit_corpus.model_dump()
    assert default_corpus.text_id == "bhagavad_gita_canonical"


def test_load_real_canonical_file_succeeds() -> None:
    corpus = load_canonical_raw_corpus()
    assert corpus.total_chapters == 18
    assert corpus.total_verses == 701
    assert len(corpus.chapters) == 18
    assert sum(len(ch.verses) for ch in corpus.chapters) == 701


def test_real_file_verse_refs_match_chapter_prefix() -> None:
    corpus = load_canonical_raw_corpus()
    for ch, v in iter_canonical_verses(corpus):
        head = v.verse_ref.split(".", 1)[0]
        assert int(head) == ch.chapter_number
        assert v.chapter == ch.chapter_number


def test_minimal_fixture_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "mini.json"
    path.write_text(json.dumps(_minimal_corpus_dict()), encoding="utf-8")
    corpus = load_canonical_raw_corpus(path)
    assert isinstance(corpus, CanonicalRawCorpus)
    assert corpus.total_verses == 1


def test_missing_required_field_rejected(tmp_path: Path) -> None:
    data = _minimal_corpus_dict()
    del data["chapters"][0]["verses"][0]["english_translation"]
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="failed validation"):
        load_canonical_raw_corpus(path)


def test_extra_field_rejected(tmp_path: Path) -> None:
    data = _minimal_corpus_dict()
    data["chapters"][0]["verses"][0]["unexpected"] = "x"
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="failed validation"):
        load_canonical_raw_corpus(path)


def test_duplicate_verse_ref_rejected(tmp_path: Path) -> None:
    data = _minimal_corpus_dict()
    v = data["chapters"][0]["verses"][0].copy()
    v["verse_id"] = "BG-OTHER"
    data["chapters"][0]["verses"].append(v)
    data["total_verses"] = 2
    path = tmp_path / "dup.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="Duplicate verse_ref"):
        load_canonical_raw_corpus(path)


def test_verse_chapter_mismatch_rejected(tmp_path: Path) -> None:
    data = _minimal_corpus_dict()
    data["chapters"][0]["verses"][0]["chapter"] = 2
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="chapter_number"):
        load_canonical_raw_corpus(path)


def test_total_verses_mismatch_rejected(tmp_path: Path) -> None:
    data = _minimal_corpus_dict()
    data["total_verses"] = 99
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="total_verses"):
        load_canonical_raw_corpus(path)


def test_verse_end_before_start_rejected(tmp_path: Path) -> None:
    data = _minimal_corpus_dict()
    data["chapters"][0]["verses"][0]["verse_end"] = 0
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="failed validation|verse_end"):
        load_canonical_raw_corpus(path)
