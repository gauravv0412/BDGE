"""
Verdict aggregation: alignment score, classification, confidence, stub prose.

Dimension *notes* remain the scorer’s responsibility; this layer only consumes
``EthicalDimensions`` and ambiguity signals described in design_spec.md §3, §6–7.
"""

from __future__ import annotations

from typing import TypedDict

from app.core.models import Classification, EthicalDimensions
from app.verdict.alignment import compute_alignment_score
from app.verdict.classification import count_scorable_dimensions, resolve_classification
from app.verdict.confidence import compute_confidence


class VerdictResult(TypedDict):
    """
    Deterministic outputs of the verdict stage.

    Narrative prose (internal_driver, core_reading, gita_analysis, if_you_continue,
    higher_path) is produced by the semantic scorer and assembled by the engine
    directly — it is not the verdict layer's responsibility.
    """

    alignment_score: int
    classification: Classification
    confidence: float
    verdict_sentence: str
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
    ambiguity_can_flip_class: bool = False,
    missing_facts: list[str] | None = None,
) -> VerdictResult:
    """
    Derive verdict fields from *dimensions* for *dilemma* (text for future detectors).

    *scorable_mask* marks which of the eight dimensions count toward the §6 rule
    “fewer than four scorable dimensions → Insufficient information”.  When
    omitted, all eight are scorable.

    *context_dependent_override* is a compatibility alias for callers already
    using that name. It maps to ``ambiguity_can_flip_class``.

    *ambiguity_can_flip_class* should be set only when unresolved ambiguity is
    decisive enough that plausible answers could change classification. Non-empty
    ``missing_facts`` alone does not imply this.

    *missing_facts* is clamped to six entries (schema ``maxItems``).
    """
    _ = dilemma  # reserved for future ambiguity heuristics on raw text
    facts = list(missing_facts or [])[:6]

    scorable_count = count_scorable_dimensions(scorable_mask)
    alignment_score = compute_alignment_score(dimensions)
    ambiguity_flag = ambiguity_can_flip_class or context_dependent_override
    classification = resolve_classification(
        alignment_score,
        scorable_count=scorable_count,
        ambiguity_can_flip_class=ambiguity_flag,
    )
    confidence = compute_confidence(
        scorable_count,
        facts,
        ambiguity_flag=ambiguity_flag,
    )

    return VerdictResult(
        alignment_score=alignment_score,
        classification=classification,
        confidence=confidence,
        verdict_sentence=_stub_verdict_sentence(classification),
        missing_facts=facts,
    )
