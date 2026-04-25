"""Promotion workflow: editor-prep rows → validated :class:`CuratedVerseEntry` records.

Only rows with ``promotion_requested=True`` and **fully filled** placeholders are
eligible. This prevents lazy bulk promotion of the full corpus.

Default behavior is **plan + review artifact** only; writing production
``verses_seed.json`` requires an explicit confirmation flag.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.verses.curation_prep import (
    CURATION_PREP_DATA_DIR,
    EDITOR_PREP_ARTIFACT_FILENAME,
    CurationPrepArtifact,
    CurationPrepEntry,
    CurationPrepPlaceholders,
    load_curation_prep_artifact,
)
from app.verses.loader import (
    curated_verses_seed_path,
    validate_curated_entry,
    validate_curated_seed_payload,
    load_applies_when_vocab,
    load_blocker_vocab,
    load_theme_vocab,
)
from app.verses.types import CuratedVerseEntry, VerseRecord

DEFAULT_MAX_PROMOTION_BATCH = 25
PROMOTION_REVIEW_SCHEMA_ID = "bdge.curation_promotion_review.v1"
PROMOTION_REVIEW_ARTIFACT_ROLE = "promotion_review_not_active_retrieval"
DEFAULT_PROMOTION_REVIEW_PATH = CURATION_PREP_DATA_DIR / "verses_promotion_review.json"


class PromotionError(ValueError):
    """Promotion batch failed validation or safety checks."""


@dataclass(frozen=True)
class PromotionPlan:
    """Result of a successful promotion plan (no file writes)."""

    promoted: tuple[CuratedVerseEntry, ...]
    skipped_not_requested: int
    promotion_requested_count: int


class PromotionReviewArtifact(BaseModel):
    """Review-only JSON wrapper; not loaded by verse retrieval."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    schema_id: Literal["bdge.curation_promotion_review.v1"] = PROMOTION_REVIEW_SCHEMA_ID
    artifact_role: Literal["promotion_review_not_active_retrieval"] = (
        PROMOTION_REVIEW_ARTIFACT_ROLE
    )
    source_prep_filename: str = Field(min_length=1)
    skipped_not_requested_count: int = Field(ge=0)
    promotion_requested_count: int = Field(ge=0)
    promoted_entry_count: int = Field(ge=0)
    promoted_entries: list[dict[str, Any]] = Field(min_length=0)


def _placeholder_issues_for_promotion(p: CurationPrepPlaceholders) -> list[str]:
    issues: list[str] = []
    if not p.core_teaching.strip():
        issues.append("core_teaching is empty")
    if not p.themes:
        issues.append("themes is empty")
    if not p.applies_when:
        issues.append("applies_when is empty")
    if not p.does_not_apply_when:
        issues.append("does_not_apply_when is empty")
    if p.priority is None:
        issues.append("priority is unset")
    if p.status is None:
        issues.append("status is unset")
    return issues


def prep_entry_to_curated_dict(entry: CurationPrepEntry) -> dict[str, Any]:
    """Merge prep scripture (canonical text) with filled retrieval placeholders."""
    s = entry.scripture.model_dump(mode="json")
    p = entry.placeholders
    s["core_teaching"] = p.core_teaching.strip()
    s["themes"] = list(p.themes)
    s["applies_when"] = list(p.applies_when)
    s["does_not_apply_when"] = list(p.does_not_apply_when)
    s["dimension_affinity"] = dict(p.dimension_affinity)
    s["priority"] = p.priority
    s["status"] = p.status
    return s


def _assert_scripture_unchanged(prep_entry: CurationPrepEntry, curated: CuratedVerseEntry) -> None:
    """Ensure promotion did not alter scripture relative to prep (grounding check)."""
    include = set(VerseRecord.model_fields.keys())
    prep_s = prep_entry.scripture.model_dump(mode="json")
    cur_s = curated.model_dump(mode="json", include=include)
    if prep_s != cur_s:
        raise PromotionError(
            f"Scripture mismatch after promotion for verse_ref={prep_entry.scripture.verse_ref!r}; "
            "refusing to treat as grounded in prep."
        )


