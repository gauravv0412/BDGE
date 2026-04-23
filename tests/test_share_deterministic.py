"""Deterministic share-layer refinement (Step 7)."""

from __future__ import annotations

from typing import Any

from app.core.models import (
    CounterfactualBlock,
    Counterfactuals,
    DimensionScore,
    EthicalDimensions,
    ShareLayer,
)
from app.engine.analyzer import analyze_dilemma
from app.share.deterministic import build_refined_share_layer


def _cf() -> Counterfactuals:
    return Counterfactuals(
        clearly_adharmic_version=CounterfactualBlock(
            assumed_context="Same scene; you trim context and borrow urgency as permission.",
            decision="Act now with partial transparency.",
            why="The line moves when accountability becomes optional.",
        ),
        clearly_dharmic_version=CounterfactualBlock(
            assumed_context="Same scene; you verify facts and take one bounded step.",
            decision="Private naming first, then a written follow-up.",
            why="Method keeps truth and restraint paired.",
        ),
    )


def _dims() -> EthicalDimensions:
    def c(n: int) -> DimensionScore:
        return DimensionScore(score=n, note="n" * 12)

    return EthicalDimensions(
        dharma_duty=c(1),
        satya_truth=c(2),
        ahimsa_nonharm=c(1),
        nishkama_detachment=c(0),
        shaucha_intent=c(1),
        sanyama_restraint=c(1),
        lokasangraha_welfare=c(1),
        viveka_discernment=c(1),
    )


def _build(
    dilemma: str,
    *,
    internal: dict[str, str] | None,
    missing: list[str],
) -> dict[str, Any]:
    return build_refined_share_layer(
        dilemma=dilemma,
        classification="Mixed",
        verdict_sentence="[STUB] Mixed trade-offs; narrative pending.",
        internal_driver=internal,
        core_reading="x" * 50,
        gita_analysis="y" * 40,
        verse_match=None,
        closest_teaching="Fallback teaching text long enough for tests here.",
        counterfactuals=_cf(),
        missing_facts=missing,
    )


def test_share_fields_schema_valid_and_question_mark() -> None:
    raw = _build(
        "My manager takes credit for my work in front of leadership; should I correct him publicly?",
        internal={"primary": "Fairness and fear braided.", "hidden_risk": "Wanting the room to see you win."},
        missing=["Is there a written trail of authorship?"],
    )
    sl = ShareLayer.model_validate(raw)
    assert sl.reflective_question.endswith("?")
    assert len(sl.anonymous_share_title) <= 120
    assert len(sl.card_quote) <= 180
    assert len(sl.reflective_question) <= 200
    assert len(sl.anonymous_share_title.strip()) >= 15
    assert len(sl.card_quote.strip()) >= 15


def test_card_quote_not_verdict_echo() -> None:
    verdict = "Exact verdict sentence echo test phrase here."
    raw = build_refined_share_layer(
        dilemma="Synthetic dilemma text for unit test; must be at least twenty characters.",
        classification="Mixed",
        verdict_sentence=verdict,
        internal_driver={"primary": "p" * 15, "hidden_risk": "h" * 15},
        core_reading="c" * 50,
        gita_analysis="g" * 40,
        verse_match=None,
        closest_teaching=None,
        counterfactuals=_cf(),
        missing_facts=[],
    )
    assert raw["card_quote"].strip().lower() != verdict.strip().lower()


def test_share_outputs_differ_across_families() -> None:
    work = _build(
        "My boss rewrites my deliverables with errors; do I push back in email or in person?",
        internal={"primary": "Credibility versus harmony.", "hidden_risk": "Sounding picky."},
        missing=[],
    )
    rel = _build(
        "My partner wants to lend money to their cousin with no written agreement; do I object?",
        internal={"primary": "Trust versus boundaries.", "hidden_risk": "Being the villain."},
        missing=[],
    )
    truth = _build(
        "Should I tell my friend their spouse is cheating based on what I saw?",
        internal={"primary": "Loyalty versus honesty.", "hidden_risk": "Drama as proof of care."},
        missing=[],
    )
    assert work["anonymous_share_title"] != rel["anonymous_share_title"]
    assert work["card_quote"] != truth["card_quote"]
    assert rel["reflective_question"] != truth["reflective_question"]


def test_title_overheard_tone_not_report_label() -> None:
    raw = _build(
        "Office politics: someone spread a rumor about my promotion path and I have receipts.",
        internal={"primary": "Reputation defense.", "hidden_risk": "Humiliation as justice."},
        missing=[],
    )
    t = raw["anonymous_share_title"].lower()
    assert "classification" not in t
    assert "mixed trade" not in t
    assert any(x in t for x in ("anonymous", "slack", "overheard", "desk", "told", "group-chat", "notes-app"))


def test_banned_stub_phrases_absent() -> None:
    raw = _build(
        "I am torn about telling a small lie to protect a colleague from HR scrutiny this week.",
        internal={"primary": "Protection versus complicity.", "hidden_risk": "Moral shortcut."},
        missing=[],
    )
    blob = (raw["anonymous_share_title"] + raw["card_quote"] + raw["reflective_question"]).lower()
    assert "the hard part is method, not drama" not in blob
    assert "which missing fact would most change" not in blob


def test_analyze_dilemma_share_layer_refined(monkeypatch: Any) -> None:
    from app.semantic import scorer as scorer_mod

    monkeypatch.setattr(
        "app.engine.analyzer.semantic_scorer",
        lambda dilemma, use_stub=None: scorer_mod.semantic_scorer(dilemma, use_stub=True),
    )
    out = analyze_dilemma(
        "Work dilemma: my director takes credit for my analysis in executive readouts; what do I do?"
    )
    assert out["share_layer"]["reflective_question"].endswith("?")
    assert "the hard part is method, not drama" not in out["share_layer"]["card_quote"].lower()
