"""
Verse retrieval — stub.

Phase 2 target: build a curated index of ~80-120 verses across ~30 theme tags
(§4 of design_spec.md), score each candidate via the 6-point match threshold,
and either return a ``VerseMatch`` (branch A) or fall back to
``closest_teaching`` (branch B).

``VerseResult`` is the shared intermediate type consumed by the assembler in
``engine/analyzer.py``.  The XOR contract (exactly one of ``verse_match`` /
``closest_teaching`` non-null) is enforced at assembly time by
``WisdomizeEngineOutput``'s model validator and by the JSON Schema ``oneOf``.
"""

from __future__ import annotations

from typing import TypedDict

from app.core.models import EthicalDimensions, VerseMatch


class VerseResult(TypedDict):
    """Intermediate output of the verse retrieval stage."""

    verse_match: VerseMatch | None
    closest_teaching: str | None


_STUB_VERSE_REF = "2.47"


def retrieve_verse(dilemma: str, dimensions: EthicalDimensions) -> VerseResult:
    """
    Return a matched verse or a ``closest_teaching`` paraphrase for *dilemma*.

    Stub always returns branch A (verse populated, closest_teaching null).
    Real implementation: theme extraction → index lookup → match scoring →
    threshold filter (≥ 6 points / match_confidence ≥ 0.6) → branch decision.
    """
    return VerseResult(
        verse_match=VerseMatch(
            verse_ref=_STUB_VERSE_REF,
            sanskrit_devanagari="[STUB — not a real śloka]",
            sanskrit_iast=None,
            hindi_translation="[STUB Hindi]",
            english_translation="[STUB English placeholder]",
            source="[STUB] verses/retriever.py placeholder only.",
            why_it_applies="[STUB] Verse wiring will be implemented in Phase 2.",
            match_confidence=0.61,
        ),
        closest_teaching=None,
    )
