"""
Verdict aggregation: alignment score, classification, confidence, stub prose.

Dimension *notes* remain the scorer’s responsibility; this layer only consumes
``EthicalDimensions`` and ambiguity signals described in design_spec.md §3, §6–7.
"""

from __future__ import annotations

from typing import TypedDict

from app.core.models import Classification, EthicalDimensions, IfYouContinue, InternalDriver
from app.verdict.alignment import compute_alignment_score
from app.verdict.classification import count_scorable_dimensions, resolve_classification
from app.verdict.confidence import compute_confidence


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


def _stub_verdict_sentence(cls: Classification) -> str:
    """Short placeholder until narrative generation exists (schema ≤160 chars)."""
    return {
        Classification.DHARMIC: "[STUB] Leans dharmic by the current aggregate.",
        Classification.ADHARMIC: "[STUB] Leans adharmic by the current aggregate.",
        Classification.MIXED: "[STUB] Mixed trade-offs; narrative pending.",
        Classification.CONTEXT_DEPENDENT: "[STUB] Outcome hinges on unstated facts.",
        Classification.INSUFFICIENT_INFORMATION: "[STUB] Too little to score reliably.",
    }[cls]


def aggregate_verdict(
    dimensions: EthicalDimensions,
    dilemma: str,
    *,
    scorable_mask: tuple[bool, bool, bool, bool, bool, bool, bool, bool] | None = None,
    context_dependent_override: bool = False,
    missing_facts: list[str] | None = None,
) -> VerdictResult:
    """
    Derive verdict fields from *dimensions* for *dilemma* (text for future detectors).

    *scorable_mask* marks which of the eight dimensions count toward the §6 rule
    “fewer than four scorable dimensions → Insufficient information”.  When
    omitted, all eight are scorable.

    *context_dependent_override* forces Context-dependent when ambiguity is
    detected without a populated ``missing_facts`` list yet.

    *missing_facts* is clamped to six entries (schema ``maxItems``).
    """
    _ = dilemma  # reserved for future ambiguity heuristics on raw text
    facts = list(missing_facts or [])[:6]

    scorable_count = count_scorable_dimensions(scorable_mask)
    alignment_score = compute_alignment_score(dimensions)
    classification = resolve_classification(
        alignment_score,
        scorable_count=scorable_count,
        missing_facts=facts,
        context_dependent_override=context_dependent_override,
    )
    confidence = compute_confidence(
        scorable_count,
        facts,
        context_dependent=context_dependent_override,
    )

    return VerdictResult(
        alignment_score=alignment_score,
        classification=classification,
        confidence=confidence,
        verdict_sentence=_stub_verdict_sentence(classification),
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
        missing_facts=facts,
    )
