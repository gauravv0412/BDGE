"""Tests for the V1.1 presentation view-model adapter."""

from __future__ import annotations

from copy import deepcopy

from app.presentation import ResultPresentationViewModel, build_result_view_model


def _base_output() -> dict[str, object]:
    return {
        "dilemma_id": "presentation-1",
        "dilemma": "I found a wallet with cash and an ID, and I am tempted to keep the cash.",
        "verdict_sentence": "Return what can be returned.",
        "classification": "Adharmic",
        "alignment_score": -72,
        "confidence": 0.85,
        "internal_driver": {"primary": "Need", "hidden_risk": "Turning pressure into permission"},
        "core_reading": "This is a test of whether need becomes permission to take what is identifiable.",
        "gita_analysis": "The cleaner action is the one that disciplines impulse before it becomes harm.",
        "verse_match": None,
        "closest_teaching": "Act from clarity rather than appetite.",
        "if_you_continue": {
            "short_term": "You may feel immediate relief.",
            "long_term": "The act becomes easier to justify next time.",
        },
        "counterfactuals": {
            "clearly_adharmic_version": {
                "assumed_context": "You let pressure define the owner as irrelevant.",
                "decision": "Keep the cash.",
                "why": "It converts need into entitlement.",
            },
            "clearly_dharmic_version": {
                "assumed_context": "You accept the pressure without erasing the owner.",
                "decision": "Return the wallet.",
                "why": "It solves action before rationalization grows.",
            },
        },
        "higher_path": "Return it through the ID or the cafe counter.",
        "ethical_dimensions": {
            "dharma_duty": {"score": -3, "note": "The wallet can be returned."},
            "satya_truth": {"score": -4, "note": "The owner is identifiable."},
            "ahimsa_nonharm": {"score": -3, "note": "Keeping it harms the owner."},
            "nishkama_detachment": {"score": -2, "note": "Rent pressure is driving the choice."},
            "shaucha_intent": {"score": -3, "note": "The motive is mixed with self-justification."},
            "sanyama_restraint": {"score": -4, "note": "The temptation asks for restraint."},
            "lokasangraha_welfare": {"score": -2, "note": "Trust around public goods weakens."},
            "viveka_discernment": {"score": -3, "note": "The facts are clear enough to act."},
        },
        "missing_facts": [],
        "share_layer": {
            "anonymous_share_title": "Need vs honesty",
            "card_quote": "Pressure does not erase the owner.",
            "reflective_question": "What action would still feel clean tomorrow?",
        },
    }


def _envelope(output: dict[str, object]) -> dict[str, object]:
    return {
        "meta": {"contract_version": "1.0", "engine_version": "2.1", "semantic_mode_default": "live_default"},
        "output": output,
    }


