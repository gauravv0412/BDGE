"""
Deterministic refinement for ``if_you_continue`` and ``higher_path`` (Step 8).

Semantic JSON still carries placeholder-shaped text for schema validation;
``app/engine/analyzer.py`` replaces these fields in the final output.
"""

from __future__ import annotations

import hashlib
from typing import Any

from app.core.models import Counterfactuals, EthicalDimensions, VerseMatch
from app.counterfactuals.deterministic import _clip, _driver_snippets, detect_dilemma_family

_BANNED_SUBSTRINGS = (
    "tension may rise briefly",
    "ambiguity in expectations",
    "consistent decision process",
    "name the core duty, state the truth plainly",
    "document key facts before acting",
)


def _pick(key: str, options: tuple[str, ...]) -> str:
    if not options:
        return ""
    idx = hashlib.sha256(key.encode("utf-8")).digest()[0] % len(options)
    return options[idx]


def _ensure_min(s: str, *, min_len: int, pad: str, max_len: int) -> str:
    t = (s or "").strip()
    while len(t) < min_len:
        t = f"{t} {pad}".strip()
    return _clip(t, max_len)


def _scrub_generic(blob: str) -> str:
    low = blob.lower()
    for banned in _BANNED_SUBSTRINGS:
        if banned in low:
            return (
                "You keep buying runway with tighter stories; the invoice shows up in who still calls you "
                "for the hard facts."
            )
    return blob


def build_refined_if_you_continue(
    *,
    dilemma: str,
    classification: str,
    internal_driver: dict[str, Any] | None,
    dimensions: EthicalDimensions,
    missing_facts: list[str],
    counterfactuals: Counterfactuals,
    verse_match: VerseMatch | None,
    closest_teaching: str | None,
) -> dict[str, str]:
    _ = classification, dimensions, missing_facts, counterfactuals, verse_match, closest_teaching
    family = detect_dilemma_family(dilemma)
    key = (dilemma or "")[:120]
    _, hidden = _driver_snippets(internal_driver)
    hidden_bit = _clip(hidden, 70)

    if family == "work":
        short_opts = (
            "Same week: tighter smiles, more forwarded threads, and the argument you rehearse in the shower instead of sleeping.",
            "Immediate cost is social heat—people clock your tone before they re-open the spreadsheet.",
            "You trade focus for vigilance: small wins in meetings, larger tabs kept open on who said what.",
        )
        long_opts = (
            "The pattern can harden into who is 'safe to borrow credit from'—your fairness gets priced as a personality trait.",
            "What people remember is how pressure felt in the room; the factual record stops being the headline.",
            "Teams quietly route around you if the story becomes 'hard to work with' even when you were right on paper.",
        )
    elif family == "relationship":
        short_opts = (
            "Relief if you vent sideways: someone else carries the stress as gossip instead of as information.",
            "Short term you win quiet at the dinner table; the hardest sentence does not get spoken where it belongs.",
            "You buy a few calm days by tightening the family narrative—then the next surprise lands louder.",
        )
        long_opts = (
            "Trust becomes positional: who is 'in' on edits to the story, and which facts stop traveling with the kids.",
            "The workaround becomes habit—honesty deferred until 'after the holidays' becomes its own kind of policy.",
            "People learn what not to ask you; intimacy shrinks to what can be safely performed.",
        )
    elif family == "truth_disclosure":
        short_opts = (
            "The uncomfortable sentence passes; what lingers is who learned last—and who got to choreograph surprise.",
            "Short term you manage faces; you also train everyone on which channels are 'safe' for real news.",
            "You get fewer pointed questions, more careful wording around you—politeness as distance.",
        )
        long_opts = (
            "Small omissions become muscle memory; later truths land as betrayal even when they are finally accurate.",
            "The ledger of what was withheld becomes the relationship's hidden balance sheet.",
            "People stop testing your transparency because they stop expecting it.",
        )
    else:
        short_opts = (
            "You buy days of relief by polishing your inner narration and dodging the one detail you do not want said aloud.",
            "Immediate cost is mental bandwidth: the move you almost took keeps replaying as a cleaner version.",
            "Short term the room relaxes; you pay in private rumination and sharper self-editing.",
        )
        long_opts = (
            "The workaround becomes character: faster stories, cleaner self-image, a smaller circle that actually knows what is true.",
            "What starts as a one-time smoothing becomes the default tool whenever stakes rise.",
            "You get fluent at plausible deniability—not as a villain move, but as a fatigue move.",
        )

    short = _pick(key, short_opts)
    long = _pick(key + ":lt", long_opts)
    if hidden_bit and family != "truth_disclosure":
        short = _clip(f"{short} ({hidden_bit} gets louder when nothing is named.)", 400)
    out = {
        "short_term": _ensure_min(_clip(_scrub_generic(short), 400), min_len=20, pad="Observable costs show up quickly.", max_len=400),
        "long_term": _ensure_min(_clip(_scrub_generic(long), 400), min_len=20, pad="Patterns outlive single decisions.", max_len=400),
    }
    return out


