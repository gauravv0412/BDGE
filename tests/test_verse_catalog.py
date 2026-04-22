"""Tests for in-memory curated verse catalog."""

from __future__ import annotations

from app.verses.catalog import VerseCatalog
from app.verses.loader import load_curated_verses


def test_catalog_get_by_ref() -> None:
    entries = load_curated_verses()
    catalog = VerseCatalog(entries)
    found = catalog.get_by_ref("2.47")
    assert found is not None
    assert found.verse_id == "BG-2-47"


def test_catalog_list_by_theme() -> None:
    entries = load_curated_verses()
    catalog = VerseCatalog(entries)
    duty_entries = catalog.list_by_theme("duty")
    refs = {entry.verse_ref for entry in duty_entries}
    assert "2.47" in refs
    assert "3.35" in refs


def test_catalog_list_by_theme_excludes_draft_entries() -> None:
    entries = load_curated_verses()
    active_entry = next(entry for entry in entries if "duty" in entry.themes)
    draft_entry = active_entry.model_copy(
        update={"verse_id": "BG-DRAFT-TEST", "verse_ref": "9.99", "status": "draft"}
    )
    catalog = VerseCatalog([active_entry, draft_entry])

    themed = catalog.list_by_theme("duty")
    assert len(themed) == 1
    assert themed[0].status == "active"

