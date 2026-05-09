"""Smoke tests for the interactive shell dispatcher."""

from __future__ import annotations

from pathlib import Path

from src.main import SearchShell
from src.indexer import build_inverted_index, save_index
from src.crawler import PageDocument


def test_shell_load_missing_file(tmp_path: Path) -> None:
    shell = SearchShell(index_path=tmp_path / "missing.json")
    out = shell.dispatch(["load"])
    assert "No index file" in out


def test_shell_print_requires_index(tmp_path: Path) -> None:
    shell = SearchShell(index_path=tmp_path / "x.json")
    assert "No index in memory" in shell.dispatch(["print", "hello"])


def test_shell_find_empty_query(tmp_path: Path) -> None:
    idx_path = tmp_path / "idx.json"
    save_index(
        build_inverted_index([PageDocument(url="https://u/", text="a b")]),
        idx_path,
    )
    shell = SearchShell(index_path=idx_path)
    assert "Loaded" in shell.dispatch(["load"])
    out = shell.dispatch(["find"])
    assert "Usage" in out
