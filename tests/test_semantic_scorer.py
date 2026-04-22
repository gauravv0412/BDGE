"""Semantic scorer scaffold tests."""

from __future__ import annotations

import json
import sys
import types
from typing import Any

import pytest

from app.semantic.guards import run_post_generation_guards
from app.semantic.scorer import (
    _get_anthropic_client,
    _stub_payload,
    load_semantic_config,
    load_semantic_config as _load_cfg,
    load_local_secrets,
    semantic_scorer,
    validate_semantic_payload,
)


def test_semantic_config_loading() -> None:
    cfg = load_semantic_config()
    assert cfg["provider"] == "anthropic"
    assert cfg["model"]
    assert isinstance(cfg["temperature"], int | float)


def test_stub_semantic_payload_validates_against_schema() -> None:
    payload = semantic_scorer(
        "I need to decide whether to confront a teammate now or gather more evidence first.",
        use_stub=True,
    )
    ok, errors = validate_semantic_payload(payload)
    assert ok, errors


def test_guards_pass_on_stub_output() -> None:
    payload = semantic_scorer(
        "I am unsure whether delaying this decision protects people or avoids discomfort.",
        use_stub=True,
    )
    ok, issues = run_post_generation_guards(payload)
    assert ok, issues


def test_live_anthropic_success_json_parse(monkeypatch: Any) -> None:
    payload = semantic_scorer(
        "Need a deterministic payload for testing.",
        use_stub=True,
    )
    payload_json = json.dumps(payload)

    class _Block:
        def __init__(self, text: str) -> None:
            self.text = text

    class _Resp:
        def __init__(self, text: str) -> None:
            self.content = [_Block(text)]

    class _Messages:
        @staticmethod
        def create(**_kwargs: Any) -> _Resp:
            return _Resp(payload_json)

    class _Client:
        messages = _Messages()

    monkeypatch.setattr("app.semantic.scorer._get_anthropic_client", lambda: _Client())
    out = semantic_scorer("Test dilemma for live path.", use_stub=False)
    assert out["ethical_dimensions"]["dharma_duty"]["score"] == payload["ethical_dimensions"]["dharma_duty"]["score"]


def test_live_schema_failure_path(monkeypatch: Any) -> None:
    invalid_payload = {"wrong": "shape"}

    class _Block:
        def __init__(self, text: str) -> None:
            self.text = text

    class _Resp:
        def __init__(self, text: str) -> None:
            self.content = [_Block(text)]

    class _Messages:
        @staticmethod
        def create(**_kwargs: Any) -> _Resp:
            return _Resp(json.dumps(invalid_payload))

    class _Client:
        messages = _Messages()

    monkeypatch.setattr("app.semantic.scorer._get_anthropic_client", lambda: _Client())
    with pytest.raises(ValueError, match="schema validation failed"):
        semantic_scorer("Test dilemma for schema failure.", use_stub=False)


def test_live_guard_failure_path(monkeypatch: Any) -> None:
    payload = semantic_scorer("Need deterministic payload", use_stub=True)
    payload["share_layer"]["card_quote"] = "This holy framing should trigger banned-word guard checks."

    class _Block:
        def __init__(self, text: str) -> None:
            self.text = text

    class _Resp:
        def __init__(self, text: str) -> None:
            self.content = [_Block(text)]

    class _Messages:
        @staticmethod
        def create(**_kwargs: Any) -> _Resp:
            return _Resp(json.dumps(payload))

    class _Client:
        messages = _Messages()

    monkeypatch.setattr("app.semantic.scorer._get_anthropic_client", lambda: _Client())
    with pytest.raises(ValueError, match="guard checks failed"):
        semantic_scorer("Test dilemma for guard failure.", use_stub=False)


