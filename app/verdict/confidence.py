"""
Confidence in the verdict, with the §2 / §7 cap rule.

``confidence > 0.85`` is allowed only when all eight dimensions are scorable
and ``missing_facts`` is empty.  An additional ``ambiguity_flag`` lets the
aggregator apply the cap when the class-flip signal fires, even before explicit
missing-facts strings are populated.
"""

from __future__ import annotations

_CAP_IF_INCOMPLETE = 0.85
_CAP_IF_COMPLETE = 0.88


def compute_confidence(
    scorable_count: int,
    missing_facts: list[str],
    *,
    ambiguity_flag: bool = False,
) -> float:
    """
    Return a deterministic confidence in ``[0.5, 0.88]`` from coverage signals.

    Baseline rises with the number of scorable dimensions.  The 0.85 cap kicks
    in when *any* incompleteness signal is present:

    - fewer than 8 scorable dimensions
    - at least one entry in ``missing_facts``
    - ``ambiguity_flag=True`` (class-flip ambiguity detected, even without
      explicit facts yet — set by the aggregator from ``ambiguity_can_flip_class``)
    """
    incomplete = scorable_count < 8 or bool(missing_facts) or ambiguity_flag
    inner = 0.5 + (scorable_count / 8.0) * 0.38
    return min(_CAP_IF_INCOMPLETE if incomplete else _CAP_IF_COMPLETE, inner)
