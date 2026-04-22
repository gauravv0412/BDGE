"""Tests for JSON Schema validation of engine output dicts."""

from __future__ import annotations

import copy

import pytest

from app.core.benchmark_loader import load_dilemmas
from app.core.validator import validate_against_output_schema


def test_sample_benchmark_item_passes_schema() -> None:
    dilemmas = load_dilemmas()
    assert dilemmas, "benchmark should contain at least one dilemma"
    first = dilemmas[0]
    ok, errors = validate_against_output_schema(first)
    assert ok, f"expected first benchmark item to validate: {errors}"


def test_broken_sample_fails_schema() -> None:
    dilemmas = load_dilemmas()
    broken = copy.deepcopy(dilemmas[0])
    # Violates XOR: both verse_match and closest_teaching non-null
    broken["closest_teaching"] = "Paraphrased teaching while verse_match is still set."

    ok, errors = validate_against_output_schema(broken)
    assert not ok
    assert errors


def test_assert_valid_output_raises_on_invalid() -> None:
    from jsonschema.exceptions import ValidationError

    from app.core.validator import assert_valid_output

    dilemmas = load_dilemmas()
    broken = copy.deepcopy(dilemmas[0])
    broken["dilemma_id"] = ""

    with pytest.raises(ValidationError):
        assert_valid_output(broken)
