"""Tests for tokenisation and inverted index construction."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.crawler import PageDocument
from src.indexer import INDEX_FORMAT_VERSION, build_inverted_index, load_index, save_index, tokenize


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
    assert idx["version"] == INDEX_FORMAT_VERSION
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


def test_load_rejects_wrong_format_version(tmp_path: Path) -> None:
    path = tmp_path / "badver.json"
    path.write_text(
        '{"version": 999, "inverted": {}}',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="format version"):
        load_index(path)


def test_load_rejects_non_object_inverted(tmp_path: Path) -> None:
    path = tmp_path / "badinv.json"
    path.write_text(
        '{"version": 1, "inverted": "broken"}',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="object"):
        load_index(path)
