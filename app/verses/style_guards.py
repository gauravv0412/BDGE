"""Style/tone guards for verse explanations and fallbacks."""

from __future__ import annotations

import re

_SANSKRIT_MARKERS = ("॥", "karmaṇ", "dharmaḥ", "ś", "ā", "ī", "ū", "ṛ", "ṅ", "ñ", "ṭ", "ḍ")
_DEBUG_LEAK_MARKERS = (
    "deterministic match basis",
    "themes=",
    "applies_when=",
    "score=",
    "blockers=",
)
_OVERCLAIM_MARKERS = (
    "the gita clearly commands",
    "the gita commands",
    "scripture proves",
    "this verse proves",
)
_PREACHY_IMPERATIVES_RE = re.compile(r"\b(you must|you should|do this now)\b", re.IGNORECASE)
_FAKE_QUOTE_RE = re.compile(r"\"[^\"]+\"")


def check_no_sanskrit(text: str) -> bool:
    lowered = text.lower()
    return not any(marker in lowered for marker in _SANSKRIT_MARKERS)


def check_no_debug_leak(text: str) -> bool:
    lowered = text.lower()
    return not any(marker in lowered for marker in _DEBUG_LEAK_MARKERS)


def check_no_overclaim(text: str) -> bool:
    lowered = text.lower()
    return not any(marker in lowered for marker in _OVERCLAIM_MARKERS)


def check_no_fake_quote_behavior(text: str) -> bool:
    return _FAKE_QUOTE_RE.search(text) is None


def check_no_preachy_imperative(text: str) -> bool:
    return _PREACHY_IMPERATIVES_RE.search(text) is None


def evaluate_why_it_applies_style(text: str) -> list[str]:
    issues: list[str] = []
    if not check_no_debug_leak(text):
        issues.append("why_it_applies_debug_leak")
    if not check_no_overclaim(text):
        issues.append("why_it_applies_overclaim")
    if len(text) > 500:
        issues.append("why_it_applies_too_long")
    return issues


def evaluate_closest_teaching_style(text: str) -> list[str]:
    issues: list[str] = []
    if not check_no_sanskrit(text):
        issues.append("closest_teaching_contains_sanskrit")
    if not check_no_fake_quote_behavior(text):
        issues.append("closest_teaching_quote_like")
    if not check_no_overclaim(text):
        issues.append("closest_teaching_overclaim")
    if not check_no_preachy_imperative(text):
        issues.append("closest_teaching_preachy_imperative")
    if len(text) > 500:
        issues.append("closest_teaching_too_long")
    return issues

