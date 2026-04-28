"""Prompt builders for presentation narrator and repair loop."""

from __future__ import annotations

import hashlib
import json
from typing import Any

_STYLE_PROFILES = (
    {
        "name": "blunt_confrontational",
        "instruction": "Blunt / confrontational: direct, tight, no throat-clearing, no shaming.",
    },
    {
        "name": "reflective_calm",
        "instruction": "Reflective / calm: clear-eyed, spacious, emotionally steady.",
    },
    {
        "name": "sharp_punchline_heavy",
        "instruction": "Sharp / punchline-heavy: compressed, memorable, built around one clean hook.",
    },
    {
        "name": "krishna_like_questioning",
        "instruction": "Krishna-like questioning: probing questions, mirror-like insight, no commands.",
    },
    {
        "name": "practical_grounded",
        "instruction": "Practical / grounded: concrete, usable, plainspoken, still vivid.",
    },
)

_ANTI_REPETITION_CONSTRAINTS = (
    "Do not reuse opening templates across responses.",
    'Do not use the pattern "the real test isn\'t...", "the real question isn\'t...", or "the choice isn\'t...".',
    "simple.headline must be one strong hook, not a structured explanation.",
    "simple.headline should not start with a repeated template.",
    "brutal_truth.punchline must be dense, memorable, and no more than 2-3 sentences.",
)

_SHARE_LINE_REQUIREMENTS = (
    "Produce top-level share_line.",
    "share_line must be 1-2 lines max.",
    "share_line must be highly memorable, screenshot-worthy, emotionally compressed, and specific.",
    "share_line must not be generic advice.",
    "share_line must not use repeated phrasing patterns.",
    "share_line must not be preachy.",
    "share_line must align with the core decision direction and higher_path.",
)

_HOOK_EXAMPLES = (
    "You're not choosing between X and Y. You're choosing who you become after this.",
    "This feels small. It isn't.",
    "You already know what's wrong here.",
    "This is where people start lying to themselves.",
)

_SHARE_LINE_EXAMPLES = (
    "You're not choosing the easier path. You're choosing the habit you'll repeat.",
    "This works today. It weakens you tomorrow.",
    "You're not protecting them. You're protecting your discomfort.",
    "The decision isn't the problem. The pattern is.",
)


def build_narrator_system_prompt() -> str:
    return (
        "You are Wisdomize Presentation Narrator v1.\n"
        "Rewrite only presentation copy for UI readability and emotional clarity.\n"
        "Do not alter decision semantics from the provided engine output.\n"
        "Hard constraints:\n"
        "- Never change classification direction, alignment_score, confidence, or verdict meaning.\n"
        "- Never edit, paraphrase, or invent verse_ref or scripture translations.\n"
        "- If verse_match is null, never imply a direct verse quote.\n"
        "- Preserve missing_facts meaning; do not erase uncertainty.\n"
        "- Never use internal taxonomy terms: theme, themes, dimension, scorer, classification, score.\n"
        "- Avoid preachy or shaming language.\n"
        "- Strong tone, provocative framing, emotional compression, and spicy metaphors are allowed when grounded.\n"
        '- Never reuse "the real test/question/choice isn\'t..." opening templates.\n'
        "- Vary style across outputs: blunt, reflective, punchline-heavy, Krishna-like questioning, or practical.\n"
        "- Always include top-level share_line: 1-2 lines, screenshot-worthy, compressed, non-generic, and aligned.\n"
        "- Output valid JSON only, no markdown.\n"
        "JSON shape:\n"
        "{"
        '"share_line":"",'
        '"simple":{"headline":"","explanation":"","next_step":""},'
        '"krishna_lens":{"question":"","teaching":"","mirror":""},'
        '"brutal_truth":{"headline":"","punchline":"","share_quote":""},'
        '"deep_view":{"what_is_happening":"","risk":"","higher_path":""}'
        "}"
    )


