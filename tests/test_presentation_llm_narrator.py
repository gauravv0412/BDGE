"""Step 32C tests for narrator provider + repair loop."""

from __future__ import annotations

from app.presentation.config import PresentationLLMConfig
from app.presentation.llm_narrator import build_presentation_narrator
from app.presentation.provider import ProviderCallResult
from app.presentation.view_model import build_result_view_model


def _output(verse: bool = False, crisis: bool = False) -> dict[str, object]:
    dilemma = "I found a wallet with cash and an ID, and I am tempted to keep the cash."
    if crisis:
        dilemma = "I feel everyone would be better without me and I may do anything harmful tonight."
    base: dict[str, object] = {
        "dilemma_id": "narrator-1",
        "dilemma": dilemma,
        "verdict_sentence": "Return what can be returned.",
        "classification": "Adharmic",
        "alignment_score": -72,
        "confidence": 0.85,
        "internal_driver": {"primary": "Need", "hidden_risk": "Turning pressure into permission"},
        "core_reading": "Need pressure is being used as permission to keep identifiable property.",
        "gita_analysis": "The clean action is to restore ownership before self-justification grows.",
        "verse_match": None,
        "closest_teaching": "Act from clarity rather than appetite.",
        "if_you_continue": {"short_term": "Relief now.", "long_term": "Trust erosion later."},
        "counterfactuals": {
            "clearly_adharmic_version": {"assumed_context": "Need becomes entitlement.", "decision": "Keep cash.", "why": "Owner is ignored."},
            "clearly_dharmic_version": {"assumed_context": "Need is real but bounded.", "decision": "Return wallet.", "why": "Ownership is respected."},
        },
        "higher_path": "Return the wallet intact, then seek support for rent pressure.",
        "ethical_dimensions": {
            "dharma_duty": {"score": -3, "note": "Owner is identifiable."},
            "satya_truth": {"score": -3, "note": "Keeping cash requires denial."},
        },
        "missing_facts": [],
        "share_layer": {
            "anonymous_share_title": "Need vs integrity",
            "card_quote": "Pressure does not erase ownership.",
            "reflective_question": "What action survives daylight?",
        },
    }
    if verse:
        base["closest_teaching"] = None
        base["verse_match"] = {
            "verse_ref": "6.5",
            "sanskrit_devanagari": "उद्धरेदात्मनात्मानं",
            "sanskrit_iast": "uddhared ātmanātmānaṁ",
            "hindi_translation": "अपने द्वारा अपना उद्धार करे।",
            "english_translation": "Let a man raise himself by himself.",
            "source": "Gita Press / public domain",
            "why_it_applies": "Self-mastery under pressure.",
            "match_confidence": 0.82,
        }
    return {"meta": {"contract_version": "1.0", "engine_version": "2.1", "semantic_mode_default": "stub_default"}, "output": base}


def _valid_narrator() -> dict[str, object]:
    return {
        "share_line": "This works today. It weakens you tomorrow.",
        "simple": {
            "headline": "Return it, then solve your pressure cleanly.",
            "explanation": "Need is real; ownership still stands.",
            "next_step": "Return the wallet first.",
        },
        "krishna_lens": {
            "question": "Which action survives tomorrow's daylight?",
            "teaching": "Method under pressure reveals alignment.",
            "mirror": "Relief without integrity turns costly later.",
        },
        "brutal_truth": {
            "headline": "Pressure is loud, truth is quieter.",
            "punchline": "A shortcut now can become your new normal.",
            "share_quote": "Need explains pressure, not permission.",
        },
        "deep_view": {
            "what_is_happening": "Urgency is compressing judgment.",
            "risk": "Compromise today trains compromise tomorrow.",
            "higher_path": "Return it intact, then address the rent pressure directly.",
        },
    }


