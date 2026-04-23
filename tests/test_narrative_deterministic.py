"""Deterministic if_you_continue and higher_path (Step 8)."""

from __future__ import annotations

from typing import Any

from app.core.models import (
    CounterfactualBlock,
    Counterfactuals,
    DimensionScore,
    EthicalDimensions,
    IfYouContinue,
)
from app.engine.analyzer import analyze_dilemma
from app.narrative.deterministic import build_refined_higher_path, build_refined_if_you_continue


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
        satya_truth=c(1),
        ahimsa_nonharm=c(1),
        nishkama_detachment=c(0),
        shaucha_intent=c(1),
        sanyama_restraint=c(1),
        lokasangraha_welfare=c(1),
        viveka_discernment=c(1),
    )


def _build_iyc(dilemma: str, internal: dict[str, str] | None) -> dict[str, str]:
    return build_refined_if_you_continue(
        dilemma=dilemma,
        classification="Mixed",
        internal_driver=internal,
        dimensions=_dims(),
        missing_facts=[],
        counterfactuals=_cf(),
        verse_match=None,
        closest_teaching=None,
    )


def test_if_you_continue_schema_valid_and_distinct() -> None:
    raw = _build_iyc(
        "My manager takes credit for my work in leadership meetings; should I push back?",
        internal={"primary": "Fairness and reputation.", "hidden_risk": "Wanting a public win."},
    )
    iyc = IfYouContinue.model_validate(raw)
    assert iyc.short_term.strip()
    assert iyc.long_term.strip()
    assert iyc.short_term != iyc.long_term
    assert len(iyc.short_term) <= 400
    assert len(iyc.long_term) <= 400


def test_higher_path_not_counterfactual_copy() -> None:
    cf = _cf()
    hp = build_refined_higher_path(
        dilemma="Synthetic dilemma text for unit test; must be at least twenty characters.",
        classification="Mixed",
        internal_driver={"primary": "p" * 15, "hidden_risk": "h" * 15},
        dimensions=_dims(),
        missing_facts=[],
        counterfactuals=cf,
        verse_match=None,
        closest_teaching=None,
    )
    assert len(hp) <= 500
    assert len(hp) >= 30
    assert hp.strip().lower() != cf.clearly_dharmic_version.decision.strip().lower()
    assert hp.strip().lower() != cf.clearly_dharmic_version.assumed_context.strip().lower()
    assert "private naming first" not in hp.lower()


def test_outputs_differ_across_families() -> None:
    work = _build_iyc(
        "My director rewrites my slides with errors before the board meeting.",
        internal={"primary": "Credibility.", "hidden_risk": "Sounding insubordinate."},
    )
    rel = _build_iyc(
        "My sibling wants me to cover for them with our parents about last weekend.",
        internal={"primary": "Loyalty.", "hidden_risk": "Becoming the alibi."},
    )
    truth = _build_iyc(
        "Should I tell my team the full scope of the layoff risk before HR signs off?",
        internal={"primary": "Transparency.", "hidden_risk": "Panic."},
    )
    assert work["short_term"] != rel["short_term"]
    assert rel["long_term"] != truth["long_term"]


def test_banned_stub_phrases_absent() -> None:
    raw = _build_iyc(
        "I could report a safety issue at work but fear retaliation from my supervisor.",
        internal={"primary": "Duty versus fear.", "hidden_risk": "Silence as safety."},
    )
    blob = (raw["short_term"] + raw["long_term"]).lower()
    assert "tension may rise briefly" not in blob
    assert "consistent decision process" not in blob


def test_analyze_dilemma_narrative_refined(monkeypatch: Any) -> None:
    from app.semantic import scorer as scorer_mod

    monkeypatch.setattr(
        "app.engine.analyzer.semantic_scorer",
        lambda dilemma, use_stub=None: scorer_mod.semantic_scorer(dilemma, use_stub=True),
    )
    out = analyze_dilemma(
        "Work dilemma: my VP presents my analysis as theirs in executive sessions; what should I do first?"
    )
    assert out["if_you_continue"]["short_term"] != out["if_you_continue"]["long_term"]
    assert "name the core duty, state the truth plainly" not in out["higher_path"].lower()
    assert len(out["higher_path"]) >= 30
