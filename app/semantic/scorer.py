"""
Semantic scorer scaffold.

Loads semantic scorer config and schema, supports Anthropic live mode, and
validates the payload against ``schemas/semantic_scorer_schema.json``.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator

from app.semantic.guards import run_post_generation_guards
from app.semantic.prompts import SYSTEM_PROMPT, build_user_prompt

_ROOT = Path(__file__).resolve().parents[2]
_CONFIG_PATH = _ROOT / "config" / "app_config.json"
_SCHEMA_PATH = _ROOT / "schemas" / "semantic_scorer_schema.json"
_LOCAL_SECRETS_PATH = _ROOT / "config" / "local_secrets.json"


@lru_cache(maxsize=1)
def load_semantic_config(config_path: Path | None = None) -> dict[str, Any]:
    """Load ``semantic_scorer`` config from app config JSON."""
    path = config_path or _CONFIG_PATH
    with path.open(encoding="utf-8") as f:
        raw = json.load(f)
    return dict(raw["semantic_scorer"])


@lru_cache(maxsize=1)
def load_semantic_schema(schema_path: Path | None = None) -> dict[str, Any]:
    """Load the semantic scorer JSON schema."""
    path = schema_path or _SCHEMA_PATH
    with path.open(encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def load_local_secrets(secrets_path: Path | None = None) -> dict[str, Any]:
    """
    Load local developer secrets from ``config/local_secrets.json``.

    Expected shape:
    {
      "anthropic": {
        "api_key": "sk-ant-..."
      }
    }
    """
    path = secrets_path or _LOCAL_SECRETS_PATH
    try:
        with path.open(encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as exc:
        raise RuntimeError(
            "Missing config/local_secrets.json. Create config/local_secrets.json with "
            '{"anthropic": {"api_key": "YOUR_KEY"}}.'
        ) from exc


def validate_semantic_payload(payload: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate payload against semantic scorer schema."""
    schema = load_semantic_schema()
    validator = Draft7Validator(schema)
    errors: list[str] = []
    for error in validator.iter_errors(payload):
        loc = ".".join(str(p) for p in error.absolute_path) or "(root)"
        errors.append(f"{loc}: {error.message}")
    return (len(errors) == 0, errors)


def _extract_json_object(text: str) -> dict[str, Any]:
    """
    Parse a JSON object from model text output.

    Accepts plain JSON or fenced markdown JSON blocks.
    """
    blob = text.strip()
    if blob.startswith("```"):
        lines = blob.splitlines()
        if len(lines) >= 3 and lines[0].startswith("```") and lines[-1].startswith("```"):
            blob = "\n".join(lines[1:-1]).strip()
            if blob.lower().startswith("json"):
                blob = blob[4:].strip()
    parsed = json.loads(blob)
    if not isinstance(parsed, dict):
        raise ValueError("Model output must be a JSON object.")
    return parsed


def _get_anthropic_client(*, secrets_path: Path | None = None) -> Any:
    """Construct and return Anthropic client (lazy import for testability)."""
    try:
        from anthropic import Anthropic  # type: ignore
    except ImportError as exc:  # pragma: no cover - covered via message path in tests
        raise RuntimeError(
            "Anthropic SDK is not installed. Install `anthropic` to use live semantic mode."
        ) from exc
    secrets = load_local_secrets(secrets_path=secrets_path)
    api_key = secrets.get("anthropic", {}).get("api_key")
    if not isinstance(api_key, str) or not api_key.strip():
        raise RuntimeError(
            "Missing Anthropic api_key in config/local_secrets.json. "
            'Create config/local_secrets.json with {"anthropic": {"api_key": "YOUR_KEY"}}.'
        )
    return Anthropic(api_key=api_key.strip())


def _build_repair_prompt(base_prompt: str, validation_errors: list[str]) -> str:
    """Append a corrective repair instruction with exact schema violations."""
    error_lines = "\n".join(f"- {err}" for err in validation_errors)
    return (
        f"{base_prompt}\n\n"
        "REPAIR REQUIRED: Your previous JSON failed schema validation.\n"
        "Fix the output and return ONLY corrected JSON.\n"
        "Validation errors:\n"
        f"{error_lines}\n\n"
        "Use ONLY the fixed Wisdomize schema keys.\n"
        "Do NOT invent alternate moral dimensions.\n"
        "ethical_dimensions must be an object with exactly these keys:\n"
        "- dharma_duty\n"
        "- satya_truth\n"
        "- ahimsa_nonharm\n"
        "- nishkama_detachment\n"
        "- shaucha_intent\n"
        "- sanyama_restraint\n"
        "- lokasangraha_welfare\n"
        "- viveka_discernment\n"
        "reflective_question must be nested under share_layer, not top-level.\n"
    )