def build_promotion_plan(
    prep: CurationPrepArtifact,
    *,
    existing_entries: Iterable[CuratedVerseEntry] | None = None,
    max_promotions: int = DEFAULT_MAX_PROMOTION_BATCH,
    allow_large_batch: bool = False,
) -> PromotionPlan:
    """Plan promotion: only ``promotion_requested`` rows with complete placeholders.

    Validates each promoted row with :func:`app.verses.loader.validate_curated_entry`
    and checks ``verse_ref`` / ``verse_id`` against ``existing_entries`` and within
    the promotion batch.
    """
    existing = tuple(existing_entries) if existing_entries is not None else ()
    existing_refs = {e.verse_ref for e in existing}
    existing_ids = {e.verse_id for e in existing}

    skipped = sum(1 for e in prep.entries if not e.promotion_requested)
    requested_count = sum(1 for e in prep.entries if e.promotion_requested)

    if requested_count > max_promotions and not allow_large_batch:
        raise PromotionError(
            f"Promotion batch has {requested_count} requested rows; "
            f"max is {max_promotions} unless allow_large_batch=True "
            "(bulk promotion guard)."
        )

    if requested_count == 0:
        return PromotionPlan(
            promoted=(),
            skipped_not_requested=skipped,
            promotion_requested_count=0,
        )

    theme_vocab = load_theme_vocab()
    applies_when_vocab = load_applies_when_vocab()
    blocker_vocab = load_blocker_vocab()

    failures: list[str] = []
    promoted: list[CuratedVerseEntry] = []
    batch_refs: list[str] = []
    batch_ids: list[str] = []

    for idx, entry in enumerate(prep.entries):
        if not entry.promotion_requested:
            continue
        ref = entry.scripture.verse_ref
        ph_issues = _placeholder_issues_for_promotion(entry.placeholders)
        if ph_issues:
            failures.append(
                f"entries[{idx}] verse_ref={ref!r}: requested promotion but incomplete — "
                + "; ".join(ph_issues)
            )
            continue
        try:
            raw_dict = prep_entry_to_curated_dict(entry)
            curated = validate_curated_entry(
                raw_dict,
                theme_vocab=theme_vocab,
                applies_when_vocab=applies_when_vocab,
                blocker_vocab=blocker_vocab,
            )
        except ValueError as exc:
            failures.append(f"entries[{idx}] verse_ref={ref!r}: {exc}")
            continue

        try:
            _assert_scripture_unchanged(entry, curated)
        except PromotionError as exc:
            failures.append(f"entries[{idx}] verse_ref={ref!r}: {exc}")
            continue

        if ref in existing_refs:
            failures.append(
                f"entries[{idx}] verse_ref={ref!r}: conflicts with existing curated verse_ref."
            )
            continue
        if curated.verse_id in existing_ids:
            failures.append(
                f"entries[{idx}] verse_id={curated.verse_id!r}: conflicts with existing curated verse_id."
            )
            continue
        if ref in batch_refs:
            failures.append(
                f"entries[{idx}] verse_ref={ref!r}: duplicate verse_ref within this promotion batch."
            )
            continue
        if curated.verse_id in batch_ids:
            failures.append(
                f"entries[{idx}] verse_id={curated.verse_id!r}: duplicate verse_id within this promotion batch."
            )
            continue

        batch_refs.append(ref)
        batch_ids.append(curated.verse_id)
        promoted.append(curated)

    if failures:
        raise PromotionError(
            "Promotion failed for one or more requested rows:\n- "
            + "\n- ".join(failures)
        )

    return PromotionPlan(
        promoted=tuple(promoted),
        skipped_not_requested=skipped,
        promotion_requested_count=requested_count,
    )


