"""
Counterfactual generation — stub (not currently called by the live pipeline).

The live pipeline obtains counterfactuals from ``app/semantic/scorer.py``,
which produces them as part of the LLM semantic payload.  This module is
retained for offline testing of counterfactual shapes without invoking
the full semantic scorer.

If a deterministic or template-based counterfactual generator is ever needed
alongside the LLM path, implement it here (§8 of design_spec.md).
"""

from __future__ import annotations

from app.core.models import CounterfactualBlock, Counterfactuals
from app.verdict.aggregator import VerdictResult


def generate_counterfactuals(dilemma: str, verdict: VerdictResult) -> Counterfactuals:
    """
    Produce adharmic and dharmic counterfactual variants for *dilemma*.

    Stub returns clearly-marked placeholder blocks.  Real implementation will
    use ``verdict["classification"]`` and ``verdict["alignment_score"]`` to
    calibrate how far each variant is tilted from the center.
    """
    return Counterfactuals(
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
    )