def test_adapter_accepts_verse_match_response_and_builds_expected_cards() -> None:
    output = _base_output()
    output["closest_teaching"] = None
    output["verse_match"] = {
        "verse_ref": "6.5",
        "sanskrit_devanagari": "उद्धरेदात्मनात्मानं",
        "sanskrit_iast": "uddhared ātmanātmānaṁ",
        "hindi_translation": "अपने द्वारा अपना उद्धार करे।",
        "english_translation": "Let a man raise himself by himself.",
        "source": "Gita Press / public domain",
        "why_it_applies": "The verse points to self-mastery before impulse takes over.",
        "match_confidence": 0.82,
    }

    view_model = build_result_view_model(_envelope(output))

    assert isinstance(view_model, ResultPresentationViewModel)
    assert view_model.presentation_mode == "standard"
    assert view_model.verdict_card.title == "Verdict"
    assert view_model.guidance_card.title == "Gita Verse"
    assert view_model.guidance_card.primary_text == "The verse points to self-mastery before impulse takes over."
    lower_primary = view_model.guidance_card.primary_text.lower()
    for forbidden in (
        "engine",
        "threshold",
        "fallback",
        "verse_match",
        "retrieval",
        "schema",
        "signal",
        "signals",
        "dominant ethical pull",
        "theme",
        "theme tags",
        "applies",
        "metadata",
        "classifier",
    ):
        assert forbidden not in lower_primary
    explain = _section_text(view_model.guidance_card, "Explain simply")
    assert explain != view_model.guidance_card.primary_text
    assert "strengthens you or weakens you" in explain
    assert "wallet" not in explain.lower()
    lower_explain = explain.lower()
    for forbidden in (
        "engine",
        "threshold",
        "fallback",
        "verse_match",
        "retrieval",
        "schema",
        "signal",
        "signals",
        "dominant ethical pull",
        "theme",
        "theme tags",
        "applies",
        "metadata",
        "classifier",
    ):
        assert forbidden not in lower_explain
    assert "Show Gita anchor" in _section_labels(view_model.guidance_card)
    assert "Verse: 6.5" in _section_text(view_model.guidance_card, "Show Gita anchor")
    assert "English: Let a man raise himself by himself." in _section_text(view_model.guidance_card, "Show Gita anchor")
    assert view_model.if_you_continue_card.title == "If You Continue"
    assert view_model.counterfactuals_card.title == "Counterfactuals"
    assert view_model.higher_path_card.title == "Higher Path"
    assert view_model.ethical_dimensions_card.title == "Ethical Dimensions"
    assert view_model.share_card.needs_copy_refinement is False
    assert view_model.safety_card is None


def test_adapter_accepts_closest_teaching_without_faking_direct_verse() -> None:
    output = _base_output()

    view_model = build_result_view_model(_envelope(output))

    assert view_model.guidance_card.title == "Closest Gita Lens"
    assert "Closest lens: Act from clarity rather than appetite." in view_model.guidance_card.primary_text
    assert "Use this as a lens, not a command." in view_model.guidance_card.primary_text
    labels = _section_labels(view_model.guidance_card)
    assert "Explain simply" in labels
    assert "Why this stays provisional" in labels
    assert "Show Gita anchor" not in labels
    assert _section_text(view_model.guidance_card, "Explain simply") != view_model.guidance_card.primary_text
    forbidden = (
        "engine",
        "threshold",
        "fallback",
        "verse_match",
        "selected",
        "retrieval",
        "schema",
        "signal",
        "signals",
        "dominant ethical pull",
        "theme",
        "theme tags",
        "applies",
        "metadata",
        "classifier",
    )
    combined = " ".join(
        [view_model.guidance_card.primary_text, *[section.text for section in view_model.guidance_card.sections]]
    ).lower()
    for word in forbidden:
        assert word not in combined


def test_adapter_uses_guidance_title_when_both_verse_and_closest_are_empty() -> None:
    output = _base_output()
    output["verse_match"] = None
    output["closest_teaching"] = None

    view_model = build_result_view_model(_envelope(output))

    assert view_model.presentation_mode == "standard"
    assert view_model.guidance_card.title == "Guidance"
    assert "No verse or closest teaching is currently available" in view_model.guidance_card.primary_text
    assert "Why this is not a direct verse verdict" not in _section_labels(view_model.guidance_card)


def test_adapter_output_contains_expandable_sections_and_preserves_primary_text() -> None:
    view_model = build_result_view_model(_envelope(_base_output()))

    assert view_model.verdict_card.primary_text == "Return what can be returned."
    assert "Explain simply" in _section_labels(view_model.verdict_card)
    assert "Why this applies to your situation" in _section_labels(view_model.verdict_card)
    assert "Short-term: You may feel immediate relief." in view_model.if_you_continue_card.primary_text
    assert "Long-term: The act becomes easier to justify next time." in view_model.if_you_continue_card.primary_text
    assert "Adharmic assumed inner state" in _section_labels(view_model.counterfactuals_card)
    assert "Dharmic likely decision" in _section_labels(view_model.counterfactuals_card)
    assert _section_text(view_model.higher_path_card, "Explain simply") != view_model.higher_path_card.primary_text
    assert view_model.share_card.title == "Share Layer"
    assert view_model.share_card.needs_copy_refinement is False
    assert len(view_model.share_card.primary_text) <= 160
    question = _section_text(view_model.share_card, "Reflective question")
    assert question.endswith("?")
    assert " keeps I " not in question
    assert "..." not in question


