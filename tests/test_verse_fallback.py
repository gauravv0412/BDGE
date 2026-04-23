"""Tests for deterministic closest_teaching fallback modes."""

from __future__ import annotations

from app.verses.fallback import build_closest_teaching
from app.verses.scorer import RetrievalContext
from app.verses.style_guards import evaluate_closest_teaching_style
from app.verses.types import DimensionKey


def _context(
    *,
    classification: str = "Mixed",
    themes: list[str],
    applies: list[str],
    blockers: list[str],
    dominant_dimensions: list[DimensionKey],
) -> RetrievalContext:
    return RetrievalContext(
        dilemma_id="WTEST",
        classification=classification,
        primary_driver="test",
        hidden_risk="test",
        dominant_dimensions=dominant_dimensions,
        theme_tags=themes,
        applies_signals=applies,
        blocker_signals=blockers,
        missing_facts=[],
    )


def test_concept_linked_fallback_for_grief_detachment_context() -> None:
    result = build_closest_teaching(
        _context(
            themes=["grief", "detachment"],
            applies=["bereavement"],
            blockers=[],
            dominant_dimensions=["nishkama_detachment", "viveka_discernment"],
        )
    )
    assert result.acknowledges_gap
    assert "closest Gita lens" in result.closest_teaching
    assert "2" in result.chapter_refs
    assert result.concept_tags


def test_chapter_anchored_fallback_for_speech_duty_weak_fit() -> None:
    result = build_closest_teaching(
        _context(
            themes=["speech", "duty", "action", "charity"],
            applies=["ethical-speech", "duty-conflict", "service-without-return"],
            blockers=[],
            dominant_dimensions=["dharma_duty"],
        )
    )
    assert result.acknowledges_gap
    assert "Chapter" in result.closest_teaching
    assert any(ch in {"17", "18"} for ch in result.chapter_refs)


def test_explicit_no_clean_fit_for_modern_niche_case() -> None:
    result = build_closest_teaching(
        _context(
            themes=[],
            applies=["body_autonomy_question"],
            blockers=[],
            dominant_dimensions=[],
        )
    )
    assert result.acknowledges_gap
    assert "does not map cleanly" in result.closest_teaching
    assert not result.chapter_refs


def test_fallback_never_includes_sanskrit_or_quotes() -> None:
    result = build_closest_teaching(
        _context(
            themes=["desire", "anger"],
            applies=["temptation"],
            blockers=[],
            dominant_dimensions=["sanyama_restraint"],
        )
    )
    lowered = result.closest_teaching.lower()
    assert "॥" not in result.closest_teaching
    assert "karmaṇy" not in lowered
    assert '"' not in result.closest_teaching
    assert "'" not in result.closest_teaching


def test_fallback_stays_within_schema_length() -> None:
    result = build_closest_teaching(
        _context(
            classification="Context-dependent",
            themes=["duty", "action", "detachment", "equality", "restraint", "grief"],
            applies=["duty-conflict", "ethical-speech", "career-crossroads"],
            blockers=[],
            dominant_dimensions=["dharma_duty", "viveka_discernment"],
        )
    )
    assert len(result.closest_teaching) <= 500


def test_fallback_style_guards_no_overclaim_or_preachy() -> None:
    result = build_closest_teaching(
        _context(
            classification="Mixed",
            themes=["duty", "action"],
            applies=["duty-conflict"],
            blockers=[],
            dominant_dimensions=["dharma_duty"],
        )
    )
    issues = evaluate_closest_teaching_style(result.closest_teaching)
    assert "closest_teaching_overclaim" not in issues
    assert "closest_teaching_preachy_imperative" not in issues

