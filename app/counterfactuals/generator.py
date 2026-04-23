"""
Counterfactual generation — stub (not currently called by the live pipeline).

The live pipeline overlays counterfactuals in ``app/engine/analyzer.py`` using
``app/counterfactuals/deterministic.build_refined_counterfactuals`` (deterministic,
dilemma-shaped).  ``semantic_scorer`` still returns counterfactual-shaped keys for
schema validation of the semantic payload; the engine replaces them before output.

This module remains a small offline stub for tests that import
``generate_counterfactuals`` directly.
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
