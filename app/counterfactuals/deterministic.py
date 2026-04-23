"""
Deterministic counterfactual refinement (Step 6).

Builds ``clearly_adharmic_version`` / ``clearly_dharmic_version`` from the
same situation as the user dilemma, using classification, internal_driver,
ethical dimensions, and missing_facts — without LLM calls.

The live pipeline still runs ``semantic_scorer`` for other fields; the analyzer
overlays counterfactuals with this module so stub and live modes share one
counterfactual shape.
"""

from __future__ import annotations

import re
from typing import Any, Literal

from app.core.models import EthicalDimensions

Family = Literal["work", "relationship", "truth_disclosure", "general"]

_DIM_READABLE: dict[str, str] = {
    "dharma_duty": "duty and role",
    "satya_truth": "truth-telling",
    "ahimsa_nonharm": "non-harm",
    "nishkama_detachment": "attachment to outcomes",
    "shaucha_intent": "motive clarity",
    "sanyama_restraint": "restraint",
    "lokasangraha_welfare": "wider welfare",
    "viveka_discernment": "judgment",
}

_DIM_KEYS: tuple[str, ...] = tuple(_DIM_READABLE)


def _clip(s: str, max_len: int) -> str:
    t = re.sub(r"\s+", " ", (s or "").strip())
    if len(t) <= max_len:
        return t
    cut = t[: max_len - 1].rsplit(" ", 1)[0]
    return (cut or t[:max_len]).rstrip() + "…"


def _ensure_min(s: str, *, min_len: int, pad: str) -> str:
    t = (s or "").strip()
    while len(t) < min_len:
        t = f"{t} {pad}".strip()
    return t


def _situation_spine(dilemma: str, *, max_len: int = 160) -> str:
    """Short, dilemma-anchored spine for 'same situation' framing."""
    raw = re.sub(r"\s+", " ", (dilemma or "").strip())
    if not raw:
        return "the situation you described"
    return _clip(raw, max_len)


def _detect_family(low: str) -> Family:
    def _has_word(token: str) -> bool:
        return bool(re.search(rf"\b{re.escape(token)}\b", low))

    if any(
        _has_word(w)
        for w in (
            "manager",
            "boss",
            "workplace",
            "coworker",
            "colleague",
            "office",
            "promotion",
            "work",
            "job",
            "director",
            "vp",
            "executive",
            "leadership",
            "board",
        )
    ) or "team lead" in low:
        return "work"
    if any(
        _has_word(w)
        for w in (
            "spouse",
            "partner",
            "marriage",
            "parent",
            "mother",
            "father",
            "family",
            "child",
            "relative",
            "ex",
        )
    ) or "divorc" in low:
        return "relationship"
    if any(
        _has_word(w)
        for w in (
            "lie",
            "truth",
            "hide",
            "disclose",
            "secret",
            "conceal",
            "honest",
        )
    ) or "tell them" in low:
        return "truth_disclosure"
    return "general"


def detect_dilemma_family(dilemma: str) -> Family:
    """Public helper for other deterministic stages (e.g. share layer)."""
    return _detect_family((dilemma or "").lower())


def _axis_phrases(dimensions: EthicalDimensions) -> tuple[str, str]:
    pairs: list[tuple[str, int]] = []
    for key in _DIM_KEYS:
        pairs.append((key, int(getattr(dimensions, key).score)))
    neg = sorted(((k, s) for k, s in pairs if s < 0), key=lambda x: x[1])[:2]
    pos = sorted(((k, s) for k, s in pairs if s > 0), key=lambda x: -x[1])[:2]
    neg_label = ", ".join(_DIM_READABLE[k] for k, _ in neg) or "restraint and proportion"
    pos_label = ", ".join(_DIM_READABLE[k] for k, _ in pos) or "clarity and proportion"
    return neg_label, pos_label


def _looks_like_taxonomy_label(text: str) -> bool:
    """
    Suppress curator-style tags (e.g. ``provider-duty``, ``career_crossroads``)
    from user-facing narrative surfaces.
    """
    t = (text or "").strip().lower()
    if not t:
        return False
    if re.fullmatch(r"[a-z0-9]+(?:[-_][a-z0-9]+){1,5}", t):
        return True
    if " " not in t and any(ch in t for ch in ("-", "_")):
        return True
    return False


def _driver_snippets(internal_driver: dict[str, Any] | None) -> tuple[str, str]:
    if not isinstance(internal_driver, dict):
        return "the stated tension", "an unnamed rationalization"
    primary = _clip(str(internal_driver.get("primary", "")), 90).rstrip(".!?")
    hidden = _clip(str(internal_driver.get("hidden_risk", "")), 90).rstrip(".!?")
    if _looks_like_taxonomy_label(primary):
        primary = ""
    if _looks_like_taxonomy_label(hidden):
        hidden = ""
    if not primary:
        primary = "the stated tension"
    if not hidden:
        hidden = "a story that makes delay feel reasonable"
    return primary, hidden


def _missing_facts_tail(missing_facts: list[str]) -> str:
    facts = [str(x).strip() for x in missing_facts if str(x).strip()][:2]
    if not facts:
        return ""
    joined = "; ".join(_clip(f, 70) for f in facts)
    return _clip(f"You still lack key facts ({joined}), so the move stays provisional.", 200)


