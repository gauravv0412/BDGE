"""
Pydantic models mirroring the Wisdomize engine output contract (v2.1).

Full contract enforcement uses JSON Schema in ``docs/output_schema.json`` via
``validator.validate_against_output_schema``. These models document structure
and support typed construction without implementing ethical or scoring logic.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Classification(StrEnum):
    """Allowed ``classification`` values from the output schema."""

    DHARMIC = "Dharmic"
    ADHARMIC = "Adharmic"
    MIXED = "Mixed"
    CONTEXT_DEPENDENT = "Context-dependent"
    INSUFFICIENT_INFORMATION = "Insufficient information"


class DimensionScore(BaseModel):
    """Single ethical dimension: score in [-5, 5] plus a one-line note."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    score: int = Field(ge=-5, le=5)
    note: str = Field(max_length=200)


class CounterfactualBlock(BaseModel):
    """One plausible variant of the same situation (adharmic or dharmic tilt)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    assumed_context: str = Field(max_length=400)
    decision: str = Field(max_length=200)
    why: str = Field(max_length=300)


class Counterfactuals(BaseModel):
    """Paired counterfactuals for the same dilemma."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    clearly_adharmic_version: CounterfactualBlock
    clearly_dharmic_version: CounterfactualBlock


class InternalDriver(BaseModel):
    """Dominant inner force and the main rationalization risk."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    primary: str = Field(max_length=200)
    hidden_risk: str = Field(max_length=200)


class VerseMatch(BaseModel):
    """Canonical verse retrieval when match confidence clears the threshold."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    verse_ref: str
    sanskrit_devanagari: str
    sanskrit_iast: str | None
    hindi_translation: str
    english_translation: str
    source: str
    why_it_applies: str = Field(max_length=500)
    match_confidence: float = Field(ge=0.6, le=1.0)


class IfYouContinue(BaseModel):
    """Observed short- and long-term consequences of staying on the current path."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    short_term: str = Field(max_length=400)
    long_term: str = Field(max_length=400)


class EthicalDimensions(BaseModel):
    """All eight ethical dimensions required by the contract."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    dharma_duty: DimensionScore
    satya_truth: DimensionScore
    ahimsa_nonharm: DimensionScore
    nishkama_detachment: DimensionScore
    shaucha_intent: DimensionScore
    sanyama_restraint: DimensionScore
    lokasangraha_welfare: DimensionScore
    viveka_discernment: DimensionScore


class ShareLayer(BaseModel):
    """Shareable, anonymized snippets for social/card use."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    anonymous_share_title: str = Field(max_length=120)
    card_quote: str = Field(max_length=180)
    reflective_question: str = Field(max_length=200, pattern=r".*\?$")


class WisdomizeEngineOutput(BaseModel):
    """
    Top-level engine output shape (per dilemma).

    ``verse_match`` and ``closest_teaching`` are both required keys; exactly
    one must be non-null (enforced by JSON Schema ``allOf`` / ``oneOf``).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    dilemma_id: str = Field(min_length=1, max_length=64)
    dilemma: str = Field(min_length=20, max_length=600)
    verdict_sentence: str = Field(max_length=160)
    classification: Classification
    alignment_score: int = Field(ge=-100, le=100)
    confidence: float = Field(ge=0, le=1)
    internal_driver: InternalDriver
    core_reading: str = Field(max_length=600)
    gita_analysis: str = Field(max_length=500)
    verse_match: VerseMatch | None
    closest_teaching: str | None = Field(default=None, max_length=500)
    if_you_continue: IfYouContinue
    counterfactuals: Counterfactuals
    higher_path: str = Field(max_length=500)
    ethical_dimensions: EthicalDimensions
    missing_facts: list[str] = Field(max_length=6)
    share_layer: ShareLayer
