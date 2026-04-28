"""Validation rules for LLM narrator output."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

_INTERNAL_TERMS = (
    "theme",
    "themes",
    "dimension",
    "dimensions",
    "scorer",
    "classification",
    "score",
)

_PREACHY_PATTERNS = (
    "you must",
    "you should",
    "shame on",
    "disgusting",
    "bad person",
    "you are evil",
)

_VERSE_INVENTION_PATTERNS = (
    r"\bchapter\s+\d+\s*verse\s+\d+",
    r"\bbg\s*\d+\.\d+",
    r"\b\d+\.\d+\b",
)

_REPETITIVE_OPENING_PATTERNS = (
    (r"^\s*the real test\s+(?:isn't|is not)\b", "repeated template: the real test isn't"),
    (r"^\s*the real question\s+(?:isn't|is not)\b", "repeated template: the real question isn't"),
    (r"^\s*the choice\s+(?:isn't|is not)\b", "repeated template: the choice isn't"),
)

_GENERIC_OPENING_PATTERNS = (
    (r"^\s*this decision\b", "generic opening: this decision"),
    (r"^\s*this choice\b", "generic opening: this choice"),
    (r"^\s*the situation\b", "generic opening: the situation"),
    (r"^\s*at the end of the day\b", "generic opening: at the end of the day"),
    (r"^\s*the key is\b", "generic opening: the key is"),
)

_GENERIC_SHARE_LINE_PATTERNS = (
    r"\bdo the right thing\b",
    r"\bmake a good choice\b",
    r"\bchoose wisely\b",
    r"\btake the high road\b",
    r"\bbe honest\b",
    r"\bfollow your heart\b",
    r"\bthink carefully\b",
    r"\bmake the ethical choice\b",
    r"\bthis is important\b",
)


def validate_narrator_output(
    *,
    narrator: dict[str, Any],
    engine_output: dict[str, Any],
    presentation_mode: str,
) -> tuple[bool, str | None]:
    required_paths = [
        ("simple", "headline"),
        ("simple", "explanation"),
        ("simple", "next_step"),
        ("krishna_lens", "question"),
        ("krishna_lens", "teaching"),
        ("krishna_lens", "mirror"),
        ("brutal_truth", "headline"),
        ("brutal_truth", "punchline"),
        ("brutal_truth", "share_quote"),
        ("deep_view", "what_is_happening"),
        ("deep_view", "risk"),
        ("deep_view", "higher_path"),
    ]
    for section, key in required_paths:
        if not isinstance(narrator.get(section), dict):
            return False, f"missing section {section}"
        value = narrator[section].get(key)
        if not isinstance(value, str) or not value.strip():
            return False, f"missing field {section}.{key}"
    share_line = narrator.get("share_line")
    if not isinstance(share_line, str) or not share_line.strip():
        return False, "missing field share_line"
    share_line_valid, share_line_reason = _validate_share_line(share_line)
    if not share_line_valid:
        return False, share_line_reason

    full_text = _all_text(narrator).lower()
    for term in _INTERNAL_TERMS:
        if re.search(rf"\b{re.escape(term)}\b", full_text):
            return False, f"internal taxonomy leaked: {term}"
    for phrase in _PREACHY_PATTERNS:
        if phrase in full_text:
            return False, f"preachy language: {phrase}"

    if presentation_mode == "crisis_safe":
        crisis_banned = ("krishna", "spiritual", "viral", "share this")
        for word in crisis_banned:
            if word in full_text:
                return False, f"crisis-safe violation: {word}"

    if _has_direction_contradiction(full_text, str(engine_output.get("classification", ""))):
        return False, "verdict direction contradiction"

    if _changes_intensity(full_text, str(engine_output.get("classification", ""))):
        return False, "classification intensification"

    if _contradicts_higher_path(full_text, str(engine_output.get("higher_path", ""))):
        return False, "higher_path contradiction"

    if _identical_cross_section_copy(narrator):
        return False, "duplicate copy across sections"

    verse_match = engine_output.get("verse_match")
    if not isinstance(verse_match, dict):
        for pattern in _VERSE_INVENTION_PATTERNS:
            if re.search(pattern, full_text, flags=re.IGNORECASE):
                return False, "invented direct verse in closest_teaching case"

    return True, None


def detect_style_repetition_warnings(previews: list[dict[str, str]]) -> list[dict[str, Any]]:
    """Return non-blocking batch style warnings for shadow-eval review."""
    counts: Counter[str] = Counter()
    examples: dict[str, list[str]] = {}
    for preview in previews:
        headline = _normalize(str(preview.get("simple.headline") or ""))
        if not headline:
            continue
        for pattern, label in (*_REPETITIVE_OPENING_PATTERNS, *_GENERIC_OPENING_PATTERNS):
            if re.search(pattern, headline):
                counts[label] += 1
                examples.setdefault(label, []).append(headline[:160])
    warnings: list[dict[str, Any]] = []
    for label, count in counts.items():
        threshold = 0 if label.startswith("repeated template:") else 2
        if count > threshold:
            warnings.append(
                {
                    "warning": label,
                    "count": count,
                    "examples": examples.get(label, [])[:3],
                }
            )
    return warnings


def _all_text(narrator: dict[str, Any]) -> str:
    parts: list[str] = [str(narrator.get("share_line") or "").strip()]
    for section in ("simple", "krishna_lens", "brutal_truth", "deep_view"):
        block = narrator.get(section)
        if isinstance(block, dict):
            for value in block.values():
                if isinstance(value, str):
                    parts.append(value.strip())
    return " ".join(parts)


def _validate_share_line(value: str) -> tuple[bool, str | None]:
    stripped = value.strip()
    lines = [line for line in stripped.splitlines() if line.strip()]
    if len(lines) > 2:
        return False, "share_line too long"
    normalized = _normalize(stripped)
    if len(normalized.split()) < 5:
        return False, "share_line too generic"
    for pattern in _GENERIC_SHARE_LINE_PATTERNS:
        if re.search(pattern, normalized):
            return False, "share_line generic advice"
    for pattern, label in _REPETITIVE_OPENING_PATTERNS:
        if re.search(pattern, normalized):
            return False, f"share_line {label}"
    for pattern, label in _GENERIC_OPENING_PATTERNS:
        if re.search(pattern, normalized):
            return False, f"share_line {label}"
    return True, None


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def _identical_cross_section_copy(narrator: dict[str, Any]) -> bool:
    section_blobs: list[str] = []
    for section in ("simple", "brutal_truth", "deep_view"):
        block = narrator.get(section, {})
        if isinstance(block, dict):
            blob = _normalize(" ".join(v for v in block.values() if isinstance(v, str)))
            section_blobs.append(blob)
    unique = {blob for blob in section_blobs if blob}
    return len(unique) < len(section_blobs)


def _has_direction_contradiction(text: str, classification: str) -> bool:
    c = classification.strip().lower()
    positive_claims = (
        "this is ethical",
        "this is right",
        "this is clean",
        "you are right to do this",
    )
    negative_claims = (
        "this is unethical",
        "this is wrong",
        "you should not do this",
        "this is harmful and unjustified",
    )
    if c == "dharmic":
        return any(token in text for token in negative_claims)
    if c == "adharmic":
        return any(token in text for token in positive_claims)
    return False


def _changes_intensity(text: str, classification: str) -> bool:
    c = classification.strip().lower()
    absolute_tokens = (
        "no doubt",
        "certainly",
        "guaranteed",
        "100% sure",
        "pure evil",
        "completely righteous",
        "absolutely right",
        "absolutely wrong",
    )
    if c in {"mixed", "context-dependent", "insufficient information"}:
        return any(token in text for token in absolute_tokens)
    return False


def _contradicts_higher_path(text: str, higher_path: str) -> bool:
    hp = higher_path.strip().lower()
    if not hp:
        return False
    contradiction_pairs = [
        (("return", "restore"), ("keep", "hold onto", "take it")),
        (("disclose", "tell the truth"), ("hide", "conceal", "cover up")),
        (("pause", "wait"), ("rush", "act immediately")),
        (("set a boundary", "distance"), ("stay available for harm", "ignore boundary")),
    ]
    for positives, negatives in contradiction_pairs:
        if any(token in hp for token in positives) and any(token in text for token in negatives):
            return True
    return False
