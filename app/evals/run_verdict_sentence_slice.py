"""
Eval slice for deterministic verdict_sentence quality (Step 9).

Run:
  PYTHONPATH=. .venv/bin/python -m app.evals.run_verdict_sentence_slice
"""

from __future__ import annotations

from collections import Counter

from app.core.models import Classification, DimensionScore, EthicalDimensions
from app.verdict.aggregator import aggregate_verdict


def _uniform_dimensions(score: int) -> EthicalDimensions:
    d = DimensionScore(score=score, note="slice")
    return EthicalDimensions(
        dharma_duty=d,
        satya_truth=d,
        ahimsa_nonharm=d,
        nishkama_detachment=d,
        shaucha_intent=d,
        sanyama_restraint=d,
        lokasangraha_welfare=d,
        viveka_discernment=d,
    )


def main() -> None:
    cases: list[tuple[str, EthicalDimensions, dict[str, object], Classification]] = [
        (
            "My manager takes credit for my work and I want to call him out in the all-hands.",
            _uniform_dimensions(1),
            {},
            Classification.MIXED,
        ),
        (
            "I can hide this audit discrepancy now and patch it after the board meeting.",
            _uniform_dimensions(-5),
            {},
            Classification.ADHARMIC,
        ),
        (
            "My parents want me to lie to relatives about why I left the family business.",
            _uniform_dimensions(5),
            {},
            Classification.DHARMIC,
        ),
        (
            "I found a wallet with cash and no one would know if I kept it.",
            _uniform_dimensions(-5),
            {},
            Classification.ADHARMIC,
        ),
        (
            "Should I relocate for promotion if it disrupts my child's routine with the other parent?",
            _uniform_dimensions(1),
            {},
            Classification.MIXED,
        ),
        (
            "A family asks me to withhold a terminal diagnosis from the patient.",
            _uniform_dimensions(5),
            {},
            Classification.DHARMIC,
        ),
        (
            "A colleague is being extorted, but the reported facts are partial and contradictory.",
            _uniform_dimensions(5),
            {"ambiguity_can_flip_class": True},
            Classification.CONTEXT_DEPENDENT,
        ),
        (
            "I heard conflicting claims about misconduct and only have two weak data points.",
            _uniform_dimensions(5),
            {"scorable_mask": (True, True, True, False, False, False, False, False)},
            Classification.INSUFFICIENT_INFORMATION,
        ),
        (
            "I can exaggerate startup metrics this quarter to keep everyone employed.",
            _uniform_dimensions(-5),
            {},
            Classification.ADHARMIC,
        ),
        (
            "I want to reveal true screenshots because a teammate spread lies about me.",
            _uniform_dimensions(1),
            {},
            Classification.MIXED,
        ),
    ]

    rows: list[tuple[str, Classification, str]] = []
    for dilemma, dims, kwargs, expected_cls in cases:
        out = aggregate_verdict(dims, dilemma, **kwargs)
        cls = out["classification"]
        sentence = out["verdict_sentence"]
        if cls != expected_cls:
            raise SystemExit(f"classification mismatch: expected={expected_cls} got={cls}")
        if len(sentence) > 160:
            raise SystemExit("verdict_sentence exceeds schema max length")
        rows.append((dilemma, cls, sentence))
        print("---")
        print(dilemma[:70] + ("..." if len(dilemma) > 70 else ""))
        print(f"classification={cls}")
        print(f"verdict_sentence={sentence}")

    sentences = [row[2] for row in rows]
    if len(set(sentences)) < 8:
        raise SystemExit("slice diversity failure: verdict_sentence not distinct enough")

    opener_counts = Counter(s.lower().split(" because")[0] for s in sentences)
    top_repeat = max(opener_counts.values())
    if top_repeat > 2:
        raise SystemExit("slice template dominance failure: repeated opener exceeded threshold")

    print("\nSummary")
    print(f"  cases={len(rows)}")
    print(f"  unique_verdict_sentences={len(set(sentences))}")
    print(f"  max_repeated_opener={top_repeat}")


if __name__ == "__main__":
    main()