def build_refined_higher_path(
    *,
    dilemma: str,
    classification: str,
    internal_driver: dict[str, Any] | None,
    dimensions: EthicalDimensions,
    missing_facts: list[str],
    counterfactuals: Counterfactuals,
    verse_match: VerseMatch | None,
    closest_teaching: str | None,
) -> str:
    _ = classification, dimensions, missing_facts, verse_match, closest_teaching
    family = detect_dilemma_family(dilemma)
    key = (dilemma or "")[:120]
    primary, hidden = _driver_snippets(internal_driver)

    if family == "work":
        opts = (
            "List three dated receipts of your work, request a 1:1 with the narrow claim, then escalate only along the written path your org already advertises—no ambush, no side-channel dossier.",
            "Put the dispute in one email thread with specifics and dates; ask for a correction window; if none, attach the same packet to whoever owns integrity reviews—keep the audience shrinking, not growing.",
            "Treat 'being right' as a logistics problem: who must hear it first, on what timeline, with what artifact—then stop when the logistics are done, not when the feeling is done.",
        )
    elif family == "relationship":
        opts = (
            "Tell the one person who truly needs the fact first, in one sitting, with no audience; refuse to triangulate through kids or group chats; schedule a second conversation instead of a second performance.",
            "Write a short paragraph you would stand by if forwarded—then send it once, to the smallest circle that can act on it; let silence after that be a choice, not a dodge.",
            "Name the trade in one sentence your future self would sign; pick the channel that protects dignity more than drama; end with a clear next date, not a moral flourish.",
        )
    elif family == "truth_disclosure":
        opts = (
            "Separate what you know from what you fear saying; choose the smallest accurate disclosure that still preserves consent; offer a follow-up window instead of dumping the whole file at once.",
            "Put the hardest true sentence in the smallest room that can handle it; leave space for questions; refuse 'technically true' frames that steer more than they inform.",
            "If silence has been doing work, replace it with a dated, bounded plan: who learns what, by when, with what support—then stop selling the plan as kindness.",
        )
    else:
        opts = (
            "Write the next move as if it could be read aloud: one timestamp, one audience, one ask, one boundary—then stop.",
            "Name {primary} without adjectives for sixty seconds on paper; delete the story lines; pick the smallest external step that still matches what is left.".format(
                primary=_clip(primary, 80)
            ),
            "Before you act, write {hidden} as a single observable sentence; strip blame; choose the channel where repair is still possible—not the channel where you win.".format(
                hidden=_clip(hidden, 70)
            ),
        )

    hp = _pick(key + ":hp", opts)
    hp = _clip(_scrub_generic(hp), 500)

    dh = counterfactuals.clearly_dharmic_version
    if len(dh.decision) > 15 and dh.decision.lower() in hp.lower():
        alt = tuple(o for o in opts if dh.decision.lower() not in o.lower()) or opts
        hp = _pick(key + ":hp2", alt)
        hp = _clip(_scrub_generic(hp), 500)

    return _ensure_min(hp, min_len=30, pad="Pick one bounded, reviewable step that matches the facts you already have.", max_len=500)
