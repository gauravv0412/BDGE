"""Raw → editor-prep workflow: canonical scripture to curation skeleton artifacts.

Produces JSON meant for **human review and later promotion** into
``app/verses/data/curated/verses_seed.json``. It is not active retrieval
metadata and must not be loaded by :func:`app.verses.loader.load_curated_verses`.

Canonical input is **only** :data:`app.verses.raw_corpus.CANONICAL_RAW_CORPUS_PATH`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from app.verses.raw_corpus import (
    CANONICAL_RAW_CORPUS_FILENAME,
    CanonicalRawCorpus,
    CanonicalRawVerse,
    load_canonical_raw_corpus,
    iter_canonical_verses,
)
from app.verses.types import VerseRecord, VerseSource, VerseStatus

CURATION_PREP_DATA_DIR = Path(__file__).resolve().parent / "data" / "curation_prep"
EDITOR_PREP_ARTIFACT_FILENAME = "verses_editor_prep.json"
DEFAULT_EDITOR_PREP_PATH = CURATION_PREP_DATA_DIR / EDITOR_PREP_ARTIFACT_FILENAME

_CURATED_DIR = Path(__file__).resolve().parent / "data" / "curated"
_ACTIVE_CURATED_GUARDED_NAMES = frozenset(
    {"verses_seed.json", "themes.json", "applies_when.json", "blockers.json"}
)

SCHEMA_ID = "bdge.curation_prep.v1"
ARTIFACT_ROLE = "editor_prep_not_active_retrieval"


class CurationPrepHeader(BaseModel):
    """Document header: identifies artifact role and source corpus file."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    schema_id: Literal["bdge.curation_prep.v1"] = SCHEMA_ID
    artifact_role: Literal["editor_prep_not_active_retrieval"] = ARTIFACT_ROLE
    canonical_raw_filename: str = Field(min_length=1)
    verse_entry_count: int = Field(ge=1)


class CurationPrepPlaceholders(BaseModel):
    """Non-authoritative retrieval fields for editors; empty until filled.

    Not validated against theme / applies_when vocabularies — that happens when
    promoting into active curated entries.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    core_teaching: str = ""
    themes: list[str] = Field(default_factory=list)
    applies_when: list[str] = Field(default_factory=list)
    does_not_apply_when: list[str] = Field(default_factory=list)
    dimension_affinity: dict[str, int] = Field(default_factory=dict)
    priority: int | None = None
    status: VerseStatus | None = None

    @field_validator("themes", "applies_when", "does_not_apply_when")
    @classmethod
    def _non_empty_strings(cls, value: list[str]) -> list[str]:
        for item in value:
            if not str(item).strip():
                raise ValueError("Placeholder tag lists must not contain empty strings.")
        return value

    @field_validator("dimension_affinity")
    @classmethod
    def _affinity_range(cls, value: dict[str, int]) -> dict[str, int]:
        for key, score in value.items():
            if not str(key).strip():
                raise ValueError("dimension_affinity keys must be non-empty.")
            if score < 1 or score > 5:
                raise ValueError(f"dimension_affinity[{key!r}] must be in [1, 5].")
        return value

    @field_validator("priority")
    @classmethod
    def _priority_range(cls, value: int | None) -> int | None:
        if value is not None and (value < 1 or value > 5):
            raise ValueError("priority must be in [1, 5] when set.")
        return value


class CurationPrepEntry(BaseModel):
    """One verse row: scripture from raw corpus + empty retrieval placeholders."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    entry_kind: Literal["curation_prep"] = "curation_prep"
    promotion_requested: bool = Field(
        default=False,
        description="Editors set True to include this row in a promotion batch.",
    )
    scripture: VerseRecord
    placeholders: CurationPrepPlaceholders


