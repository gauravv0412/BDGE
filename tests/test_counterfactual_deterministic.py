"""Deterministic counterfactual refinement (Step 6)."""

from __future__ import annotations

from app.core.models import Counterfactuals, DimensionScore, EthicalDimensions
from app.counterfactuals.deterministic import build_refined_counterfactuals, detect_dilemma_family
from app.engine.analyzer import analyze_dilemma


def _dims(**scores: int) -> EthicalDimensions:
    def cell(n: int) -> DimensionScore:
        return DimensionScore(score=n, note="x" * 12)

    return EthicalDimensions(
        dharma_duty=cell(scores.get("dharma_duty", 0)),
        satya_truth=cell(scores.get("satya_truth", 0)),
        ahimsa_nonharm=cell(scores.get("ahimsa_nonharm", 0)),
        nishkama_detachment=cell(scores.get("nishkama_detachment", 0)),
        shaucha_intent=cell(scores.get("shaucha_intent", 0)),
        sanyama_restraint=cell(scores.get("sanyama_restraint", 0)),
        lokasangraha_welfare=cell(scores.get("lokasangraha_welfare", 0)),
        viveka_discernment=cell(scores.get("viveka_discernment", 0)),
    )


def test_counterfactuals_are_non_empty_and_schema_valid() -> None:
    dilemma = (
        "My manager takes credit for my deliverables in leadership meetings. "
        "Should I call it out publicly in the next all-hands?"
    )
    raw = build_refined_counterfactuals(
        dilemma=dilemma,
        classification="Mixed",
        internal_driver={
            "primary": "Fairness braided with fear of being seen as difficult.",
            "hidden_risk": "Letting the story become about your tone, not the theft.",
        },
        dimensions=_dims(satya_truth=2, sanyama_restraint=-2, ahimsa_nonharm=-1),
        missing_facts=["Is there a written trail of your contributions?"],
    )
    cf = Counterfactuals.model_validate(raw)
    for side in (cf.clearly_adharmic_version, cf.clearly_dharmic_version):
        assert len(side.assumed_context) >= 30
        assert len(side.decision) >= 10
        assert len(side.why) >= 20
        assert len(side.assumed_context) <= 400
        assert len(side.decision) <= 200
        assert len(side.why) <= 300


def test_adharmic_and_dharmic_are_distinct_and_situation_anchored() -> None:
    dilemma = (
        "I found out my sibling has been lying to our parents about debt. "
        "Do I tell them before the holidays or wait?"
    )
    raw = build_refined_counterfactuals(
        dilemma=dilemma,
        classification="Context-dependent",
        internal_driver={
            "primary": "Protecting parents from shock versus enabling silence.",
            "hidden_risk": "Using 'timing' to avoid being the messenger.",
        },
        dimensions=_dims(satya_truth=1, ahimsa_nonharm=1, shaucha_intent=-2),
        missing_facts=[],
    )
    ad = raw["clearly_adharmic_version"]
    dh = raw["clearly_dharmic_version"]
    assert ad["decision"] != dh["decision"]
    assert ad["assumed_context"] != dh["assumed_context"]
    assert ad["why"] != dh["why"]
    spine = dilemma[:40].lower()
    assert spine in ad["assumed_context"].lower()
    assert spine in dh["assumed_context"].lower()


def test_counterfactuals_not_generic_stub_phrases() -> None:
    """Old semantic stub used these exact phrases; engine output should not."""
    raw = build_refined_counterfactuals(
        dilemma="Synthetic dilemma text for unit test; must be at least twenty characters.",
        classification="Mixed",
        internal_driver={"primary": "p" * 15, "hidden_risk": "h" * 15},
        dimensions=_dims(),
        missing_facts=[],
    )
    blob = str(raw).lower()
    assert "proceed through concealment" not in blob
    assert "transparent communication and documented safeguards" not in blob


def test_why_references_tension_axes_when_scores_present() -> None:
    raw = build_refined_counterfactuals(
        dilemma="Should I hide a material error from the audit committee to protect my team?",
        classification="Mixed",
        internal_driver={"primary": "Team protection versus institutional truth.", "hidden_risk": "Hero narrative."},
        dimensions=_dims(satya_truth=-3, shaucha_intent=-2, dharma_duty=2),
        missing_facts=[],
    )
    assert "truth-telling" in raw["clearly_adharmic_version"]["why"].lower()


def test_analyze_dilemma_counterfactuals_differ_across_dilemmas(monkeypatch: object) -> None:
    from app.semantic import scorer as scorer_mod

    def _stub(dilemma: str, *, use_stub: bool | None = None) -> dict:
        return scorer_mod.semantic_scorer(dilemma, use_stub=True)

    monkeypatch.setattr("app.engine.analyzer.semantic_scorer", _stub)
    a = analyze_dilemma(
        "Work dilemma: my director rewrites my slides with errors; do I fix them quietly or push back?"
    )
    b = analyze_dilemma(
        "Relationship dilemma: my partner wants to lend money to their cousin without a written agreement."
    )
    ac_a = a["counterfactuals"]["clearly_adharmic_version"]["assumed_context"]
    ac_b = b["counterfactuals"]["clearly_adharmic_version"]["assumed_context"]
    assert ac_a != ac_b


def test_eval_slice_no_template_domination() -> None:
    """Representative dilemmas: adharmic assumed_contexts should not collapse to one string."""
    specs = [
        (
            "The VP asked me to misstate our pipeline in an investor email. Refusing may cost my bonus.",
            "Coercion versus truth at work.",
            "Fear of being replaced.",
        ),
        (
            "My ex and I disagree on whether to tell our teenager we are considering reconciliation.",
            "Co-parent coordination.",
            "Using the child as a pressure point.",
        ),
        (
            "I could return the lost phone I found, or sell it; the owner might never trace it.",
            "Temptation versus straightforward return.",
            "Rationalizing convenience as fairness.",
        ),
        (
            "A colleague spread a rumor about me; I have receipts that would embarrass them if I posted.",
            "Reputation defense.",
            "Humiliation disguised as truth-telling.",
        ),
        (
            "My parents insist I lie to relatives about why I left the family business.",
            "Loyalty versus honesty.",
            "Peace bought with ongoing falsehood.",
        ),
        (
            "I want to disclose a safety issue on my team, but HR has warned whistleblowers before.",
            "Protection versus retaliation risk.",
            "Treating silence as neutrality.",
        ),
    ]
    bodies: list[str] = []
    for dilemma, primary, hidden in specs:
        raw = build_refined_counterfactuals(
            dilemma=dilemma,
            classification="Mixed",
            internal_driver={"primary": primary, "hidden_risk": hidden},
            dimensions=_dims(satya_truth=1, ahimsa_nonharm=1, nishkama_detachment=-1),
            missing_facts=[],
        )
        ad = raw["clearly_adharmic_version"]["assumed_context"]
        dh = raw["clearly_dharmic_version"]["assumed_context"]
        assert ad != dh
        assert len(set(ad.split())) > 12
        bodies.append(ad)
    assert len(set(bodies)) >= 5, "adharmic contexts should mostly diverge across dilemmas"


def test_family_detection_word_boundary_avoids_ex_in_next() -> None:
    family = detect_dilemma_family(
        "I need to decide the next step after a contract dispute with no relationship context."
    )
    assert family != "relationship"
