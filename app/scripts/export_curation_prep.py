"""
Generate ``verses_editor_prep.json`` from the canonical raw Bhagavad Gita corpus.

This writes **editor-prep** data under ``app/verses/data/curation_prep/``, not
active retrieval metadata under ``data/curated/``.

Usage (from repo root)::

    PYTHONPATH=. .venv/bin/python -m app.scripts.export_curation_prep
"""

from __future__ import annotations

import sys

from app.verses.curation_prep import (
    DEFAULT_EDITOR_PREP_PATH,
    build_curation_prep_artifact,
    write_curation_prep_artifact,
)


def main() -> int:
    artifact = build_curation_prep_artifact()
    path = write_curation_prep_artifact(artifact)
    assert path.resolve() == DEFAULT_EDITOR_PREP_PATH.resolve()
    print(f"Wrote {path} ({artifact.header.verse_entry_count} entries).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
