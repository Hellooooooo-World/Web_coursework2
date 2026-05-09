"""Build, serialise, and load an inverted index from crawled page text."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .crawler import PageDocument

# Word tokens: letters and digits; apostrophe inside words (e.g. don't).
_TOKEN_RE = re.compile(r"[a-z0-9]+(?:'[a-z0-9]+)?", re.IGNORECASE)


def tokenize(text: str) -> list[str]:
    return [m.group(0).lower() for m in _TOKEN_RE.finditer(text)]


def build_inverted_index(documents: list[PageDocument]) -> dict[str, Any]:
    """
    Build inverted index: word -> url -> {frequency, positions}.
    Positions are 0-based word indices in the page token sequence.
    """
    inverted: dict[str, dict[str, dict[str, Any]]] = {}
    for doc in documents:
        tokens = tokenize(doc.text)
        for position, word in enumerate(tokens):
            if word not in inverted:
                inverted[word] = {}
            page_entry = inverted[word].setdefault(
                doc.url,
                {"frequency": 0, "positions": []},
            )
            page_entry["frequency"] += 1
            page_entry["positions"].append(position)
    return {"version": 1, "inverted": inverted}


def save_index(index: dict[str, Any], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def load_index(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict) or "inverted" not in data:
        raise ValueError("Invalid index file: missing 'inverted' root key")
    return data