def test_verdict_fallback_explain_simply_has_no_engine_wording() -> None:
    output = _base_output()
    output["core_reading"] = ""
    vm = build_result_view_model(_envelope(output))
    explain = _section_text(vm.verdict_card, "Explain simply").lower()
    assert "based on the available details" in explain
    assert "engine" not in explain
    assert "classifies" not in explain


def test_share_livelihood_case_is_not_relationship_phrased() -> None:
    output = _base_output()
    output["dilemma"] = "I can legally open an alcohol shop in my neighborhood, but I worry it may increase harm even though it would support my family."
    output["core_reading"] = "The tension is livelihood versus community harm."
    view_model = build_result_view_model(_envelope(output))

    share_text = view_model.share_card.primary_text.lower()
    assert "chemistry" not in share_text
    assert "betray" not in share_text
    assert "partner" not in share_text
    assert any(term in share_text for term in ("legal", "income", "profit", "harm", "community", "livelihood"))


def test_share_differs_across_domains_and_has_no_internal_terms() -> None:
    base = _base_output()

    wallet_vm = build_result_view_model(_envelope(base))

    workplace = _base_output()
    workplace["dilemma"] = "My manager publicly took credit for my work, and I am considering correcting the record in the same public meeting."
    workplace_vm = build_result_view_model(_envelope(workplace))

    low_info = _base_output()
    low_info["dilemma"] = "I need to decide whether to do the thing soon, but I cannot share many details right now."
    low_info_vm = build_result_view_model(_envelope(low_info))

    quotes = {wallet_vm.share_card.primary_text, workplace_vm.share_card.primary_text, low_info_vm.share_card.primary_text}
    assert len(quotes) >= 3

    for vm in (wallet_vm, workplace_vm, low_info_vm):
        combined = " ".join([vm.share_card.primary_text, _section_text(vm.share_card, "Reflective question")]).lower()
        for forbidden in ("engine", "threshold", "fallback", "verse_match", "retrieval", "schema"):
            assert forbidden not in combined


def test_counterfactual_domain_copy_differs_across_cases() -> None:
    wallet = _base_output()
    wallet_vm = build_result_view_model(_envelope(wallet))

    workplace = _base_output()
    workplace["dilemma"] = "My manager publicly took credit for my work, and I am considering correcting the record in the same public meeting."
    workplace_vm = build_result_view_model(_envelope(workplace))

    desire = _base_output()
    desire["dilemma"] = "I have developed desire for my close friend's partner, and they seem interested too, but acting on it would betray my friend."
    desire_vm = build_result_view_model(_envelope(desire))

    low_info = _base_output()
    low_info["dilemma"] = "I need to decide whether to do the thing soon, but I cannot share many details right now."
    low_info_vm = build_result_view_model(_envelope(low_info))

    decisions = {
        _section_text(wallet_vm.counterfactuals_card, "Adharmic likely decision"),
        _section_text(workplace_vm.counterfactuals_card, "Adharmic likely decision"),
        _section_text(desire_vm.counterfactuals_card, "Adharmic likely decision"),
        _section_text(low_info_vm.counterfactuals_card, "Adharmic likely decision"),
    }
    assert len(decisions) >= 4


def test_counterfactual_wallet_case_uses_integrity_property_wording() -> None:
    vm = build_result_view_model(_envelope(_base_output()))
    adh = _section_text(vm.counterfactuals_card, "Adharmic likely decision").lower()
    dh = _section_text(vm.counterfactuals_card, "Dharmic likely decision").lower()
    assert "wallet" in adh or "cash" in adh
    assert "wallet" in dh or "cash" in dh


