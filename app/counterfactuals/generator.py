"""
Counterfactual generation — stub.

Phase 3 target: given the dilemma text and the verdict, produce two plausible
variants of the same situation: one tilted adharmic (worse motive / fewer
safeguards) and one tilted dharmic (better motive / more safeguards).

Both variants must be realistic, not strawmen, and must bracket the actual
dilemma (§8 of design_spec.md).
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