def promotion_plan_to_review_artifact(
    plan: PromotionPlan,
    *,
    source_prep_filename: str = EDITOR_PREP_ARTIFACT_FILENAME,
) -> PromotionReviewArtifact:
    """Build a review JSON model from a promotion plan."""
    promoted_entries = [e.model_dump(mode="json") for e in plan.promoted]
    return PromotionReviewArtifact(
        source_prep_filename=source_prep_filename,
        skipped_not_requested_count=plan.skipped_not_requested,
        promotion_requested_count=plan.promotion_requested_count,
        promoted_entry_count=len(plan.promoted),
        promoted_entries=promoted_entries,
    )


def dumps_promotion_review_artifact(plan: PromotionPlan, **kwargs: Any) -> str:
    """Deterministic JSON for review / hand-off (not a retrieval file)."""
    review = promotion_plan_to_review_artifact(plan, **kwargs)
    body: dict[str, Any] = {
        "artifact_role": review.artifact_role,
        "promoted_entries": review.promoted_entries,
        "promoted_entry_count": review.promoted_entry_count,
        "promotion_requested_count": review.promotion_requested_count,
        "schema_id": review.schema_id,
        "skipped_not_requested_count": review.skipped_not_requested_count,
        "source_prep_filename": review.source_prep_filename,
    }
    return json.dumps(body, ensure_ascii=False, indent=2) + "\n"


def write_promotion_review_artifact(
    plan: PromotionPlan,
    path: Path | None = None,
    **kwargs: Any,
) -> Path:
    """Write review artifact under ``curation_prep/`` by default."""
    target = path if path is not None else DEFAULT_PROMOTION_REVIEW_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(dumps_promotion_review_artifact(plan, **kwargs), encoding="utf-8")
    return target


def validate_promotion_review_payload(payload: Any) -> PromotionReviewArtifact:
    if not isinstance(payload, dict):
        raise ValueError("Promotion review artifact must be a JSON object.")
    try:
        return PromotionReviewArtifact.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(f"Promotion review artifact failed validation: {exc}") from exc


def merge_promoted_into_seed_json(
    seed_path: Path,
    promoted: Sequence[CuratedVerseEntry],
    *,
    write: bool = False,
    confirm_production_curated_write: bool = False,
) -> list[CuratedVerseEntry]:
    """Append promoted entries to a seed JSON list and validate the merged result.

    When ``write`` is True, writes ``seed_path`` after validation. Writing the
    production ``verses_seed.json`` additionally requires
    ``confirm_production_curated_write=True``.
    """
    production = seed_path.resolve() == curated_verses_seed_path().resolve()
    if write and production and not confirm_production_curated_write:
        raise ValueError(
            "Refusing to write production verses_seed.json without "
            "confirm_production_curated_write=True."
        )

    existing_payload = json.loads(seed_path.read_text(encoding="utf-8"))
    existing_entries = validate_curated_seed_payload(existing_payload)
    existing_refs = {e.verse_ref for e in existing_entries}
    existing_ids = {e.verse_id for e in existing_entries}

    for p in promoted:
        if p.verse_ref in existing_refs:
            raise PromotionError(
                f"Promoted verse_ref={p.verse_ref!r} already exists in seed {seed_path.name}."
            )
        if p.verse_id in existing_ids:
            raise PromotionError(
                f"Promoted verse_id={p.verse_id!r} already exists in seed {seed_path.name}."
            )

    merged_payload: list[dict[str, Any]] = [
        e.model_dump(mode="json") for e in existing_entries
    ] + [p.model_dump(mode="json") for p in promoted]
    merged_entries = validate_curated_seed_payload(merged_payload)

    if write:
        seed_path.write_text(
            json.dumps(merged_payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    return merged_entries


def plan_promotion_from_prep_path(
    prep_path: Path,
    **kwargs: Any,
) -> PromotionPlan:
    """Convenience: load prep artifact then :func:`build_promotion_plan`."""
    prep = load_curation_prep_artifact(prep_path)
    return build_promotion_plan(prep, **kwargs)
