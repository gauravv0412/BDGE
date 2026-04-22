"""
Confidence in the verdict, with the §2 / §7 cap rule.

``confidence > 0.85`` is allowed only when all eight dimensions are scorable,
``missing_facts`` is empty, *and* no ambiguity override was signalled.
Any of those conditions failing caps the result at 0.85.
"""

from __future__ import annotations

_CAP_IF_INCOMPLETE = 0.85
_CAP_IF_COMPLETE = 0.88


def compute_confidence(
    scorable_count: int,
    missing_facts: list[str],
    *,
    context_dependent: bool = False,
) -> float:
    """
    Return a deterministic confidence in ``[0.5, 0.88]`` from coverage signals.

    Baseline rises with the number of scorable dimensions.  The 0.85 cap kicks
    in when *any* incompleteness signal is present:

    - fewer than 8 scorable dimensions
    - at least one entry in ``missing_facts``
    - ``context_dependent=True`` (ambiguity flagged even without explicit facts)
    """
    incomplete = scorable_count < 8 or bool(missing_facts) or context_dependent
    inner = 0.5 + (scorable_count / 8.0) * 0.38
    return min(_CAP_IF_INCOMPLETE if incomplete else _CAP_IF_COMPLETE, inner)
