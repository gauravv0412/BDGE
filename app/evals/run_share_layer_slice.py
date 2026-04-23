"""
Deterministic eval slice for share-layer refinement (Step 7).

Run:
  PYTHONPATH=. .venv/bin/python -m app.evals.run_share_layer_slice
"""

from __future__ import annotations

from app.core.models import CounterfactualBlock, Counterfactuals
from app.share.deterministic import build_refined_share_layer

CASES: list[tuple[str, dict[str, str], list[str]]] = [
    (
        "My manager takes credit for my work in front of leadership; should I correct him publicly?",
        {"primary": "Justice braided with ego.", "hidden_risk": "Wanting the room to see you win."},
        ["Is there a paper trail?"],
    ),
    (
        "My parents want me to lie to relatives about why I left the family business.",
        {"primary": "Peace versus honesty.", "hidden_risk": "Peace as silence."},
        [],
    ),
    (
        "Should I hide a material error from the audit committee to protect my team?",
        {"primary": "Team protection.", "hidden_risk": "Soft fraud as pragmatism."},
        ["What is the error magnitude?"],
    ),
    (
        "A colleague is spreading false rumors; I have true but humiliating screenshots to post.",
        {"primary": "Reputation.", "hidden_risk": "Revenge as truth."},
        [],
    ),
    (
        "My startup asks me to exaggerate metrics to investors; refusing may sink the round.",
        {"primary": "Survival versus honesty.", "hidden_risk": "Culture as excuse."},
        [],
    ),
    (
        "We disagree on telling our teenager we are considering reconciliation after separation.",
        {"primary": "Co-parent coordination.", "hidden_risk": "Using the child as messenger."},
        [],
    ),
    (
        "I found a wallet with ID; I could keep the cash or return it through the police.",
        {"primary": "Temptation.", "hidden_risk": "Self-story."},
        [],
    ),
    (
        "Should I accept a promotion that relocates my kids away from their other parent?",
        {"primary": "Ambition versus stability.", "hidden_risk": "Framing as inevitable."},
        ["What custody arrangement exists?"],
    ),
]


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


def main() -> None:
    titles: list[str] = []
    cards: list[str] = []
    for dilemma, internal, missing in CASES:
        raw = build_refined_share_layer(
            dilemma=dilemma,
            classification="Mixed",
            verdict_sentence="[STUB] Mixed trade-offs; narrative pending.",
            internal_driver=internal,
            core_reading="c" * 50,
            gita_analysis="g" * 40,
            verse_match=None,
            closest_teaching=None,
            counterfactuals=_cf(),
            missing_facts=missing,
        )
        assert raw["reflective_question"].endswith("?")
        titles.append(raw["anonymous_share_title"])
        cards.append(raw["card_quote"])
        print("---")
        print(dilemma[:70] + ("…" if len(dilemma) > 70 else ""))
        print(" title:", raw["anonymous_share_title"][:100])
        print(" card: ", raw["card_quote"][:90] + ("…" if len(raw["card_quote"]) > 90 else ""))

    ut = len(set(titles))
    uc = len(set(cards))
    print("\nSummary")
    print(f"  cases={len(CASES)} unique_titles={ut} unique_card_quotes={uc}")
    if ut < 5 or uc < 4:
        raise SystemExit("Share slice: too much template repetition across cases.")


if __name__ == "__main__":
    main()
