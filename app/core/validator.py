"""
Validate raw dicts against ``docs/output_schema.json`` (JSON Schema draft-07).
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator

# Repo root: app/core/validator.py -> parents[2]
_DEFAULT_SCHEMA_PATH = Path(__file__).resolve().parents[2] / "docs" / "output_schema.json"


@lru_cache(maxsize=1)
def load_output_schema(*, schema_path: Path | None = None) -> dict[str, Any]:
    """
    Load and return the engine output JSON Schema.

    Parameters
    ----------
    schema_path
        Override path (defaults to ``docs/output_schema.json`` under the repo root).
    """
    path = schema_path or _DEFAULT_SCHEMA_PATH
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def validate_against_output_schema(
    instance: dict[str, Any],
    *,
    schema_path: Path | None = None,
) -> tuple[bool, list[str]]:
    """
    Validate ``instance`` against the Wisdomize output JSON Schema.

    Returns
    -------
    tuple[bool, list[str]]
        ``(True, [])`` if valid; otherwise ``(False, [human-readable errors...])``.
    """
    schema = load_output_schema(schema_path=schema_path)
    validator = Draft7Validator(schema)
    errors: list[str] = []
    for error in validator.iter_errors(instance):
        path = ".".join(str(p) for p in error.absolute_path) or "(root)"
        errors.append(f"{path}: {error.message}")
    return (len(errors) == 0, errors)


def validate_against_schema(
    instance: dict[str, Any],
    schema: dict[str, Any],
) -> tuple[bool, list[str]]:
    """
    Validate ``instance`` against an arbitrary JSON Schema object (draft-07).

    Use this for tests or alternate schemas; production checks use
    :func:`validate_against_output_schema`.
    """
    Draft7Validator.check_schema(schema)
    validator = Draft7Validator(schema)
    errors: list[str] = []
    for error in validator.iter_errors(instance):
        path = ".".join(str(p) for p in error.absolute_path) or "(root)"
        errors.append(f"{path}: {error.message}")
    return (len(errors) == 0, errors)


def assert_valid_output(
    instance: dict[str, Any],
    *,
    schema_path: Path | None = None,
) -> None:
    """
    Raise :class:`jsonschema.exceptions.ValidationError` if validation fails.

    Convenience for callers that prefer exceptions over ``(ok, errors)`` tuples.
    """
    schema = load_output_schema(schema_path=schema_path)
    Draft7Validator(schema).validate(instance)
