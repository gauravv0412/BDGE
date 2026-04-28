"""Tests for presentation LLM config (env + optional .env)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest import mock

import pytest

from app.presentation import config as presentation_config

_PRESENTATION_ENV_NAMES = [
    "PRESENTATION_LLM_PROVIDER",
    "PRESENTATION_LLM_ENABLED",
    "PRESENTATION_LLM_SHADOW",
    "PRESENTATION_LLM_MODEL",
    "PRESENTATION_LLM_TIMEOUT_SECONDS",
    "PRESENTATION_LLM_REPAIR_ENABLED",
    "PRESENTATION_LLM_MAX_REPAIR_ATTEMPTS",
    "PRESENTATION_LLM_BASE_URL",
    "PRESENTATION_LLM_API_KEY",
]


@pytest.fixture(autouse=True)
def _clear_config_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in _PRESENTATION_ENV_NAMES:
        monkeypatch.delenv(name, raising=False)
    presentation_config._loaded_dotenv_paths.clear()
    yield
    presentation_config._loaded_dotenv_paths.clear()


def test_load_presentation_llm_config_reads_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PRESENTATION_LLM_PROVIDER", "openai_compatible")
    monkeypatch.setenv("PRESENTATION_LLM_ENABLED", "true")
    monkeypatch.setenv("PRESENTATION_LLM_SHADOW", "1")
    monkeypatch.setenv("PRESENTATION_LLM_MODEL", "test-model-x")
    monkeypatch.setenv("PRESENTATION_LLM_TIMEOUT_SECONDS", "12")
    monkeypatch.setenv("PRESENTATION_LLM_REPAIR_ENABLED", "yes")
    monkeypatch.setenv("PRESENTATION_LLM_MAX_REPAIR_ATTEMPTS", "99")
    monkeypatch.setenv("PRESENTATION_LLM_BASE_URL", "https://example.invalid/v1/chat/completions")
    monkeypatch.setenv("PRESENTATION_LLM_API_KEY", "placeholder-not-a-real-secret")

    cfg = presentation_config.load_presentation_llm_config()

    assert cfg.provider == "openai_compatible"
    assert cfg.enabled is True
    assert cfg.shadow is True
    assert cfg.model == "test-model-x"
    assert cfg.timeout_seconds == 12
    assert cfg.repair_enabled is True
    assert cfg.max_repair_attempts == 1
    assert cfg.base_url == "https://example.invalid/v1/chat/completions"
    assert cfg.api_key == "placeholder-not-a-real-secret"


def test_load_presentation_llm_config_invalid_provider_defaults_to_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PRESENTATION_LLM_PROVIDER", "unknown_vendor")
    cfg = presentation_config.load_presentation_llm_config()
    assert cfg.provider == "none"


def test_load_presentation_llm_config_defaults_to_enabled_repair_non_shadow(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("WISDOMIZE_LOAD_DOTENV", "false")
    missing_secrets = tmp_path / "missing_local_secrets.json"

    cfg = presentation_config.load_presentation_llm_config(local_secrets_path=missing_secrets)

    assert cfg.enabled is True
    assert cfg.shadow is False
    assert cfg.repair_enabled is True


def test_wisdomize_load_dotenv_false_skips_dotenv(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WISDOMIZE_LOAD_DOTENV", "false")
    with mock.patch("dotenv.load_dotenv") as load_dotenv_mock:
        presentation_config.load_presentation_llm_config()
    load_dotenv_mock.assert_not_called()


def test_load_presentation_llm_config_reads_nested_anthropic_key_and_defaults(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("WISDOMIZE_LOAD_DOTENV", "false")
    secrets = tmp_path / "local_secrets.json"
    secrets.write_text(json.dumps({"anthropic": {"api_key": "nested-anthropic-key"}}), encoding="utf-8")

    cfg = presentation_config.load_presentation_llm_config(local_secrets_path=secrets)

    assert cfg.provider == "anthropic"
    assert cfg.api_key == "nested-anthropic-key"
    assert cfg.base_url == "https://api.anthropic.com/v1/messages"
    assert cfg.model == "claude-haiku-4-5"
    assert cfg.timeout_seconds == 20
    assert cfg.enabled is True
    assert cfg.shadow is False
    assert cfg.repair_enabled is True


def test_load_presentation_llm_config_env_overrides_nested_local_secrets(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("WISDOMIZE_LOAD_DOTENV", "false")
    monkeypatch.setenv("PRESENTATION_LLM_PROVIDER", "openai_compatible")
    monkeypatch.setenv("PRESENTATION_LLM_API_KEY", "env-key")
    monkeypatch.setenv("PRESENTATION_LLM_BASE_URL", "https://env.example.invalid/v1/chat/completions")
    monkeypatch.setenv("PRESENTATION_LLM_MODEL", "env-model")
    secrets = tmp_path / "local_secrets.json"
    secrets.write_text(json.dumps({"anthropic": {"api_key": "nested-key"}}), encoding="utf-8")

    cfg = presentation_config.load_presentation_llm_config(local_secrets_path=secrets)

    assert cfg.provider == "openai_compatible"
    assert cfg.api_key == "env-key"
    assert cfg.base_url == "https://env.example.invalid/v1/chat/completions"
    assert cfg.model == "env-model"


def test_load_presentation_llm_config_flat_local_secrets_still_work(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("WISDOMIZE_LOAD_DOTENV", "false")
    secrets = tmp_path / "local_secrets.json"
    secrets.write_text(
        json.dumps(
            {
                "PRESENTATION_LLM_PROVIDER": "openai_compatible",
                "PRESENTATION_LLM_ENABLED": "true",
                "PRESENTATION_LLM_MODEL": "flat-model",
                "PRESENTATION_LLM_BASE_URL": "https://flat.example.invalid/v1/chat/completions",
                "PRESENTATION_LLM_API_KEY": "flat-key",
                "PRESENTATION_LLM_REPAIR_ENABLED": "yes",
            }
        ),
        encoding="utf-8",
    )

    cfg = presentation_config.load_presentation_llm_config(local_secrets_path=secrets)

    assert cfg.provider == "openai_compatible"
    assert cfg.enabled is True
    assert cfg.model == "flat-model"
    assert cfg.base_url == "https://flat.example.invalid/v1/chat/completions"
    assert cfg.api_key == "flat-key"
    assert cfg.repair_enabled is True


def test_presentation_llm_config_repr_redacts_api_key() -> None:
    cfg = presentation_config.PresentationLLMConfig(api_key="secret-key")

    assert "secret-key" not in repr(cfg)
    assert "api_key" not in repr(cfg)
