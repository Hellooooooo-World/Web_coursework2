"""Unit tests for cli dispatch, build/load edge cases, and main() entry paths."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

from src.crawler import Crawler, PageDocument
from src.main import SearchShell, main, run_interactive


def test_dispatch_empty_returns_none() -> None:
    shell = SearchShell(index_path=Path("/tmp/unused"))
    assert shell.dispatch([]) is None


def test_dispatch_quit_exit() -> None:
    shell = SearchShell(index_path=Path("/tmp/unused"))
    assert shell.dispatch(["quit"]) == "__EXIT__"
    assert shell.dispatch(["EXIT"]) == "__EXIT__"


def test_dispatch_help() -> None:
    shell = SearchShell(index_path=Path("/tmp/unused"))
    out = shell.dispatch(["help"])
    assert "build" in out and "find" in out
    out_q = shell.dispatch(["?"])
    assert "build" in out_q


def test_dispatch_unknown_command() -> None:
    shell = SearchShell(index_path=Path("/tmp/unused"))
    out = shell.dispatch(["nope"])
    assert "Unknown command" in out


def test_print_usage_missing_word(tmp_path: Path) -> None:
    idx_path = tmp_path / "idx.json"
    from src.indexer import build_inverted_index, save_index

    save_index(
        build_inverted_index([PageDocument(url="https://x/", text="hi")]),
        idx_path,
    )
    shell = SearchShell(index_path=idx_path)
    shell.dispatch(["load"])
    assert "Usage: print" in shell.dispatch(["print"])


def test_find_no_match(tmp_path: Path) -> None:
    idx_path = tmp_path / "idx.json"
    from src.indexer import build_inverted_index, save_index

    save_index(
        build_inverted_index([PageDocument(url="https://x/", text="only here")]),
        idx_path,
    )
    shell = SearchShell(index_path=idx_path)
    shell.dispatch(["load"])
    assert shell.dispatch(["find", "only", "missing"]) == "No pages matched."


def test_load_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("{ not json", encoding="utf-8")
    shell = SearchShell(index_path=path)
    out = shell.dispatch(["load"])
    assert "Failed to load index" in out


def test_load_missing_inverted_key(tmp_path: Path) -> None:
    path = tmp_path / "bad2.json"
    path.write_text('{"version": 1}', encoding="utf-8")
    shell = SearchShell(index_path=path)
    out = shell.dispatch(["load"])
    assert "Failed to load index" in out


@patch("src.main.Crawler")
def test_build_saves_index(mock_crawler_cls: MagicMock, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    inst = MagicMock()

    def fake_crawl(progress=None):
        if progress:
            progress("https://quotes.toscrape.com/", 1, 0)
        return [
            PageDocument(url="https://quotes.toscrape.com/", text="hello world"),
            PageDocument(url="https://quotes.toscrape.com/page/2/", text="world peace"),
        ]

    inst.crawl.side_effect = fake_crawl
    mock_crawler_cls.return_value = inst

    idx = tmp_path / "idx.json"
    shell = SearchShell(index_path=idx)
    out = shell.dispatch(["build"])
    captured = capsys.readouterr()

    assert "Done" in out and "Indexed 2 pages" in out
    assert idx.is_file()
    assert "Progress" in captured.out or "[1]" in captured.out

    inst.crawl.assert_called_once()


@patch("src.main.Crawler")
def test_build_no_pages(mock_crawler_cls: MagicMock, tmp_path: Path) -> None:
    inst = MagicMock()
    inst.crawl.return_value = []
    mock_crawler_cls.return_value = inst
    shell = SearchShell(index_path=tmp_path / "idx.json")
    out = shell.dispatch(["build"])
    assert "No pages retrieved" in out


@patch("src.main.Crawler")
def test_build_warns_when_some_fetches_fail(mock_crawler_cls: MagicMock, tmp_path: Path) -> None:
    session = MagicMock()
    html_home = (
        '<html><body><a href="https://quotes.toscrape.com/page/2/">next</a></body></html>'
    )

    def fake_get(url: str, **_kwargs):
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        if "page/2" in url:
            raise requests.ConnectionError("simulated failure")
        resp.text = html_home
        return resp

    session.get.side_effect = fake_get
    real_crawler = Crawler(session=session, sleeper=lambda _: None)
    mock_crawler_cls.return_value = real_crawler

    shell = SearchShell(index_path=tmp_path / "idx.json")
    out = shell.dispatch(["build"])
    assert "Done" in out
    assert "could not be fetched" in out


def test_main_one_shot_command(tmp_path: Path) -> None:
    from src.indexer import build_inverted_index, save_index

    idx_path = tmp_path / "idx.json"
    save_index(
        build_inverted_index([PageDocument(url="https://u/", text="alpha beta")]),
        idx_path,
    )
    rc = main(["-c", "find alpha beta", "-i", str(idx_path)])
    assert rc == 0


def test_main_one_shot_bad_shlex(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["-c", "print \"unclosed", "-i", str(tmp_path / "x.json")])
    assert rc == 2
    err = capsys.readouterr().err
    assert "Parse error" in err


def test_main_one_shot_quit_exits_zero() -> None:
    assert main(["-c", "quit"]) == 0


def test_main_run_interactive_sequence(tmp_path: Path) -> None:
    from src.indexer import build_inverted_index, save_index

    idx_path = tmp_path / "idx.json"
    save_index(
        build_inverted_index([PageDocument(url="https://u/", text="x y")]),
        idx_path,
    )
    lines = iter(["load", "find x y", "quit"])
    outputs: list[str] = []

    def fake_input(prompt: str = "") -> str:
        return next(lines)

    run_interactive(index_path=idx_path, input_fn=fake_input, output_fn=lambda s: outputs.append(s))
    joined = "\n".join(outputs)
    assert "Loaded index" in joined
    assert "https://u/" in joined


def test_run_interactive_eof(tmp_path: Path) -> None:
    def eof_input(_: str = "") -> str:
        raise EOFError

    outputs: list[str] = []
    run_interactive(index_path=tmp_path / "n.json", input_fn=eof_input, output_fn=lambda s: outputs.append(s))
    assert any(o == "" for o in outputs) or len(outputs) >= 1


def test_run_interactive_shlex_error(tmp_path: Path) -> None:
    from src.indexer import build_inverted_index, save_index

    idx_path = tmp_path / "idx.json"
    save_index(
        build_inverted_index([PageDocument(url="https://u/", text="a")]),
        idx_path,
    )
    bad_then_quit = iter(['print "bad', "quit"])

    def fake_input(_: str = "") -> str:
        return next(bad_then_quit)

    outputs: list[str] = []
    run_interactive(index_path=idx_path, input_fn=fake_input, output_fn=lambda s: outputs.append(s))
    assert any("Parse error" in o for o in outputs)


def test_run_interactive_blank_line_ignored(tmp_path: Path) -> None:
    lines = iter(["", "quit"])

    def fake_input(_: str = "") -> str:
        return next(lines)

    outputs: list[str] = []
    run_interactive(index_path=tmp_path / "n.json", input_fn=fake_input, output_fn=lambda s: outputs.append(s))
    assert "Search engine tool" in "\n".join(outputs)


@patch("src.main.run_interactive")
def test_main_default_invokes_interactive(mock_run: MagicMock) -> None:
    assert main([]) == 0
    mock_run.assert_called_once()
