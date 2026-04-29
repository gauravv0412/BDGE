"""Strict validation for public feedback payloads."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

ALLOWED_SIGNALS = {"up", "down"}
ALLOWED_TAGS = {
    "verdict_felt_right",
    "verse_felt_relevant",
    "too_harsh",
    "too_vague",
    "unsafe_concerning",
}
ALLOWED_ROUTES = {"presentation"}
ALLOWED_THEMES = {"light", "dark"}
ALLOWED_GUIDANCE_TYPES = {"verse_match", "closest_teaching", "none"}
ALLOWED_KEYS = {
    "result_id",
    "dilemma_id",
    "usefulness",
    "verse_relevance",
    "tags",
    "comment",
    "route",
    "client_theme",
    "guidance_type",
}
MAX_RESULT_ID_LEN = 64
MAX_COMMENT_LEN = 500
MAX_TAGS = 5


@dataclass(frozen=True)
class FeedbackValidationError(Exception):
    """User-safe validation failure for feedback requests."""

    message: str = "Invalid feedback payload."


def validate_feedback_payload(payload: object) -> dict[str, object]:
    if not isinstance(payload, dict):
        raise FeedbackValidationError()

    unknown = set(payload) - ALLOWED_KEYS
    if unknown:
        raise FeedbackValidationError()

    result_id = _clean_result_id(payload.get("result_id") or payload.get("dilemma_id"))
    if not result_id:
        raise FeedbackValidationError()

    route = _clean_required_enum(payload.get("route"), ALLOWED_ROUTES)
    usefulness = _clean_optional_signal(payload.get("usefulness"))
    verse_relevance = _clean_optional_signal(payload.get("verse_relevance"))
    tags = _clean_tags(payload.get("tags", []))
    comment = _clean_comment(payload.get("comment"))
    client_theme = _clean_optional_enum(payload.get("client_theme"), ALLOWED_THEMES)
    guidance_type = _clean_optional_enum(payload.get("guidance_type"), ALLOWED_GUIDANCE_TYPES) or "none"

    return {
        "result_id": result_id,
        "usefulness": usefulness,
        "verse_relevance": verse_relevance,
        "tags": tags,
        "comment": comment,
        "route": route,
        "client_theme": client_theme,
        "guidance_type": guidance_type,
    }


def _clean_result_id(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    if not cleaned or len(cleaned) > MAX_RESULT_ID_LEN:
        return None
    return cleaned


def _clean_optional_signal(value: Any) -> str | None:
    if value is None:
        return None
    return _clean_required_enum(value, ALLOWED_SIGNALS)


def _clean_required_enum(value: Any, allowed: set[str]) -> str:
    if not isinstance(value, str):
        raise FeedbackValidationError()
    cleaned = value.strip()
    if cleaned not in allowed:
        raise FeedbackValidationError()
    return cleaned


def _clean_optional_enum(value: Any, allowed: set[str]) -> str | None:
    if value is None:
        return None
    return _clean_required_enum(value, allowed)


def _clean_tags(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or len(value) > MAX_TAGS:
        raise FeedbackValidationError()
    seen: set[str] = set()
    tags: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise FeedbackValidationError()
        cleaned = item.strip()
        if cleaned not in ALLOWED_TAGS:
            raise FeedbackValidationError()
        if cleaned not in seen:
            seen.add(cleaned)
            tags.append(cleaned)
    return tags


def _clean_comment(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise FeedbackValidationError()
    cleaned = value.strip()
    if not cleaned:
        return None
    if len(cleaned) > MAX_COMMENT_LEN:
        raise FeedbackValidationError()
    return cleaned
