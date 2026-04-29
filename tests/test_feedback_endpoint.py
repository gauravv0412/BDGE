"""Safe feedback endpoint and storage tests."""

from __future__ import annotations

import json
import os

import django
from django.contrib.auth.models import User
from django.test import Client

from app.accounts.services import ensure_profile
from app.feedback.storage import append_feedback_record

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.django_test_settings")
django.setup()


def _post_feedback(client: Client, payload: dict[str, object]):
    return client.post("/api/v1/feedback", data=json.dumps(payload), content_type="application/json")


def _authenticated_client(username: str = "feedback-user") -> Client:
    user = User.objects.create_user(username=username, password="test-pass-12345")
    ensure_profile(user, verified=True, provider="password")
    client = Client()
    assert client.login(username=username, password="test-pass-12345")
    return client


def _valid_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "result_id": "fb-result-1",
        "usefulness": "up",
        "verse_relevance": None,
        "tags": ["verdict_felt_right"],
        "comment": "Clear and useful.",
        "route": "presentation",
        "client_theme": "dark",
        "guidance_type": "closest_teaching",
    }
    payload.update(overrides)
    return payload


def _records(path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_feedback_endpoint_accepts_valid_minimal_payload(tmp_path, monkeypatch) -> None:
    feedback_path = tmp_path / "nested" / "feedback.jsonl"
    monkeypatch.setenv("WISDOMIZE_FEEDBACK_JSONL", str(feedback_path))
    client = _authenticated_client()

    response = _post_feedback(
        client,
        {
            "dilemma_id": "fb-minimal-1",
            "usefulness": "up",
            "verse_relevance": None,
            "tags": [],
            "route": "presentation",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["feedback_id"]
    records = _records(feedback_path)
    assert len(records) == 1
    assert records[0]["result_id"] == "fb-minimal-1"
    assert records[0]["usefulness"] == "up"


def test_feedback_endpoint_rejects_invalid_enum_values(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("WISDOMIZE_FEEDBACK_JSONL", str(tmp_path / "feedback.jsonl"))
    response = _post_feedback(_authenticated_client(), _valid_payload(usefulness="maybe"))

    assert response.status_code == 400
    body = response.json()
    assert body == {
        "ok": False,
        "error": {
            "code": "feedback_validation_failed",
            "message": "Feedback could not be saved. Please check the fields and try again.",
        },
    }


def test_feedback_endpoint_rejects_oversized_comments(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("WISDOMIZE_FEEDBACK_JSONL", str(tmp_path / "feedback.jsonl"))
    response = _post_feedback(_authenticated_client(), _valid_payload(comment="x" * 501))

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "feedback_validation_failed"


def test_feedback_endpoint_does_not_require_or_store_raw_dilemma_text(tmp_path, monkeypatch) -> None:
    feedback_path = tmp_path / "feedback.jsonl"
    monkeypatch.setenv("WISDOMIZE_FEEDBACK_JSONL", str(feedback_path))
    raw_dilemma = "This raw dilemma text should never be written into feedback storage."

    response = _post_feedback(_authenticated_client(), _valid_payload(result_id="privacy-1", comment=None))

    assert response.status_code == 200
    stored_text = feedback_path.read_text(encoding="utf-8")
    assert raw_dilemma not in stored_text
    assert "dilemma" not in stored_text
    assert "output" not in stored_text


def test_feedback_storage_is_append_only_and_testable(tmp_path) -> None:
    feedback_path = tmp_path / "feedback.jsonl"
    first = append_feedback_record(_valid_payload(result_id="append-1"), path=feedback_path)
    second = append_feedback_record(_valid_payload(result_id="append-2", usefulness="down"), path=feedback_path)

    records = _records(feedback_path)
    assert [record["feedback_id"] for record in records] == [first["feedback_id"], second["feedback_id"]]
    assert [record["result_id"] for record in records] == ["append-1", "append-2"]


def test_feedback_endpoint_returns_user_safe_errors_for_unknown_fields(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("WISDOMIZE_FEEDBACK_JSONL", str(tmp_path / "feedback.jsonl"))
    payload = _valid_payload(dilemma="raw secret", output={"full": "engine response"})

    response = _post_feedback(_authenticated_client(), payload)

    assert response.status_code == 400
    text = response.content.decode("utf-8")
    assert "raw secret" not in text
    assert "engine response" not in text
    assert "Feedback could not be saved" in text


def test_feedback_endpoint_rejects_anonymous_requests(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("WISDOMIZE_FEEDBACK_JSONL", str(tmp_path / "feedback.jsonl"))
    response = _post_feedback(Client(), _valid_payload())

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "authentication_required"