def build_narrator_user_prompt(
    *,
    output: dict[str, Any],
    deterministic_presentation: dict[str, Any],
) -> str:
    style_profile = select_narrator_style(output)
    payload = {
        "engine_output": output,
        "deterministic_presentation": deterministic_presentation,
        "style_profile": style_profile,
        "anti_repetition_constraints": list(_ANTI_REPETITION_CONSTRAINTS),
        "share_line_requirements": list(_SHARE_LINE_REQUIREMENTS),
        "hook_examples": list(_HOOK_EXAMPLES),
        "share_line_examples": list(_SHARE_LINE_EXAMPLES),
        "instruction": (
            "Rewrite UI copy to be clear and human while preserving decision content. "
            "Use deterministic presentation as grounding and do not add new claims. "
            "Follow the selected style_profile for this response so outputs do not all sound the same."
        ),
    }
    return json.dumps(payload, ensure_ascii=False)


def build_narrator_repair_user_prompt(
    *,
    output: dict[str, Any],
    deterministic_presentation: dict[str, Any],
    rejected_narrator: dict[str, Any],
    rejection_reasons: list[str],
) -> str:
    repair_constraints = _repair_constraints_for_rejections(rejection_reasons)
    style_profile = select_narrator_style(output)
    payload = {
        "engine_output": output,
        "deterministic_presentation": deterministic_presentation,
        "rejected_narrator_output": rejected_narrator,
        "rejection_reasons": rejection_reasons,
        "style_profile": style_profile,
        "anti_repetition_constraints": list(_ANTI_REPETITION_CONSTRAINTS),
        "share_line_requirements": list(_SHARE_LINE_REQUIREMENTS),
        "repair_constraints": repair_constraints,
        "instruction": (
            "Repair only the invalid parts. Preserve core decision direction and meaning. "
            "Keep the viral punch, emotional compression, and sharp language. "
            "Treat every repair_constraint as a hard constraint. "
            "Do not flatten into generic advice. Return valid JSON only."
        ),
    }
    return json.dumps(payload, ensure_ascii=False)


def select_narrator_style(output_or_key: dict[str, Any] | str) -> dict[str, str]:
    """Pick a stable style profile so batch evals rotate without test flakiness."""
    if isinstance(output_or_key, dict):
        key = str(output_or_key.get("dilemma_id") or output_or_key.get("dilemma") or "")
    else:
        key = output_or_key
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    idx = int(digest[:8], 16) % len(_STYLE_PROFILES)
    return dict(_STYLE_PROFILES[idx])


def _repair_constraints_for_rejections(rejection_reasons: list[str]) -> list[str]:
    constraints = [
        "Preserve the engine verdict direction, higher_path, uncertainty, and missing_facts.",
        "Keep punchy tone and vivid language only when it is grounded in the engine output.",
    ]
    for reason in rejection_reasons:
        lowered = reason.lower()
        if lowered.startswith("preachy language:"):
            phrase = reason.split(":", 1)[1].strip() if ":" in reason else "the preachy phrase"
            constraints.extend(
                [
                    f'Remove preachy phrase "{phrase}" everywhere.',
                    "Use observational phrasing instead of commands.",
                    "Keep the punchy tone without shaming the person.",
                ]
            )
        if "internal taxonomy leaked" in lowered:
            constraints.append("Remove score/classification/dimension/theme/scorer language and describe the situation in user-facing words.")
        if "classification intensification" in lowered:
            constraints.extend(
                [
                    "Preserve edge but reduce certainty.",
                    'Use calibrated language such as "this leans", "this risks", or "this looks like".',
                    "Avoid absolute moral judgment and certainty language.",
                ]
            )
        if "verdict direction contradiction" in lowered:
            constraints.append("Do not flip the ethical direction; align the repair with the verdict_sentence and higher_path.")
        if "higher_path contradiction" in lowered:
            constraints.append("Make the next_step and higher_path compatible with the engine higher_path.")
        if "invented direct verse" in lowered:
            constraints.append("Do not cite or imply a direct Bhagavad Gita verse when verse_match is null.")
    return constraints
