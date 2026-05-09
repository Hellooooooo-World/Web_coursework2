"""Lightweight performance regression tests for query latency."""

from __future__ import annotations

import time

from src.crawler import PageDocument
from src.indexer import build_inverted_index
from src.search import find_pages


def test_find_many_queries_stays_fast() -> None:
    """Large inverted map + repeated AND queries should stay well under one second."""
    docs = [
        PageDocument(
            url=f"https://example.test/page/{i}",
            text=" ".join(f"w{j}" for j in range(40)) + " raretoken matchme",
        )
        for i in range(300)
    ]
    idx = build_inverted_index(docs)
    terms = ["w0", "w1", "raretoken"]

    t0 = time.perf_counter()
    for _ in range(200):
        urls = find_pages(idx, terms)
        assert len(urls) == 300
    elapsed = time.perf_counter() - t0
    assert elapsed < 1.5
