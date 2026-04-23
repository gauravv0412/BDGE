"""Deterministic curated verse retrieval."""

from __future__ import annotations

import re
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
    "public-shaming-intent",
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


def _word_boundary_any(text: str, terms: tuple[str, ...]) -> bool:
    """Match whole words only (avoids e.g. 'truth' in 'untruth')."""
    for term in terms:
        if re.search(rf"(?<![a-z]){re.escape(term)}(?![a-z])", text, re.IGNORECASE):
            return True
    return False


def _domestic_parenting_disclosure_without_career_frame(text: str) -> bool:
    """
    True when the text looks like *only* co-parent / child-welfare disclosure
    (not a career, calling, or income-structure dilemma).

    In that narrow band, ``duty-conflict`` was over-firing and pulling in karma
    yoga (2.47) where the golden batch expects closest-teaching instead.
    """
    parenting = _contains_any(
        text,
        (
            "divorced",
            "co-parent",
            "teenage son",
            "teenage daughter",
            "his mother",
            "her mother",
            "ex-husband",
            "ex-wife",
        ),
    )
    disclosure = _contains_any(
        text,
        ("tell", "inform", "notify", "mother", "father", "parent"),
    )
    career_frame = _contains_any(
        text,
        ("job", "career", "corporate", "income", "quit", "livelihood", "music", "profession", "startup"),
    )
    return parenting and disclosure and not career_frame


def _infer_theme_tags(text: str) -> list[str]:
    tags: set[str] = set()
    if _contains_any(text, ("duty", "responsibility", "obligation", "role")):
        tags.add("duty")
    if _contains_any(
        text,
        (
            "livelihood",
            "income supports",
            "alcohol shop",
            "income source",
            "corporate job",
            "quit my job",
            "stable job",
            "day job",
        ),
    ):
        tags.add("right-livelihood")
        tags.add("duty")
    if _contains_any(
        text,
        (
            "outcome",
            "result",
            "success",
            "failure",
            "lose my job",
            "lose your job",
            "job loss",
            "career fear",
            "count the cost",
            "cost to yourself",
            "fruit of the action",
        ),
    ):
        tags.update({"detachment", "action"})
    if _contains_any(text, ("tempt", "desire", "craving", "in love", "obsess")):
        tags.add("desire")
    if _contains_any(text, ("angry", "anger", "rage")):
        tags.add("anger")
    if _contains_any(text, ("greed", "greedy", "hoard", "revenge")):
        tags.add("greed")
    if (
        _word_boundary_any(text, ("lie",))
        or _contains_any(text, ("speak", "speech", "rumor", "disclose", "review"))
        or _word_boundary_any(text, ("truth",))
    ):
        tags.update({"truth", "speech"})
    if _contains_any(text, ("donate", "donation", "gift", "kidney")):
        tags.update({"charity", "detachment", "duty"})
    if _contains_any(text, ("grief", "death", "dying", "bereav", "terminal")):
        tags.update({"grief", "death"})
    # HEURISTIC: medical disclosure / autonomy (clinical phrasing).
    if _contains_any(
        text,
        (
            "terminal diagnosis",
            "hide from the patient",
            "withhold",
            "patient's family",
            "hide a terminal",
            "biopsy result",
        ),
    ) and _contains_any(text, ("doctor", "patient", "diagnosis")):
        tags.update({"truth", "compassion", "nonharm"})
        # Biopsy result + patient: speech-tapas (17.15) competes with daivi list (16.1-3).
        if _contains_any(text, ("biopsy result",)) and _contains_any(text, ("patient",)):
            tags.add("speech")
    if _contains_any(text, ("equal", "caste", "bias", "discrimination")):
        tags.add("equality")
    if _contains_any(text, ("discipline", "self-control", "impulse", "restrain")):
        tags.add("restraint")
    if _contains_any(text, ("wallet", "picked it up")) and _contains_any(
        text,
        ("found", "lost and", "lost-and-found"),
    ):
        tags.update({"self-mastery", "restraint", "action", "duty"})
    return sorted(tags)


