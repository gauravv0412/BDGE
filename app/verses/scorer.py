"""Deterministic scoring for curated verse retrieval."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.verses.types import CuratedVerseEntry, DimensionKey


def verse_coordinate(verse_ref: str) -> tuple[int, int]:
    """
    Map ``chapter.verse`` / ``chapter.start-end`` to (chapter, first_verse).

    Used only as a **last-resort deterministic tie-break** after score, overlap
    counts, priority, and dimension hit — not as a semantic ranking. Earlier
    Bhagavad Gita positions sort first (smaller tuple).
    """
    s = verse_ref.strip().replace("–", "-")
    if "." not in s:
        return (9999, 9999)
    ch_s, rest = s.split(".", 1)
    chapter = int(ch_s)
    if "-" in rest:
        verse_start = int(rest.split("-", 1)[0])
    else:
        verse_start = int(rest)
    return (chapter, verse_start)


class RetrievalContext(BaseModel):
    """Signals extracted from current dilemma state for deterministic matching."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    dilemma_id: str
    classification: str
    primary_driver: str
    hidden_risk: str
    dominant_dimensions: list[DimensionKey]
    theme_tags: list[str]
    applies_signals: list[str]
    blocker_signals: list[str]
    missing_facts: list[str]


class VerseScoreResult(BaseModel):
    """Scoring outcome for one curated verse candidate."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    verse_ref: str
    total_score: int
    theme_overlap: list[str]
    applies_overlap: list[str]
    blocker_overlap: list[str]
    dominant_dimension_hit: bool
    priority_used: int
    rejected: bool
    rejection_reason: str | None = None


def score_entry(entry: CuratedVerseEntry, context: RetrievalContext) -> VerseScoreResult:
    """Score one entry with deterministic overlap heuristics."""
    theme_overlap = sorted(set(entry.themes) & set(context.theme_tags))
    applies_overlap = sorted(set(entry.applies_when) & set(context.applies_signals))
    blocker_overlap = sorted(set(entry.does_not_apply_when) & set(context.blocker_signals))
    dominant_dimension_hit = any(key in context.dominant_dimensions for key in entry.dimension_affinity)

    rejected = bool(blocker_overlap)
    total_score = (3 * len(theme_overlap)) + (2 * len(applies_overlap)) - (5 * len(blocker_overlap))
    if dominant_dimension_hit:
        total_score += 1

    return VerseScoreResult(
        verse_ref=entry.verse_ref,
        total_score=total_score,
        theme_overlap=theme_overlap,
        applies_overlap=applies_overlap,
        blocker_overlap=blocker_overlap,
        dominant_dimension_hit=dominant_dimension_hit,
        priority_used=entry.priority,
        rejected=rejected,
        rejection_reason="blocker_overlap" if rejected else None,
    )


def rank_candidates(
    entries: list[CuratedVerseEntry],
    context: RetrievalContext,
) -> list[VerseScoreResult]:
    """
    Rank scored candidates, preferring stronger thematic matches.

    Tie order (first wins): non-rejected, >=2 theme hits, total_score,
    theme_overlap count, applies_overlap count, curated ``priority``,
    dominant-dimension hit, then ``verse_coordinate`` (earlier Gita text).
    """
    scored = [score_entry(entry, context) for entry in entries]

    def _sort_key(result: VerseScoreResult) -> tuple[int, int, int, int, int, int, int, int]:
        two_plus_theme = 1 if len(result.theme_overlap) >= 2 else 0
        non_rejected = 1 if not result.rejected else 0
        dim_hit = 1 if result.dominant_dimension_hit else 0
        ch, v0 = verse_coordinate(result.verse_ref)
        return (
            -non_rejected,
            -two_plus_theme,
            -result.total_score,
            -len(result.theme_overlap),
            -len(result.applies_overlap),
            -result.priority_used,
            -dim_hit,
            ch,
            v0,
        )

    return sorted(scored, key=_sort_key)

