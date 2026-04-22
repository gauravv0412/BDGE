"""
Ethical dimension scorer — stub (not currently called by the live pipeline).

The live pipeline obtains dimension scores from ``app/semantic/scorer.py``,
which produces them as part of the LLM semantic payload.  This module is
retained as a standalone fixture for unit tests that need
``EthicalDimensions`` without invoking the full semantic scorer.

If a deterministic rule-based scorer is ever needed alongside the LLM path
(e.g. for offline evaluation), implement it here.
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
