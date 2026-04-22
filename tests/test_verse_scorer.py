"""Tests for deterministic verse scoring and ranking."""

from __future__ import annotations

from app.verses.loader import load_curated_verses
from app.verses.scorer import RetrievalContext, rank_candidates, score_entry
from app.verses.types import DimensionKey


def _context(
    *,
    theme_tags: list[str],
    applies_signals: list[str],
    blocker_signals: list[str],
    dominant_dimensions: list[DimensionKey],
) -> RetrievalContext:
    return RetrievalContext(
        dilemma_id="WTEST",
        classification="Mixed",
        primary_driver="test",
        hidden_risk="test",
        dominant_dimensions=dominant_dimensions,
        theme_tags=theme_tags,
        applies_signals=applies_signals,
        blocker_signals=blocker_signals,
        missing_facts=[],
    )


def test_score_entry_positive_for_247_outcome_duty() -> None:
    entries = load_curated_verses()
    entry = next(item for item in entries if item.verse_ref == "2.47")
    result = score_entry(
        entry,
        _context(
            theme_tags=["duty", "detachment", "action"],
            applies_signals=["outcome-anxiety", "duty-conflict"],
            blocker_signals=[],
            dominant_dimensions=["nishkama_detachment"],
        ),
    )
    assert result.total_score >= 6
    assert set(result.theme_overlap) >= {"duty", "detachment"}
    assert "outcome-anxiety" in result.applies_overlap
    assert not result.rejected


def test_score_entry_positive_for_337_desire_temptation() -> None:
    entries = load_curated_verses()
    entry = next(item for item in entries if item.verse_ref == "3.37")
    result = score_entry(
        entry,
        _context(
            theme_tags=["desire", "anger", "restraint", "self-mastery"],
            applies_signals=["temptation", "anger-spike"],
            blocker_signals=[],
            dominant_dimensions=["sanyama_restraint"],
        ),
    )
    assert result.total_score >= 6
    assert "anger" in result.theme_overlap
    assert "temptation" in result.applies_overlap
    assert not result.rejected


def test_blocker_suppression_rejects_candidate() -> None:
    entries = load_curated_verses()
    entry = next(item for item in entries if item.verse_ref == "2.47")
    result = score_entry(
        entry,
        _context(
            theme_tags=["duty", "detachment", "action"],
            applies_signals=["outcome-anxiety"],
            blocker_signals=["active-harm"],
            dominant_dimensions=["dharma_duty"],
        ),
    )
    assert result.rejected
    assert result.rejection_reason == "blocker_overlap"


def test_stronger_thematic_match_beats_shallow_match() -> None:
    entries = load_curated_verses()
    strong = next(item for item in entries if item.verse_ref == "2.47")
    shallow = next(item for item in entries if item.verse_ref == "18.47")
    context = _context(
        theme_tags=["duty", "detachment", "action"],
        applies_signals=["outcome-anxiety", "duty-conflict"],
        blocker_signals=[],
        dominant_dimensions=["nishkama_detachment"],
    )
    ranked = rank_candidates([shallow, strong], context)
    assert ranked[0].verse_ref == "2.47"


def test_deterministic_tie_break_by_verse_ref() -> None:
    entries = load_curated_verses()
    base = next(item for item in entries if item.verse_ref == "2.47")
    first = base.model_copy(update={"verse_id": "BG-T1", "verse_ref": "2.47"})
    second = base.model_copy(update={"verse_id": "BG-T2", "verse_ref": "3.01"})
    context = _context(
        theme_tags=["duty", "detachment"],
        applies_signals=["outcome-anxiety"],
        blocker_signals=[],
        dominant_dimensions=["nishkama_detachment"],
    )
    ranked = rank_candidates([second, first], context)
    assert ranked[0].verse_ref == "2.47"

