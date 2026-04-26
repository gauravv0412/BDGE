"""Deterministic 10-batch workflow for full-corpus curation prep drafts.

This module keeps raw/cursor/prep/curated boundaries strict:
- Reads canonical scripture only from ``raw/bhagavad_gita_corpus_canonical.json``.
- Writes batch artifacts only under ``data/curation_prep/``.
- Never mutates active curated retrieval files.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from app.verses.curation_prep import (
    CurationPrepArtifact,
    CurationPrepEntry,
    CurationPrepHeader,
    CurationPrepPlaceholders,
    CURATION_PREP_DATA_DIR,
    dumps_curation_prep_artifact,
    validate_curation_prep_payload,
)
from app.verses.raw_corpus import (
    CANONICAL_RAW_CORPUS_FILENAME,
    CanonicalRawCorpus,
    CanonicalRawVerse,
    iter_canonical_verses,
    load_canonical_raw_corpus,
)
from app.verses.types import VerseRecord, VerseSource

BATCHES_DIR = CURATION_PREP_DATA_DIR / "batches"
BATCH_SCHEMA_ID = "bdge.curation_batch.v1"
BATCH_ARTIFACT_ROLE = "editor_prep_batch_not_active_retrieval"
BATCH_ARTIFACT_FILENAME_TEMPLATE = "curation_batch_{batch_id}.json"

_CURATED_DIR = Path(__file__).resolve().parent / "data" / "curated"

_GENERIC_PLACEHOLDER_VALUES = {
    "",
    "todo",
    "tbd",
    "na",
    "n/a",
    "none",
    "misc",
    "generic",
    "placeholder",
    "lorem ipsum",
}


@dataclass(frozen=True)
class BatchSlice:
    chapter: int
    verse_start: int
    verse_end: int


@dataclass(frozen=True)
class BatchPlanItem:
    batch_id: str
    label: str
    slices: tuple[BatchSlice, ...]


TEN_BATCH_PLAN: tuple[BatchPlanItem, ...] = (
    BatchPlanItem(
        batch_id="B01",
        label="Chapter 1 + Chapter 2 (1-36)",
        slices=(BatchSlice(1, 1, 47), BatchSlice(2, 1, 36)),
    ),
    BatchPlanItem(
        batch_id="B02",
        label="Chapter 2 (37-72)",
        slices=(BatchSlice(2, 37, 72),),
    ),
    BatchPlanItem(
        batch_id="B03",
        label="Chapters 3-4",
        slices=(BatchSlice(3, 1, 43), BatchSlice(4, 1, 42)),
    ),
    BatchPlanItem(
        batch_id="B04",
        label="Chapters 5-6",
        slices=(BatchSlice(5, 1, 29), BatchSlice(6, 1, 47)),
    ),
    BatchPlanItem(
        batch_id="B05",
        label="Chapters 7-9",
        slices=(BatchSlice(7, 1, 30), BatchSlice(8, 1, 28), BatchSlice(9, 1, 34)),
    ),
    BatchPlanItem(
        batch_id="B06",
        label="Chapters 10-11",
        slices=(BatchSlice(10, 1, 42), BatchSlice(11, 1, 55)),
    ),
    BatchPlanItem(
        batch_id="B07",
        label="Chapters 12-13",
        slices=(BatchSlice(12, 1, 20), BatchSlice(13, 1, 35)),
    ),
    BatchPlanItem(
        batch_id="B08",
        label="Chapters 14-15",
        slices=(BatchSlice(14, 1, 27), BatchSlice(15, 1, 20)),
    ),
    BatchPlanItem(
        batch_id="B09",
        label="Chapters 16-17",
        slices=(BatchSlice(16, 1, 24), BatchSlice(17, 1, 28)),
    ),
    BatchPlanItem(
        batch_id="B10",
        label="Chapter 18",
        slices=(BatchSlice(18, 1, 78),),
    ),
)


class CurationBatchHeader(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    schema_id: Literal["bdge.curation_batch.v1"] = BATCH_SCHEMA_ID
    artifact_role: Literal["editor_prep_batch_not_active_retrieval"] = BATCH_ARTIFACT_ROLE
    canonical_raw_filename: str = Field(min_length=1)
    batch_id: str = Field(pattern=r"^B[0-9]{2}$")
    batch_label: str = Field(min_length=1)
    chapter_coverage: list[int]
    verse_entry_count: int = Field(ge=1)


class CurationBatchArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    header: CurationBatchHeader
    entries: list[CurationPrepEntry]

    @model_validator(mode="after")
    def _integrity(self) -> "CurationBatchArtifact":
        if self.header.canonical_raw_filename != CANONICAL_RAW_CORPUS_FILENAME:
            raise ValueError(
                "batch header canonical_raw_filename must equal "
                f"{CANONICAL_RAW_CORPUS_FILENAME!r}."
            )
        if self.header.verse_entry_count != len(self.entries):
            raise ValueError("header.verse_entry_count mismatch.")
        refs = [e.scripture.verse_ref for e in self.entries]
        ids = [e.scripture.verse_id for e in self.entries]
        if len(refs) != len(set(refs)):
            raise ValueError("Duplicate verse_ref inside batch artifact.")
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate verse_id inside batch artifact.")
        return self


class BatchCoverageReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    total_canonical_verses: int
    total_planned_verses: int
    missing_verse_refs: list[str]
    duplicate_verse_refs: list[str]


def get_ten_batch_plan() -> tuple[BatchPlanItem, ...]:
    return TEN_BATCH_PLAN


def _plan_by_id(batch_id: str) -> BatchPlanItem:
    normalized = batch_id.strip().upper()
    for item in TEN_BATCH_PLAN:
        if item.batch_id == normalized:
            return item
    raise ValueError(f"Unknown batch_id {batch_id!r}. Expected one of {[p.batch_id for p in TEN_BATCH_PLAN]}.")


def _canonical_verses(corpus: CanonicalRawCorpus) -> list[CanonicalRawVerse]:
    return [v for _ch, v in iter_canonical_verses(corpus)]


def _verse_in_slice(verse: CanonicalRawVerse, sl: BatchSlice) -> bool:
    if verse.chapter != sl.chapter:
        return False
    # Range verse (e.g. 16.1-3) belongs if it starts inside slice.
    return sl.verse_start <= verse.verse_start <= sl.verse_end


def verses_for_batch(batch_id: str, *, corpus: CanonicalRawCorpus | None = None) -> list[CanonicalRawVerse]:
    planned = _plan_by_id(batch_id)
    loaded = corpus if corpus is not None else load_canonical_raw_corpus()
    selected: list[CanonicalRawVerse] = []
    for verse in _canonical_verses(loaded):
        if any(_verse_in_slice(verse, sl) for sl in planned.slices):
            selected.append(verse)
    if not selected:
        raise ValueError(f"Batch {planned.batch_id} resolved to zero verses.")
    return selected


def _to_prep_entry(verse: CanonicalRawVerse) -> CurationPrepEntry:
    scripture = VerseRecord(
        verse_id=verse.verse_id,
        verse_ref=verse.verse_ref,
        chapter=verse.chapter,
        verse_start=verse.verse_start,
        verse_end=verse.verse_end,
        sanskrit_devanagari=verse.sanskrit_devanagari,
        sanskrit_iast=verse.sanskrit_iast,
        hindi_translation=verse.hindi_translation,
        english_translation=verse.english_translation,
        source=VerseSource(hindi=verse.source.hindi, english=verse.source.english),
    )
    return CurationPrepEntry(
        promotion_requested=False,
        scripture=scripture,
        placeholders=CurationPrepPlaceholders(),
    )


def build_batch_artifact(
    batch_id: str,
    *,
    corpus: CanonicalRawCorpus | None = None,
) -> CurationBatchArtifact:
    planned = _plan_by_id(batch_id)
    loaded = corpus if corpus is not None else load_canonical_raw_corpus()
    verses = verses_for_batch(planned.batch_id, corpus=loaded)
    entries = [_to_prep_entry(v) for v in verses]
    chapter_coverage = sorted({v.chapter for v in verses})
    return CurationBatchArtifact(
        header=CurationBatchHeader(
            canonical_raw_filename=CANONICAL_RAW_CORPUS_FILENAME,
            batch_id=planned.batch_id,
            batch_label=planned.label,
            chapter_coverage=chapter_coverage,
            verse_entry_count=len(entries),
        ),
        entries=entries,
    )


def dumps_batch_artifact(artifact: CurationBatchArtifact) -> str:
    body: dict[str, Any] = {
        "header": artifact.header.model_dump(mode="json"),
        "entries": [
            {
                "entry_kind": e.entry_kind,
                "promotion_requested": e.promotion_requested,
                "placeholders": e.placeholders.model_dump(mode="json"),
                "scripture": e.scripture.model_dump(mode="json"),
            }
            for e in artifact.entries
        ],
    }
    return json.dumps(body, ensure_ascii=False, indent=2) + "\n"


def _guard_curation_prep_path(path: Path) -> None:
    resolved = path.resolve()
    curated_resolved = _CURATED_DIR.resolve()
    if resolved == curated_resolved or curated_resolved in resolved.parents:
        raise ValueError(f"Refusing curated output path for batch workflow: {path}")


def default_batch_path(batch_id: str) -> Path:
    planned = _plan_by_id(batch_id)
    return BATCHES_DIR / BATCH_ARTIFACT_FILENAME_TEMPLATE.format(batch_id=planned.batch_id.lower())


def write_batch_artifact(artifact: CurationBatchArtifact, path: Path | None = None) -> Path:
    target = path or default_batch_path(artifact.header.batch_id)
    _guard_curation_prep_path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(dumps_batch_artifact(artifact), encoding="utf-8")
    return target


def load_batch_artifact(path: Path) -> CurationBatchArtifact:
    if not path.is_file():
        raise FileNotFoundError(f"Batch artifact not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    return validate_batch_payload(payload)


def validate_batch_payload(payload: Any) -> CurationBatchArtifact:
    if not isinstance(payload, dict):
        raise ValueError("Batch artifact must be a JSON object.")
    try:
        return CurationBatchArtifact.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(f"Batch artifact failed validation: {exc}") from exc


def _is_generic(value: str) -> bool:
    return value.strip().lower() in _GENERIC_PLACEHOLDER_VALUES


def _promotable_issues(entry: CurationPrepEntry) -> list[str]:
    p = entry.placeholders
    issues: list[str] = []
    if not p.core_teaching.strip():
        issues.append("core_teaching is empty")
    elif _is_generic(p.core_teaching):
        issues.append("core_teaching is generic placeholder")

    for field_name in ("themes", "applies_when", "does_not_apply_when"):
        values = list(getattr(p, field_name))
        if not values:
            issues.append(f"{field_name} is empty")
            continue
        if any(_is_generic(v) for v in values):
            issues.append(f"{field_name} contains generic placeholder values")

    if p.priority is None:
        issues.append("priority is unset")
    if p.status is None:
        issues.append("status is unset")
    return issues


def validate_ai_filled_batch(
    artifact: CurationBatchArtifact,
    *,
    corpus: CanonicalRawCorpus | None = None,
) -> CurationBatchArtifact:
    loaded = corpus if corpus is not None else load_canonical_raw_corpus()
    expected = build_batch_artifact(artifact.header.batch_id, corpus=loaded)
    if len(artifact.entries) != len(expected.entries):
        raise ValueError("AI-filled batch entry count changed from canonical batch definition.")

    errors: list[str] = []
    for idx, (got, exp) in enumerate(zip(artifact.entries, expected.entries, strict=True)):
        if got.scripture.model_dump(mode="json") != exp.scripture.model_dump(mode="json"):
            errors.append(
                f"entries[{idx}] verse_ref={exp.scripture.verse_ref!r}: scripture identity/text/source modified"
            )
            continue
        if got.promotion_requested:
            issues = _promotable_issues(got)
            if issues:
                errors.append(
                    f"entries[{idx}] verse_ref={got.scripture.verse_ref!r}: " + "; ".join(issues)
                )

    if errors:
        raise ValueError("AI-filled batch failed validation:\n- " + "\n- ".join(errors))
    return artifact


def coverage_report(*, corpus: CanonicalRawCorpus | None = None) -> BatchCoverageReport:
    loaded = corpus if corpus is not None else load_canonical_raw_corpus()
    canonical_refs = [v.verse_ref for v in _canonical_verses(loaded)]

    planned_refs: list[str] = []
    for plan in TEN_BATCH_PLAN:
        planned_refs.extend(v.verse_ref for v in verses_for_batch(plan.batch_id, corpus=loaded))

    duplicates = sorted({ref for ref in planned_refs if planned_refs.count(ref) > 1})
    missing = sorted(set(canonical_refs) - set(planned_refs))
    return BatchCoverageReport(
        total_canonical_verses=len(canonical_refs),
        total_planned_verses=len(planned_refs),
        missing_verse_refs=missing,
        duplicate_verse_refs=duplicates,
    )


def assert_ten_batch_coverage(*, corpus: CanonicalRawCorpus | None = None) -> BatchCoverageReport:
    report = coverage_report(corpus=corpus)
    if report.total_planned_verses != report.total_canonical_verses:
        raise ValueError(
            f"Batch plan covers {report.total_planned_verses} verses but canonical has {report.total_canonical_verses}."
        )
    if report.missing_verse_refs:
        raise ValueError(f"Missing verse_ref in batch plan: {report.missing_verse_refs[:10]}")
    if report.duplicate_verse_refs:
        raise ValueError(f"Duplicate verse_ref across batch plan: {report.duplicate_verse_refs[:10]}")
    return report


def merge_batch_into_curation_prep(
    batch_artifact: CurationBatchArtifact,
    *,
    base_prep: CurationPrepArtifact | None = None,
) -> CurationPrepArtifact:
    # Validate before merge to ensure scripture grounding and promotable row quality.
    validate_ai_filled_batch(batch_artifact)

    base = base_prep
    if base is None:
        from app.verses.curation_prep import build_curation_prep_artifact

        base = build_curation_prep_artifact()

    by_ref = {e.scripture.verse_ref: e for e in base.entries}
    batch_refs = {e.scripture.verse_ref for e in batch_artifact.entries}
    if len(batch_refs) != len(batch_artifact.entries):
        raise ValueError("Duplicate verse_ref inside batch merge payload.")

    merged_entries: list[CurationPrepEntry] = []
    for entry in base.entries:
        ref = entry.scripture.verse_ref
        if ref in batch_refs:
            merged_entries.append(next(e for e in batch_artifact.entries if e.scripture.verse_ref == ref))
        else:
            merged_entries.append(entry)

    missing_from_base = sorted(batch_refs - set(by_ref))
    if missing_from_base:
        raise ValueError(f"Batch contains verse_ref not present in base prep: {missing_from_base[:10]}")

    return CurationPrepArtifact(
        header=CurationPrepHeader(
            canonical_raw_filename=CANONICAL_RAW_CORPUS_FILENAME,
            verse_entry_count=len(merged_entries),
        ),
        entries=merged_entries,
    )


def write_merged_prep_artifact(
    merged: CurationPrepArtifact,
    *,
    batch_id: str,
    path: Path | None = None,
) -> Path:
    target = path or (BATCHES_DIR / f"merged_editor_prep_{batch_id.lower()}.json")
    _guard_curation_prep_path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(dumps_curation_prep_artifact(merged), encoding="utf-8")
    return target


def export_batch(
    batch_id: str,
    *,
    path: Path | None = None,
) -> Path:
    artifact = build_batch_artifact(batch_id)
    return write_batch_artifact(artifact, path=path)


def export_all_batches(*, allow_all: bool = False) -> list[Path]:
    if not allow_all:
        raise ValueError("Refusing all-batch export unless allow_all=True.")
    paths: list[Path] = []
    for item in TEN_BATCH_PLAN:
        paths.append(export_batch(item.batch_id))
    return paths


def import_batch_to_prep(
    batch_path: Path,
    *,
    base_prep_path: Path | None = None,
    out_path: Path | None = None,
) -> Path:
    batch = load_batch_artifact(batch_path)
    validate_ai_filled_batch(batch)

    if base_prep_path is None:
        from app.verses.curation_prep import build_curation_prep_artifact

        base = build_curation_prep_artifact()
    else:
        payload = json.loads(base_prep_path.read_text(encoding="utf-8"))
        base = validate_curation_prep_payload(payload)

    merged = merge_batch_into_curation_prep(batch, base_prep=base)
    return write_merged_prep_artifact(merged, batch_id=batch.header.batch_id, path=out_path)
