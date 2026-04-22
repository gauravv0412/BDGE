"""
Build placeholder engine outputs. Real scoring, retrieval, and prose generation
will replace this; for now responses are obviously fake but schema-valid.
"""

from __future__ import annotations

import uuid
from typing import Final

from app.core.models import (
    Classification,
    CounterfactualBlock,
    Counterfactuals,
    DimensionScore,
    EthicalDimensions,
    IfYouContinue,
    InternalDriver,
    ShareLayer,
    VerseMatch,
    WisdomizeEngineOutput,
)

_PLACEHOLDER_NOTE: Final[str] = "[STUB] Replace when ethical dimensions module exists."
_STUB_VERSE_REF: Final[str] = "2.47"


def _normalize_dilemma_text(text: str) -> str:
    """
    Ensure ``dilemma`` meets JSON Schema length bounds (20–600 chars).

    Stubs pad short input so pipeline calls still emit valid payloads during development.
    """
    t = text.strip()
    if len(t) < 20:
        pad = " [stub padding for schema minLength]"
        t = (t + pad)[:600]
    if len(t) < 20:
        t = (t + " " * (20 - len(t)))[:600]
    return t[:600]


def build_placeholder_response(
    dilemma: str,
    *,
    dilemma_id: str | None = None,
) -> WisdomizeEngineOutput:
    """
    Construct a clearly fake but contract-valid :class:`~app.core.models.WisdomizeEngineOutput`.

    Uses ``verse_match`` populated and ``closest_teaching`` null (schema branch A).
    """
    did = dilemma_id or f"stub-{uuid.uuid4().hex[:16]}"
    dilemma_out = _normalize_dilemma_text(dilemma)

    dimensions = EthicalDimensions(
        dharma_duty=DimensionScore(score=0, note=_PLACEHOLDER_NOTE),
        satya_truth=DimensionScore(score=0, note=_PLACEHOLDER_NOTE),
        ahimsa_nonharm=DimensionScore(score=0, note=_PLACEHOLDER_NOTE),
        nishkama_detachment=DimensionScore(score=0, note=_PLACEHOLDER_NOTE),
        shaucha_intent=DimensionScore(score=0, note=_PLACEHOLDER_NOTE),
        sanyama_restraint=DimensionScore(score=0, note=_PLACEHOLDER_NOTE),
        lokasangraha_welfare=DimensionScore(score=0, note=_PLACEHOLDER_NOTE),
        viveka_discernment=DimensionScore(score=0, note=_PLACEHOLDER_NOTE),
    )

    verse = VerseMatch(
        verse_ref=_STUB_VERSE_REF,
        sanskrit_devanagari="[STUB — not a real śloka]",
        sanskrit_iast=None,
        hindi_translation="[STUB Hindi]",
        english_translation="[STUB English placeholder]",
        source="[STUB] Factory placeholder only.",
        why_it_applies="[STUB] Verse wiring will be implemented in the verse module.",
        match_confidence=0.61,
    )

    return WisdomizeEngineOutput(
        dilemma_id=did,
        dilemma=dilemma_out,
        verdict_sentence="[STUB] Verdict sentence pending real analysis.",
        classification=Classification.CONTEXT_DEPENDENT,
        alignment_score=0,
        confidence=0.5,
        internal_driver=InternalDriver(
            primary="[STUB] Primary driver text.",
            hidden_risk="[STUB] Hidden risk text.",
        ),
        core_reading="[STUB] Core reading: observational prose will be filled by the analyzer stage.",
        gita_analysis="[STUB] What would Krishna question here? (Not implemented.)",
        verse_match=verse,
        closest_teaching=None,
        if_you_continue=IfYouContinue(
            short_term="[STUB] Short-term consequence placeholder.",
            long_term="[STUB] Long-term consequence placeholder.",
        ),
        counterfactuals=Counterfactuals(
            clearly_adharmic_version=CounterfactualBlock(
                assumed_context="[STUB] Adharmic tilt context.",
                decision="[STUB] Adharmic decision.",
                why="[STUB] Why adharmic.",
            ),
            clearly_dharmic_version=CounterfactualBlock(
                assumed_context="[STUB] Dharmic tilt context.",
                decision="[STUB] Dharmic decision.",
                why="[STUB] Why dharmic.",
            ),
        ),
        higher_path="[STUB] Higher path: concrete steps will come from the engine.",
        ethical_dimensions=dimensions,
        missing_facts=[],
        share_layer=ShareLayer(
            anonymous_share_title="[STUB] Overheard: the app said …",
            card_quote="[STUB] Card-sized takeaway.",
            reflective_question="[STUB] What would change if you saw this clearly?",
        ),
    )