def test_counterfactual_livelihood_case_not_relationship_wording() -> None:
    output = _base_output()
    output["dilemma"] = "I can legally open an alcohol shop in my neighborhood, but I worry it may increase harm even though it would support my family."
    output["core_reading"] = "The tension is livelihood versus community harm."
    vm = build_result_view_model(_envelope(output))
    text_blob = " ".join(
        [vm.counterfactuals_card.primary_text, *[s.text for s in vm.counterfactuals_card.sections]]
    ).lower()
    assert "chemistry" not in text_blob
    assert "partner" not in text_blob
    assert "betrayal as rare chemistry" not in text_blob
    assert any(t in text_blob for t in ("legal", "income", "community", "harm", "neighborhood"))


def test_counterfactual_desire_case_uses_betrayal_wording() -> None:
    output = _base_output()
    output["dilemma"] = "I have developed desire for my close friend's partner, and they seem interested too, but acting on it would betray my friend."
    vm = build_result_view_model(_envelope(output))
    adh = _section_text(vm.counterfactuals_card, "Adharmic likely decision").lower()
    dh = _section_text(vm.counterfactuals_card, "Dharmic likely decision").lower()
    assert "chemistry" in adh or "betray" in adh
    assert "protect the friendship" in dh or "refuse secrecy" in dh


def test_counterfactual_low_information_case_uses_reversibility_wording() -> None:
    output = _base_output()
    output["dilemma"] = "I need to decide whether to do the thing soon, but I cannot share many details right now."
    vm = build_result_view_model(_envelope(output))
    text_blob = " ".join([vm.counterfactuals_card.primary_text, *[s.text for s in vm.counterfactuals_card.sections]]).lower()
    assert "missing fact" in text_blob or "missing facts" in text_blob
    assert "delay irreversible action" in text_blob or "reversible" in text_blob


def test_counterfactual_no_step31d_placeholder_lines_or_internal_terms() -> None:
    vm = build_result_view_model(_envelope(_base_output()))
    text_blob = " ".join([vm.counterfactuals_card.primary_text, *[s.text for s in vm.counterfactuals_card.sections]]).lower()
    banned_lines = (
        "move now with partial transparency; tidy the record later if pressed.",
        "one bounded, reviewable move before anything irreversible.",
        "the line moves when method stops being accountable.",
        "the upgrade is procedural: same situation, clearer safeguards",
    )
    for line in banned_lines:
        assert line not in text_blob
    for forbidden in ("engine", "threshold", "fallback", "verse_match", "retrieval", "schema"):
        assert forbidden not in text_blob
    assert len(vm.counterfactuals_card.primary_text) <= 220


def test_guidance_verse_1847_alcohol_explains_legality_not_equal_dharma() -> None:
    output = _base_output()
    output["dilemma"] = "I can legally open an alcohol shop in my neighborhood, but I worry it may increase harm even though it would support my family."
    output["core_reading"] = "The tension is livelihood versus community harm."
    output["closest_teaching"] = None
    output["verse_match"] = {
        "verse_ref": "18.47",
        "english_translation": "Better one's own duty, though imperfect.",
        "hindi_translation": "स्वधर्म में स्थित रहना श्रेष्ठ है।",
        "why_it_applies": "Examine whether your work path is aligned.",
    }
    vm = build_result_view_model(_envelope(output))
    explain = _section_text(vm.guidance_card, "Explain simply").lower()
    assert "not saying every legal job is clean" in explain
    assert "responsible way of living" in explain


def test_guidance_verse_518_caste_explains_dignity() -> None:
    output = _base_output()
    output["dilemma"] = "I want to marry someone I love, but my family rejects the relationship because of caste and threatens to cut ties."
    output["closest_teaching"] = None
    output["verse_match"] = {
        "verse_ref": "5.18",
        "english_translation": "The wise see with equal vision.",
        "hindi_translation": "विद्या विनय संपन्ने...",
        "why_it_applies": "Look beyond social hierarchy.",
    }
    vm = build_result_view_model(_envelope(output))
    explain = _section_text(vm.guidance_card, "Explain simply").lower()
    assert "dignity" in explain
    assert "caste" in explain