class CurationPrepArtifact(BaseModel):
    """Root object written to ``verses_editor_prep.json``."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    header: CurationPrepHeader
    entries: list[CurationPrepEntry]

    @model_validator(mode="after")
    def _header_matches_entries(self) -> CurationPrepArtifact:
        if self.header.verse_entry_count != len(self.entries):
            raise ValueError(
                f"header.verse_entry_count ({self.header.verse_entry_count}) "
                f"does not match len(entries) ({len(self.entries)})."
            )
        if self.header.canonical_raw_filename != CANONICAL_RAW_CORPUS_FILENAME:
            raise ValueError(
                "curation prep must declare canonical_raw_filename="
                f"{CANONICAL_RAW_CORPUS_FILENAME!r}, "
                f"got {self.header.canonical_raw_filename!r}."
            )
        return self


def _raw_verse_to_record(verse: CanonicalRawVerse) -> VerseRecord:
    return VerseRecord(
        verse_id=verse.verse_id,
        verse_ref=verse.verse_ref,
        chapter=verse.chapter,
        verse_start=verse.verse_start,
        verse_end=verse.verse_end,
        sanskrit_devanagari=verse.sanskrit_devanagari,
        sanskrit_iast=verse.sanskrit_iast,
        hindi_translation=verse.hindi_translation,
        english_translation=verse.english_translation,
        source=VerseSource(hindi=verse.source.hindi, english=verse.source.english),
    )


def build_curation_prep_artifact(
    *,
    corpus: CanonicalRawCorpus | None = None,
) -> CurationPrepArtifact:
    """Build editor-prep artifact from the canonical raw corpus (default load)."""
    loaded = corpus if corpus is not None else load_canonical_raw_corpus()
    entries: list[CurationPrepEntry] = []
    for _ch, verse in iter_canonical_verses(loaded):
        entries.append(
            CurationPrepEntry(
                scripture=_raw_verse_to_record(verse),
                placeholders=CurationPrepPlaceholders(),
            )
        )
    header = CurationPrepHeader(
        canonical_raw_filename=CANONICAL_RAW_CORPUS_FILENAME,
        verse_entry_count=len(entries),
    )
    return CurationPrepArtifact(header=header, entries=entries)


def _reject_if_active_curated_target(path: Path) -> None:
    resolved = path.resolve()
    curated_resolved = _CURATED_DIR.resolve()
    if resolved.parent == curated_resolved and path.name in _ACTIVE_CURATED_GUARDED_NAMES:
        raise ValueError(
            f"Refusing to write editor-prep artifact over active curated file: {path.name}"
        )


def validate_curation_prep_payload(payload: Any) -> CurationPrepArtifact:
    """Validate a decoded JSON object as a curation-prep artifact."""
    if not isinstance(payload, dict):
        raise ValueError("Curation prep artifact must be a JSON object.")
    try:
        return CurationPrepArtifact.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(f"Curation prep artifact failed validation: {exc}") from exc


def load_curation_prep_artifact(path: Path) -> CurationPrepArtifact:
    """Load and validate ``verses_editor_prep.json`` (or compatible path)."""
    if not path.is_file():
        raise FileNotFoundError(f"Curation prep artifact not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    return validate_curation_prep_payload(payload)


def dumps_curation_prep_artifact(artifact: CurationPrepArtifact) -> str:
    """Serialize artifact to a deterministic UTF-8 JSON string (stable key order)."""

    def _entry_ordered(e: CurationPrepEntry) -> dict[str, Any]:
        return {
            "entry_kind": e.entry_kind,
            "promotion_requested": e.promotion_requested,
            "placeholders": e.placeholders.model_dump(mode="json"),
            "scripture": e.scripture.model_dump(mode="json"),
        }

    body: dict[str, Any] = {
        "header": artifact.header.model_dump(mode="json"),
        "entries": [_entry_ordered(e) for e in artifact.entries],
    }
    return json.dumps(body, ensure_ascii=False, indent=2) + "\n"


def write_curation_prep_artifact(
    artifact: CurationPrepArtifact,
    path: Path | None = None,
) -> Path:
    """Write artifact to disk. Refuses active curated production filenames."""
    target = path if path is not None else DEFAULT_EDITOR_PREP_PATH
    _reject_if_active_curated_target(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(dumps_curation_prep_artifact(artifact), encoding="utf-8")
    return target