def _call_anthropic_once(user_prompt: str, config: dict[str, Any]) -> dict[str, Any]:
    """
    Call Anthropic Messages API once and return parsed JSON payload.
    """
    client = _get_anthropic_client()
    resp = client.messages.create(
        model=config["model"],
        max_tokens=int(config["max_tokens"]),
        temperature=float(config["temperature"]),
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    content_blocks = getattr(resp, "content", [])
    text_parts = [getattr(block, "text", "") for block in content_blocks]
    raw_text = "\n".join(part for part in text_parts if part)
    if not raw_text:
        raise ValueError("Anthropic response did not contain text content.")
    return _extract_json_object(raw_text)


def _stub_payload() -> dict[str, Any]:
    """Schema-valid stub payload for scaffold mode."""
    return {
        "ethical_dimensions": {
            "dharma_duty": {"score": 1, "note": "Role obligations are present but not singularly decisive here."},
            "satya_truth": {"score": 2, "note": "The user appears oriented toward truthful disclosure over convenience."},
            "ahimsa_nonharm": {"score": 1, "note": "The likely path can reduce avoidable harm with measured communication."},
            "nishkama_detachment": {"score": 0, "note": "Attachment to outcome is mixed and not yet clear from details."},
            "shaucha_intent": {"score": 1, "note": "Intent seems partly clean but still braided with self-protection."},
            "sanyama_restraint": {"score": 2, "note": "There are signs of restraint rather than impulsive escalation."},
            "lokasangraha_welfare": {"score": 1, "note": "A careful decision could improve collective trust and stability."},
            "viveka_discernment": {"score": 1, "note": "Discernment is emerging though some practical unknowns remain."},
        },
        "internal_driver": {
            "primary": "A desire to act responsibly while preserving relationships and credibility.",
            "hidden_risk": "Delaying a hard choice until circumstances force a weaker option.",
        },
        "core_reading": (
            "The dilemma is not about choosing between good and bad, but about sequencing truth, "
            "restraint, and impact. The user is balancing duty and consequences under uncertainty, "
            "which makes process quality as important as outcome preference."
        ),
        "gita_analysis": (
            "The central question is whether the action is grounded in clarity rather than fear or ego. "
            "A steady move that protects truth and minimizes collateral harm carries stronger alignment."
        ),
        "higher_path": (
            "Name the core duty, state the truth plainly, and choose the least harmful execution path. "
            "Document key facts before acting so intention and method stay aligned under pressure."
        ),
        "missing_facts": [
            "Which stakeholder bears the highest downside if this choice goes wrong?"
        ],
        "ambiguity_flag": False,
        "if_you_continue": {
            "short_term": "Tension may rise briefly, but ambiguity in expectations can reduce over time.",
            "long_term": "A consistent decision process can strengthen trust and reduce reactive conflicts.",
        },
        "counterfactuals": {
            "clearly_adharmic_version": {
                "assumed_context": (
                    "The user chooses a tactic that hides key facts and frames the move as principled only after the fact."
                ),
                "decision": "Proceed through concealment and strategic half-truths.",
                "why": "It protects image over duty and increases harm through preventable deception.",
            },
            "clearly_dharmic_version": {
                "assumed_context": (
                    "The user verifies facts, names impacts transparently, and chooses a proportional action with safeguards."
                ),
                "decision": "Proceed with transparent communication and documented safeguards.",
                "why": "It aligns duty, truth, restraint, and welfare without performative moralizing.",
            },
        },
        "share_layer": {
            "anonymous_share_title": "The app said the hard part is method, not drama.",
            "card_quote": "Clarity without restraint becomes violence; restraint without clarity becomes delay.",
            "reflective_question": "Which missing fact would most change your decision?",
        },
    }


def semantic_scorer(dilemma: str, *, use_stub: bool | None = None) -> dict[str, Any]:
    """
    Run semantic scorer and return validated payload.

    If ``use_stub`` is None, behavior defaults to a safe development mode
    controlled by config key ``use_stub_default`` (default: True).
    """
    config = load_semantic_config()
    stub_default = bool(config.get("use_stub_default", True))
    resolved_use_stub = stub_default if use_stub is None else use_stub

    if resolved_use_stub:
        payload = _stub_payload()
    else:
        provider = str(config.get("provider", "")).lower().strip()
        if provider != "anthropic":
            raise ValueError(f"Unsupported semantic scorer provider: {provider!r}")
        attempts = int(config.get("max_retries", 0)) + 1
        user_prompt = build_user_prompt(dilemma)
        last_error: Exception | None = None
        last_validation_errors: list[str] = []
        payload: dict[str, Any] | None = None

        for attempt in range(attempts):
            try:
                candidate = _call_anthropic_once(user_prompt, config)
                ok, validation_errors = validate_semantic_payload(candidate)
                if ok:
                    payload = candidate
                    break

                last_validation_errors = validation_errors
                if attempt < attempts - 1:
                    user_prompt = _build_repair_prompt(user_prompt, validation_errors)
                    continue
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if attempt < attempts - 1:
                    continue

        if payload is None:
            if last_validation_errors:
                raise ValueError(
                    "Semantic scorer schema validation failed after retries: "
                    f"{last_validation_errors}"
                )
            raise RuntimeError(
                f"Anthropic semantic scoring failed after {attempts} attempts: {last_error}"
            )

    ok, errors = validate_semantic_payload(payload)
    if not ok:
        raise ValueError(f"Semantic scorer schema validation failed: {errors}")

    guards_ok, guard_issues = run_post_generation_guards(payload)
    if not guards_ok:
        raise ValueError(f"Semantic scorer guard checks failed: {guard_issues}")
    return payload

