"""
Run the stub engine on one hardcoded sample dilemma, validate JSON Schema, print JSON.

Usage (from repo root)::

    PYTHONPATH=. .venv/bin/python -m app.scripts.run_single_dilemma
"""

from __future__ import annotations

import json
import sys

from app.core.validator import validate_against_output_schema
from app.engine.analyzer import analyze_dilemma

# Hardcoded sample (≥20 chars per schema).
SAMPLE_DILEMMA = (
    "I keep postponing a difficult conversation at work because I fear the conflict. "
    "What should I optimize for first: peace or clarity?"
)


def main() -> int:
    output = analyze_dilemma(SAMPLE_DILEMMA)
    ok, errors = validate_against_output_schema(output)
    if not ok:
        print("Schema validation FAILED:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print(json.dumps(output, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
