"""Tests for deterministic verse retriever selection."""

from __future__ import annotations

from typing import Any

from app.core.benchmark_loader import load_dilemmas
from app.core.models import DimensionScore, EthicalDimensions
from app.engine.analyzer import analyze_dilemma
from app.evals.run_verse_retrieval_benchmarks import _build_context
from app.verses.loader import load_curated_verses
from app.verses.retriever import (
    _infer_applies_signals,
    _infer_blocker_signals,
    _infer_theme_tags,
    retrieve_verse,
)
from app.verses.scorer import RetrievalContext
from app.verses.types import DimensionKey


def _dimensions() -> EthicalDimensions:
    return EthicalDimensions(
        dharma_duty=DimensionScore(score=3, note="duty"),
        satya_truth=DimensionScore(score=1, note="truth"),
        ahimsa_nonharm=DimensionScore(score=0, note="nonharm"),
        nishkama_detachment=DimensionScore(score=4, note="detachment"),
        shaucha_intent=DimensionScore(score=0, note="intent"),
        sanyama_restraint=DimensionScore(score=3, note="restraint"),
        lokasangraha_welfare=DimensionScore(score=0, note="welfare"),
        viveka_discernment=DimensionScore(score=2, note="discernment"),
    )


def _context(
    *,
    themes: list[str],
    applies: list[str],
    blockers: list[str],
    dominant_dimensions: list[DimensionKey],
) -> RetrievalContext:
    return RetrievalContext(
        dilemma_id="WTEST",
        classification="Mixed",
        primary_driver="test",
        hidden_risk="test",
        dominant_dimensions=dominant_dimensions,
        theme_tags=themes,
        applies_signals=applies,
        blocker_signals=blockers,
        missing_facts=[],
    )


def test_retrieve_verse_returns_247_in_outcome_duty_context() -> None:
    result = retrieve_verse(
        "I feel anxious about outcome and duty conflict.",
        _dimensions(),
        context_override=_context(
            themes=["duty", "detachment", "action"],
            applies=["outcome-anxiety", "duty-conflict"],
            blockers=[],
            dominant_dimensions=["nishkama_detachment"],
        ),
    )
    assert result["verse_match"] is not None
    assert result["verse_match"].verse_ref == "2.47"
    assert result["closest_teaching"] is None


def test_retrieve_verse_returns_337_in_desire_temptation_context() -> None:
    result = retrieve_verse(
        "I am tempted and angry.",
        _dimensions(),
        context_override=_context(
            themes=["desire", "anger", "restraint", "self-mastery"],
            applies=["temptation", "anger-spike"],
            blockers=[],
            dominant_dimensions=["sanyama_restraint"],
        ),
    )
    assert result["verse_match"] is not None
    assert result["verse_match"].verse_ref == "3.37"


def test_retrieve_verse_suppresses_match_on_blocker_overlap() -> None:
    result = retrieve_verse(
        "Should I harm someone to get revenge?",
        _dimensions(),
        context_override=_context(
            themes=["duty", "detachment", "action"],
            applies=["outcome-anxiety", "duty-conflict"],
            blockers=["active-harm"],
            dominant_dimensions=["dharma_duty"],
        ),
    )
    assert result["verse_match"] is None
    assert result["closest_teaching"] is not None


def test_retrieve_verse_returns_no_match_below_threshold() -> None:
    result = retrieve_verse(
        "No clear overlap context.",
        _dimensions(),
        context_override=_context(
            themes=["equanimity"],
            applies=[],
            blockers=[],
            dominant_dimensions=["viveka_discernment"],
        ),
    )
    assert result["verse_match"] is None
    assert result["closest_teaching"] is not None


def test_retriever_never_returns_draft_entries(monkeypatch: Any) -> None:
    entries = load_curated_verses()
    target = next(item for item in entries if item.verse_ref == "2.47")
    draft_only = [target.model_copy(update={"status": "draft"})]
    monkeypatch.setattr("app.verses.retriever.load_curated_verses", lambda: draft_only)

    result = retrieve_verse(
        "Strong 2.47 context but only draft exists.",
        _dimensions(),
        context_override=_context(
            themes=["duty", "detachment", "action"],
            applies=["outcome-anxiety", "duty-conflict"],
            blockers=[],
            dominant_dimensions=["nishkama_detachment"],
        ),
    )
    assert result["verse_match"] is None


