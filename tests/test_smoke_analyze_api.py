"""Smoke contract for ``app.scripts.smoke_analyze_api`` (also runnable via Makefile)."""

from __future__ import annotations

from app.scripts.smoke_analyze_api import run_smoke


def test_smoke_analyze_api_script_equivalent() -> None:
    assert run_smoke() == 0
