"""
Deterministic share-layer refinement (Step 7).

Builds ``anonymous_share_title``, ``card_quote``, and ``reflective_question``
for screenshot-style sharing, anchored to the dilemma and drivers.

The semantic scorer still supplies share-shaped placeholders for its own
schema validation; ``app/engine/analyzer.py`` replaces them in the final
``WisdomizeEngineOutput``.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

from app.core.models import Counterfactuals, VerseMatch
from app.counterfactuals.deterministic import Family, _clip, _driver_snippets, detect_dilemma_family

# Phrases to avoid (old stub / report tone); tests may assert absence.
_BANNED_GENERIC_SUBSTRINGS = (
    "the hard part is method, not drama",
    "which missing fact would most change",
    "the app said this was mixed",
    "the app said",
)


def _stable_pick(key: str, options: tuple[str, ...]) -> str:
    if not options:
        return ""
    idx = hashlib.sha256(key.encode("utf-8")).digest()[0] % len(options)
    return options[idx]


# Longest first so e.g. "should we" removes before a shorter shared prefix.
_LEADING_QUESTION_STARTERS: tuple[str, ...] = (
    "should we ",
    "should i ",
    "would you ",
    "do i ",
    "am i ",
    "can i ",
)


def _strip_leading_question_starters(text: str) -> str:
    t = text.strip()
    while t:
        low = t.lower()
        stripped = False
        for prefix in _LEADING_QUESTION_STARTERS:
            if low.startswith(prefix):
                t = t[len(prefix) :].strip()
                stripped = True
                break
        if not stripped:
            break
    return t


def _hook_phrase(dilemma: str, *, max_len: int = 52) -> str:
    words = re.sub(r"\s+", " ", (dilemma or "").strip()).split()
    chunk = " ".join(words[:10]) if words else ""
    chunk = _strip_leading_question_starters(chunk)
    h = _clip(chunk, max_len).rstrip(".!?")
    return h if h else "this choice"


def _ensure_question(s: str, *, max_len: int = 200) -> str:
    t = _clip((s or "").strip(), max_len).rstrip()
    if not t.endswith("?"):
        t = t.rstrip(".! ") + "?"
    return _clip(t, max_len)


def _ensure_min_len(s: str, *, min_len: int, pad: str, max_len: int) -> str:
    t = (s or "").strip()
    while len(t) < min_len:
        t = f"{t} {pad}".strip()
    return _clip(t, max_len)


def _title_work(hook: str, key: str) -> str:
    opts = (
        f"Anonymous desk energy: {hook}—who owns calm when credit walks off?",
        f"Slack would not log the real part: {hook}… audience first, or record first?",
        f"Told after a standup: {hook}—truth as relief, or truth as theater?",
    )
    return _stable_pick(key, opts)


def _title_relationship(hook: str, key: str) -> str:
    opts = (
        f"Someone texted: {hook}—loyalty, or accurate witness?",
        f"A group-chat leak vibe: {hook}… peace now, or clarity later?",
        f"Therapist-coded: {hook}—care, or control dressed as care?",
    )
    return _stable_pick(key, opts)


def _title_truth(hook: str, key: str) -> str:
    opts = (
        f"Notes-app at 2am: {hook}—kindness, or a clean ledger?",
        f"Anonymous: {hook}… what can silence buy that disclosure cannot?",
        f"Sent without a name: {hook}—which audience gets the full sentence?",
    )
    return _stable_pick(key, opts)


def _title_general(hook: str, key: str) -> str:
    opts = (
        f"Overheard: {hook}—fast relief versus slow fairness.",
        f"Coffee-shop version: {hook}… which cost are you pretending is small?",
        f"Anonymous: {hook}—what flips if the kindest move were also the clearest?",
    )
    return _stable_pick(key, opts)


def _card_work(key: str) -> str:
    opts = (
        "The slide can be accurate and still become harm if the microphone is the first tool you reach for.",
        "Credit is a fact; how you spend your reputation retrieving it is a choice with interest.",
        "Public truth can be righteous and still train the room to remember your tone, not the theft.",
    )
    return _stable_pick(key, opts)


def _card_relationship(key: str) -> str:
    opts = (
        "Intimacy is not a license to edit someone else's information for your comfort.",
        "Family peace bought with selective silence still has a receipt—someone reads it later.",
        "The gentlest story can still steer someone if they never get to see the full map.",
    )
    return _stable_pick(key, opts)


def _card_truth(key: str) -> str:
    opts = (
        "Softening the sentence for comfort still trains people which cues to trust.",
        "A technically true frame can smuggle a lie if the listener is not free to decide.",
        "Disclosure is not only what you say—it is what you let someone do with the next hour.",
    )
    return _stable_pick(key, opts)


def _card_general(key: str) -> str:
    opts = (
        "Most costly moves are not malice—they are hurry with good adjectives.",
        "The trade is rarely between good and evil; usually it is between fast and fair.",
        "Clarity without restraint becomes noise; restraint without clarity becomes drift.",
    )
    return _stable_pick(key, opts)


def _reflective(
    *,
    family: Family,
    hook: str,
    hidden: str,
    primary: str,
    missing_facts: list[str],
    counterfactuals: Counterfactuals,
    key: str,
) -> str:
    mf = _clip(str(missing_facts[0]), 55) if missing_facts else ""
    dh_hint = _clip(counterfactuals.clearly_dharmic_version.decision, 42).rstrip(".!?") or "a steadier boundary"

    if mf:
        base = (
            f'About "{mf}": would your next step be quieter, braver, or neither—and why?'
            if family == "work"
            else f'If "{mf}" were settled, would you still pick the same audience for the hard sentence?'
        )
    elif family == "relationship":
        base = (
            f"What would you refuse to label as 'just family stuff' if a stranger described {hook}?"
        )
    elif family == "truth_disclosure":
        base = (
            f"Where does {hidden} quietly steer the story if nobody names the first omission aloud?"
        )
    elif family == "work":
        base = (
            f"What are you optimizing for next—being seen as right, or moving the record without owning the room?"
        )
    else:
        base = (
            f"If {hidden} were one sentence on a sticky note, would {primary} still endorse your method?"
        )

    alt = _stable_pick(
        key + ":alt",
        (
            base,
            f"Does the cleaner path—{dh_hint}—feel closer than you want to admit, or farther than it should?",
            f"What is the smallest step that keeps {hook} honest without making harm the delivery vehicle?",
        ),
    )
    return _ensure_question(alt, max_len=200)


def build_refined_share_layer(
    *,
    dilemma: str,
    classification: str,
    verdict_sentence: str,
    internal_driver: dict[str, Any] | None,
    core_reading: str,
    gita_analysis: str,
    verse_match: VerseMatch | None,
    closest_teaching: str | None,
    counterfactuals: Counterfactuals,
    missing_facts: list[str],
) -> dict[str, Any]:
    """
    Return a ``share_layer`` dict valid for ``ShareLayer.model_validate``.

    ``verse_match`` / ``closest_teaching`` are accepted for future hooks; v1
    templates do not quote scripture or verse markers.
    """
    _ = classification, core_reading, gita_analysis, verse_match, closest_teaching

    low_key = (dilemma or "")[:120]
    family = detect_dilemma_family(dilemma)
    hook = _hook_phrase(dilemma)
    primary, hidden = _driver_snippets(internal_driver)

    if family == "work":
        title = _title_work(hook, low_key)
        card = _card_work(low_key)
    elif family == "relationship":
        title = _title_relationship(hook, low_key)
        card = _card_relationship(low_key)
    elif family == "truth_disclosure":
        title = _title_truth(hook, low_key)
        card = _card_truth(low_key)
    else:
        title = _title_general(hook, low_key)
        card = _card_general(low_key)

    vs = (verdict_sentence or "").strip()
    if vs and card.strip().lower() == vs.lower():
        card = _card_general(low_key + ":altcard")

    rq = _reflective(
        family=family,
        hook=hook,
        hidden=hidden,
        primary=primary,
        missing_facts=missing_facts,
        counterfactuals=counterfactuals,
        key=low_key,
    )

    title_out = _ensure_min_len(_clip(title, 120), min_len=15, pad="Same tension, sharper frame.", max_len=120)
    card_out = _ensure_min_len(_clip(card, 180), min_len=15, pad="Method still matters.", max_len=180)
    rq_out = _ensure_question(_clip(rq, 200), max_len=200)

    blob = (title_out + card_out + rq_out).lower()
    for banned in _BANNED_GENERIC_SUBSTRINGS:
        if banned in blob:
            title_out = _clip(f"{title_out} (fresh read.)", 120)
            card_out = _clip(
                "Hurry wears polite language; the cost shows up in what people stop telling you.",
                180,
            )
            rq_out = _ensure_question(
                "What is one fact you could name tomorrow that would make the next step less performative?",
                max_len=200,
            )
            break

    return {
        "anonymous_share_title": title_out,
        "card_quote": card_out,
        "reflective_question": rq_out,
    }
