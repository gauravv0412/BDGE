"""Append-only local storage for safe feedback records."""

from __future__ import annotations

import json
import os
import uuid
from datetime import UTC, datetime
from pathlib import Path

DEFAULT_FEEDBACK_PATH = Path(__file__).resolve().parents[2] / "artifacts" / "feedback" / "feedback.jsonl"
FEEDBACK_PATH_ENV = "WISDOMIZE_FEEDBACK_JSONL"


def append_feedback_record(payload: dict[str, object], *, path: Path | None = None) -> dict[str, object]:
    storage_path = path or feedback_storage_path()
    storage_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "feedback_id": uuid.uuid4().hex,
        "created_at": datetime.now(UTC).isoformat(),
        **payload,
    }
    with storage_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    return record


def feedback_storage_path() -> Path:
    configured = os.environ.get(FEEDBACK_PATH_ENV)
    if configured:
        return Path(configured)
    return DEFAULT_FEEDBACK_PATH
