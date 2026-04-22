"""
Post-generation guard checks for semantic scorer payloads.
"""

from __future__ import annotations

from typing import Any

_BANNED_WORDS = {"evil", "sinful", "shameful", "disgusting", "pure", "holy"}
_SCRIPTURE_MARKERS = (
    "bhagavad gita",
    "chapter ",
    "verse ",
    "shloka",
    "śloka",
    "2.47",
    "16.21",
)


def check_no_fake_scripture(payload: dict[str, Any]) -> list[str]:
    """
    Placeholder scripture check.

    For scaffold mode, we simply block obvious scripture-claim markers in text
    fields that should be semantic prose.
    """
    issues: list[str] = []
    text_fields = [
        payload.get("core_reading", ""),
        payload.get("gita_analysis", ""),
        payload.get("higher_path", ""),
        payload.get("share_layer", {}).get("card_quote", ""),
    ]
    lower_blob = " ".join(str(t).lower() for t in text_fields)
    for marker in _SCRIPTURE_MARKERS:
        if marker in lower_blob:
            issues.append(f"possible_scripture_claim: found marker '{marker}'")
            break
    return issues


def check_banned_words(payload: dict[str, Any]) -> list[str]:
    """Block restricted words in selected narrative fields."""
    issues: list[str] = []
    restricted_fields = {
        "core_reading": payload.get("core_reading", ""),
        "gita_analysis": payload.get("gita_analysis", ""),
        "share_layer.card_quote": payload.get("share_layer", {}).get("card_quote", ""),
    }
    for field_name, text in restricted_fields.items():
        lower_text = str(text).lower()
        for word in _BANNED_WORDS:
            if word in lower_text:
                issues.append(f"{field_name}: contains banned word '{word}'")
    return issues


def check_reflective_question(payload: dict[str, Any]) -> list[str]:
    """Ensure share_layer.reflective_question ends with a question mark."""
    question = str(payload.get("share_layer", {}).get("reflective_question", ""))
    if question.endswith("?"):
        return []
    return ["share_layer.reflective_question must end with '?'"]


def check_ambiguity_not_conflated(payload: dict[str, Any]) -> list[str]:
    """
    Basic placeholder check for v2.1.1 ambiguity semantics.

    Non-empty missing_facts should not imply ambiguity_flag must be true.
    This check only ensures types and presence are coherent.
    """
    issues: list[str] = []
    ambiguity_flag = payload.get("ambiguity_flag")
    missing_facts = payload.get("missing_facts")
    if not isinstance(ambiguity_flag, bool):
        issues.append("ambiguity_flag must be boolean")
    if not isinstance(missing_facts, list):
        issues.append("missing_facts must be a list")
    return issues


def run_post_generation_guards(payload: dict[str, Any]) -> tuple[bool, list[str]]:
    """Run all guard checks and return (ok, issues)."""
    issues = []
    issues.extend(check_no_fake_scripture(payload))
    issues.extend(check_banned_words(payload))
    issues.extend(check_reflective_question(payload))
    issues.extend(check_ambiguity_not_conflated(payload))
    return (len(issues) == 0, issues)

