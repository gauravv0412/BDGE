"""Telemetry helpers for narrator metadata."""

from __future__ import annotations

from typing import Any


def narrator_meta(
    *,
    source: str,
    provider_called: bool,
    shadow_mode: bool,
    accepted: bool,
    fallback_returned: bool,
    initial_attempt_valid: bool,
    initial_rejection_reasons: list[str],
    repair_attempted: bool,
    repair_valid: bool,
    repair_rejection_reasons: list[str],
    final_source: str,
    repair_attempt_count: int,
    rejection_reasons: list[str] | None = None,
    accepted_llm_preview: dict[str, str] | None = None,
) -> dict[str, Any]:
    meta = {
        "source": source,
        "provider_called": provider_called,
        "shadow_mode": shadow_mode,
        "accepted": accepted,
        "fallback_returned": fallback_returned,
        "initial_attempt_valid": initial_attempt_valid,
        "initial_rejection_reasons": initial_rejection_reasons,
        "repair_attempted": repair_attempted,
        "repair_valid": repair_valid,
        "repair_rejection_reasons": repair_rejection_reasons,
        "final_source": final_source,
        "repair_attempt_count": repair_attempt_count,
        "rejection_reasons": rejection_reasons or [],
    }
    if accepted_llm_preview is not None:
        meta["accepted_llm_preview"] = accepted_llm_preview
    return meta
