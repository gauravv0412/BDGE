# Canonical raw scripture corpus (Bhagavad Gita)

## Raw vs curated

| Location | Role |
|----------|------|
| `app/verses/data/raw/` | Full scripture corpus (canonical text, translations, per-verse attribution). Not used for retrieval ranking metadata. |
| `app/verses/data/curated/` | Active retrieval metadata (themes, `applies_when`, dimension affinity, etc.). Loaded by `app/verses/loader.py`. |

Do not store curated retrieval fields in the raw corpus, and do not treat curated seed files as the canonical scripture source.

## Canonical raw source file

For the raw-corpus workflow, the **only** source of truth is:

`app/verses/data/raw/bhagavad_gita_corpus_canonical.json`

Other files in `raw/` (e.g. alternate English exports) are **not** canonical for this workflow. The loader in `app/verses/raw_corpus.py` defaults to the filename above explicitly — it does not discover or merge multiple raw JSON files.

## What is validated

`load_canonical_raw_corpus()` parses the JSON and validates structure via Pydantic models (`CanonicalRawCorpus` and nested types). Invariants include:

- Top-level object shape: required string metadata, `sources`, `notes`, `chapters`.
- `extra="forbid"` on models — unknown fields are rejected.
- Each verse: required text fields (Devanagari, IAST, English, Hindi), `verse_ref` format (`chapter.verse` or hyphenated range), `verse_start` ≤ `verse_end`, `chapter` matches the parent chapter’s `chapter_number`.
- Corpus-wide: `total_chapters` / `total_verses` match actual list lengths; chapter numbers are exactly `1 … total_chapters` with no duplicates; `verse_ref` and `verse_id` are unique across the file.

This is **storage and structural** quality for a canonical scripture base — not verse retrieval scoring, theme tagging, or benchmark tuning.

## Out of scope

- Admin/editor UI, bulk curation campaigns, or automatic reconciliation across multiple raw files.
- Changing engine output schema, transport, or replacing curated retrieval with raw corpus for MVP matching.
- Lazy tagging or doctrine expansion beyond this Bhagavad Gita corpus.

## Usage

```python
from app.verses.raw_corpus import load_canonical_raw_corpus, iter_canonical_verses

corpus = load_canonical_raw_corpus()
for chapter, verse in iter_canonical_verses(corpus):
    ...
```

Tests: `tests/test_verse_raw_corpus.py`.

For expanding raw verses into editor-ready skeletons (without touching active retrieval), see `docs/curation_prep_workflow.md`.
