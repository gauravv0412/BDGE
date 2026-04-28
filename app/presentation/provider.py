"""External LLM provider adapter for presentation narrator."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from app.presentation.config import PresentationLLMConfig


@dataclass(frozen=True)
class ProviderCallResult:
    ok: bool
    payload: dict[str, Any] | None
    error_code: str | None = None
    error_message: str | None = None


def call_presentation_provider(
    *,
    config: PresentationLLMConfig,
    system_prompt: str,
    user_prompt: str,
) -> ProviderCallResult:
    if config.provider == "openai_compatible":
        return _call_openai_compatible_provider(
            config=config,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )
    if config.provider == "anthropic":
        return _call_anthropic_provider(
            config=config,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )
    return ProviderCallResult(ok=False, payload=None, error_code="provider_disabled", error_message="provider disabled")


def _call_openai_compatible_provider(
    *,
    config: PresentationLLMConfig,
    system_prompt: str,
    user_prompt: str,
) -> ProviderCallResult:
    if not config.base_url or not config.api_key:
        return ProviderCallResult(ok=False, payload=None, error_code="provider_not_configured", error_message="missing provider credentials")

    request_body = {
        "model": config.model,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
    }
    return _post_provider_json(
        config=config,
        request_body=request_body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.api_key}",
        },
        extract_content=_extract_openai_compatible_content,
    )


def _call_anthropic_provider(
    *,
    config: PresentationLLMConfig,
    system_prompt: str,
    user_prompt: str,
) -> ProviderCallResult:
    if not config.base_url or not config.api_key:
        return ProviderCallResult(ok=False, payload=None, error_code="provider_not_configured", error_message="missing provider credentials")

    request_body = {
        "model": config.model,
        "max_tokens": 1200,
        "temperature": 0.2,
        "system": system_prompt,
        "messages": [
            {"role": "user", "content": user_prompt},
        ],
    }
    return _post_provider_json(
        config=config,
        request_body=request_body,
        headers={
            "Content-Type": "application/json",
            "x-api-key": config.api_key,
            "anthropic-version": "2023-06-01",
        },
        extract_content=_extract_anthropic_content,
    )


def _post_provider_json(
    *,
    config: PresentationLLMConfig,
    request_body: dict[str, Any],
    headers: dict[str, str],
    extract_content: Any,
) -> ProviderCallResult:
    if config.provider not in {"openai_compatible", "anthropic"}:
        return ProviderCallResult(ok=False, payload=None, error_code="provider_disabled", error_message="provider disabled")
    if not config.base_url or not config.api_key:
        return ProviderCallResult(ok=False, payload=None, error_code="provider_not_configured", error_message="missing provider credentials")

    data = json.dumps(request_body).encode("utf-8")
    req = urllib.request.Request(
        url=config.base_url,
        data=data,
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=config.timeout_seconds) as response:  # noqa: S310
            raw = response.read().decode("utf-8", errors="replace").strip()
    except TimeoutError:
        return ProviderCallResult(ok=False, payload=None, error_code="timeout", error_message="provider timeout")
    except urllib.error.HTTPError as exc:
        return ProviderCallResult(ok=False, payload=None, error_code=f"http_{exc.code}", error_message=f"http {exc.code}")
    except urllib.error.URLError:
        return ProviderCallResult(ok=False, payload=None, error_code="transport_error", error_message="provider unavailable")
    except Exception:  # noqa: BLE001
        return ProviderCallResult(ok=False, payload=None, error_code="provider_exception", error_message="provider call failed")

    if not raw:
        return ProviderCallResult(ok=False, payload=None, error_code="empty_response", error_message="provider returned empty body")

    try:
        envelope = json.loads(raw)
    except Exception:  # noqa: BLE001
        return ProviderCallResult(ok=False, payload=None, error_code="invalid_provider_json", error_message="provider returned invalid json")

    content = extract_content(envelope)
    if not content:
        return ProviderCallResult(ok=False, payload=None, error_code="empty_content", error_message="provider content empty")
    try:
        payload = _parse_content_json(content)
    except Exception:  # noqa: BLE001
        return ProviderCallResult(ok=False, payload=None, error_code="invalid_content_json", error_message="assistant content is not valid json")
    if not isinstance(payload, dict):
        return ProviderCallResult(ok=False, payload=None, error_code="invalid_content_shape", error_message="assistant content must be json object")
    return ProviderCallResult(ok=True, payload=payload)


def _extract_openai_compatible_content(envelope: dict[str, Any]) -> str:
    choices = envelope.get("choices")
    if isinstance(choices, list) and choices:
        first = choices[0] if isinstance(choices[0], dict) else {}
        message = first.get("message") if isinstance(first.get("message"), dict) else {}
        content = message.get("content")
        if isinstance(content, str):
            return content.strip()
    return ""


def _extract_anthropic_content(envelope: dict[str, Any]) -> str:
    content = envelope.get("content")
    if isinstance(content, str):
        return content.strip()
    if not isinstance(content, list):
        return ""
    text_parts: list[str] = []
    for block in content:
        if not isinstance(block, dict):
            continue
        if block.get("type") == "text" and isinstance(block.get("text"), str):
            text_parts.append(block["text"])
    return "\n".join(part.strip() for part in text_parts if part.strip()).strip()


def _parse_content_json(content: str) -> Any:
    blob = content.strip()
    if blob.startswith("```"):
        lines = blob.splitlines()
        if len(lines) >= 3 and lines[0].startswith("```") and lines[-1].startswith("```"):
            blob = "\n".join(lines[1:-1]).strip()
            if blob.lower().startswith("json"):
                blob = blob[4:].strip()
    return json.loads(blob)
