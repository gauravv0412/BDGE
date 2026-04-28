"""Tests for presentation narrator provider adapters."""

from __future__ import annotations

import json
import urllib.error
from typing import Any

from app.presentation.config import PresentationLLMConfig
from app.presentation.provider import call_presentation_provider


class _FakeResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")


def test_anthropic_provider_uses_messages_api_shape(monkeypatch) -> None:
    captured: dict[str, Any] = {}
    narrator = {"simple": {"headline": "Clean action wins."}}

    def _urlopen(req: Any, timeout: int) -> _FakeResponse:
        captured["url"] = req.full_url
        captured["timeout"] = timeout
        captured["headers"] = {key.lower(): value for key, value in req.header_items()}
        captured["body"] = json.loads(req.data.decode("utf-8"))
        return _FakeResponse({"content": [{"type": "text", "text": f"```json\n{json.dumps(narrator)}\n```"}]})

    monkeypatch.setattr("urllib.request.urlopen", _urlopen)

    result = call_presentation_provider(
        config=PresentationLLMConfig(
            provider="anthropic",
            model="claude-haiku-4-5",
            base_url="https://api.anthropic.com/v1/messages",
            api_key="test-key",
            timeout_seconds=7,
        ),
        system_prompt="system text",
        user_prompt="user text",
    )

    assert result.ok is True
    assert result.payload == narrator
    assert captured["url"] == "https://api.anthropic.com/v1/messages"
    assert captured["timeout"] == 7
    assert captured["headers"]["x-api-key"] == "test-key"
    assert captured["headers"]["anthropic-version"] == "2023-06-01"
    assert captured["body"]["model"] == "claude-haiku-4-5"
    assert captured["body"]["system"] == "system text"
    assert captured["body"]["messages"] == [{"role": "user", "content": "user text"}]
    assert "response_format" not in captured["body"]


def test_openai_compatible_provider_shape_still_works(monkeypatch) -> None:
    captured: dict[str, Any] = {}
    narrator = {"simple": {"headline": "Clean action wins."}}

    def _urlopen(req: Any, timeout: int) -> _FakeResponse:
        captured["headers"] = {key.lower(): value for key, value in req.header_items()}
        captured["body"] = json.loads(req.data.decode("utf-8"))
        return _FakeResponse({"choices": [{"message": {"content": json.dumps(narrator)}}]})

    monkeypatch.setattr("urllib.request.urlopen", _urlopen)

    result = call_presentation_provider(
        config=PresentationLLMConfig(
            provider="openai_compatible",
            model="test-model",
            base_url="https://example.invalid/v1/chat/completions",
            api_key="test-key",
        ),
        system_prompt="system text",
        user_prompt="user text",
    )

    assert result.ok is True
    assert result.payload == narrator
    assert captured["headers"]["authorization"] == "Bearer test-key"
    assert captured["body"]["response_format"] == {"type": "json_object"}
    assert captured["body"]["messages"] == [
        {"role": "system", "content": "system text"},
        {"role": "user", "content": "user text"},
    ]


def test_http_error_preserves_status_code(monkeypatch) -> None:
    def _urlopen(req: Any, timeout: int) -> _FakeResponse:
        raise urllib.error.HTTPError(
            url=req.full_url,
            code=400,
            msg="Bad Request",
            hdrs=None,
            fp=None,
        )

    monkeypatch.setattr("urllib.request.urlopen", _urlopen)

    result = call_presentation_provider(
        config=PresentationLLMConfig(
            provider="anthropic",
            base_url="https://api.anthropic.com/v1/messages",
            api_key="test-key",
        ),
        system_prompt="system text",
        user_prompt="user text",
    )

    assert result.ok is False
    assert result.error_code == "http_400"
    assert result.error_message == "http 400"
