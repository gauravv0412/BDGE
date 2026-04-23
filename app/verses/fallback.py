"""Deterministic closest_teaching fallback for no-verse-match cases."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.verses.scorer import RetrievalContext

_MAX_CLOSEST_TEACHING_LEN = 500

_THEME_TO_CONCEPT: dict[str, str] = {
    "detachment": "detachment from outcomes while still acting",
    "desire": "desire as a driver that can narrow judgment",
    "grief": "grief with steadiness rather than denial",
    "restraint": "self-restraint over impulse reaction",
    "self-mastery": "self-mastery in private choices",
    "welfare-of-all": "welfare-of-all as an ethical direction",
    "right-livelihood": "right livelihood with minimal social harm",
    "speech": "speech that is truthful and non-injurious",
    "duty": "duty aligned with role responsibility",
}

_THEME_TO_CHAPTERS: dict[str, list[str]] = {
    "grief": ["2"],
    "detachment": ["2", "18"],
    "desire": ["2", "3", "16"],
    "anger": ["2", "3", "16"],
    "greed": ["16"],
    "speech": ["17"],
    "charity": ["17"],
    "duty": ["2", "3", "18"],
    "action": ["2", "3", "18"],
    "right-livelihood": ["18"],
    "equality": ["5"],
    "self-mastery": ["6"],
    "restraint": ["6"],
}

_DIMENSION_TO_CONCEPT: dict[str, str] = {
    "dharma_duty": "duty aligned with role responsibility",
    "satya_truth": "truth with proportional expression",
    "ahimsa_nonharm": "non-harm as a hard ethical boundary",
    "nishkama_detachment": "detachment from fruits while doing the work",
    "shaucha_intent": "clean intention before action",
    "sanyama_restraint": "inner restraint before reaction",
    "lokasangraha_welfare": "welfare-of-all as the wider test",
    "viveka_discernment": "discernment over emotional rush",
}

_STRONGLY_MODERN_SIGNALS = {
    "body_autonomy_question",
    "identity_hiding_in_family",
    "online_review_venting",
    "co_parenting_across_separation",
    "medical_coercion",
}


class ClosestTeachingResult(BaseModel):
    """Internal deterministic fallback contract."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    closest_teaching: str = Field(min_length=1, max_length=_MAX_CLOSEST_TEACHING_LEN)
    concept_tags: list[str]
    chapter_refs: list[str]
    acknowledges_gap: bool


def _unique(values: list[str]) -> list[str]:
    return sorted(set(values))


def _infer_concepts(context: RetrievalContext) -> list[str]:
    concepts: list[str] = []
    for theme in context.theme_tags:
        concept = _THEME_TO_CONCEPT.get(theme)
        if concept:
            concepts.append(concept)
    for dim in context.dominant_dimensions:
        concept = _DIMENSION_TO_CONCEPT.get(dim)
        if concept:
            concepts.append(concept)
    return _unique(concepts)


def _infer_chapters(context: RetrievalContext) -> list[str]:
    chapters: list[str] = []
    for theme in context.theme_tags:
        chapters.extend(_THEME_TO_CHAPTERS.get(theme, []))
    if any(signal in {"ethical-speech", "service-without-return"} for signal in context.applies_signals):
        chapters.append("17")
    if any(signal in {"duty-conflict", "career-crossroads"} for signal in context.applies_signals):
        chapters.extend(["3", "18"])
    if any(signal in {"bereavement"} for signal in context.applies_signals):
        chapters.append("2")
    return _unique(chapters)


def _classification_phrase(classification: str) -> str:
    value = classification.strip().lower()
    if value == "context-dependent":
        return "The dilemma turns on missing context, so this stays provisional."
    if value == "mixed":
        return "The pull here is mixed, not one-dimensional."
    return ""


def _mode_a_concept_linked(
    context: RetrievalContext,
    concepts: list[str],
    chapters: list[str],
) -> ClosestTeachingResult:
    chapter_part = f" Related grounding appears in Chapter {', '.join(chapters)}." if chapters else ""
    class_part = _classification_phrase(context.classification)
    text = (
        f"No single verse clears the match threshold, but the closest Gita lens here is {concepts[0]}."
        f" This is concept-level guidance, not a scripture quote.{chapter_part}"
        f" {class_part} The framing is useful, while the modern details still need case-level judgment."
    ).strip()
    return ClosestTeachingResult(
        closest_teaching=text[:_MAX_CLOSEST_TEACHING_LEN],
        concept_tags=concepts,
        chapter_refs=chapters,
        acknowledges_gap=True,
    )


def _mode_b_chapter_anchored(
    context: RetrievalContext,
    concepts: list[str],
    chapters: list[str],
) -> ClosestTeachingResult:
    class_part = _classification_phrase(context.classification)
    concept_part = f" Key lenses: {', '.join(concepts[:3])}." if concepts else ""
    text = (
        "No verse was strong enough to attach responsibly, but the nearest zone is "
        f"Chapter {', '.join(chapters)}.{concept_part} This is chapter-anchored guidance, not a verse quotation. "
        f"{class_part} The Gita offers a stable ethical frame, while the exact modern structure remains partially outside direct one-verse mapping."
    ).strip()
    return ClosestTeachingResult(
        closest_teaching=text[:_MAX_CLOSEST_TEACHING_LEN],
        concept_tags=concepts,
        chapter_refs=chapters,
        acknowledges_gap=True,
    )


def _mode_c_no_clean_fit(context: RetrievalContext) -> ClosestTeachingResult:
    class_part = _classification_phrase(context.classification)
    text = (
        "No specific verse cleared the threshold for this case. The Gita still offers useful lenses "
        "through duty, intention, non-harm, restraint, and welfare-of-all, but this modern structure "
        "does not map cleanly to one verse without forced certainty. "
        f"{class_part}"
    ).strip()
    return ClosestTeachingResult(
        closest_teaching=text[:_MAX_CLOSEST_TEACHING_LEN],
        concept_tags=[],
        chapter_refs=[],
        acknowledges_gap=True,
    )


def build_closest_teaching(context: RetrievalContext) -> ClosestTeachingResult:
    """Build deterministic closest_teaching in one of three guarded modes."""
    concepts = _infer_concepts(context)
    chapters = _infer_chapters(context)
    modern_niche = any(signal in _STRONGLY_MODERN_SIGNALS for signal in context.applies_signals)

    if modern_niche or (not concepts and not chapters):
        return _mode_c_no_clean_fit(context)
    if concepts and (
        len(chapters) <= 2
        or any(tag in {"detachment", "desire", "grief", "restraint", "self-mastery"} for tag in context.theme_tags)
    ):
        return _mode_a_concept_linked(context, concepts, chapters)
    return _mode_b_chapter_anchored(context, concepts, chapters)