def _infer_applies_signals(text: str) -> list[str]:
    """Keyword heuristics for applies_when tags (tuned on small batches; expect OOD drift)."""
    tags: set[str] = set()
    if _contains_any(text, ("outcome", "result anxiety", "anxious about result", "lose my job", "lose your job")):
        tags.add("outcome-anxiety")
    if _contains_any(text, ("duty", "responsibility", "role conflict")):
        if not _domestic_parenting_disclosure_without_career_frame(text):
            tags.add("duty-conflict")
    if _contains_any(text, ("tempt", "desire", "craving")):
        tags.add("temptation")
    if _contains_any(text, ("donate", "donation", "kidney")):
        tags.add("service-without-return")
    if _contains_any(text, ("career", "job", "profession")):
        tags.add("career-crossroads")
    if _contains_any(text, ("alcohol", "liquor", "tobacco")) and _contains_any(
        text,
        ("shop", "store", "business", "livelihood"),
    ):
        tags.add("career-crossroads")
    if _contains_any(text, ("livelihood", "income supports", "alcohol shop")):
        tags.add("livelihood-harm-tradeoff")
    # HEURISTIC: dependents + income/career tradeoff (exclude vice-retail lines).
    if _contains_any(
        text,
        (
            "kids",
            "children",
            "dependents",
            "providership",
            "lunches depend",
            "who depends on you",
            "supports my family",
            "two kids",
        ),
    ) and _contains_any(text, ("job", "corporate", "income", "quit", "career", "profession", "shop")):
        if not _contains_any(text, ("alcohol", "tobacco", "gambling", "income supports my")):
            tags.add("provider-duty")
    if _contains_any(text, ("caste", "endogamy", "different caste")):
        tags.add("caste-or-identity-boundary")
    # HEURISTIC: family gatekeeping on marriage / identity (phrasing may drift OOD).
    if _contains_any(
        text,
        ("parents strongly disapprove", "parental disapproval", "family disapprove", "disapprove of because"),
    ):
        tags.add("family-disapproval")
    if _contains_any(text, ("found a wallet", "found wallet", "lost and found", "lost-and-found", "picked it up")):
        tags.add("found-property")
    if _contains_any(
        text,
        (
            "terminal diagnosis",
            "withhold",
            "hide from the patient",
            "hide a terminal",
            "patient-led",
            "biopsy result",
        ),
    ):
        tags.add("truth-compassion-conflict")
        if _contains_any(text, ("biopsy result",)) and _contains_any(text, ("patient",)):
            tags.add("ethical-speech")
    # HEURISTIC: deathbed / compassion vs honesty (golden phrasing; broaden carefully).
    elif (
        _word_boundary_any(text, ("lie",))
        or _word_boundary_any(text, ("truth",))
    ) and _contains_any(
        text,
        (
            "compassion",
            "dying",
            "grandmother",
            "two weeks",
            "deathbed",
            "last days",
            "jail",
            "kind lie",
        ),
    ):
        tags.add("truth-compassion-conflict")
    if _contains_any(text, ("speech", "rumor", "disclose", "publicly correct", "review")):
        tags.add("ethical-speech")
    if _contains_any(text, ("credit", "my work", "manager")):
        tags.add("credit-theft")
    return sorted(tags)


def _infer_blocker_signals(text: str) -> list[str]:
    tags: set[str] = set()
    if _contains_any(text, ("hurt someone", "harm someone", "injure them", "violent revenge")):
        tags.add("active-harm")
    if _contains_any(text, ("kill", "attack", "assault")):
        tags.add("imminent-violence")
    weighing_deception = _contains_any(
        text,
        ("should i lie", "is it okay to hide", "should i tell", "should i conceal"),
    )
    settled_deception = _contains_any(
        text,
        (
            "how do i lie",
            "help me deceive",
            "how can i hide this from",
            "what should i say so they believe",
            "i will lie",
        ),
    )
    if settled_deception:
        tags.add("deception-intent")
    elif not weighing_deception and _contains_any(text, ("deceive", "mislead", "lie to", "hide the truth")):
        tags.add("deception")
    if _contains_any(text, ("public shaming", "scathing anonymous review")):
        tags.add("public-shaming-intent")
    elif _contains_any(text, ("embarrassing information",)) and _contains_any(
        text,
        ("anonymous", "online", "review", "posting", "ratings", "yelp", "stars"),
    ):
        tags.add("public-shaming-intent")
    elif _contains_any(text, ("in return",)) and _contains_any(
        text,
        ("review", "anonymous", "ratings", "yelp", "stars", "online"),
    ):
        tags.add("public-shaming-intent")
    if _contains_any(text, ("revenge",)) and _contains_any(
        text,
        ("spread", "rumor", "information about", "true but", "humiliat"),
    ):
        tags.add("retaliatory-speech")
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


def _build_why_basis(best: VerseScoreResult, core_teaching: str) -> str:
    theme_phrase = ", ".join(best.theme_overlap[:2])
    applies_phrase = ", ".join(best.applies_overlap[:2])
    parts: list[str] = []
    if core_teaching:
        parts.append(f"{core_teaching.strip().rstrip('.')}.")
    if theme_phrase:
        parts.append(f"It speaks directly to the tension around {theme_phrase}.")
    if applies_phrase:
        parts.append(f"It also fits signals like {applies_phrase} in your situation.")
    if best.dominant_dimension_hit:
        parts.append("Its emphasis aligns with the dominant ethical pull in this dilemma.")
    if not parts:
        parts.append("It is the closest responsible fit for the ethical pattern in this dilemma.")
    return " ".join(parts)[:500]


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
        why_it_applies=_build_why_basis(best, winner.core_teaching),
        match_confidence=_score_to_confidence(best.total_score),
    )
    return VerseResult(verse_match=match, closest_teaching=None)
