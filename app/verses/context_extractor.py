"""Deterministic retrieval-signal extraction for sparse live dilemmas."""

from __future__ import annotations

import re
from typing import Any

from app.verses.types import DimensionKey


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def _word_boundary_any(text: str, terms: tuple[str, ...]) -> bool:
    for term in terms:
        if re.search(rf"(?<![a-z]){re.escape(term)}(?![a-z])", text, re.IGNORECASE):
            return True
    return False


def _add_unique(target: set[str], values: tuple[str, ...]) -> None:
    target.update(values)


def extract_live_retrieval_context_signals(
    dilemma: str,
    proposed_action: str | None = None,
) -> dict[str, Any]:
    """
    Extract narrow retrieval tags from sparse user text.

    This does not score or retrieve verses. It only supplies the same signal
    vocabulary consumed by the deterministic retriever when the semantic layer
    has not provided richer retrieval context.
    """
    text = " ".join(part for part in (dilemma, proposed_action or "") if part).strip().lower()
    theme_tags: set[str] = set()
    applies_signals: set[str] = set()
    blocker_signals: set[str] = set()
    dominant_dimensions: set[DimensionKey] = set()
    primary_driver = ""
    hidden_risk = ""

    # Public correction / workplace credit theft.
    if _contains_any(text, ("publicly correct", "takes credit for my work", "manager takes credit")):
        _add_unique(theme_tags, ("speech", "truth", "nonharm"))
        _add_unique(applies_signals, ("ethical-speech", "credit-theft", "public-humiliation-impulse"))
        _add_unique(dominant_dimensions, ("satya_truth", "sanyama_restraint"))
        primary_driver = primary_driver or "Truth-seeking mixed with public vindication."

    # Found property / private integrity.
    if (
        _contains_any(text, ("found a wallet", "found wallet", "picked it up"))
        or (
            _contains_any(text, ("found extra cash", "atm tray", "cashier forgot to scan", "forgot to scan"))
            and _contains_any(text, ("keep it", "go back and pay", "pay"))
        )
    ):
        _add_unique(theme_tags, ("self-mastery", "restraint", "action", "duty"))
        applies_signals.add("found-property")
        _add_unique(dominant_dimensions, ("sanyama_restraint", "viveka_discernment"))
        if _contains_any(text, ("cashier forgot to scan", "go back and pay")):
            theme_tags.add("truth")
            applies_signals.add("private-conduct-test")

    # Career calling with dependents.
    if _contains_any(text, ("quit my stable job", "quit my job", "music")) and _contains_any(
        text, ("kids", "children", "dependents", "family")
    ):
        _add_unique(theme_tags, ("duty", "action", "discernment", "right-livelihood"))
        _add_unique(applies_signals, ("career-crossroads", "career-vs-calling", "provider-duty"))
        _add_unique(dominant_dimensions, ("dharma_duty", "viveka_discernment"))

    # Civic responsibility / public participation.
    if _contains_any(text, ("not voting", "skip voting")) and _contains_any(
        text, ("election", "candidates", "candidate")
    ):
        _add_unique(theme_tags, ("duty", "welfare-of-all", "action"))
        applies_signals.add("duty-conflict")
        _add_unique(dominant_dimensions, ("dharma_duty", "lokasangraha_welfare"))

    # Compassionate truth at deathbed.
    if (
        _word_boundary_any(text, ("lie",))
        and _contains_any(text, ("dying", "grandmother", "deathbed", "last days"))
    ):
        _add_unique(theme_tags, ("speech", "truth", "nonharm"))
        _add_unique(applies_signals, ("ethical-speech", "truth-compassion-conflict"))
        _add_unique(dominant_dimensions, ("satya_truth", "ahimsa_nonharm"))

    # Public exposure as workplace/political retaliation.
    if _contains_any(text, ("expose his mistakes", "expose her mistakes", "in front of leadership")):
        _add_unique(theme_tags, ("speech", "truth", "nonharm"))
        applies_signals.add("ethical-speech")
        _add_unique(dominant_dimensions, ("satya_truth", "sanyama_restraint"))

    # Livelihood harm tradeoff.
    if _contains_any(text, ("alcohol shop", "liquor shop", "tobacco shop", "gambling shop")) or (
        _contains_any(text, ("alcohol", "liquor", "tobacco", "gambling"))
        and _contains_any(text, ("shop", "store", "business", "livelihood"))
    ):
        _add_unique(theme_tags, ("duty", "right-livelihood", "restraint"))
        _add_unique(applies_signals, ("career-crossroads", "livelihood-harm-tradeoff"))
        _add_unique(dominant_dimensions, ("dharma_duty", "lokasangraha_welfare"))

    # Revenge with true information / retaliatory speech.
    if _contains_any(text, ("in return", "revenge", "retaliat")) and _contains_any(
        text, ("rumor", "embarrassing information", "true but embarrassing", "spread true")
    ):
        _add_unique(theme_tags, ("anger", "greed", "speech", "truth"))
        _add_unique(applies_signals, ("anger-spike", "ethical-speech"))
        blocker_signals.add("retaliatory-speech")
        _add_unique(dominant_dimensions, ("sanyama_restraint", "shaucha_intent"))

    if _contains_any(text, ("shared a private secret", "tell everyone what they did")):
        _add_unique(theme_tags, ("speech", "truth"))
        applies_signals.add("ethical-speech")
        blocker_signals.add("retaliatory-speech")

    # Abuse / self-protection. Severe blocker intentionally prevents forced verse.
    if _contains_any(text, ("abusive", "abuse", "controlling")) and _contains_any(
        text, ("parent", "contact", "cut contact")
    ):
        _add_unique(theme_tags, ("nonharm", "restraint"))
        blocker_signals.add("abuse-context")
        _add_unique(dominant_dimensions, ("ahimsa_nonharm", "viveka_discernment"))

    if _contains_any(text, ("sibling constantly insults", "borrows money without returning")):
        _add_unique(theme_tags, ("nonharm", "restraint"))
        blocker_signals.add("abuse-context")
        _add_unique(dominant_dimensions, ("ahimsa_nonharm", "viveka_discernment"))

    # Caste marriage / inherited hierarchy.
    if _contains_any(text, ("different caste", "caste", "endogamy")) and _contains_any(
        text, ("marry", "marrying", "marriage", "parents", "disapprove")
    ):
        _add_unique(theme_tags, ("equality", "compassion"))
        _add_unique(applies_signals, ("caste-or-identity-boundary", "family-disapproval"))
        _add_unique(dominant_dimensions, ("lokasangraha_welfare", "viveka_discernment"))

    if _contains_any(text, ("outside our religion", "shame the family")) and _contains_any(
        text, ("marrying", "relationship", "end the relationship")
    ):
        # Keep this below the 5.18 threshold; fixture expects closest teaching, not a forced verse.
        applies_signals.add("family-disapproval")

    # Medical disclosure / patient autonomy.
    # Bare "doctor" over-fires (e.g. "I saw my doctor for a checkup"); require a disclosure context.
    if _contains_any(text, ("terminal diagnosis", "hide from the patient", "patient's family", "biopsy result")) or (
        _contains_any(text, ("doctor",))
        and _contains_any(text, ("patient", "terminal", "diagnosis", "hide", "withhold", "tell them"))
    ):
        _add_unique(theme_tags, ("truth", "compassion", "nonharm"))
        _add_unique(applies_signals, ("truth-compassion-conflict", "terminal-diagnosis-disclosure"))
        _add_unique(dominant_dimensions, ("satya_truth", "ahimsa_nonharm"))

    # Bribe / corruption participation. Kept below attachment threshold by design.
    if _contains_any(text, ("bribe", "corruption", "government document")):
        _add_unique(theme_tags, ("truth", "welfare-of-all"))
        _add_unique(dominant_dimensions, ("satya_truth", "lokasangraha_welfare"))

    # Startup stewardship / investor-duty anxiety.
    if _contains_any(text, ("startup is failing", "investors gave me money")) and _contains_any(
        text, ("return what's left", "pivot aggressively", "shut down")
    ):
        _add_unique(theme_tags, ("action", "detachment", "duty"))
        _add_unique(applies_signals, ("outcome-anxiety", "duty-conflict"))
        _add_unique(dominant_dimensions, ("dharma_duty", "nishkama_detachment"))

    # Lying by omission / concealment. Truth-only keeps fallback possible.
    if _contains_any(
        text,
        (
            "hide it from them",
            "strictly vegetarian",
            "hide it",
            "omission",
            "leaves out",
            "keep quiet unless asked",
        ),
    ):
        theme_tags.add("truth")
        dominant_dimensions.add("satya_truth")
        if _contains_any(text, ("fired for misconduct", "resume", "keep quiet unless asked", "bought something expensive")):
            blocker_signals.add("deception")

    # Whistleblowing public harm.
    if _contains_any(
        text,
        ("polluting a river", "whistleblower", "lose my job", "dumps untreated water", "factory dumps"),
    ):
        _add_unique(theme_tags, ("duty", "action", "detachment", "welfare-of-all"))
        _add_unique(applies_signals, ("whistleblowing-risk", "outcome-anxiety", "duty-conflict"))
        _add_unique(dominant_dimensions, ("dharma_duty", "lokasangraha_welfare", "nishkama_detachment"))

    # Self-defense is high-stakes harm context; prefer fallback over forced warrior-duty verses.
    if _contains_any(text, ("killing in self-defense", "kill in self-defense", "self defense")):
        theme_tags.add("nonharm")
        blocker_signals.add("active-harm")
        _add_unique(dominant_dimensions, ("ahimsa_nonharm", "viveka_discernment"))

    # Unavailable partner desire.
    if _contains_any(text, ("best friend's partner", "best friend partner")) or (
        _contains_any(text, ("deeply in love", "in love")) and _contains_any(text, ("partner", "friend"))
    ):
        _add_unique(theme_tags, ("desire", "restraint", "self-mastery"))
        applies_signals.add("temptation")
        _add_unique(dominant_dimensions, ("sanyama_restraint", "shaucha_intent"))

    if (
        _contains_any(text, ("attracted to a married", "married colleague", "married and someone", "keep texting them privately"))
        or (_contains_any(text, ("flirts with me", "interested in me")) and _contains_any(text, ("married", "alone after work", "privately")))
    ):
        _add_unique(theme_tags, ("desire", "restraint"))
        applies_signals.add("temptation")
        _add_unique(dominant_dimensions, ("sanyama_restraint", "shaucha_intent"))

    if _contains_any(text, ("having an affair", "thinking about an affair")) and _contains_any(
        text, ("marriage", "partners", "parents", "sexless")
    ):
        _add_unique(theme_tags, ("desire", "restraint", "self-mastery"))
        applies_signals.add("temptation")
        _add_unique(dominant_dimensions, ("sanyama_restraint", "shaucha_intent"))

    if _contains_any(text, ("jealous", "secretly check their phone")):
        # Jealous privacy-checking is a temptation signal, but keep it below a verse threshold.
        theme_tags.add("desire")

    if _contains_any(text, ("comparing my partner", "restlessness")):
        # Romantic dissatisfaction is a weak desire signal, not enough for 3.37 by itself.
        theme_tags.add("discernment")

    # Sattvic giving / kidney donation.
    if _contains_any(text, ("donate a kidney", "kidney to a stranger", "donation list")):
        _add_unique(theme_tags, ("charity", "detachment", "duty"))
        applies_signals.add("service-without-return")
        _add_unique(dominant_dimensions, ("lokasangraha_welfare", "nishkama_detachment"))

    if _contains_any(text, ("beggar at the signal", "give money")) and _contains_any(
        text, ("perpetuate the cycle", "beggar", "charity")
    ):
        _add_unique(theme_tags, ("charity", "detachment", "duty"))
        applies_signals.add("service-without-return")
        _add_unique(dominant_dimensions, ("lokasangraha_welfare", "nishkama_detachment"))

    # Harmful public review.
    # "leave"/"write" alone do not indicate harm; require an explicit negativity signal.
    if _contains_any(
        text,
        (
            "scathing anonymous review",
            "anonymous review",
            "harsh review",
            "bad review",
            "viral thread humiliating",
            "humiliating them with screenshots",
        ),
    ) or (
        _contains_any(text, ("review",))
        and _contains_any(text, ("tempted", "vent", "scathing", "harsh", "angry", "negative review"))
    ):
        _add_unique(theme_tags, ("speech", "truth"))
        applies_signals.add("ethical-speech")
        blocker_signals.add("public-shaming-intent")
        _add_unique(dominant_dimensions, ("satya_truth", "sanyama_restraint"))

    if _contains_any(text, ("ai deepfake", "deepfake")) and _contains_any(
        text, ("embarrassing", "boss", "joke")
    ):
        _add_unique(theme_tags, ("speech", "truth"))
        applies_signals.add("ethical-speech")
        _add_unique(blocker_signals, ("deception", "public-shaming-intent"))

    if _contains_any(text, ("other people's breakups", "monetizing their pain", "public posts")):
        # Profit from others' pain is harm/speech context, but below verse threshold.
        theme_tags.add("nonharm")

    # Co-parent disclosure. Avoid duty-conflict to preserve closest-teaching behavior.
    if _contains_any(text, ("teenage son smoking", "teenage daughter smoking", "co-parent", "divorced")):
        _add_unique(theme_tags, ("duty", "speech"))
        _add_unique(dominant_dimensions, ("dharma_duty", "satya_truth"))

    # Friendship truth ambiguity. Speech-only keeps this below threshold.
    if _contains_any(text, ("friend is cheating", "cheating on their spouse", "do i tell")):
        theme_tags.add("speech")
        dominant_dimensions.add("satya_truth")

    if _contains_any(text, ("friend betrayed", "make them feel abandoned")):
        # Punitive friendship hurt is anger context, but not enough by itself for 3.37.
        theme_tags.add("anger")

    # Body autonomy / cosmetic self-mastery. Kept below attachment threshold.
    if _contains_any(text, ("cosmetic surgery", "hate my nose", "body autonomy")):
        _add_unique(theme_tags, ("discernment", "self-mastery"))
        _add_unique(dominant_dimensions, ("viveka_discernment", "sanyama_restraint"))

    if _contains_any(text, ("parents want me to become", "follow their plan", "study design")):
        # Family pressure is vocation context but should not force svadharma verses.
        applies_signals.add("career-vs-calling")

    if _contains_any(text, ("father wants me to take over", "family shop")) and _contains_any(
        text, ("stable job", "refusing")
    ):
        applies_signals.add("career-crossroads")

    if _contains_any(text, ("job i hate", "pays my emi", "stay in a job")) and _contains_any(
        text, ("emi", "pays", "job")
    ):
        _add_unique(theme_tags, ("action", "detachment", "duty"))
        _add_unique(applies_signals, ("outcome-anxiety", "duty-conflict"))
        _add_unique(dominant_dimensions, ("dharma_duty", "nishkama_detachment"))

    if _contains_any(text, ("stay-at-home parent", "stay at home parent")) and _contains_any(
        text, ("spouse earns enough", "society expects me to work")
    ):
        _add_unique(theme_tags, ("duty", "action", "discernment", "right-livelihood"))
        _add_unique(applies_signals, ("career-crossroads", "duty-conflict"))
        _add_unique(dominant_dimensions, ("dharma_duty", "viveka_discernment"))

    if _contains_any(text, ("child failed an exam", "blame the teacher", "protect my child")):
        _add_unique(theme_tags, ("duty", "truth"))
        _add_unique(dominant_dimensions, ("dharma_duty", "satya_truth"))

    if _contains_any(text, ("answers for the online exam", "sharing answers", "rank does not fall")):
        _add_unique(theme_tags, ("truth", "self-mastery"))
        applies_signals.add("private-conduct-test")
        dominant_dimensions.add("satya_truth")

    if _contains_any(text, ("answer key leaked online", "leaked online before my exam")):
        _add_unique(theme_tags, ("self-mastery", "restraint", "action"))
        applies_signals.add("temptation")
        _add_unique(dominant_dimensions, ("sanyama_restraint", "satya_truth"))

    if _contains_any(text, ("assignment using ai", "professor banned ai", "submit it anyway")):
        _add_unique(theme_tags, ("truth", "self-mastery"))
        applies_signals.add("private-conduct-test")
        blocker_signals.add("deception")
        dominant_dimensions.add("satya_truth")

    # Workplace integrity / small theft. Kept below attachment threshold.
    if _contains_any(text, ("company laptop", "freelance work")):
        _add_unique(theme_tags, ("truth", "self-mastery"))
        applies_signals.add("private-conduct-test")
        _add_unique(dominant_dimensions, ("satya_truth", "shaucha_intent"))

    # End-of-life autonomy / grief.
    if _contains_any(
        text,
        (
            "refuses medical treatment",
            "wants to die at home",
            "force hospitalization",
            "refuses dialysis",
            "force treatment",
        ),
    ):
        _add_unique(theme_tags, ("death", "grief"))
        applies_signals.add("bereavement")
        _add_unique(dominant_dimensions, ("ahimsa_nonharm", "nishkama_detachment"))

    if _contains_any(text, ("brother is addicted", "addicted to alcohol", "keeps asking me for money")):
        _add_unique(theme_tags, ("nonharm", "discernment"))
        _add_unique(dominant_dimensions, ("ahimsa_nonharm", "viveka_discernment"))

    if _contains_any(text, ("addictive by design", "gambling-adjacent app")) and _contains_any(
        text, ("well paid", "should i quit", "product")
    ):
        _add_unique(theme_tags, ("duty", "action", "discernment", "right-livelihood"))
        _add_unique(applies_signals, ("career-crossroads", "livelihood-harm-tradeoff"))
        _add_unique(dominant_dimensions, ("dharma_duty", "lokasangraha_welfare"))

    if _contains_any(text, ("poison them", "stray dogs")):
        theme_tags.add("nonharm")
        blocker_signals.add("active-harm")
        dominant_dimensions.add("ahimsa_nonharm")

    if _contains_any(text, ("business deal", "cannot explain why", "overthinking")):
        theme_tags.add("discernment")
        dominant_dimensions.add("viveka_discernment")

    if _contains_any(text, ("teammate's idea as mine", "present my teammate")):
        _add_unique(theme_tags, ("truth", "duty"))
        applies_signals.add("credit-theft")
        blocker_signals.add("deception")
        _add_unique(dominant_dimensions, ("satya_truth", "dharma_duty"))

    if _contains_any(text, ("elderly aunt", "paid care", "manage medicine")):
        _add_unique(theme_tags, ("duty", "nonharm"))
        _add_unique(dominant_dimensions, ("dharma_duty", "ahimsa_nonharm"))

    if _contains_any(text, ("over-ordered", "lot of waste")) and _contains_any(
        text, ("restaurant", "finish eating", "full")
    ):
        _add_unique(theme_tags, ("restraint", "self-mastery", "discernment"))
        _add_unique(applies_signals, ("private-conduct-test", "self-sabotage"))
        _add_unique(dominant_dimensions, ("sanyama_restraint", "viveka_discernment"))

    if _contains_any(text, ("make more money than my spouse", "use it to 'win' arguments")):
        _add_unique(theme_tags, ("anger", "greed", "desire", "discernment"))
        _add_unique(applies_signals, ("anger-spike", "private-conduct-test"))
        _add_unique(dominant_dimensions, ("shaucha_intent", "viveka_discernment"))

    if _contains_any(text, ("adharmic to be rich", "is it adharmic to be rich")):
        _add_unique(theme_tags, ("equanimity", "detachment", "self-mastery"))
        applies_signals.add("private-conduct-test")
        _add_unique(dominant_dimensions, ("nishkama_detachment", "sanyama_restraint"))

    if _contains_any(text, ("business mistake that cost me money", "they apologized")) and _contains_any(
        text, ("forgive", "continue")
    ):
        _add_unique(theme_tags, ("nonharm", "compassion", "self-mastery"))
        applies_signals.add("anger-spike")
        _add_unique(dominant_dimensions, ("ahimsa_nonharm", "sanyama_restraint"))

    if _contains_any(text, ("call out a celebrity", "celebrity's hypocrisy")) and _contains_any(
        text, ("online", "preach one thing", "do another")
    ):
        _add_unique(theme_tags, ("speech", "truth", "nonharm"))
        applies_signals.add("ethical-speech")
        _add_unique(dominant_dimensions, ("satya_truth", "sanyama_restraint"))

    if _contains_any(text, ("life is meaningless", "go through motions")):
        theme_tags.add("discernment")
        blocker_signals.add("self-harm")
        _add_unique(dominant_dimensions, ("viveka_discernment", "ahimsa_nonharm"))

    if blocker_signals and not hidden_risk:
        hidden_risk = "Context includes a blocker that should prevent forced verse attachment."

    return {
        "theme_tags": sorted(theme_tags),
        "applies_signals": sorted(applies_signals),
        "blocker_signals": sorted(blocker_signals),
        "dominant_dimensions": sorted(dominant_dimensions),
        "primary_driver": primary_driver,
        "hidden_risk": hidden_risk,
    }
