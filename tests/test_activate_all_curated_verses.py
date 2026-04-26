"""Tests for guarded full curated activation command."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from app.scripts.activate_all_curated_verses import (
    activate_all_curated_verses,
    main,
)
from app.verses.catalog import VerseCatalog
from app.verses.loader import curated_verses_seed_path, load_curated_verses, validate_curated_seed_payload


def _clean_audit() -> dict:
    return {
        "summary": {
            "shape_lock_regressions_count": 0,
            "blocker_failure_count": 0,
            "forced_match_warning_count": 0,
            "overtrigger_warning_count": 0,
            "should_block_full_activation": False,
        }
    }


def _blocked_audit() -> dict:
    return {
        "summary": {
            "shape_lock_regressions_count": 1,
            "blocker_failure_count": 0,
            "forced_match_warning_count": 0,
            "overtrigger_warning_count": 0,
            "should_block_full_activation": True,
        }
    }


def _seed_copy_with_drafts(tmp_path: Path) -> Path:
    seed_copy = tmp_path / "verses_seed.json"
    shutil.copy(curated_verses_seed_path(), seed_copy)
    payload = json.loads(seed_copy.read_text(encoding="utf-8"))
    for entry in payload[:3]:
        entry["status"] = "draft"
    validate_curated_seed_payload(payload)
    seed_copy.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return seed_copy


def test_activation_dry_run_does_not_mutate_seed(tmp_path: Path) -> None:
    seed_copy = _seed_copy_with_drafts(tmp_path)
    before = seed_copy.read_text(encoding="utf-8")

    result = activate_all_curated_verses(seed_path=seed_copy, audit_runner=_clean_audit)

    assert result.wrote is False
    assert result.active_before == result.active_after
    assert len(result.would_activate_refs) == 3
    assert seed_copy.read_text(encoding="utf-8") == before


def test_activation_write_without_confirmation_refuses(tmp_path: Path) -> None:
    seed_copy = _seed_copy_with_drafts(tmp_path)
    before_entries = validate_curated_seed_payload(json.loads(seed_copy.read_text(encoding="utf-8")))
    before_active = sum(1 for entry in before_entries if entry.status == "active")

    result = main(["--seed", str(seed_copy), "--write", "--skip-artifact-refresh"])

    assert result == 1
    after_entries = validate_curated_seed_payload(json.loads(seed_copy.read_text(encoding="utf-8")))
    active_count = sum(1 for entry in after_entries if entry.status == "active")
    assert active_count == before_active


def test_activation_refuses_when_audit_reports_blocker(tmp_path: Path) -> None:
    seed_copy = _seed_copy_with_drafts(tmp_path)

    try:
        activate_all_curated_verses(
            seed_path=seed_copy,
            write=True,
            confirm_production_curated_write=True,
            audit_runner=_blocked_audit,
        )
    except RuntimeError as exc:
        assert "shape_lock_regressions_count=1" in str(exc)
    else:
        raise AssertionError("activation should refuse blocked audit")


def test_activation_write_with_confirmation_activates_all_entries(tmp_path: Path) -> None:
    seed_copy = _seed_copy_with_drafts(tmp_path)

    result = activate_all_curated_verses(
        seed_path=seed_copy,
        write=True,
        confirm_production_curated_write=True,
        audit_runner=_clean_audit,
    )

    assert result.wrote is True
    assert result.active_before == 106
    assert result.active_after == 109
    entries = validate_curated_seed_payload(json.loads(seed_copy.read_text(encoding="utf-8")))
    assert len(entries) == 109
    assert sum(1 for entry in entries if entry.status == "active") == 109


def test_production_catalog_all_entries_active_after_step_29c() -> None:
    entries = load_curated_verses()

    assert len(entries) == 109
    assert len(VerseCatalog(entries).list_active()) == 109
