"""Tests for deterministic verse retriever selection."""

from __future__ import annotations

from typing import Any

from app.core.models import DimensionScore, EthicalDimensions
from app.verses.loader import load_curated_verses
from app.verses.retriever import retrieve_verse
from app.verses.scorer import RetrievalContext
from app.verses.types import DimensionKey


def _dimensions() -> EthicalDimensions:
    return EthicalDimensions(
        dharma_duty=DimensionScore(score=3, note="duty"),
        satya_truth=DimensionScore(score=1, note="truth"),
        ahimsa_nonharm=DimensionScore(score=0, note="nonharm"),
        nishkama_detachment=DimensionScore(score=4, note="detachment"),
        shaucha_intent=DimensionScore(score=0, note="intent"),
        sanyama_restraint=DimensionScore(score=3, note="restraint"),
        lokasangraha_welfare=DimensionScore(score=0, note="welfare"),
        viveka_discernment=DimensionScore(score=2, note="discernment"),
    )


def _context(
    *,
    themes: list[str],
    applies: list[str],
    blockers: list[str],
    dominant_dimensions: list[DimensionKey],
) -> RetrievalContext:
    return RetrievalContext(
        dilemma_id="WTEST",
        classification="Mixed",
        primary_driver="test",
        hidden_risk="test",
        dominant_dimensions=dominant_dimensions,
        theme_tags=themes,
        applies_signals=applies,
        blocker_signals=blockers,
        missing_facts=[],
    )


def test_retrieve_verse_returns_247_in_outcome_duty_context() -> None:
    result = retrieve_verse(
        "I feel anxious about outcome and duty conflict.",
        _dimensions(),
        context_override=_context(
            themes=["duty", "detachment", "action"],
            applies=["outcome-anxiety", "duty-conflict"],
            blockers=[],
            dominant_dimensions=["nishkama_detachment"],
        ),
    )
    assert result["verse_match"] is not None
    assert result["verse_match"].verse_ref == "2.47"
    assert result["closest_teaching"] is None


def test_retrieve_verse_returns_337_in_desire_temptation_context() -> None:
    result = retrieve_verse(
        "I am tempted and angry.",
        _dimensions(),
        context_override=_context(
            themes=["desire", "anger", "restraint", "self-mastery"],
            applies=["temptation", "anger-spike"],
            blockers=[],
            dominant_dimensions=["sanyama_restraint"],
        ),
    )
    assert result["verse_match"] is not None
    assert result["verse_match"].verse_ref == "3.37"


def test_retrieve_verse_suppresses_match_on_blocker_overlap() -> None:
    result = retrieve_verse(
        "Should I harm someone to get revenge?",
        _dimensions(),
        context_override=_context(
            themes=["duty", "detachment", "action"],
            applies=["outcome-anxiety", "duty-conflict"],
            blockers=["active-harm"],
            dominant_dimensions=["dharma_duty"],
        ),
    )
    assert result["verse_match"] is None
    assert result["closest_teaching"] is not None


def test_retrieve_verse_returns_no_match_below_threshold() -> None:
    result = retrieve_verse(
        "No clear overlap context.",
        _dimensions(),
        context_override=_context(
            themes=["equanimity"],
            applies=[],
            blockers=[],
            dominant_dimensions=["viveka_discernment"],
        ),
    )
    assert result["verse_match"] is None
    assert result["closest_teaching"] is not None


def test_retriever_never_returns_draft_entries(monkeypatch: Any) -> None:
    entries = load_curated_verses()
    target = next(item for item in entries if item.verse_ref == "2.47")
    draft_only = [target.model_copy(update={"status": "draft"})]
    monkeypatch.setattr("app.verses.retriever.load_curated_verses", lambda: draft_only)

    result = retrieve_verse(
        "Strong 2.47 context but only draft exists.",
        _dimensions(),
        context_override=_context(
            themes=["duty", "detachment", "action"],
            applies=["outcome-anxiety", "duty-conflict"],
            blockers=[],
            dominant_dimensions=["nishkama_detachment"],
        ),
    )
    assert result["verse_match"] is None


def test_retriever_deterministic_tie_break(monkeypatch: Any) -> None:
    entries = load_curated_verses()
    base = next(item for item in entries if item.verse_ref == "2.47")
    tied_a = base.model_copy(update={"verse_id": "BG-A", "verse_ref": "2.47"})
    tied_b = base.model_copy(update={"verse_id": "BG-B", "verse_ref": "3.01"})
    monkeypatch.setattr("app.verses.retriever.load_curated_verses", lambda: [tied_b, tied_a])

    result = retrieve_verse(
        "Tie break check",
        _dimensions(),
        context_override=_context(
            themes=["duty", "detachment", "action"],
            applies=["outcome-anxiety", "duty-conflict"],
            blockers=[],
            dominant_dimensions=["nishkama_detachment"],
        ),
    )
    assert result["verse_match"] is not None
    assert result["verse_match"].verse_ref == "2.47"

