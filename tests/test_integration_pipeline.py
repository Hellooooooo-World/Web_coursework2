"""Integration-style tests: mocked crawl → persist → reload → query (no live HTTP)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from src.crawler import PageDocument
from src.main import SearchShell


@patch("src.main.Crawler")
def test_pipeline_build_then_second_shell_load_find(mock_crawler_cls: MagicMock, tmp_path: Path) -> None:
    docs = [
        PageDocument(url="https://quotes.toscrape.com/", text="good friends books"),
        PageDocument(url="https://quotes.toscrape.com/page/2/", text="good only"),
    ]
    inst = MagicMock()
    inst.crawl.return_value = docs
    mock_crawler_cls.return_value = inst

    idx_path = tmp_path / "idx.json"
    shell_a = SearchShell(index_path=idx_path)
    assert "Done" in shell_a.dispatch(["build"])
    assert idx_path.is_file()

    shell_b = SearchShell(index_path=idx_path)
    assert "Loaded index" in shell_b.dispatch(["load"])
    urls = shell_b.dispatch(["find", "good", "friends"]).splitlines()
    assert urls == ["https://quotes.toscrape.com/"]
    printed = shell_b.dispatch(["print", "good"])
    assert "frequency" in printed and "quotes.toscrape.com" in printed


@patch("src.main.Crawler")
def test_pipeline_print_after_build_same_shell(mock_crawler_cls: MagicMock, tmp_path: Path) -> None:
    inst = MagicMock()
    inst.crawl.return_value = [
        PageDocument(url="https://quotes.toscrape.com/tag/test/", text="uniqueword xyz"),
    ]
    mock_crawler_cls.return_value = inst
    shell = SearchShell(index_path=tmp_path / "idx.json")
    shell.dispatch(["build"])
    out = shell.dispatch(["print", "uniqueword"])
    assert "uniqueword" in out.lower()
