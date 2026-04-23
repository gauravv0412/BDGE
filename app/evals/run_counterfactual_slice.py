"""
Deterministic eval slice for counterfactual refinement (Step 6).

Run:
  PYTHONPATH=. .venv/bin/python -m app.evals.run_counterfactual_slice
"""

from __future__ import annotations

from app.core.models import DimensionScore, EthicalDimensions
from app.counterfactuals.deterministic import build_refined_counterfactuals

CASES: list[tuple[str, str, str, dict[str, int]]] = [
    (
        "My manager takes credit for my work in front of leadership; should I correct him publicly?",
        "Ego and justice braided together.",
        "Choosing the room that makes you feel righteous.",
        {"satya_truth": 2, "sanyama_restraint": -2, "ahimsa_nonharm": -1},
    ),
    (
        "Should I tell my dying grandmother the full truth about her prognosis if the family disagrees?",
        "Compassion versus honesty.",
        "Using kindness as cover for control.",
        {"satya_truth": -1, "ahimsa_nonharm": 2, "dharma_duty": 1},
    ),
    (
        "I could report a friend who is driving uninsured for gig work; it would end their income.",
        "Rule-following versus loyalty.",
        "Moral cleanliness as a shield from discomfort.",
        {"lokasangraha_welfare": 2, "dharma_duty": 1, "ahimsa_nonharm": -1},
    ),
    (
        "A client wants me to omit a known defect in a written summary; my commission depends on closing.",
        "Incentive pressure on disclosure.",
        "Soft fraud described as pragmatism.",
        {"satya_truth": -3, "shaucha_intent": -2, "nishkama_detachment": -2},
    ),
    (
        "My sibling asks me to cover a shift of lies to our parents about where they were last night.",
        "Family peace versus complicity.",
        "Becoming the reliable alibi.",
        {"satya_truth": -2, "dharma_duty": 1, "shaucha_intent": -2},
    ),
    (
        "I want to post an honest but humiliating review under a pseudonym after bad service.",
        "Venting as accountability.",
        "Anonymity as permission to injure.",
        {"ahimsa_nonharm": -2, "satya_truth": 1, "sanyama_restraint": -2},
    ),
    (
        "Should I accept a promotion that will require relocating my kids away from their other parent?",
        "Ambition versus stability.",
        "Framing the trade as inevitable.",
        {"dharma_duty": -1, "lokasangraha_welfare": 1, "nishkama_detachment": -1},
    ),
]


def _dims(**scores: int) -> EthicalDimensions:
    def cell(n: int) -> DimensionScore:
        return DimensionScore(score=n, note="n" * 15)

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


def main() -> None:
    ad_contexts: list[str] = []
    for dilemma, primary, hidden, scores in CASES:
        raw = build_refined_counterfactuals(
            dilemma=dilemma,
            classification="Mixed",
            internal_driver={"primary": primary, "hidden_risk": hidden},
            dimensions=_dims(**scores),
            missing_facts=[],
        )
        ad = raw["clearly_adharmic_version"]
        dh = raw["clearly_dharmic_version"]
        assert ad["assumed_context"] != dh["assumed_context"]
        ad_contexts.append(ad["assumed_context"])
        print("---")
        print(dilemma[:72] + ("…" if len(dilemma) > 72 else ""))
        print("  ad:", ad["decision"][:100])
        print("  dh:", dh["decision"][:100])

    uniq = len(set(ad_contexts))
    print("\nSummary")
    print(f"  cases={len(CASES)} unique_adharmic_assumed_context={uniq}")
    if uniq < max(4, len(CASES) - 1):
        raise SystemExit("Eval slice: adharmic templates too repetitive across cases.")


if __name__ == "__main__":
    main()
