"""Tests for presentation narrator prompt builders."""

from __future__ import annotations

import json

from app.presentation.prompts import build_narrator_repair_user_prompt, build_narrator_user_prompt, select_narrator_style


def test_repair_prompt_includes_rejection_specific_constraints() -> None:
    prompt = build_narrator_repair_user_prompt(
        output={"classification": "Mixed", "higher_path": "Pause and document the facts."},
        deterministic_presentation={"presentation_mode": "standard"},
        rejected_narrator={"simple": {"headline": "You should trust the score."}},
        rejection_reasons=[
            "preachy language: you should",
            "internal taxonomy leaked: score",
            "classification intensification",
        ],
    )

    payload = json.loads(prompt)
    constraints = "\n".join(payload["repair_constraints"])

    assert 'Remove preachy phrase "you should" everywhere.' in constraints
    assert "Use observational phrasing instead of commands." in constraints
    assert "Remove score/classification/dimension/theme/scorer language" in constraints
    assert "Preserve edge but reduce certainty." in constraints
    assert '"this leans", "this risks", or "this looks like"' in constraints
    assert "Treat every repair_constraint as a hard constraint" in payload["instruction"]


def test_narrator_prompt_includes_style_and_anti_repetition_constraints() -> None:
    prompt = build_narrator_user_prompt(
        output={"dilemma_id": "W001", "dilemma": "Should I publicly correct my manager?"},
        deterministic_presentation={"presentation_mode": "standard"},
    )

    payload = json.loads(prompt)
    constraints = "\n".join(payload["anti_repetition_constraints"])

    assert payload["style_profile"]["name"] == select_narrator_style("W001")["name"]
    assert "Do not reuse opening templates across responses." in constraints
    assert "the real test" in constraints
    assert "simple.headline must be one strong hook" in constraints
    assert "brutal_truth.punchline must be dense" in constraints
    assert "share_line" in payload["instruction"] or "share_line_requirements" in payload
    assert "share_line must be highly memorable" in "\n".join(payload["share_line_requirements"])
    assert "This feels small. It isn't." in payload["hook_examples"]
    assert "This works today. It weakens you tomorrow." in payload["share_line_examples"]


def test_style_selection_varies_across_benchmark_ids() -> None:
    styles = {select_narrator_style(f"W{i:03d}")["name"] for i in range(1, 21)}

    assert len(styles) >= 3
