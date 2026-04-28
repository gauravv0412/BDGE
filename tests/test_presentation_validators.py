"""Tests for presentation narrator validation rules."""

from __future__ import annotations

from app.presentation.validators import detect_style_repetition_warnings, validate_narrator_output


def _engine_output(classification: str = "Mixed") -> dict[str, object]:
    return {
        "classification": classification,
        "higher_path": "Document the facts, pause, and choose the clean next step.",
        "verse_match": None,
    }


def _narrator(**overrides: str) -> dict[str, object]:
    narrator = {
        "share_line": "This works today. It weakens you tomorrow.",
        "simple": {
            "headline": "This leans messy, but the clean step is still visible.",
            "explanation": "Pressure is narrowing the room without making the shortcut wise.",
            "next_step": "Document the facts and pause before acting.",
        },
        "krishna_lens": {
            "question": "What still looks clean after the adrenaline leaves?",
            "teaching": "A sharp moment can still ask for a measured method.",
            "mirror": "The loudest option is not always the clearest one.",
        },
        "brutal_truth": {
            "headline": "Panic is a fog machine.",
            "punchline": "A shortcut can wear a hero cape and still trip the alarm.",
            "share_quote": "Edge is useful only when truth stays in the driver's seat.",
        },
        "deep_view": {
            "what_is_happening": "Urgency is compressing judgment.",
            "risk": "The move risks turning a real concern into avoidable fallout.",
            "higher_path": "Document the facts, pause, and choose the clean next step.",
        },
    }
    for dotted_key, value in overrides.items():
        if dotted_key == "share_line":
            narrator["share_line"] = value
            continue
        section, key = dotted_key.replace("__", ".", 1).split(".", 1)
        block = narrator[section]
        assert isinstance(block, dict)
        block[key] = value
    return narrator


def test_repaired_output_passes_after_removing_you_should() -> None:
    invalid = _narrator(simple__next_step="You should document the facts now.")
    valid = _narrator(simple__next_step="Documenting the facts keeps the move reviewable.")

    assert validate_narrator_output(narrator=invalid, engine_output=_engine_output(), presentation_mode="standard") == (
        False,
        "preachy language: you should",
    )
    assert validate_narrator_output(narrator=valid, engine_output=_engine_output(), presentation_mode="standard") == (True, None)


def test_repaired_output_passes_after_removing_score_language() -> None:
    invalid = _narrator(deep_view__risk="The score proves this is risky.")
    valid = _narrator(deep_view__risk="The move risks turning pressure into avoidable fallout.")

    assert validate_narrator_output(narrator=invalid, engine_output=_engine_output(), presentation_mode="standard") == (
        False,
        "internal taxonomy leaked: score",
    )
    assert validate_narrator_output(narrator=valid, engine_output=_engine_output(), presentation_mode="standard") == (True, None)


def test_viral_spice_allowed_without_truth_drift() -> None:
    narrator = _narrator(
        brutal_truth__punchline="A shortcut can wear a hero cape and still trip the alarm."
    )

    assert validate_narrator_output(narrator=narrator, engine_output=_engine_output(), presentation_mode="standard") == (True, None)


def test_unsupported_certainty_still_rejected_for_mixed_cases() -> None:
    narrator = _narrator(simple__headline="This is 100% sure and completely settled.")

    assert validate_narrator_output(narrator=narrator, engine_output=_engine_output(), presentation_mode="standard") == (
        False,
        "classification intensification",
    )


def test_share_line_required_and_valid_when_memorable() -> None:
    narrator = _narrator(share_line="You're choosing the habit you'll repeat.")

    assert validate_narrator_output(narrator=narrator, engine_output=_engine_output(), presentation_mode="standard") == (True, None)


def test_share_line_must_be_present_and_not_empty() -> None:
    narrator = _narrator(share_line="")

    assert validate_narrator_output(narrator=narrator, engine_output=_engine_output(), presentation_mode="standard") == (
        False,
        "missing field share_line",
    )


def test_share_line_must_be_two_lines_or_less() -> None:
    narrator = _narrator(share_line="Line one.\nLine two.\nLine three.")

    assert validate_narrator_output(narrator=narrator, engine_output=_engine_output(), presentation_mode="standard") == (
        False,
        "share_line too long",
    )


def test_share_line_rejects_generic_advice() -> None:
    narrator = _narrator(share_line="Do the right thing and make a good choice.")

    assert validate_narrator_output(narrator=narrator, engine_output=_engine_output(), presentation_mode="standard") == (
        False,
        "share_line generic advice",
    )


def test_share_line_rejects_repeated_patterns() -> None:
    narrator = _narrator(share_line="The real test isn't whether this feels urgent.")

    assert validate_narrator_output(narrator=narrator, engine_output=_engine_output(), presentation_mode="standard") == (
        False,
        "share_line repeated template: the real test isn't",
    )


def test_share_line_rejects_verdict_contradiction() -> None:
    narrator = _narrator(share_line="This is ethical and clean.")

    assert validate_narrator_output(narrator=narrator, engine_output=_engine_output("Adharmic"), presentation_mode="standard") == (
        False,
        "verdict direction contradiction",
    )


def test_style_repetition_warnings_detect_real_test_templates() -> None:
    warnings = detect_style_repetition_warnings(
        [
            {"simple.headline": "The real test isn't whether you win the room."},
            {"simple.headline": "The real question isn't whether anger is justified."},
            {"simple.headline": "This feels small. It isn't."},
        ]
    )

    labels = {warning["warning"] for warning in warnings}
    assert "repeated template: the real test isn't" in labels
    assert "repeated template: the real question isn't" in labels


def test_style_repetition_warnings_are_soft_not_truth_drift_rejections() -> None:
    narrator = _narrator(simple__headline="The real test isn't whether this hurts.")

    assert validate_narrator_output(narrator=narrator, engine_output=_engine_output(), presentation_mode="standard") == (True, None)
    assert detect_style_repetition_warnings([{"simple.headline": narrator["simple"]["headline"]}])
