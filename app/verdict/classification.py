"""
Map ``alignment_score`` and ambiguity signals to ``Classification``.

Precedence follows design_spec.md §3 table plus §6 ambiguity rules:

1. Fewer than four scorable dimensions (at model confidence ≥ 0.5) → Insufficient information.
2. Ambiguity only when the unresolved signal could flip class → Context-dependent.
3. Otherwise score bands: ≥ +40 Dharmic, ≤ −40 Adharmic, else Mixed.
"""

from __future__ import annotations

from app.core.models import Classification


def count_scorable_dimensions(
    mask: tuple[bool, bool, bool, bool, bool, bool, bool, bool] | None,
) -> int:
    """
    Count dimensions treated as confidently scorable (≥ 0.5 confidence hook).

    *mask* is parallel to the fixed field order on ``EthicalDimensions``.  When
    ``None``, all eight dimensions count as scorable (fully specified dilemma).
    """
    if mask is None:
        return 8
    if len(mask) != 8:
        raise ValueError("scorable_mask must have length 8")
    return sum(1 for m in mask if m)


def resolve_classification(
    alignment_score: int,
    *,
    scorable_count: int,
    ambiguity_can_flip_class: bool = False,
) -> Classification:
    """
    Choose ``Classification`` given numeric score and ambiguity signals.

    ``missing_facts`` are intentionally not an input here. Per v2.1.1 spec,
    missing facts can coexist with Dharmic/Adharmic/Mixed when they refine the
    recommendation but do not plausibly change class.
    """
    if scorable_count < 4:
        return Classification.INSUFFICIENT_INFORMATION
    if ambiguity_can_flip_class:
        return Classification.CONTEXT_DEPENDENT
    if alignment_score >= 40:
        return Classification.DHARMIC
    if alignment_score <= -40:
        return Classification.ADHARMIC
    return Classification.MIXED
