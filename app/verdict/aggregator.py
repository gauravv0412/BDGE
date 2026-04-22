"""
Verdict aggregation — stub.

Phase 1 target: implement ``aggregate_verdict`` to compute ``alignment_score``
as a weighted sum of the eight dimension scores (scaled to [-100, +100]),
derive ``classification`` from the score band (§3 of design_spec.md), and
enforce the ``confidence`` cap (> 0.85 only when all 8 dimensions scored AND
``missing_facts`` is empty).

``VerdictResult`` is the shared intermediate type consumed by the assembler in
``engine/analyzer.py``, ``counterfactuals/generator.py``, and
``share/layer.py``.  Keep it stable — downstream stubs depend on these keys.
"""

from __future__ import annotations

from typing import TypedDict

from app.core.models import Classification, EthicalDimensions, IfYouContinue, InternalDriver


class VerdictResult(TypedDict):
    """Intermediate output of the verdict stage."""

    alignment_score: int
    classification: Classification
    confidence: float
    verdict_sentence: str
    internal_driver: InternalDriver
    core_reading: str
    gita_analysis: str
    if_you_continue: IfYouContinue
    higher_path: str
    missing_facts: list[str]


def aggregate_verdict(dimensions: EthicalDimensions, dilemma: str) -> VerdictResult:
    """
    Derive verdict fields from *dimensions* scores for *dilemma*.

    Stub returns zeroed score, CONTEXT_DEPENDENT classification, and
    confidence 0.5.  Real implementation: weighted sum → alignment_score →
    classification band → confidence cap logic (verdict/rules.py).
    """
    return VerdictResult(
        alignment_score=0,
        classification=Classification.CONTEXT_DEPENDENT,
        confidence=0.5,
        verdict_sentence="[STUB] Verdict sentence pending real analysis.",
        internal_driver=InternalDriver(
            primary="[STUB] Primary driver text.",
            hidden_risk="[STUB] Hidden risk text.",
        ),
        core_reading="[STUB] Core reading will be filled by the analyzer stage.",
        gita_analysis="[STUB] What would Krishna question here? (Not implemented.)",
        if_you_continue=IfYouContinue(
            short_term="[STUB] Short-term consequence placeholder.",
            long_term="[STUB] Long-term consequence placeholder.",
        ),
        higher_path="[STUB] Higher path: concrete steps will come from the engine.",
        missing_facts=[],
    )
