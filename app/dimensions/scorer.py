"""
Ethical dimension scorer — stub.

Phase 1 target: replace ``score_dimensions`` with real per-dimension scorers,
each in its own submodule (dharma_duty.py, satya_truth.py, …) that implements
``score(dilemma_text: str) -> DimensionScore``.  This function then aggregates
all eight calls into ``EthicalDimensions``.
"""

from __future__ import annotations

from app.core.models import DimensionScore, EthicalDimensions

_STUB_NOTE = "[STUB] Implement in app/dimensions/scorer.py."


def score_dimensions(dilemma: str) -> EthicalDimensions:
    """
    Score all eight ethical dimensions for *dilemma*.

    Returns a zeroed ``EthicalDimensions`` until real scorers are wired in.
    Score 0 means "neutral / not yet assessed", which is the correct stub
    value per the spec (§3: "Use zero rather than forcing a signed score").
    """
    stub = DimensionScore(score=0, note=_STUB_NOTE)
    return EthicalDimensions(
        dharma_duty=stub,
        satya_truth=stub,
        ahimsa_nonharm=stub,
        nishkama_detachment=stub,
        shaucha_intent=stub,
        sanyama_restraint=stub,
        lokasangraha_welfare=stub,
        viveka_discernment=stub,
    )
