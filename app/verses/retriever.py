"""Deterministic curated verse retrieval."""

from __future__ import annotations

from typing import TypedDict

from app.core.models import EthicalDimensions, VerseMatch
from app.verses.catalog import VerseCatalog
from app.verses.fallback import build_closest_teaching
from app.verses.loader import load_curated_verses
from app.verses.scorer import RetrievalContext, VerseScoreResult, rank_candidates
from app.verses.types import DimensionKey


class VerseResult(TypedDict):
    """Intermediate output of the verse retrieval stage."""

    verse_match: VerseMatch | None
    closest_teaching: str | None


_MATCH_THRESHOLD = 6
_SEVERE_BLOCKERS = {
    "active-harm",
    "imminent-violence",
    "self-harm",
    "abuse-context",
    "criminal-intent",
}


def _dominant_dimensions(
    dimensions: EthicalDimensions,
    *,
    min_score: int = 2,
) -> list[DimensionKey]:
    pairs = [
        ("dharma_duty", dimensions.dharma_duty.score),
        ("satya_truth", dimensions.satya_truth.score),
        ("ahimsa_nonharm", dimensions.ahimsa_nonharm.score),
        ("nishkama_detachment", dimensions.nishkama_detachment.score),
        ("shaucha_intent", dimensions.shaucha_intent.score),
        ("sanyama_restraint", dimensions.sanyama_restraint.score),
        ("lokasangraha_welfare", dimensions.lokasangraha_welfare.score),
        ("viveka_discernment", dimensions.viveka_discernment.score),
    ]
    ranked = sorted(pairs, key=lambda item: item[1], reverse=True)
    return [name for name, score in ranked if score >= min_score]


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def _infer_theme_tags(text: str) -> list[str]:
    tags: set[str] = set()
    if _contains_any(text, ("duty", "responsibility", "obligation", "role")):
        tags.add("duty")
    if _contains_any(text, ("outcome", "result", "success", "failure")):
        tags.update({"detachment", "action"})
    if _contains_any(text, ("tempt", "desire", "craving")):
        tags.add("desire")
    if _contains_any(text, ("angry", "anger", "rage")):
        tags.add("anger")
    if _contains_any(text, ("lie", "truth", "speak", "speech")):
        tags.update({"truth", "speech"})
    if _contains_any(text, ("grief", "death", "dying", "bereav")):
        tags.update({"grief", "death"})
    if _contains_any(text, ("equal", "caste", "bias", "discrimination")):
        tags.add("equality")
    return sorted(tags)


def _infer_applies_signals(text: str) -> list[str]:
    tags: set[str] = set()
    if _contains_any(text, ("outcome", "result anxiety", "anxious about result")):
        tags.add("outcome-anxiety")
    if _contains_any(text, ("duty", "responsibility", "role conflict")):
        tags.add("duty-conflict")
    if _contains_any(text, ("tempt", "desire", "craving")):
        tags.add("temptation")
    if _contains_any(text, ("career", "job", "profession")):
        tags.add("career-crossroads")
    if _contains_any(text, ("speech", "say", "tell", "disclose")):
        tags.add("ethical-speech")
    if _contains_any(text, ("credit", "my work", "manager")):
        tags.add("credit-theft")
    return sorted(tags)


def _infer_blocker_signals(text: str) -> list[str]:
    tags: set[str] = set()
    if _contains_any(text, ("hurt", "harm", "injure", "violence")):
        tags.add("active-harm")
    if _contains_any(text, ("kill", "attack", "assault")):
        tags.add("imminent-violence")
    if _contains_any(text, ("deceive", "mislead", "lie to", "hide the truth")):
        tags.add("deception")
    if _contains_any(text, ("suicide", "self harm", "harm myself")):
        tags.add("self-harm")
    return sorted(tags)


def _build_context(
    dilemma: str,
    dimensions: EthicalDimensions,
    context_override: RetrievalContext | None,
) -> RetrievalContext:
    if context_override is not None:
        return context_override

    normalized = dilemma.strip().lower()
    return RetrievalContext(
        dilemma_id="live-unknown",
        classification="Unknown",
        primary_driver="",
        hidden_risk="",
        dominant_dimensions=_dominant_dimensions(dimensions),
        theme_tags=_infer_theme_tags(normalized),
        applies_signals=_infer_applies_signals(normalized),
        blocker_signals=_infer_blocker_signals(normalized),
        missing_facts=[],
    )


def _score_to_confidence(score: int) -> float:
    """Map eligible score (>=6) into [0.6, 1.0]."""
    bounded = max(_MATCH_THRESHOLD, min(score, 14))
    return round(0.6 + ((bounded - _MATCH_THRESHOLD) / (14 - _MATCH_THRESHOLD)) * 0.4, 2)


def _build_why_basis(best: VerseScoreResult) -> str:
    theme_bits = ", ".join(best.theme_overlap) or "none"
    applies_bits = ", ".join(best.applies_overlap) or "none"
    blockers = ", ".join(best.blocker_overlap) or "none"
    return (
        f"Deterministic match basis: themes={theme_bits}; applies_when={applies_bits}; "
        f"blockers={blockers}; dominant_dimension_hit={best.dominant_dimension_hit}; "
        f"score={best.total_score}."
    )[:500]


def retrieve_verse(
    dilemma: str,
    dimensions: EthicalDimensions,
    context_override: RetrievalContext | None = None,
) -> VerseResult:
    """
    Deterministically select a curated verse match for *dilemma*.

    ``why_it_applies`` is not stored in curated verse data; retrieval builds a
    structured basis from overlap signals.
    """
    entries = load_curated_verses()
    catalog = VerseCatalog(entries)
    active_entries = catalog.list_active()
    context = _build_context(dilemma, dimensions, context_override)

    if set(context.blocker_signals) & _SEVERE_BLOCKERS:
        fallback = build_closest_teaching(context)
        return VerseResult(verse_match=None, closest_teaching=fallback.closest_teaching)

    ranked = rank_candidates(active_entries, context)

    if not ranked:
        fallback = build_closest_teaching(context)
        return VerseResult(verse_match=None, closest_teaching=fallback.closest_teaching)

    best = ranked[0]
    if best.rejected or best.total_score < _MATCH_THRESHOLD:
        fallback = build_closest_teaching(context)
        return VerseResult(verse_match=None, closest_teaching=fallback.closest_teaching)

    winner = catalog.get_by_ref(best.verse_ref)
    if winner is None:
        fallback = build_closest_teaching(context)
        return VerseResult(verse_match=None, closest_teaching=fallback.closest_teaching)

    match = VerseMatch(
        verse_ref=winner.verse_ref,
        sanskrit_devanagari=winner.sanskrit_devanagari,
        sanskrit_iast=winner.sanskrit_iast,
        hindi_translation=winner.hindi_translation or "",
        english_translation=winner.english_translation,
        source=winner.source.format_for_output(),
        why_it_applies=_build_why_basis(best),
        match_confidence=_score_to_confidence(best.total_score),
    )
    return VerseResult(verse_match=match, closest_teaching=None)
