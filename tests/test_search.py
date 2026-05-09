"""Tests for print/find query helpers."""

from __future__ import annotations

from src.indexer import build_inverted_index
from src.crawler import PageDocument
from src.search import find_pages, format_print_word


def _sample_index() -> dict:
    docs = [
        PageDocument(
            url="https://quotes.toscrape.com/",
            text="good friends and good books",
        ),
        PageDocument(
            url="https://quotes.toscrape.com/page/2/",
            text="friends trust peace",
        ),
    ]
    return build_inverted_index(docs)


def test_format_print_unknown_word() -> None:
    idx = _sample_index()
    out = format_print_word(idx, "nonsense")
    assert "No index entry" in out


def test_format_print_shows_urls_stats() -> None:
    idx = _sample_index()
    out = format_print_word(idx, "good")
    assert "good" in out.lower()
    assert "frequency" in out
    assert "quotes.toscrape.com" in out


def test_find_single_word() -> None:
    idx = _sample_index()
    urls = find_pages(idx, ["friends"])
    assert len(urls) == 2


def test_find_multiword_and_semantics() -> None:
    idx = _sample_index()
    urls = find_pages(idx, ["good", "friends"])
    assert urls == ["https://quotes.toscrape.com/"]


def test_find_impossible_and_returns_empty() -> None:
    idx = _sample_index()
    assert find_pages(idx, ["good", "nope"]) == []


def test_find_empty_terms() -> None:
    idx = _sample_index()
    assert find_pages(idx, []) == []