def test_guidance_verse_1613_doctor_truth_with_compassion() -> None:
    output = _base_output()
    output["dilemma"] = "As a doctor, I know a patient has a terminal diagnosis, and the family asks me to hide it from the patient to preserve hope."
    output["closest_teaching"] = None
    output["verse_match"] = {
        "verse_ref": "16.1-3",
        "english_translation": "Fearlessness, purity, and truthfulness.",
        "hindi_translation": "अभयं सत्त्वसंशुद्धिः...",
        "why_it_applies": "Hold truth with compassion.",
    }
    vm = build_result_view_model(_envelope(output))
    explain = _section_text(vm.guidance_card, "Explain simply").lower()
    assert "truth with compassion" in explain
    assert "right to know" in explain


def test_verse_guidance_primary_is_sanitized_but_anchor_text_preserved() -> None:
    output = _base_output()
    output["closest_teaching"] = None
    output["verse_match"] = {
        "verse_ref": "6.5",
        "english_translation": "Let a man raise himself by himself.",
        "hindi_translation": "अपने द्वारा अपना उद्धार करे।",
        "why_it_applies": "Engine selected this due to dominant ethical pull and signals like ownership metadata.",
    }
    vm = build_result_view_model(_envelope(output))
    primary = vm.guidance_card.primary_text.lower()
    for forbidden in (
        "engine",
        "threshold",
        "fallback",
        "verse_match",
        "retrieval",
        "schema",
        "signal",
        "signals",
        "dominant ethical pull",
        "theme",
        "theme tags",
        "applies",
        "metadata",
        "classifier",
    ):
        assert forbidden not in primary
    anchor = _section_text(vm.guidance_card, "Show Gita anchor")
    assert "English: Let a man raise himself by himself." in anchor
    assert "Hindi: अपने द्वारा अपना उद्धार करे।" in anchor


def test_higher_path_explain_differs_across_domains() -> None:
    wallet = build_result_view_model(_envelope(_base_output()))

    workplace = _base_output()
    workplace["dilemma"] = "My manager publicly took credit for my work, and I am considering correcting the record in the same public meeting."
    workplace_vm = build_result_view_model(_envelope(workplace))

    desire = _base_output()
    desire["dilemma"] = "I have developed desire for my close friend's partner, and they seem interested too, but acting on it would betray my friend."
    desire_vm = build_result_view_model(_envelope(desire))

    low_info = _base_output()
    low_info["dilemma"] = "I need to decide whether to do the thing soon, but I cannot share many details right now."
    low_info_vm = build_result_view_model(_envelope(low_info))

    explains = {
        _section_text(wallet.higher_path_card, "Explain simply"),
        _section_text(workplace_vm.higher_path_card, "Explain simply"),
        _section_text(desire_vm.higher_path_card, "Explain simply"),
        _section_text(low_info_vm.higher_path_card, "Explain simply"),
    }
    assert len(explains) >= 4


def test_higher_path_low_info_mentions_missing_facts_and_irreversibility() -> None:
    output = _base_output()
    output["dilemma"] = "I need to decide whether to do the thing soon, but I cannot share many details right now."
    vm = build_result_view_model(_envelope(output))
    explain = _section_text(vm.higher_path_card, "Explain simply").lower()
    assert "irreversible" in explain
    assert "facts" in explain or "missing" in explain


def test_domain_detection_prioritizes_dilemma_for_body_insecurity() -> None:
    output = _base_output()
    output["dilemma"] = "I am considering cosmetic surgery because I feel insecure about my looks and want social approval."
    output["core_reading"] = "Manager took credit in a workplace record and wallet ownership signals."
    output["higher_path"] = "Correct the public meeting record and return wallet property."
    vm = build_result_view_model(_envelope(output))
    assert vm.meta["share_domain"] == "body_insecurity"
    assert "approval-seeking" in _section_text(vm.higher_path_card, "Explain simply").lower()


def test_domain_detection_prioritizes_dilemma_for_abuse_boundary() -> None:
    output = _base_output()
    output["dilemma"] = "My abusive parent keeps contacting me, and I am considering no contact while relatives say duty."
    output["core_reading"] = "Friend's partner attraction and workplace conflict are present."
    output["higher_path"] = "Correct manager record and protect relationship trust."
    vm = build_result_view_model(_envelope(output))
    assert vm.meta["share_domain"] == "abuse_boundary"
    assert "boundary" in _section_text(vm.higher_path_card, "Explain simply").lower()


