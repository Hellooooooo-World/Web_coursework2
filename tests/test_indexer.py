"""Tests for tokenisation and inverted index construction."""

from __future__ import annotations

import json
from pathlib import Path

from src.crawler import PageDocument
from src.indexer import build_inverted_index, load_index, save_index, tokenize


def test_tokenize_case_insensitive_tokens() -> None:
    assert tokenize("Good Friends! GOOD") == ["good", "friends", "good"]


def test_tokenize_apostrophe() -> None:
    toks = tokenize("Don't stop")
    assert "don't" in toks
    assert "stop" in toks


def test_build_inverted_index_positions_and_freq() -> None:
    docs = [
        PageDocument(url="https://a.example/u1", text="hello world hello"),
        PageDocument(url="https://a.example/u2", text="world peace"),
    ]
    idx = build_inverted_index(docs)
    hello = idx["inverted"]["hello"]["https://a.example/u1"]
    assert hello["frequency"] == 2
    assert hello["positions"] == [0, 2]
    world_urls = idx["inverted"]["world"]
    assert set(world_urls) == {"https://a.example/u1", "https://a.example/u2"}


def test_save_and_roundtrip_index(tmp_path: Path) -> None:
    docs = [PageDocument(url="https://x/", text="one two one")]
    idx = build_inverted_index(docs)
    path = tmp_path / "idx.json"
    save_index(idx, path)
    loaded = load_index(path)
    assert loaded["inverted"]["one"]["https://x/"]["frequency"] == 2
    raw = path.read_text(encoding="utf-8")
    assert "inverted" in json.loads(raw)