def test_retriever_deterministic_tie_break(monkeypatch: Any) -> None:
    entries = load_curated_verses()
    base = next(item for item in entries if item.verse_ref == "2.47")
    tied_a = base.model_copy(update={"verse_id": "BG-A", "verse_ref": "2.47"})
    tied_b = base.model_copy(update={"verse_id": "BG-B", "verse_ref": "3.01"})
    monkeypatch.setattr("app.verses.retriever.load_curated_verses", lambda: [tied_b, tied_a])

    result = retrieve_verse(
        "Tie break check",
        _dimensions(),
        context_override=_context(
            themes=["duty", "detachment", "action"],
            applies=["outcome-anxiety", "duty-conflict"],
            blockers=[],
            dominant_dimensions=["nishkama_detachment"],
        ),
    )
    assert result["verse_match"] is not None
    assert result["verse_match"].verse_ref == "2.47"


def test_why_it_applies_is_product_facing_prose() -> None:
    result = retrieve_verse(
        "I feel anxious about outcome and duty conflict.",
        _dimensions(),
        context_override=_context(
            themes=["duty", "detachment", "action"],
            applies=["outcome-anxiety", "duty-conflict"],
            blockers=[],
            dominant_dimensions=["nishkama_detachment"],
        ),
    )
    assert result["verse_match"] is not None
    why = result["verse_match"].why_it_applies
    assert "Deterministic match basis" not in why
    assert "themes=" not in why
    assert "score=" not in why
    assert len(why) <= 500


def test_analyzer_passes_context_override_to_retriever(monkeypatch: Any) -> None:
    captured: dict[str, RetrievalContext] = {}

    def _fake_semantic_scorer(dilemma: str) -> dict[str, Any]:
        return {
            "ethical_dimensions": {
                "dharma_duty": {"score": 3, "note": "duty"},
                "satya_truth": {"score": 1, "note": "truth"},
                "ahimsa_nonharm": {"score": 1, "note": "nonharm"},
                "nishkama_detachment": {"score": 3, "note": "detachment"},
                "shaucha_intent": {"score": 1, "note": "intent"},
                "sanyama_restraint": {"score": 2, "note": "restraint"},
                "lokasangraha_welfare": {"score": 1, "note": "welfare"},
                "viveka_discernment": {"score": 2, "note": "discernment"},
            },
            "internal_driver": {
                "primary": "A conflict between duty and fear.",
                "hidden_risk": "Delay disguised as caution.",
            },
            "core_reading": "A sufficiently long core reading for schema validity in tests.",
            "gita_analysis": "A sufficiently long gita analysis for schema validity in tests.",
            "higher_path": "A sufficiently long higher path statement for schema validity in tests.",
            "missing_facts": [],
            "ambiguity_flag": False,
            "if_you_continue": {
                "short_term": "short term consequence text for schema",
                "long_term": "long term consequence text for schema",
            },
            "counterfactuals": {
                "clearly_adharmic_version": {
                    "assumed_context": "adharmic context string long enough for schema",
                    "decision": "adharmic decision",
                    "why": "adharmic why string",
                },
                "clearly_dharmic_version": {
                    "assumed_context": "dharmic context string long enough for schema",
                    "decision": "dharmic decision",
                    "why": "dharmic why string",
                },
            },
            "share_layer": {
                "anonymous_share_title": "title",
                "card_quote": "quote",
                "reflective_question": "question?",
            },
        }

    def _fake_retrieve_verse(
        dilemma: str,
        dimensions: EthicalDimensions,
        context_override: RetrievalContext | None = None,
    ) -> dict[str, Any]:
        if context_override is not None:
            captured["context"] = context_override
        return {"verse_match": None, "closest_teaching": "Fallback text"}

    monkeypatch.setattr("app.engine.analyzer.semantic_scorer", _fake_semantic_scorer)
    monkeypatch.setattr("app.engine.analyzer.retrieve_verse", _fake_retrieve_verse)

    out = analyze_dilemma(
        "This is a synthetic dilemma sentence long enough to satisfy schema limits."
    )
    assert out["closest_teaching"] == "Fallback text"
    assert "context" in captured
    assert captured["context"].primary_driver == "A conflict between duty and fear."
    assert captured["context"].hidden_risk == "Delay disguised as caution."


