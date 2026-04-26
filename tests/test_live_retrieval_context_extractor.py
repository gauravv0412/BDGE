"""Tests for deterministic sparse-text retrieval context extraction."""

from __future__ import annotations

from app.core.benchmark_loader import load_dilemmas
from app.verses.context_extractor import extract_live_retrieval_context_signals


def test_w001_w020_sparse_dilemmas_produce_useful_retrieval_signals() -> None:
    rows = load_dilemmas()

    assert len(rows) == 20
    for item in rows:
        signals = extract_live_retrieval_context_signals(str(item["dilemma"]))
        assert (
            signals["theme_tags"]
            or signals["applies_signals"]
            or signals["blocker_signals"]
            or signals["dominant_dimensions"]
        ), item["dilemma_id"]


def test_public_correction_extracts_speech_conflict() -> None:
    signals = extract_live_retrieval_context_signals(
        "My manager takes credit for my work. Should I publicly correct him?"
    )

    assert {"speech", "truth"}.issubset(set(signals["theme_tags"]))
    assert "ethical-speech" in signals["applies_signals"]


def test_found_wallet_extracts_private_integrity() -> None:
    signals = extract_live_retrieval_context_signals(
        "I found a wallet and picked it up. Should I keep the cash?"
    )

    assert {"self-mastery", "restraint"}.issubset(set(signals["theme_tags"]))
    assert "found-property" in signals["applies_signals"]


def test_abusive_parent_extracts_abuse_blocker() -> None:
    signals = extract_live_retrieval_context_signals(
        "My elderly parent is abusive and controlling. I want to cut contact."
    )

    assert "abuse-context" in signals["blocker_signals"]


def test_neutral_role_does_not_trigger_duty() -> None:
    signals = extract_live_retrieval_context_signals(
        "The actor accepted a role in a school play."
    )

    assert "duty" not in signals["theme_tags"]


def test_neutral_review_does_not_trigger_ethical_speech() -> None:
    signals = extract_live_retrieval_context_signals(
        "The quarterly business review is scheduled for Friday."
    )

    assert "speech" not in signals["theme_tags"]
    assert "ethical-speech" not in signals["applies_signals"]


def test_untruth_does_not_trigger_truth() -> None:
    signals = extract_live_retrieval_context_signals(
        "This is an untruthful-looking variable name in test data."
    )

    assert "truth" not in signals["theme_tags"]


def test_generic_job_alone_does_not_trigger_karma_yoga_duty() -> None:
    signals = extract_live_retrieval_context_signals("I have a job downtown.")

    assert "duty" not in signals["theme_tags"]
    assert "duty-conflict" not in signals["applies_signals"]


def test_generic_family_alone_does_not_trigger_filial_duty() -> None:
    signals = extract_live_retrieval_context_signals("My family is visiting this weekend.")

    assert "duty" not in signals["theme_tags"]
    assert "provider-duty" not in signals["applies_signals"]


def test_routine_doctor_visit_does_not_trigger_medical_disclosure() -> None:
    signals = extract_live_retrieval_context_signals("I saw my doctor today for a checkup.")

    assert "truth" not in signals["theme_tags"]
    assert "terminal-diagnosis-disclosure" not in signals["applies_signals"]
    assert "truth-compassion-conflict" not in signals["applies_signals"]


def test_doctor_with_terminal_patient_context_does_trigger_disclosure() -> None:
    signals = extract_live_retrieval_context_signals(
        "The doctor wants to hide the terminal diagnosis from the patient's family."
    )

    assert "truth" in signals["theme_tags"]
    assert "terminal-diagnosis-disclosure" in signals["applies_signals"]


def test_positive_review_intent_does_not_trigger_public_shaming() -> None:
    signals = extract_live_retrieval_context_signals(
        "I want to leave a positive review for the restaurant."
    )

    assert "public-shaming-intent" not in signals["blocker_signals"]
    assert "ethical-speech" not in signals["applies_signals"]


def test_scathing_review_intent_still_triggers_public_shaming() -> None:
    signals = extract_live_retrieval_context_signals(
        "I am tempted to leave a scathing review to destroy their business."
    )

    assert "public-shaming-intent" in signals["blocker_signals"]
    assert "ethical-speech" in signals["applies_signals"]


