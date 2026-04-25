"""Tests for curated verse data loading and validation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.verses.loader import (
    curated_verses_seed_path,
    load_applies_when_vocab,
    load_blocker_vocab,
    load_curated_verses,
    load_theme_vocab,
    validate_curated_entry,
    validate_curated_seed_payload,
)
from app.verses.types import VerseSource


def _sample_entry(*, status: str = "active", hindi_translation: str | None = "Hindi text") -> dict:
    return {
        "verse_id": "BG-TEST-1",
        "verse_ref": "2.47",
        "chapter": 2,
        "verse_start": 47,
        "verse_end": 47,
        "sanskrit_devanagari": "कर्मण्येवाधिकारस्ते...",
        "sanskrit_iast": None,
        "hindi_translation": hindi_translation,
        "english_translation": "You have the right to action alone.",
        "source": {
            "hindi": "Gita Press Gorakhpur",
            "english": "Edwin Arnold (public domain)",
        },
        "core_teaching": "Act without attachment to outcomes.",
        "themes": ["duty"],
        "applies_when": ["duty-conflict"],
        "does_not_apply_when": ["active-harm"],
        "dimension_affinity": {"dharma_duty": 4},
        "priority": 4,
        "status": status,
    }


def _write_seed(path: Path, entries: list[dict]) -> None:
    path.write_text(json.dumps(entries), encoding="utf-8")


def test_validate_curated_seed_payload_matches_load_curated_verses() -> None:
    path = curated_verses_seed_path()
    payload = json.loads(path.read_text(encoding="utf-8"))
    from_payload = validate_curated_seed_payload(payload)
    from_loader = load_curated_verses(path)
    assert [e.model_dump() for e in from_payload] == [e.model_dump() for e in from_loader]


def test_load_curated_vocab_files() -> None:
    assert "duty" in load_theme_vocab()
    assert "duty-conflict" in load_applies_when_vocab()
    assert "active-harm" in load_blocker_vocab()


def test_duplicate_verse_rejection(tmp_path: Path) -> None:
    seed = tmp_path / "seed.json"
    first = _sample_entry()
    second = _sample_entry()
    second["verse_id"] = "BG-TEST-2"
    _write_seed(seed, [first, second])

    with pytest.raises(ValueError, match="Duplicate verse_ref"):
        load_curated_verses(seed)


def test_unknown_tag_rejection() -> None:
    entry = _sample_entry()
    entry["themes"] = ["not-a-known-theme"]
    with pytest.raises(ValueError, match="unknown theme tags"):
        validate_curated_entry(
            entry,
            theme_vocab=load_theme_vocab(),
            applies_when_vocab=load_applies_when_vocab(),
            blocker_vocab=load_blocker_vocab(),
        )


def test_active_entry_missing_hindi_rejected() -> None:
    entry = _sample_entry(status="active", hindi_translation=None)
    with pytest.raises(ValueError, match="active entries require hindi_translation"):
        validate_curated_entry(
            entry,
            theme_vocab=load_theme_vocab(),
            applies_when_vocab=load_applies_when_vocab(),
            blocker_vocab=load_blocker_vocab(),
        )


def test_draft_entry_missing_hindi_allowed() -> None:
    entry = _sample_entry(status="draft", hindi_translation=None)
    parsed = validate_curated_entry(
        entry,
        theme_vocab=load_theme_vocab(),
        applies_when_vocab=load_applies_when_vocab(),
        blocker_vocab=load_blocker_vocab(),
    )
    assert parsed.status == "draft"
    assert parsed.hindi_translation is None


def test_source_formatter_for_output() -> None:
    source = VerseSource(hindi="Gita Press Gorakhpur", english="Edwin Arnold")
    assert (
        source.format_for_output()
        == "Gita Press Gorakhpur (Hindi) / Edwin Arnold (English)"
    )


def test_source_formatter_preserves_existing_qualifiers() -> None:
    source = VerseSource(
        hindi="Gita Press Gorakhpur",
        english="Edwin Arnold (public domain)",
    )
    assert (
        source.format_for_output()
        == "Gita Press Gorakhpur (Hindi) / Edwin Arnold (public domain) (English)"
    )


@pytest.mark.parametrize("score", [0, 6])
def test_dimension_affinity_out_of_range_rejected(score: int) -> None:
    entry = _sample_entry()
    entry["dimension_affinity"] = {"dharma_duty": score}
    with pytest.raises(ValueError, match="dimension_affinity\\[dharma_duty\\] must be in \\[1, 5\\]"):
        validate_curated_entry(
            entry,
            theme_vocab=load_theme_vocab(),
            applies_when_vocab=load_applies_when_vocab(),
            blocker_vocab=load_blocker_vocab(),
        )

