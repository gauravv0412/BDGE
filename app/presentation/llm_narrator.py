"""Step 32B: LLM-backed presentation narrator with provider + shadow mode."""

from __future__ import annotations

from typing import Any

from app.presentation.config import load_presentation_llm_config
from app.presentation.provider import call_presentation_provider
from app.presentation.prompts import (
    build_narrator_repair_user_prompt,
    build_narrator_system_prompt,
    build_narrator_user_prompt,
)
from app.presentation.telemetry import narrator_meta
from app.presentation.validators import validate_narrator_output


def build_presentation_narrator(
    *,
    engine_response: dict[str, Any],
    deterministic_presentation: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    output = _extract_output(engine_response)
    mode = str(deterministic_presentation.get("presentation_mode") or "standard")
    config = load_presentation_llm_config()

    if mode == "crisis_safe":
        fallback = _deterministic_narrator(output=output, presentation_mode=mode)
        return fallback, narrator_meta(
            source="deterministic_fallback",
            provider_called=False,
            shadow_mode=False,
            accepted=False,
            fallback_returned=True,
            initial_attempt_valid=False,
            initial_rejection_reasons=["crisis_safe_mode"],
            repair_attempted=False,
            repair_valid=False,
            repair_rejection_reasons=[],
            final_source="deterministic_fallback",
            repair_attempt_count=0,
            rejection_reasons=["crisis_safe_mode"],
        )

    should_call_provider = (config.enabled or config.shadow) and config.provider != "none"
    if not should_call_provider:
        fallback = _deterministic_narrator(output=output, presentation_mode=mode)
        return fallback, narrator_meta(
            source="deterministic_fallback",
            provider_called=False,
            shadow_mode=False,
            accepted=False,
            fallback_returned=True,
            initial_attempt_valid=False,
            initial_rejection_reasons=["provider_disabled"],
            repair_attempted=False,
            repair_valid=False,
            repair_rejection_reasons=[],
            final_source="deterministic_fallback",
            repair_attempt_count=0,
            rejection_reasons=["provider_disabled"],
        )

    system_prompt = build_narrator_system_prompt()
    user_prompt = build_narrator_user_prompt(output=output, deterministic_presentation=deterministic_presentation)
    provider_result = call_presentation_provider(
        config=config,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )

    initial_rejection_reasons: list[str] = []
    repair_rejection_reasons: list[str] = []
    accepted = False
    narrator_candidate: dict[str, Any] | None = None
    initial_attempt_valid = False
    repair_attempted = False
    repair_valid = False
    repair_attempt_count = 0
    no_retry_error_codes = {"timeout", "transport_error", "provider_exception"}
    if provider_result.ok and isinstance(provider_result.payload, dict):
        narrator_candidate = provider_result.payload
        valid, reason = validate_narrator_output(
            narrator=narrator_candidate,
            engine_output=output,
            presentation_mode=mode,
        )
        if valid:
            accepted = True
            initial_attempt_valid = True
        elif reason:
            initial_rejection_reasons.append(reason)
    else:
        initial_rejection_reasons.append(provider_result.error_code or "provider_error")

    if (
        not accepted
        and narrator_candidate is not None
        and config.max_repair_attempts > 0
        and config.repair_enabled
        and not any(reason in no_retry_error_codes or reason.startswith("http_") for reason in initial_rejection_reasons)
    ):
        repair_attempted = True
        repair_attempt_count = 1
        repair_prompt = build_narrator_repair_user_prompt(
            output=output,
            deterministic_presentation=deterministic_presentation,
            rejected_narrator=narrator_candidate,
            rejection_reasons=initial_rejection_reasons,
        )
        repair_result = call_presentation_provider(
            config=config,
            system_prompt=system_prompt,
            user_prompt=repair_prompt,
        )
        if repair_result.ok and isinstance(repair_result.payload, dict):
            repaired = repair_result.payload
            valid, reason = validate_narrator_output(
                narrator=repaired,
                engine_output=output,
                presentation_mode=mode,
            )
            if valid:
                accepted = True
                repair_valid = True
                narrator_candidate = repaired
            elif reason:
                repair_rejection_reasons.append(reason)
        else:
            repair_rejection_reasons.append(repair_result.error_code or "provider_error")

    if config.shadow and not config.enabled:
        fallback = _deterministic_narrator(output=output, presentation_mode=mode)
        return fallback, narrator_meta(
            source="deterministic_fallback",
            provider_called=True,
            shadow_mode=True,
            accepted=accepted,
            fallback_returned=True,
            initial_attempt_valid=initial_attempt_valid,
            initial_rejection_reasons=initial_rejection_reasons,
            repair_attempted=repair_attempted,
            repair_valid=repair_valid,
            repair_rejection_reasons=repair_rejection_reasons,
            final_source="shadow_fallback",
            repair_attempt_count=repair_attempt_count,
            rejection_reasons=[*initial_rejection_reasons, *repair_rejection_reasons],
            accepted_llm_preview=_accepted_preview(narrator_candidate) if accepted and narrator_candidate is not None else None,
        )

    if accepted and narrator_candidate is not None:
        return narrator_candidate, narrator_meta(
            source="llm_repair" if repair_valid else "llm_initial",
            provider_called=True,
            shadow_mode=False,
            accepted=True,
            fallback_returned=False,
            initial_attempt_valid=initial_attempt_valid,
            initial_rejection_reasons=initial_rejection_reasons,
            repair_attempted=repair_attempted,
            repair_valid=repair_valid,
            repair_rejection_reasons=repair_rejection_reasons,
            final_source="llm_repair" if repair_valid else "llm_initial",
            repair_attempt_count=repair_attempt_count,
            rejection_reasons=[],
            accepted_llm_preview=_accepted_preview(narrator_candidate),
        )

    # enabled mode with provider/validator failure: deterministic fallback
    all_rejections = [*initial_rejection_reasons, *repair_rejection_reasons]
    if not all_rejections:
        all_rejections = ["unknown_rejection"]
    fallback = _deterministic_narrator(output=output, presentation_mode=mode)
    return fallback, narrator_meta(
        source="deterministic_fallback",
        provider_called=True,
        shadow_mode=False,
        accepted=False,
        fallback_returned=True,
        initial_attempt_valid=initial_attempt_valid,
        initial_rejection_reasons=initial_rejection_reasons,
        repair_attempted=repair_attempted,
        repair_valid=repair_valid,
        repair_rejection_reasons=repair_rejection_reasons,
        final_source="deterministic_fallback",
        repair_attempt_count=repair_attempt_count,
        rejection_reasons=all_rejections,
    )


def _extract_output(engine_response: dict[str, Any]) -> dict[str, Any]:
    output = engine_response.get("output", engine_response)
    return output if isinstance(output, dict) else {}


def _accepted_preview(narrator: dict[str, Any]) -> dict[str, str]:
    """Expose only short, non-secret LLM copy snippets for eval artifacts."""
    paths = {
        "share_line": (None, "share_line"),
        "simple.headline": ("simple", "headline"),
        "brutal_truth.punchline": ("brutal_truth", "punchline"),
        "deep_view.risk": ("deep_view", "risk"),
        "krishna_lens.question": ("krishna_lens", "question"),
    }
    preview: dict[str, str] = {}
    for label, (section, key) in paths.items():
        if section is None:
            value = narrator.get(key)
        else:
            block = narrator.get(section)
            value = block.get(key) if isinstance(block, dict) else None
        if isinstance(value, str) and value.strip():
            preview[label] = value.strip()[:240]
    return preview


def _deterministic_narrator(*, output: dict[str, Any], presentation_mode: str) -> dict[str, Any]:
    verdict = str(output.get("verdict_sentence") or "Take the next clean, reviewable step.").strip()
    core = str(output.get("core_reading") or "").strip()
    higher = str(output.get("higher_path") or "").strip()
    classification = str(output.get("classification") or "Mixed").strip()
    risk_long = str(
        ((output.get("if_you_continue") or {}).get("long_term") if isinstance(output.get("if_you_continue"), dict) else "")
        or ""
    ).strip()

    if presentation_mode == "crisis_safe":
        return {
            "share_line": "Safety comes first. Interpretation can wait.",
            "simple": {
                "headline": "Safety before interpretation",
                "explanation": "This moment needs immediate human support before deeper reflection.",
                "next_step": "Reach someone who can be with you right now.",
            },
            "krishna_lens": {
                "question": "What helps you stay safe in the next 10 minutes?",
                "teaching": "Protecting life is the immediate priority.",
                "mirror": "One grounded step is enough right now.",
            },
            "brutal_truth": {
                "headline": "Do not handle this alone",
                "punchline": "Safety is the whole task in this window.",
                "share_quote": "Choose contact over isolation.",
            },
            "deep_view": {
                "what_is_happening": "Pain is compressing options and clarity.",
                "risk": "Acting in this state can cause irreversible harm.",
                "higher_path": "Create distance from harm and involve real-time support.",
            },
        }

    return {
        "share_line": _build_deterministic_share_line(risk_long=risk_long, higher_path=higher),
        "simple": {
            "headline": verdict[:120],
            "explanation": core or "The current pattern has ethical tradeoffs that need a cleaner method.",
            "next_step": higher or "Take one accountable, reversible next action.",
        },
        "krishna_lens": {
            "question": "What action stays clean even after the pressure fades?",
            "teaching": f"Treat this as a {classification.lower()} direction check, not a dramatic identity verdict.",
            "mirror": "Your next method matters more than your current justification.",
        },
        "brutal_truth": {
            "headline": "The pressure is real; the method still counts.",
            "punchline": risk_long or "Short-term relief can become long-term ethical debt.",
            "share_quote": "A clean action should survive urgency and daylight.",
        },
        "deep_view": {
            "what_is_happening": core or "Motives and method are currently misaligned.",
            "risk": risk_long or "Repeating this move can normalize avoidable harm.",
            "higher_path": higher or "Pick the cleanest next step that reduces hidden cost.",
        },
    }


def _build_deterministic_share_line(*, risk_long: str, higher_path: str) -> str:
    if risk_long:
        first_sentence = risk_long.split(".")[0].strip()
        if first_sentence:
            return f"This may work now. {first_sentence[:120]}."
    if higher_path:
        return "The next move is the pattern. Make it one you can repeat."
    return "Pressure explains the urge. It does not erase the cost."
