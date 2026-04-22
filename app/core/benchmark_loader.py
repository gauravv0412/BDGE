"""
Load benchmark JSON files and expose the ``dilemmas`` array.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# Repo root: app/core/benchmark_loader.py -> parents[2]
_DEFAULT_BENCHMARK_PATH = (
    Path(__file__).resolve().parents[2] / "docs" / "benchmarks_v2_batch1_W001-W020.json"
)


class BenchmarkFile(BaseModel):
    """Top-level structure of a Wisdomize benchmark JSON file."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    benchmark_version: str
    schema_version: str
    batch: str
    tone_directive: str
    distribution: dict[str, Any]
    dilemmas: list[dict[str, Any]] = Field(min_length=1)


def load_benchmark_file(path: Path | None = None) -> BenchmarkFile:
    """
    Parse a benchmark file and return metadata plus the raw dilemma dicts.

    Parameters
    ----------
    path
        File path (defaults to ``docs/benchmarks_v2_batch1_W001-W020.json``).
    """
    file_path = path or _DEFAULT_BENCHMARK_PATH
    with file_path.open(encoding="utf-8") as f:
        raw = json.load(f)
    return BenchmarkFile.model_validate(raw)


def load_dilemmas(path: Path | None = None) -> list[dict[str, Any]]:
    """
    Return the ``dilemmas`` array from the default (or given) benchmark file.

    Each item is a full per-dilemma engine output dict as stored in the benchmark.
    """
    return load_benchmark_file(path=path).dilemmas