def _templates(family: Family) -> tuple[tuple[str, str, str], tuple[str, str, str]]:
    """(assumed_context, decision, why) for adharmic, then dharmic."""
    if family == "work":
        ad = (
            "Same workplace stakes: {spine} — here you let {hidden} steer the method—"
            "public cornering, selective omission, or quiet sabotage—while sounding blameless.",
            "Win the room or the narrative first; fix the record only if forced.",
            "The line moves when truth becomes a tactic and {neg_axis} drives timing. "
            "Collateral damage to trust stops being part of the calculation.",
        )
        dh = (
            "Same workplace stakes: {spine} — here you keep the grievance real but route it: "
            "private naming, dated evidence, escalation along the org norm—not ambush.",
            "Private specificity first, written follow-up, public only as a bounded last step.",
            "Same facts, safer vehicle. {pos_axis} stays in the loop so the correction does not "
            "become the headline you did not intend.",
        )
        return ad, dh
    if family == "relationship":
        ad = (
            "Same relationship field: {spine} — here {hidden} becomes the script: "
            "you triangulate, withhold selectively, or press for a win while calling it care.",
            "Optimize for relief or leverage now; let clarity arrive later if at all.",
            "The line moves when intimacy or duty becomes cover for control. "
            "{neg_axis} quietly runs the decision.",
        )
        dh = (
            "Same relationship field: {spine} — here you slow the tempo: name what is true, "
            "name what is unknown, and choose a bounded next step that {primary} would respect.",
            "One honest conversation with specifics, then space or support—not a courtroom.",
            "The upgrade is method: {pos_axis} constrains how hard you press while staying truthful.",
        )
        return ad, dh
    if family == "truth_disclosure":
        ad = (
            "Same facts on the table: {spine} — here you soften edges to reduce discomfort—"
            "strategic silence, technically true framing that misleads, or delay until the window closes.",
            "Manage perception first; treat full disclosure as optional if awkward.",
            "The line moves when convenience edits what others need to decide fairly. "
            "{neg_axis} becomes negotiable.",
        )
        dh = (
            "Same facts on the table: {spine} — here you separate *what is known* from *what you fear*—"
            "then disclose in a proportionate channel with room for questions.",
            "Plain account first, compassion in timing and tone—not compassion as erasure.",
            "The upgrade keeps truth and care in the same story. {pos_axis} sets the guardrails.",
        )
        return ad, dh
    # general
    ad = (
        "Same scene: {spine} — here {hidden} quietly sets the pace: you trim context, "
        "borrow legitimacy from urgency, and treat {neg_axis} as optional detail.",
        "Move now with partial transparency; tidy the record later if pressed.",
        "The line moves when method stops being accountable. The slip is believable because it feels efficient.",
    )
    dh = (
        "Same scene: {spine} — here you let {primary} set the *how*, not just the *whether*: "
        "verify, bound the next step, and keep {pos_axis} visible in the choice.",
        "One bounded, reviewable move before anything irreversible.",
        "The upgrade is procedural: same situation, clearer safeguards—so the trade you are in stays honest.",
    )
    return ad, dh


def build_refined_counterfactuals(
    *,
    dilemma: str,
    classification: str,
    internal_driver: dict[str, Any] | None,
    dimensions: EthicalDimensions,
    missing_facts: list[str],
) -> dict[str, Any]:
    """
    Return a ``counterfactuals`` dict matching engine / semantic schema bounds.
    """
    low = (dilemma or "").lower()
    family = _detect_family(low)
    spine = _situation_spine(dilemma)
    primary, hidden = _driver_snippets(internal_driver)
    neg_axis, pos_axis = _axis_phrases(dimensions)
    miss_tail = _missing_facts_tail(missing_facts)

    (ac_a, dec_a, why_a), (ac_d, dec_d, why_d) = _templates(family)

    def _fill(template: str) -> str:
        return template.format(
            spine=spine,
            primary=primary,
            hidden=hidden,
            neg_axis=neg_axis,
            pos_axis=pos_axis,
            classification=classification,
        )

    ac_ad = _fill(ac_a)
    ac_dh = _fill(ac_d)
    if miss_tail:
        ac_dh = _clip(f"{ac_dh} {miss_tail}", 400)

    out = {
        "clearly_adharmic_version": {
            "assumed_context": _clip(
                _ensure_min(_clip(ac_ad, 400), min_len=30, pad="Same situation, sharper tilt."),
                400,
            ),
            "decision": _clip(_ensure_min(_clip(_fill(dec_a), 200), min_len=10, pad="A riskier move."), 200),
            "why": _clip(_ensure_min(_clip(_fill(why_a), 300), min_len=20, pad="Motive and method shift the line."), 300),
        },
        "clearly_dharmic_version": {
            "assumed_context": _clip(
                _ensure_min(_clip(ac_dh, 400), min_len=30, pad="Same situation, cleaner method."),
                400,
            ),
            "decision": _clip(_ensure_min(_clip(_fill(dec_d), 200), min_len=10, pad="A steadier move."), 200),
            "why": _clip(_ensure_min(_clip(_fill(why_d), 300), min_len=20, pad="Restraint and truth stay paired."), 300),
        },
    }
    if any(w in low for w in ("suicide", "self-harm", "kill myself")):
        why_d0 = out["clearly_dharmic_version"]["why"]
        tail = " If you are unsafe, use crisis or professional support."
        out["clearly_dharmic_version"]["why"] = _clip(f"{why_d0}{tail}", 300)
    return out