def test_domain_detection_restaurant_review_is_not_livelihood() -> None:
    output = _base_output()
    output["dilemma"] = "A restaurant treated me badly, and I want to post an anonymous scathing review that might damage their reputation."
    vm = build_result_view_model(_envelope(output))
    assert vm.meta["share_domain"] == "public_review_retaliation"


def test_domain_detection_alcohol_shop_is_livelihood_community_harm() -> None:
    output = _base_output()
    output["dilemma"] = "I can legally open an alcohol shop in my neighborhood, but I worry it may increase harm while supporting my family."
    vm = build_result_view_model(_envelope(output))
    assert vm.meta["share_domain"] == "livelihood_community_harm"


def test_domain_detection_doctor_case_is_medical_truth_consent() -> None:
    output = _base_output()
    output["dilemma"] = "As a doctor, I know a patient has a terminal diagnosis, and the family asks me to hide it from the patient."
    vm = build_result_view_model(_envelope(output))
    assert vm.meta["share_domain"] == "medical_truth_consent"


def test_domain_detection_aging_parent_case_is_family_medical_autonomy() -> None:
    output = _base_output()
    output["dilemma"] = "My aging parent refuses hospitalization after a serious diagnosis, and I am torn about forcing treatment."
    vm = build_result_view_model(_envelope(output))
    assert vm.meta["share_domain"] == "family_medical_autonomy"


def test_domain_detection_low_info_case_is_low_information() -> None:
    output = _base_output()
    output["dilemma"] = "I need to do the thing soon, but I cannot share many details yet."
    vm = build_result_view_model(_envelope(output))
    assert vm.meta["share_domain"] == "low_information"


def test_adapter_does_not_mutate_input_and_does_not_require_schema_change() -> None:
    response = _envelope(_base_output())
    before = deepcopy(response)

    view_model = build_result_view_model(response)

    assert response == before
    assert view_model.meta["public_schema_changed"] is False
    assert view_model.meta["presentation_version"] == "v1.1-adapter"


def test_adapter_accepts_output_dict_without_envelope() -> None:
    view_model = build_result_view_model(_base_output())

    assert view_model.verdict_card.primary_text == "Return what can be returned."
    assert view_model.meta["source"] == "v1_engine_response"


def test_self_harm_like_case_creates_safety_card() -> None:
    output = _base_output()
    output["dilemma"] = "I feel everyone would be better without me and I may do anything harmful tonight."

    view_model = build_result_view_model(_envelope(output))

    assert view_model.presentation_mode == "crisis_safe"
    assert view_model.safety_card is not None
    assert view_model.safety_card.title == "Safety Note"
    assert "immediate human support" in view_model.safety_card.primary_text
    assert view_model.safety_card.sections[0].default_open is True
    assert view_model.guidance_card.title == "Support first"
    assert view_model.higher_path_card.title == "Immediate Next Step"
    assert "moral decision" in view_model.higher_path_card.primary_text.lower()
    assert "Adharmic" not in view_model.counterfactuals_card.primary_text
    assert "Dharmic" not in view_model.counterfactuals_card.primary_text
    for sec in view_model.counterfactuals_card.sections:
        assert "Adharmic" not in sec.label
        assert "Dharmic" not in sec.label
    assert "Score:" not in view_model.ethical_dimensions_card.primary_text
    assert view_model.share_card.primary_text == ""
    assert view_model.share_card.needs_copy_refinement is False
    assert view_model.meta["presentation_mode"] == "crisis_safe"
    assert "Why this applies to your situation" not in _section_labels(view_model.verdict_card)


def _section_labels(card) -> list[str]:
    return [section.label for section in card.sections]


def _section_text(card, label: str) -> str:
    for section in card.sections:
        if section.label == label:
            return section.text
    raise AssertionError(f"Missing section: {label}")