def test_provider_disabled_returns_fallback_and_provider_not_called(monkeypatch) -> None:
    engine = _output()
    deterministic = build_result_view_model(engine).model_dump(mode="json")
    monkeypatch.setattr(
        "app.presentation.llm_narrator.load_presentation_llm_config",
        lambda: PresentationLLMConfig(enabled=False, shadow=False, provider="none"),
    )
    called = {"n": 0}

    def _fake_provider(**kwargs):
        called["n"] += 1
        return ProviderCallResult(ok=False, payload=None, error_code="should_not_call")

    monkeypatch.setattr("app.presentation.llm_narrator.call_presentation_provider", _fake_provider)
    narrator, meta = build_presentation_narrator(engine_response=engine, deterministic_presentation=deterministic)
    assert narrator["simple"]["headline"]
    assert meta["source"] == "deterministic_fallback"
    assert meta["provider_called"] is False
    assert meta["fallback_returned"] is True
    assert meta["repair_attempted"] is False
    assert called["n"] == 0


def test_provider_none_returns_fallback_and_provider_not_called_when_enabled(monkeypatch) -> None:
    engine = _output()
    deterministic = build_result_view_model(engine).model_dump(mode="json")
    monkeypatch.setattr(
        "app.presentation.llm_narrator.load_presentation_llm_config",
        lambda: PresentationLLMConfig(enabled=True, shadow=False, provider="none", repair_enabled=True),
    )
    called = {"n": 0}

    def _fake_provider(**kwargs):
        called["n"] += 1
        return ProviderCallResult(ok=False, payload=None, error_code="should_not_call")

    monkeypatch.setattr("app.presentation.llm_narrator.call_presentation_provider", _fake_provider)
    _, meta = build_presentation_narrator(engine_response=engine, deterministic_presentation=deterministic)

    assert meta["provider_called"] is False
    assert meta["final_source"] == "deterministic_fallback"
    assert called["n"] == 0


def test_valid_first_attempt_no_repair(monkeypatch) -> None:
    engine = _output()
    deterministic = build_result_view_model(engine).model_dump(mode="json")
    calls = {"n": 0}

    def _provider(**kwargs):
        calls["n"] += 1
        return ProviderCallResult(ok=True, payload=_valid_narrator())

    monkeypatch.setattr(
        "app.presentation.llm_narrator.load_presentation_llm_config",
        lambda: PresentationLLMConfig(enabled=True, shadow=False, provider="openai_compatible", repair_enabled=True, max_repair_attempts=1),
    )
    monkeypatch.setattr("app.presentation.llm_narrator.call_presentation_provider", _provider)
    narrator, meta = build_presentation_narrator(engine_response=engine, deterministic_presentation=deterministic)
    assert narrator["simple"]["headline"] == _valid_narrator()["simple"]["headline"]
    assert meta["final_source"] == "llm_initial"
    assert meta["repair_attempted"] is False
    assert calls["n"] == 1