def test_live_repair_retry_prompt_triggered_on_invalid_output(monkeypatch: Any) -> None:
    first_invalid = {"ethical_dimensions": []}
    second_valid = _stub_payload()
    calls: list[dict[str, Any]] = []

    class _Block:
        def __init__(self, text: str) -> None:
            self.text = text

    class _Resp:
        def __init__(self, text: str) -> None:
            self.content = [_Block(text)]

    class _Messages:
        def __init__(self) -> None:
            self._idx = 0

        def create(self, **kwargs: Any) -> _Resp:
            calls.append(kwargs)
            if self._idx == 0:
                self._idx += 1
                return _Resp(json.dumps(first_invalid))
            return _Resp(json.dumps(second_valid))

    class _Client:
        def __init__(self) -> None:
            self.messages = _Messages()

    client = _Client()
    monkeypatch.setattr("app.semantic.scorer._get_anthropic_client", lambda: client)
    cfg = dict(_load_cfg())
    cfg["max_retries"] = 1
    monkeypatch.setattr("app.semantic.scorer.load_semantic_config", lambda: cfg)

    out = semantic_scorer("Retry path dilemma.", use_stub=False)
    assert out["share_layer"]["reflective_question"].endswith("?")
    assert len(calls) == 2, "Expected retry call after validation failure"
    repair_prompt = calls[1]["messages"][0]["content"]
    assert "REPAIR REQUIRED" in repair_prompt
    assert "Use ONLY the fixed Wisdomize schema keys" in repair_prompt
    assert "Do NOT invent alternate moral dimensions" in repair_prompt


def test_stub_default_mode_is_safe_for_development(monkeypatch: Any) -> None:
    cfg = dict(_load_cfg())
    cfg["use_stub_default"] = True
    monkeypatch.setattr("app.semantic.scorer.load_semantic_config", lambda: cfg)
    out = semantic_scorer("Test dilemma for config-driven default.", use_stub=None)
    ok, errors = validate_semantic_payload(out)
    assert ok, errors


def test_invalid_alternate_ethical_dimensions_structure_rejected() -> None:
    payload = _stub_payload()
    payload["ethical_dimensions"] = [
        {"name": "dharma_duty", "score": 1, "note": "wrong shape for schema"}
    ]
    ok, errors = validate_semantic_payload(payload)
    assert not ok
    assert any("ethical_dimensions" in err for err in errors)


def test_top_level_reflective_question_without_share_layer_rejected() -> None:
    payload = _stub_payload()
    payload.pop("share_layer")
    payload["reflective_question"] = "Should this be at top level?"
    ok, errors = validate_semantic_payload(payload)
    assert not ok
    assert any("share_layer" in err for err in errors)


def test_missing_local_secrets_file_raises_clear_error(tmp_path: Any) -> None:
    missing = tmp_path / "missing_local_secrets.json"
    with pytest.raises(RuntimeError, match="Create config/local_secrets.json"):
        load_local_secrets(secrets_path=missing)


def test_missing_api_key_field_raises_clear_error(tmp_path: Any, monkeypatch: Any) -> None:
    secrets = tmp_path / "local_secrets.json"
    secrets.write_text('{"anthropic": {}}', encoding="utf-8")
    fake_module = types.SimpleNamespace(Anthropic=lambda api_key: object())
    monkeypatch.setitem(sys.modules, "anthropic", fake_module)
    with pytest.raises(RuntimeError, match="Missing Anthropic api_key"):
        _get_anthropic_client(secrets_path=secrets)


def test_successful_anthropic_client_construction_path(tmp_path: Any, monkeypatch: Any) -> None:
    secrets = tmp_path / "local_secrets.json"
    secrets.write_text('{"anthropic": {"api_key": "test-anthropic-key"}}', encoding="utf-8")

    captured: dict[str, Any] = {}

    class _FakeAnthropic:
        def __init__(self, api_key: str) -> None:
            captured["api_key"] = api_key

    fake_module = types.SimpleNamespace(Anthropic=_FakeAnthropic)
    monkeypatch.setitem(sys.modules, "anthropic", fake_module)

    _ = _get_anthropic_client(secrets_path=secrets)
    assert captured["api_key"] == "test-anthropic-key"