def test_ood_expected_verse_families_extract_strong_signals() -> None:
    examples = [
        ("I found extra cash in the ATM tray. Should I keep it?", "found-property"),
        ("Should I expose his mistakes in front of leadership?", "ethical-speech"),
        ("I'm attracted to a married colleague who flirts with me.", "temptation"),
        ("My mother refuses dialysis. Should I force treatment?", "bereavement"),
        ("My family owns a legal gambling shop.", "livelihood-harm-tradeoff"),
        ("My factory dumps untreated water. If I report it, my cousins may lose jobs.", "whistleblowing-risk"),
        ("A cashier forgot to scan an item. Should I go back and pay?", "found-property"),
        ("The patient asked me directly about the biopsy result.", "truth-compassion-conflict"),
        ("I'm considering not voting in the next election because I dislike all candidates.", "duty-conflict"),
        ("A beggar at the signal — should I give money, or does it perpetuate the cycle?", "service-without-return"),
        ("My startup is failing and investors gave me money. Should I shut down?", "duty-conflict"),
        ("My company's product is addictive by design. I'm well paid. Should I quit?", "livelihood-harm-tradeoff"),
        ("I'm thinking about having an affair because my marriage is sexless.", "temptation"),
        ("I found the answer key leaked online before my exam.", "temptation"),
        ("Should I stay in a job I hate because it pays my EMI?", "outcome-anxiety"),
        ("I want to be a stay-at-home parent. My spouse earns enough.", "career-crossroads"),
        ("Is it adharmic to be rich?", "private-conduct-test"),
        ("I want to call out a celebrity's hypocrisy online. They preach one thing and do another.", "ethical-speech"),
    ]

    for text, expected_signal in examples:
        signals = extract_live_retrieval_context_signals(text)
        assert expected_signal in signals["applies_signals"], text


def test_money_alone_does_not_trigger_private_integrity_temptation() -> None:
    signals = extract_live_retrieval_context_signals("Money is stressful this month.")

    assert "found-property" not in signals["applies_signals"]
    assert "self-mastery" not in signals["theme_tags"]


def test_friend_alone_does_not_trigger_betrayal_revenge() -> None:
    signals = extract_live_retrieval_context_signals("A friend is coming over for tea.")

    assert "retaliatory-speech" not in signals["blocker_signals"]
    assert "anger-spike" not in signals["applies_signals"]


def test_love_alone_does_not_trigger_desire_restraint() -> None:
    signals = extract_live_retrieval_context_signals("I love classical music.")

    assert "desire" not in signals["theme_tags"]
    assert "temptation" not in signals["applies_signals"]


def test_sex_in_neutral_health_context_does_not_trigger_lust() -> None:
    signals = extract_live_retrieval_context_signals(
        "The health class discussed sex education and consent."
    )

    assert "desire" not in signals["theme_tags"]
    assert "temptation" not in signals["applies_signals"]


def test_ai_alone_does_not_trigger_deepfake_deception() -> None:
    signals = extract_live_retrieval_context_signals("AI helped me organize my notes.")

    assert "deception" not in signals["blocker_signals"]
    assert "ethical-speech" not in signals["applies_signals"]


def test_animal_pet_care_does_not_trigger_animal_harm() -> None:
    signals = extract_live_retrieval_context_signals("My animal needs routine pet care.")

    assert "active-harm" not in signals["blocker_signals"]


def test_generic_environment_discussion_does_not_trigger_pollution_public_harm() -> None:
    signals = extract_live_retrieval_context_signals(
        "We had a generic environment discussion at school."
    )

    assert "whistleblowing-risk" not in signals["applies_signals"]
    assert "welfare-of-all" not in signals["theme_tags"]


def test_new_reference_signal_families_have_negative_controls() -> None:
    examples = [
        ("The voting machine was repaired before the election.", "duty-conflict"),
        ("A candidate visited our office for lunch.", "duty-conflict"),
        ("I saw a beggar in a movie scene.", "service-without-return"),
        ("Investors read our public startup blog.", "duty-conflict"),
        ("This product tutorial is addictive to watch.", "livelihood-harm-tradeoff"),
        ("The word affair appears in a newspaper headline.", "temptation"),
        ("The teacher mentioned answer keys after the exam.", "temptation"),
        ("The bank explained how EMI works.", "outcome-anxiety"),
        ("My parent stayed at home today.", "career-crossroads"),
        ("A rich dessert was served after dinner.", "private-conduct-test"),
        ("A celebrity posted a recipe online.", "ethical-speech"),
    ]

    for text, blocked_signal in examples:
        signals = extract_live_retrieval_context_signals(text)
        assert blocked_signal not in signals["applies_signals"], text


def test_self_defense_and_meaninglessness_extract_severe_blockers() -> None:
    self_defense = extract_live_retrieval_context_signals("Is killing in self-defense adharmic?")
    meaningless = extract_live_retrieval_context_signals(
        "I feel my life is meaningless. I go through motions."
    )

    assert "active-harm" in self_defense["blocker_signals"]
    assert "self-harm" in meaningless["blocker_signals"]