def test_invalid_first_valid_repair_returns_repair_when_enabled(monkeypatch) -> None:
    engine = _output()
    deterministic = build_result_view_model(engine).model_dump(mode="json")
    calls = {"n": 0}

    def _provider(**kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            return ProviderCallResult(
                ok=True,
                payload={
                    "share_line": "This works today. It weakens you tomorrow.",
                    "simple": {"headline": "classification says this is fine", "explanation": "theme and scorer confirm", "next_step": "keep it"},
                    "krishna_lens": {"question": "q?", "teaching": "t", "mirror": "m"},
                    "brutal_truth": {"headline": "h", "punchline": "p", "share_quote": "s"},
                    "deep_view": {"what_is_happening": "w", "risk": "r", "higher_path": "h"},
                },
            )
        return ProviderCallResult(ok=True, payload=_valid_narrator())

    monkeypatch.setattr(
        "app.presentation.llm_narrator.load_presentation_llm_config",
        lambda: PresentationLLMConfig(enabled=True, shadow=False, provider="openai_compatible", repair_enabled=True, max_repair_attempts=1),
    )
    monkeypatch.setattr("app.presentation.llm_narrator.call_presentation_provider", _provider)
    narrator, meta = build_presentation_narrator(engine_response=engine, deterministic_presentation=deterministic)
    assert narrator["simple"]["headline"] == _valid_narrator()["simple"]["headline"]
    assert meta["repair_attempted"] is True
    assert meta["repair_valid"] is True
    assert meta["final_source"] == "llm_repair"
    assert calls["n"] == 2


def test_invalid_first_invalid_repair_falls_back(monkeypatch) -> None:
    engine = _output()
    deterministic = build_result_view_model(engine).model_dump(mode="json")
    calls = {"n": 0}

    def _provider(**kwargs):
        calls["n"] += 1
        return ProviderCallResult(
            ok=True,
            payload={
                "share_line": "This works today. It weakens you tomorrow.",
                "simple": {"headline": "classification says this is fine", "explanation": "theme and scorer confirm", "next_step": "keep it"},
                "krishna_lens": {"question": "q?", "teaching": "t", "mirror": "m"},
                "brutal_truth": {"headline": "h", "punchline": "p", "share_quote": "s"},
                "deep_view": {"what_is_happening": "w", "risk": "r", "higher_path": "h"},
            },
        )

    monkeypatch.setattr(
        "app.presentation.llm_narrator.load_presentation_llm_config",
        lambda: PresentationLLMConfig(enabled=True, shadow=False, provider="openai_compatible", repair_enabled=True, max_repair_attempts=1),
    )
    monkeypatch.setattr("app.presentation.llm_narrator.call_presentation_provider", _provider)
    narrator, meta = build_presentation_narrator(engine_response=engine, deterministic_presentation=deterministic)
    assert narrator["simple"]["headline"] != "classification says this is fine"
    assert meta["final_source"] == "deterministic_fallback"
    assert meta["repair_attempted"] is True
    assert meta["repair_valid"] is False
    assert calls["n"] == 2


def test_repair_disabled_invalid_first_falls_back(monkeypatch) -> None:
    engine = _output()
    deterministic = build_result_view_model(engine).model_dump(mode="json")
    calls = {"n": 0}

    def _provider(**kwargs):
        calls["n"] += 1
        return ProviderCallResult(
            ok=True,
            payload={
                "share_line": "This works today. It weakens you tomorrow.",
                "simple": {"headline": "classification says this is fine", "explanation": "theme and scorer confirm", "next_step": "keep it"},
                "krishna_lens": {"question": "q?", "teaching": "t", "mirror": "m"},
                "brutal_truth": {"headline": "h", "punchline": "p", "share_quote": "s"},
                "deep_view": {"what_is_happening": "w", "risk": "r", "higher_path": "h"},
            },
        )

    monkeypatch.setattr(
        "app.presentation.llm_narrator.load_presentation_llm_config",
        lambda: PresentationLLMConfig(enabled=True, shadow=False, provider="openai_compatible", repair_enabled=False, max_repair_attempts=1),
    )
    monkeypatch.setattr("app.presentation.llm_narrator.call_presentation_provider", _provider)
    _, meta = build_presentation_narrator(engine_response=engine, deterministic_presentation=deterministic)
    assert meta["final_source"] == "deterministic_fallback"
    assert meta["repair_attempted"] is False
    assert calls["n"] == 1


def test_shadow_mode_attempts_repair_but_returns_fallback(monkeypatch) -> None:
    engine = _output()
    deterministic = build_result_view_model(engine).model_dump(mode="json")
    calls = {"n": 0}

    def _provider(**kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            return ProviderCallResult(
                ok=True,
                payload={
                    "share_line": "This works today. It weakens you tomorrow.",
                    "simple": {"headline": "classification says this is fine", "explanation": "theme and scorer confirm", "next_step": "keep it"},
                    "krishna_lens": {"question": "q?", "teaching": "t", "mirror": "m"},
                    "brutal_truth": {"headline": "h", "punchline": "p", "share_quote": "s"},
                    "deep_view": {"what_is_happening": "w", "risk": "r", "higher_path": "h"},
                },
            )
        return ProviderCallResult(ok=True, payload=_valid_narrator())

    monkeypatch.setattr(
        "app.presentation.llm_narrator.load_presentation_llm_config",
        lambda: PresentationLLMConfig(enabled=False, shadow=True, provider="openai_compatible", repair_enabled=True, max_repair_attempts=1),
    )
    monkeypatch.setattr("app.presentation.llm_narrator.call_presentation_provider", _provider)
    narrator, meta = build_presentation_narrator(engine_response=engine, deterministic_presentation=deterministic)
    assert meta["provider_called"] is True
    assert meta["shadow_mode"] is True
    assert meta["fallback_returned"] is True
    assert meta["repair_attempted"] is True
    assert meta["repair_valid"] is True
    assert meta["final_source"] == "shadow_fallback"
    assert narrator["simple"]["headline"] != _valid_narrator()["simple"]["headline"]
    assert calls["n"] == 2


def test_provider_timeout_or_exception_no_repair_fallback(monkeypatch) -> None:
    engine = _output()
    deterministic = build_result_view_model(engine).model_dump(mode="json")
    calls = {"n": 0}

    def _provider(**kwargs):
        calls["n"] += 1
        return ProviderCallResult(ok=False, payload=None, error_code="timeout")

    monkeypatch.setattr(
        "app.presentation.llm_narrator.load_presentation_llm_config",
        lambda: PresentationLLMConfig(enabled=True, shadow=False, provider="openai_compatible", repair_enabled=True, max_repair_attempts=1),
    )
    monkeypatch.setattr("app.presentation.llm_narrator.call_presentation_provider", _provider)
    _, meta = build_presentation_narrator(engine_response=engine, deterministic_presentation=deterministic)
    assert meta["final_source"] == "deterministic_fallback"
    assert meta["repair_attempted"] is False
    assert calls["n"] == 1


def test_crisis_safe_bypasses_provider_and_repair(monkeypatch) -> None:
    engine = _output(crisis=True)
    deterministic = build_result_view_model(engine).model_dump(mode="json")
    called = {"n": 0}

    def _fake_provider(**kwargs):
        called["n"] += 1
        return ProviderCallResult(ok=False, payload=None, error_code="should_not_call")

    monkeypatch.setattr(
        "app.presentation.llm_narrator.load_presentation_llm_config",
        lambda: PresentationLLMConfig(enabled=True, shadow=True, provider="openai_compatible", repair_enabled=True, max_repair_attempts=1),
    )
    monkeypatch.setattr("app.presentation.llm_narrator.call_presentation_provider", _fake_provider)
    narrator, meta = build_presentation_narrator(engine_response=engine, deterministic_presentation=deterministic)
    assert meta["provider_called"] is False
    assert meta["repair_attempted"] is False
    assert called["n"] == 0
    all_text_parts = []
    for block in narrator.values():
        if isinstance(block, dict):
            all_text_parts.extend(str(v) for v in block.values())
        else:
            all_text_parts.append(str(block))
    all_text = " ".join(all_text_parts).lower()
    assert "viral" not in all_text
    assert "krishna" not in all_text


def test_viral_spice_allowed_when_direction_preserved(monkeypatch) -> None:
    engine = _output()
    deterministic = build_result_view_model(engine).model_dump(mode="json")
    monkeypatch.setattr(
        "app.presentation.llm_narrator.load_presentation_llm_config",
        lambda: PresentationLLMConfig(enabled=True, shadow=False, provider="openai_compatible"),
    )
    monkeypatch.setattr(
        "app.presentation.llm_narrator.call_presentation_provider",
        lambda **_: ProviderCallResult(
            ok=True,
            payload={
                "share_line": "This works today. It weakens you tomorrow.",
                "simple": {
                    "headline": "Your conscience is knocking hard. Answer it.",
                    "explanation": "This shortcut feels like oxygen now, but it steals trust from your future self.",
                    "next_step": "Return the wallet first, then fight the real pressure head-on.",
                },
                "krishna_lens": {
                    "question": "If this gets screenshot tomorrow, does your action still stand tall?",
                    "teaching": "Power is choosing a clean method when panic offers a shortcut.",
                    "mirror": "Pressure can be loud without becoming your permission slip.",
                },
                "brutal_truth": {
                    "headline": "Fast relief, slow regret.",
                    "punchline": "One private compromise can become your default character.",
                    "share_quote": "Need is heavy. Integrity is heavier.",
                },
                "deep_view": {
                    "what_is_happening": "Urgency is shrinking your moral bandwidth.",
                    "risk": "A quick win here can normalize a costly pattern.",
                    "higher_path": "Return what is not yours, then solve the rent problem directly.",
                },
            },
        ),
    )
    narrator, meta = build_presentation_narrator(engine_response=engine, deterministic_presentation=deterministic)
    assert meta["final_source"] == "llm_initial"
    assert narrator["brutal_truth"]["headline"] == "Fast relief, slow regret."


def test_verse_match_case_preserves_verse_ref_and_translations() -> None:
    engine = _output(verse=True)
    deterministic = build_result_view_model(engine).model_dump(mode="json")
    _, _ = build_presentation_narrator(engine_response=engine, deterministic_presentation=deterministic)
    verse = engine["output"]["verse_match"]
    assert isinstance(verse, dict)
    assert verse["verse_ref"] == "6.5"
    assert verse["english_translation"] == "Let a man raise himself by himself."
    assert verse["hindi_translation"] == "अपने द्वारा अपना उद्धार करे।"


def test_closest_teaching_case_does_not_invent_verse(monkeypatch) -> None:
    engine = _output(verse=False)
    deterministic = build_result_view_model(engine).model_dump(mode="json")
    monkeypatch.setattr(
        "app.presentation.llm_narrator.load_presentation_llm_config",
        lambda: PresentationLLMConfig(enabled=True, shadow=False, provider="openai_compatible"),
    )
    monkeypatch.setattr(
        "app.presentation.llm_narrator.call_presentation_provider",
        lambda **_: ProviderCallResult(
            ok=True,
            payload={
                "share_line": "This works today. It weakens you tomorrow.",
                "simple": {"headline": "BG 2.47 says this", "explanation": "Chapter 2 verse 47 applies", "next_step": "act"},
                "krishna_lens": {"question": "q?", "teaching": "t", "mirror": "m"},
                "brutal_truth": {"headline": "h", "punchline": "p", "share_quote": "s"},
                "deep_view": {"what_is_happening": "w", "risk": "r", "higher_path": "h"},
            },
        ),
    )
    _, meta = build_presentation_narrator(engine_response=engine, deterministic_presentation=deterministic)
    assert meta["final_source"] == "deterministic_fallback"
    assert any("invented direct verse" in reason for reason in meta["rejection_reasons"])


def test_classification_truth_drift_rejected(monkeypatch) -> None:
    engine = _output()
    deterministic = build_result_view_model(engine).model_dump(mode="json")
    monkeypatch.setattr(
        "app.presentation.llm_narrator.load_presentation_llm_config",
        lambda: PresentationLLMConfig(enabled=True, shadow=False, provider="openai_compatible"),
    )
    monkeypatch.setattr(
        "app.presentation.llm_narrator.call_presentation_provider",
        lambda **_: ProviderCallResult(
            ok=True,
            payload={
                "share_line": "This works today. It weakens you tomorrow.",
                "simple": {"headline": "This is ethical and right.", "explanation": "You are right to do this.", "next_step": "Proceed."},
                "krishna_lens": {"question": "q?", "teaching": "t", "mirror": "m"},
                "brutal_truth": {"headline": "h", "punchline": "p", "share_quote": "s"},
                "deep_view": {"what_is_happening": "w", "risk": "r", "higher_path": "h"},
            },
        ),
    )
    _, meta = build_presentation_narrator(engine_response=engine, deterministic_presentation=deterministic)
    assert meta["final_source"] == "deterministic_fallback"
    assert any("verdict direction contradiction" in reason for reason in meta["rejection_reasons"])
