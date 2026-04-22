"""Unit tests for deterministic verdict aggregation (design_spec.md §3, §6–7)."""

from __future__ import annotations

import pytest

from app.core.models import Classification, DimensionScore, EthicalDimensions
from app.verdict.aggregator import aggregate_verdict
from app.verdict.alignment import compute_alignment_score
from app.verdict.classification import resolve_classification
from app.verdict.confidence import compute_confidence

_NOTE = "test"


def _uniform_dimensions(score: int) -> EthicalDimensions:
    d = DimensionScore(score=score, note=_NOTE)
    return EthicalDimensions(
        dharma_duty=d,
        satya_truth=d,
        ahimsa_nonharm=d,
        nishkama_detachment=d,
        shaucha_intent=d,
        sanyama_restraint=d,
        lokasangraha_welfare=d,
        viveka_discernment=d,
    )


def test_strongly_positive_scores_dharmic() -> None:
    dims = _uniform_dimensions(5)
    assert compute_alignment_score(dims) == 100
    v = aggregate_verdict(dims, "x" * 25)
    assert v["classification"] == Classification.DHARMIC
    assert v["alignment_score"] == 100


def test_strongly_negative_scores_adharmic() -> None:
    dims = _uniform_dimensions(-5)
    assert compute_alignment_score(dims) == -100
    v = aggregate_verdict(dims, "x" * 25)
    assert v["classification"] == Classification.ADHARMIC
    assert v["alignment_score"] == -100


def test_mixed_mid_range_scores_mixed() -> None:
    # Sum of eight scores = 8 → alignment in inner band
    dims = _uniform_dimensions(1)
    assert compute_alignment_score(dims) == 20
    v = aggregate_verdict(dims, "x" * 25)
    assert v["classification"] == Classification.MIXED


def test_ambiguity_override_context_dependent_via_missing_facts() -> None:
    dims = _uniform_dimensions(5)
    v = aggregate_verdict(
        dims,
        "x" * 25,
        missing_facts=["Who else is affected by this choice?"],
    )
    assert v["classification"] == Classification.CONTEXT_DEPENDENT
    assert len(v["missing_facts"]) == 1


def test_ambiguity_override_context_dependent_explicit_flag() -> None:
    dims = _uniform_dimensions(5)
    v = aggregate_verdict(
        dims,
        "x" * 25,
        context_dependent_override=True,
        missing_facts=[],
    )
    assert v["classification"] == Classification.CONTEXT_DEPENDENT


def test_insufficient_scorable_dimensions() -> None:
    dims = _uniform_dimensions(3)
    mask = (True, True, True, False, False, False, False, False)
    v = aggregate_verdict(dims, "x" * 25, scorable_mask=mask)
    assert v["classification"] == Classification.INSUFFICIENT_INFORMATION


def test_insufficient_overrides_high_alignment() -> None:
    dims = _uniform_dimensions(5)
    mask = (True, True, True, False, False, False, False, False)
    v = aggregate_verdict(dims, "x" * 25, scorable_mask=mask)
    assert v["alignment_score"] == 100
    assert v["classification"] == Classification.INSUFFICIENT_INFORMATION


def test_confidence_cap_with_missing_facts() -> None:
    assert compute_confidence(8, []) == pytest.approx(0.88)
    assert compute_confidence(8, ["one fact?"]) <= 0.85


def test_resolve_classification_priority_insufficient_before_context() -> None:
    assert (
        resolve_classification(
            100,
            scorable_count=2,
            missing_facts=["fact?"],
            context_dependent_override=True,
        )
        == Classification.INSUFFICIENT_INFORMATION
    )


# --- classification boundary at ±40 ---

def test_classification_at_plus_40_is_dharmic() -> None:
    # Spec table: +40 to +100 → Dharmic.  Pinned so the boundary stays explicit.
    assert resolve_classification(40, scorable_count=8, missing_facts=[]) == Classification.DHARMIC


def test_classification_at_plus_39_is_mixed() -> None:
    assert resolve_classification(39, scorable_count=8, missing_facts=[]) == Classification.MIXED


def test_classification_at_minus_40_is_adharmic() -> None:
    # Spec table: -40 to -100 → Adharmic.
    assert resolve_classification(-40, scorable_count=8, missing_facts=[]) == Classification.ADHARMIC


def test_classification_at_minus_39_is_mixed() -> None:
    assert resolve_classification(-39, scorable_count=8, missing_facts=[]) == Classification.MIXED


# --- alignment score at the raw-sum boundary that produces ±40 ---

def test_alignment_score_at_raw_boundary_for_dharmic() -> None:
    # 8 dims each at score 2 → raw sum 16 → 16 * 2.5 = 40.
    dims = _uniform_dimensions(2)
    assert compute_alignment_score(dims) == 40


def test_alignment_score_at_raw_boundary_for_adharmic() -> None:
    # 8 dims each at score -2 → raw sum -16 → -40.
    dims = _uniform_dimensions(-2)
    assert compute_alignment_score(dims) == -40


# --- confidence cap with context_dependent_override ---

def test_confidence_cap_with_context_dependent_override() -> None:
    # All 8 scored, no missing_facts — but ambiguity flagged via override.
    # Must still be capped at 0.85 (spec: cap unless all scored AND missing_facts empty).
    result = compute_confidence(8, [], context_dependent=True)
    assert result <= 0.85


def test_confidence_no_cap_when_all_conditions_clear() -> None:
    # All 8 scored, no missing_facts, no override → allowed above 0.85.
    result = compute_confidence(8, [], context_dependent=False)
    assert result == pytest.approx(0.88)


def test_missing_facts_clamped_to_six() -> None:
    dims = _uniform_dimensions(5)
    facts = [f"fact {i}?" for i in range(10)]
    v = aggregate_verdict(dims, "x" * 25, missing_facts=facts)
    assert len(v["missing_facts"]) == 6
