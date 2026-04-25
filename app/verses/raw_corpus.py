"""Load and validate the canonical Bhagavad Gita raw scripture corpus.

The **only** raw file used by this workflow is
``bhagavad_gita_corpus_canonical.json`` under ``app/verses/data/raw/``.
Other JSON files in that directory are reference or legacy payloads and must
not be loaded or merged by this module.

Curated retrieval metadata lives under ``app/verses/data/curated/`` and is
handled by :mod:`app.verses.loader` — keep raw corpus and curated metadata
separate.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

_RAW_DATA_DIR = Path(__file__).resolve().parent / "data" / "raw"

# Explicit canonical filename — do not glob or pick "first JSON" in raw/.
CANONICAL_RAW_CORPUS_FILENAME = "bhagavad_gita_corpus_canonical.json"
CANONICAL_RAW_CORPUS_PATH = _RAW_DATA_DIR / CANONICAL_RAW_CORPUS_FILENAME

VERSE_REF_PATTERN = r"^[0-9]+\.[0-9]+(-[0-9]+)?$"


class CanonicalRawCorpusBibliography(BaseModel):
    """Top-level source attribution for the edition (not per-verse)."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    sanskrit: str = Field(min_length=1)
    transliteration: str = Field(min_length=1)
    english_translation: str = Field(min_length=1)
    hindi_translation: str = Field(min_length=1)


class CanonicalRawVerseAttribution(BaseModel):
    """Per-verse source lines (raw corpus shape; differs from curated VerseSource)."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    sanskrit: str = Field(min_length=1)
    transliteration: str = Field(min_length=1)
    english: str = Field(min_length=1)
    hindi: str = Field(min_length=1)


class CanonicalRawVerse(BaseModel):
    """One verse entry in the canonical raw corpus."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    verse_id: str = Field(min_length=1)
    verse_ref: str = Field(pattern=VERSE_REF_PATTERN)
    chapter: int = Field(ge=1)
    verse_start: int = Field(ge=1)
    verse_end: int = Field(ge=1)
    sanskrit_devanagari: str = Field(min_length=1)
    sanskrit_iast: str = Field(min_length=1)
    english_translation: str = Field(min_length=1)
    hindi_translation: str = Field(min_length=1)
    source: CanonicalRawVerseAttribution

    @model_validator(mode="after")
    def _verse_span(self) -> CanonicalRawVerse:
        if self.verse_end < self.verse_start:
            raise ValueError("verse_end must be >= verse_start.")
        return self


class CanonicalRawChapter(BaseModel):
    """One chapter block in the canonical raw corpus."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    chapter_number: int = Field(ge=1)
    chapter_title: str = Field(min_length=1)
    verses: list[CanonicalRawVerse] = Field(min_length=1)

    @model_validator(mode="after")
    def _verses_match_chapter(self) -> CanonicalRawChapter:
        bad = [v.verse_ref for v in self.verses if v.chapter != self.chapter_number]
        if bad:
            raise ValueError(
                f"Verses in chapter {self.chapter_number} must have chapter "
                f"equal to chapter_number; inconsistent verse_ref: {bad[:5]}"
            )
        return self


class CanonicalRawCorpus(BaseModel):
    """Root object for ``bhagavad_gita_corpus_canonical.json``."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    text_id: str = Field(min_length=1)
    tradition: str = Field(min_length=1)
    verse_count_convention: str = Field(min_length=1)
    total_chapters: int = Field(ge=1)
    total_verses: int = Field(ge=1)
    sources: CanonicalRawCorpusBibliography
    notes: list[str]
    chapters: list[CanonicalRawChapter] = Field(min_length=1)

    @model_validator(mode="after")
    def _aggregate_integrity(self) -> CanonicalRawCorpus:
        if len(self.chapters) != self.total_chapters:
            raise ValueError(
                f"total_chapters is {self.total_chapters} but chapters has "
                f"{len(self.chapters)} entries."
            )
        verse_count = sum(len(ch.verses) for ch in self.chapters)
        if verse_count != self.total_verses:
            raise ValueError(
                f"total_verses is {self.total_verses} but corpus contains "
                f"{verse_count} verse entries."
            )
        nums = [ch.chapter_number for ch in self.chapters]
        if len(set(nums)) != len(nums):
            raise ValueError(f"Duplicate chapter_number values: {nums}.")
        expected = list(range(1, self.total_chapters + 1))
        if sorted(nums) != expected:
            raise ValueError(
                f"chapter_number values must be exactly {expected!r} (sorted); "
                f"got {sorted(nums)!r}."
            )

        seen_ref: dict[str, str] = {}
        seen_id: dict[str, str] = {}
        for ch in self.chapters:
            for v in ch.verses:
                if v.verse_ref in seen_ref:
                    raise ValueError(
                        f"Duplicate verse_ref {v.verse_ref!r} "
                        f"(verse_id {v.verse_id!r} and {seen_ref[v.verse_ref]!r})."
                    )
                seen_ref[v.verse_ref] = v.verse_id
                if v.verse_id in seen_id:
                    raise ValueError(
                        f"Duplicate verse_id {v.verse_id!r} "
                        f"(verse_ref {v.verse_ref!r} and {seen_id[v.verse_id]!r})."
                    )
                seen_id[v.verse_id] = v.verse_ref
        return self


def load_canonical_raw_corpus(path: Path | None = None) -> CanonicalRawCorpus:
    """Load and validate the canonical raw corpus JSON.

    Defaults to :data:`CANONICAL_RAW_CORPUS_PATH` (``bhagavad_gita_corpus_canonical.json``).
    """
    resolved = path if path is not None else CANONICAL_RAW_CORPUS_PATH
    if not resolved.is_file():
        raise FileNotFoundError(f"Canonical raw corpus not found: {resolved}")
    payload: Any = json.loads(resolved.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Canonical raw corpus must be a JSON object at {resolved}.")
    try:
        return CanonicalRawCorpus.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(
            f"Canonical raw corpus failed validation at {resolved}: {exc}"
        ) from exc


def iter_canonical_verses(
    corpus: CanonicalRawCorpus,
) -> Iterator[tuple[CanonicalRawChapter, CanonicalRawVerse]]:
    """Yield (chapter, verse) pairs in corpus order."""
    for ch in corpus.chapters:
        for v in ch.verses:
            yield ch, v
