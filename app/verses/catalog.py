"""In-memory catalog wrapper for curated verse entries."""

from __future__ import annotations

from collections import defaultdict

from app.verses.types import CuratedVerseEntry


class VerseCatalog:
    """Lookup and list operations over curated verse entries."""

    def __init__(self, entries: list[CuratedVerseEntry]) -> None:
        self._entries = list(entries)
        self._by_ref = {entry.verse_ref: entry for entry in self._entries}
        self._by_theme: dict[str, list[CuratedVerseEntry]] = defaultdict(list)
        for entry in self._entries:
            for theme in entry.themes:
                self._by_theme[theme].append(entry)

    def get_by_ref(self, ref: str) -> CuratedVerseEntry | None:
        """Return a single entry by verse_ref."""
        return self._by_ref.get(ref)

    def list_active(self) -> list[CuratedVerseEntry]:
        """Return active entries only."""
        return [entry for entry in self._entries if entry.status == "active"]

    def list_by_theme(self, theme: str) -> list[CuratedVerseEntry]:
        """Return active entries tagged with a theme (safe default for retrieval)."""
        return [entry for entry in self._by_theme.get(theme, []) if entry.status == "active"]

