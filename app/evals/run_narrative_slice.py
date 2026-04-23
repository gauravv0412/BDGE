"""
Eval slice for deterministic if_you_continue / higher_path (Step 8).

Run:
  PYTHONPATH=. .venv/bin/python -m app.evals.run_narrative_slice
"""

from __future__ import annotations

from app.core.models import CounterfactualBlock, Counterfactuals, DimensionScore, EthicalDimensions
from app.narrative.deterministic import build_refined_higher_path, build_refined_if_you_continue


CASES: list[tuple[str, dict[str, str]]] = [
    (
        "My manager takes credit for my work in front of leadership; should I correct him publicly?",
        {"primary": "Justice and ego braided.", "hidden_risk": "Wanting the room to see you win."},
    ),
    (
        "My parents want me to lie to relatives about why I left the family business.",
        {"primary": "Peace versus honesty.", "hidden_risk": "Peace bought with silence."},
    ),
    (
        "Should I hide a material error from the audit committee to protect my team?",
        {"primary": "Protection.", "hidden_risk": "Soft fraud as pragmatism."},
    ),
    (
        "A colleague spreads false rumors; I have true but humiliating screenshots I could post.",
        {"primary": "Reputation.", "hidden_risk": "Revenge as truth."},
    ),
    (
        "My startup asks me to exaggerate metrics to investors; refusing may sink the round.",
        {"primary": "Survival versus honesty.", "hidden_risk": "Culture as excuse."},
    ),
    (
        "We disagree on telling our teenager we are considering reconciliation after separation.",
        {"primary": "Co-parent coordination.", "hidden_risk": "Using the child as messenger."},
    ),
    (
        "I found a wallet with ID; I could keep the cash or return it through the police.",
        {"primary": "Temptation.", "hidden_risk": "Self-story."},
    ),
    (
        "Should I accept a promotion that relocates my kids away from their other parent?",
        {"primary": "Ambition versus stability.", "hidden_risk": "Framing as inevitable."},
    ),
]


def _cf() -> Counterfactuals:
    return Counterfactuals(
        clearly_adharmic_version=CounterfactualBlock(
            assumed_context="x" * 35,
            decision="y" * 12,
            why="z" * 22,
        ),
        clearly_dharmic_version=CounterfactualBlock(
            assumed_context="a" * 35,
            decision=(
                "List three dated receipts of your work, request a 1:1 with the narrow claim, then escalate only "
                "along the written path your org already advertises—no ambush, no side-channel dossier."
            ),
            why="c" * 22,
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


def main() -> None:
    st: list[str] = []
    lt: list[str] = []
    hp: list[str] = []
    for dilemma, internal in CASES:
        iyc = build_refined_if_you_continue(
            dilemma=dilemma,
            classification="Mixed",
            internal_driver=internal,
            dimensions=_dims(),
            missing_facts=[],
            counterfactuals=_cf(),
            verse_match=None,
            closest_teaching=None,
        )
        h = build_refined_higher_path(
            dilemma=dilemma,
            classification="Mixed",
            internal_driver=internal,
            dimensions=_dims(),
            missing_facts=[],
            counterfactuals=_cf(),
            verse_match=None,
            closest_teaching=None,
        )
        assert iyc["short_term"] != iyc["long_term"]
        assert len(h) >= 30
        st.append(iyc["short_term"])
        lt.append(iyc["long_term"])
        hp.append(h)
        print("---")
        print(dilemma[:64] + ("…" if len(dilemma) > 64 else ""))
        print(" st:", iyc["short_term"][:90] + "…")
        print(" hp:", h[:90] + "…")

    overlap = sum(1 for a, b in zip(st, lt, strict=True) if a[:40] == b[:40])
    print("\nSummary")
    print(f"  cases={len(CASES)} unique_short_term={len(set(st))} unique_long_term={len(set(lt))} unique_higher_path={len(set(hp))}")
    print(f"  short_vs_long_same_prefix_pairs={overlap}")

    # Ensure higher_path de-dup guard is exercised when dharmic decision is long and template-like.
    dedup_probe = build_refined_higher_path(
        dilemma="My manager takes credit for my work in front of leadership; should I correct him publicly?",
        classification="Mixed",
        internal_driver={"primary": "Justice and ego braided.", "hidden_risk": "Wanting the room to see you win."},
        dimensions=_dims(),
        missing_facts=[],
        counterfactuals=_cf(),
        verse_match=None,
        closest_teaching=None,
    )
    assert dedup_probe.strip().lower() != _cf().clearly_dharmic_version.decision.strip().lower()

    if len(set(st)) < 5 or len(set(lt)) < 5 or len(set(hp)) < 4:
        raise SystemExit("Narrative slice: insufficient cross-case diversity.")
    if overlap > 2:
        raise SystemExit("Narrative slice: short/long too often share the same opening.")


if __name__ == "__main__":
    main()
