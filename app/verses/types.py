"""Typed contracts for curated verse retrieval data.

`core_teaching` belongs to curated data.
`why_it_applies` does not: it must be generated during retrieval from the
dilemma + verse match context, then written into `verse_match`.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

DimensionKey = Literal[
    "dharma_duty",
    "satya_truth",
    "ahimsa_nonharm",
    "nishkama_detachment",
    "shaucha_intent",
    "sanyama_restraint",
    "lokasangraha_welfare",
    "viveka_discernment",
]

VerseStatus = Literal["draft", "active", "archived"]


class VerseSource(BaseModel):
    """Source citation for Hindi and English renderings."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    hindi: str = Field(min_length=1)
    english: str = Field(min_length=1)

    def format_for_output(self) -> str:
        """Render source in output-schema `verse_match.source` format."""
        return f"{self.hindi} (Hindi) / {self.english} (English)"


class VerseRecord(BaseModel):
    """Canonical verse text record used by retrieval."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    verse_id: str = Field(min_length=1)
    verse_ref: str = Field(pattern=r"^[0-9]+\.[0-9]+(-[0-9]+)?$")
    chapter: int = Field(ge=1)
    verse_start: int = Field(ge=1)
    verse_end: int = Field(ge=1)
    sanskrit_devanagari: str = Field(min_length=1)
    sanskrit_iast: str | None = None
    hindi_translation: str | None = None
    english_translation: str = Field(min_length=1)
    source: VerseSource


class VerseRetrievalMeta(BaseModel):
    """Retrieval metadata for filtering and ranking."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    core_teaching: str = Field(min_length=1)
    themes: list[str]
    applies_when: list[str]
    does_not_apply_when: list[str]
    dimension_affinity: dict[DimensionKey, int] = Field(default_factory=dict)
    priority: int = Field(ge=1, le=5)
    status: VerseStatus

    @field_validator("dimension_affinity")
    @classmethod
    def _validate_dimension_affinity_range(
        cls, value: dict[DimensionKey, int]
    ) -> dict[DimensionKey, int]:
        for key, score in value.items():
            if score < 1 or score > 5:
                raise ValueError(f"dimension_affinity[{key}] must be in [1, 5].")
        return value


class CuratedVerseEntry(VerseRecord, VerseRetrievalMeta):
    """Complete curated entry used by verse retrieval index."""

