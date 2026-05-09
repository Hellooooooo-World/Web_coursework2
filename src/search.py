"""Query helpers for the inverted index (print / find)."""

from __future__ import annotations

from typing import Any


def format_print_word(index: dict[str, Any], word: str) -> str:
    """Human-readable inverted list for a single word (case-insensitive)."""
    key = word.strip().lower()
    inverted: dict[str, Any] = index.get("inverted", {})
    if not key:
        return "(empty word)"
    entry = inverted.get(key)
    if entry is None:
        return f"No index entry for '{word}'."
    lines = [f"Inverted index for '{key}':"]
    for url in sorted(entry.keys()):
        stats = entry[url]
        freq = stats.get("frequency", 0)
        positions = stats.get("positions", [])
        lines.append(f"  {url}")
        lines.append(f"    frequency: {freq}")
        lines.append(f"    positions: {positions}")
    return "\n".join(lines)


def find_pages(index: dict[str, Any], query_terms: list[str]) -> list[str]:
    """
    AND search: pages that contain every term at least once.
    Terms are lowercased; empty list returns [].
    """
    inverted: dict[str, Any] = index.get("inverted", {})
    terms = [t.lower() for t in query_terms if t.strip()]
    if not terms:
        return []

    url_sets: list[set[str]] = []
    for term in terms:
        pages = inverted.get(term)
        if not pages:
            return []
        url_sets.append(set(pages.keys()))

    common = set.intersection(*url_sets)
    return sorted(common)
