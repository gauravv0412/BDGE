"""
Run JSON Schema validation over every dilemma in the benchmark file.

Prints aggregate pass/fail counts. Does not compute ethical scores or grades.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from app.core.benchmark_loader import load_dilemmas
from app.core.validator import validate_against_output_schema


def run_validation_benchmark(*, benchmark_path: Path | None = None) -> tuple[int, int]:
    """
    Validate each benchmark dilemma against the output schema.

    Returns
    -------
    tuple[int, int]
        ``(pass_count, fail_count)``.
    """
    dilemmas = load_dilemmas(path=benchmark_path)
    passed = 0
    failed = 0
    for item in dilemmas:
        ok, _errors = validate_against_output_schema(item)
        if ok:
            passed += 1
        else:
            failed += 1
    return passed, failed


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate benchmark dilemmas against docs/output_schema.json",
    )
    parser.add_argument(
        "--benchmark",
        type=Path,
        default=None,
        help="Path to benchmark JSON (default: docs/benchmarks_v2_batch1_W001-W020.json)",
    )
    args = parser.parse_args()

    passed, failed = run_validation_benchmark(benchmark_path=args.benchmark)
    total = passed + failed
    print(f"Schema validation: {passed}/{total} passed, {failed}/{total} failed")


if __name__ == "__main__":
    main()