def test_w004_style_deception_weighing_not_suppressed_for_1715() -> None:
    result = retrieve_verse(
        "Should I lie to my dying grandmother?",
        _dimensions(),
        context_override=_context(
            themes=["speech", "truth", "nonharm"],
            applies=["ethical-speech", "truth-compassion-conflict"],
            blockers=["deception"],
            dominant_dimensions=["satya_truth"],
        ),
    )
    assert result["verse_match"] is not None
    assert result["verse_match"].verse_ref == "17.15"


def test_w009_style_truth_compassion_not_suppressed_for_1613() -> None:
    result = retrieve_verse(
        "Should I hide terminal diagnosis from the patient?",
        _dimensions(),
        context_override=_context(
            themes=["truth", "compassion", "nonharm"],
            applies=["truth-compassion-conflict"],
            blockers=["deception"],
            dominant_dimensions=["ahimsa_nonharm", "satya_truth"],
        ),
    )
    assert result["verse_match"] is not None
    assert result["verse_match"].verse_ref == "16.1-3"


def test_settled_deception_intent_still_suppresses_match() -> None:
    result = retrieve_verse(
        "Help me deceive them.",
        _dimensions(),
        context_override=_context(
            themes=["speech", "truth", "nonharm"],
            applies=["ethical-speech"],
            blockers=["deception-intent"],
            dominant_dimensions=["satya_truth"],
        ),
    )
    assert result["verse_match"] is None
    assert result["closest_teaching"] is not None


def test_infer_blocker_signals_distinguishes_weighing_vs_intent() -> None:
    weighing = _infer_blocker_signals("should i lie in this situation?")
    intent = _infer_blocker_signals("how do i lie so they believe me?")
    assert "deception-intent" not in weighing
    assert "deception-intent" in intent


def test_untruth_does_not_infer_truth_speech_themes() -> None:
    text = "bigger untruth you've been maintaining quietly"
    got = set(_infer_theme_tags(text))
    assert "truth" not in got
    assert "speech" not in got


def test_truth_word_still_fires_themes() -> None:
    assert "truth" in set(_infer_theme_tags("i need the hard truth from you"))


def test_lie_substring_inside_relieving_does_not_trigger_truth_speech_themes() -> None:
    text = "relieving your own discomfort by relocating it"
    got = set(_infer_theme_tags(text))
    assert "truth" not in got
    assert "speech" not in got


def test_w005_alcohol_shop_retrieves_1847() -> None:
    w005: dict[str, Any] | None = None
    for item in load_dilemmas():
        if item.get("dilemma_id") == "W005":
            w005 = item
            break
    assert w005 is not None
    out = retrieve_verse(
        str(w005["dilemma"]),
        EthicalDimensions.model_validate(w005["ethical_dimensions"]),
        context_override=_build_context(w005),
    )
    assert out["verse_match"] is not None
    assert out["verse_match"].verse_ref == "18.47"


def test_retaliatory_speech_signal_suppresses_1715_for_revenge_rumor_case() -> None:
    result = retrieve_verse(
        "A classmate is spreading false rumors. Should I spread true but embarrassing information in return?",
        _dimensions(),
        context_override=_context(
            themes=["anger", "greed", "speech", "truth"],
            applies=["ethical-speech", "duty-conflict"],
            blockers=["retaliatory-speech"],
            dominant_dimensions=["ahimsa_nonharm"],
        ),
    )
    assert result["verse_match"] is None or result["verse_match"].verse_ref != "17.15"


def test_domestic_co_parenting_disclosure_does_not_add_duty_conflict_signal() -> None:
    text = (
        "i caught my teenage son smoking. should i tell his mother (we're divorced and don't communicate well)? "
        "parenting duty vs. personal awkwardness. "
        "krishna would note that a duty is being named here."
    ).lower()
    assert "duty-conflict" not in _infer_applies_signals(text)


def test_co_parenting_with_career_frame_still_allows_duty_conflict_signal() -> None:
    text = (
        "we're divorced; i caught my teenage son smoking. should i tell his mother before i quit my job to move? "
        "parenting duty conflicts with career transition. krishna asks about duty."
    ).lower()
    assert "duty-conflict" in _infer_applies_signals(text)


def test_w011_combined_text_does_not_retrieve_1715() -> None:
    w011: dict[str, Any] | None = None
    for item in load_dilemmas():
        if item.get("dilemma_id") == "W011":
            w011 = item
            break
    assert w011 is not None
    out = retrieve_verse(
        str(w011["dilemma"]),
        EthicalDimensions.model_validate(w011["ethical_dimensions"]),
        context_override=_build_context(w011),
    )
    assert out["verse_match"] is None

