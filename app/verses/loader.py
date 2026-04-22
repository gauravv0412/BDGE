"""Loading and validation helpers for curated verse data."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.verses.types import CuratedVerseEntry

_CURATED_DIR = Path(__file__).resolve().parent / "data" / "curated"
_THEMES_PATH = _CURATED_DIR / "themes.json"
_APPLIES_WHEN_PATH = _CURATED_DIR / "applies_when.json"
_BLOCKERS_PATH = _CURATED_DIR / "blockers.json"
_VERSES_SEED_PATH = _CURATED_DIR / "verses_seed.json"


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_vocab(path: Path) -> set[str]:
    payload = _load_json(path)
    if not isinstance(payload, list):
        raise ValueError(f"Expected list payload in {path.name}.")
    normalized = {str(item).strip() for item in payload if str(item).strip()}
    if not normalized:
        raise ValueError(f"{path.name} cannot be empty.")
    return normalized


def load_theme_vocab() -> set[str]:
    """Load allowed theme tags."""
    return _load_vocab(_THEMES_PATH)


def load_applies_when_vocab() -> set[str]:
    """Load allowed applies_when tags."""
    return _load_vocab(_APPLIES_WHEN_PATH)


def load_blocker_vocab() -> set[str]:
    """Load allowed does_not_apply_when tags."""
    return _load_vocab(_BLOCKERS_PATH)


def validate_curated_entry(
    entry: dict[str, Any],
    *,
    theme_vocab: set[str],
    applies_when_vocab: set[str],
    blocker_vocab: set[str],
) -> CuratedVerseEntry:
    """Validate one curated entry and return a typed model."""
    parsed = CuratedVerseEntry.model_validate(entry)

    unknown_themes = set(parsed.themes) - theme_vocab
    if unknown_themes:
        raise ValueError(f"{parsed.verse_id}: unknown theme tags {sorted(unknown_themes)}.")

    unknown_applies = set(parsed.applies_when) - applies_when_vocab
    if unknown_applies:
        raise ValueError(f"{parsed.verse_id}: unknown applies_when tags {sorted(unknown_applies)}.")

    unknown_blockers = set(parsed.does_not_apply_when) - blocker_vocab
    if unknown_blockers:
        raise ValueError(
            f"{parsed.verse_id}: unknown does_not_apply_when tags {sorted(unknown_blockers)}."
        )

    if parsed.status == "active" and not (parsed.hindi_translation and parsed.hindi_translation.strip()):
        raise ValueError(f"{parsed.verse_id}: active entries require hindi_translation.")

    return parsed


def load_curated_verses(path: Path | None = None) -> list[CuratedVerseEntry]:
    """Load validated curated verse entries from the seed file."""
    target_path = path or _VERSES_SEED_PATH
    payload = _load_json(target_path)
    if not isinstance(payload, list):
        raise ValueError(f"Expected list payload in {target_path.name}.")

    theme_vocab = load_theme_vocab()
    applies_when_vocab = load_applies_when_vocab()
    blocker_vocab = load_blocker_vocab()

    seen_ids: set[str] = set()
    seen_refs: set[str] = set()
    entries: list[CuratedVerseEntry] = []
    for raw_entry in payload:
        if not isinstance(raw_entry, dict):
            raise ValueError("Each curated verse entry must be an object.")
        entry = validate_curated_entry(
            raw_entry,
            theme_vocab=theme_vocab,
            applies_when_vocab=applies_when_vocab,
            blocker_vocab=blocker_vocab,
        )
        if entry.verse_id in seen_ids:
            raise ValueError(f"Duplicate verse_id: {entry.verse_id}")
        if entry.verse_ref in seen_refs:
            raise ValueError(f"Duplicate verse_ref: {entry.verse_ref}")
        seen_ids.add(entry.verse_id)
        seen_refs.add(entry.verse_ref)
        entries.append(entry)

    return entries

