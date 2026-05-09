"""Interactive command-line shell: build, load, print, find."""

from __future__ import annotations

import argparse
import logging
import shlex
import sys
from pathlib import Path
from typing import Any, Callable

from .crawler import Crawler
from .indexer import build_inverted_index, load_index, save_index
from .search import find_pages, format_print_word


def _configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s", force=True)


def default_index_path() -> Path:
    return Path(__file__).resolve().parent.parent / "data" / "index.json"


class SearchShell:
    """Stateful CLI matching the coursework brief."""

    def __init__(self, index_path: Path | None = None) -> None:
        self.index_path = index_path or default_index_path()
        self.index: dict[str, Any] | None = None

    def dispatch(self, parts: list[str]) -> str | None:
        if not parts:
            return None
        cmd = parts[0].lower()
        if cmd in ("quit", "exit"):
            return "__EXIT__"
        if cmd == "help" or cmd == "?":
            return _help_text()
        if cmd == "build":
            return self._cmd_build()
        if cmd == "load":
            return self._cmd_load()
        if cmd == "print":
            return self._cmd_print(parts)
        if cmd == "find":
            return self._cmd_find(parts)
        return f"Unknown command: {parts[0]}. Type 'help'."

    def _cmd_build(self) -> str:
        intro = (
            "Crawling quotes.toscrape.com (≥6s between requests; expect several minutes).\n"
            "Progress (each line = one page fetched):"
        )
        print(intro, flush=True)

        def _progress(url: str, n: int, qsize: int) -> None:
            print(f"  [{n}] {url}  (queue: {qsize})", flush=True)

        crawler = Crawler()
        docs = crawler.crawl(progress=_progress)
        if not docs:
            return "No pages retrieved. Check your network connection."
        idx = build_inverted_index(docs)
        save_index(idx, self.index_path)
        self.index = idx
        n_terms = len(idx.get("inverted", {}))
        lines = [
            f"Done. Indexed {len(docs)} pages; {n_terms} distinct tokens.",
            f"Saved index to {self.index_path}",
        ]
        failed = getattr(crawler, "failed_fetch_count", 0)
        if isinstance(failed, int) and failed > 0:
            lines.append(
                f"Warning: {failed} URL(s) could not be fetched "
                "(network or HTTP errors); results use successfully retrieved pages only.",
            )
        return "\n".join(lines)

    def _cmd_load(self) -> str:
        try:
            self.index = load_index(self.index_path)
        except FileNotFoundError:
            return f"No index file at {self.index_path}. Run 'build' first."
        except (OSError, ValueError) as exc:
            return f"Failed to load index: {exc}"
        n_terms = len(self.index.get("inverted", {}))
        return f"Loaded index ({n_terms} tokens) from {self.index_path}"

    def _cmd_print(self, parts: list[str]) -> str:
        if self.index is None:
            return "No index in memory. Run 'load' or 'build' first."
        if len(parts) < 2:
            return "Usage: print <word>"
        word = parts[1]
        return format_print_word(self.index, word)

    def _cmd_find(self, parts: list[str]) -> str:
        if self.index is None:
            return "No index in memory. Run 'load' or 'build' first."
        terms = parts[1:]
        if not terms:
            return "Usage: find <word> [<word> ...]  (empty query is not allowed)"
        urls = find_pages(self.index, terms)
        if not urls:
            return "No pages matched."
        return "\n".join(urls)


def _help_text() -> str:
    return (
        "Commands:\n"
        "  build              Crawl site, build inverted index, save to data/\n"
        "  load               Load index from disk\n"
        "  print <word>       Show inverted index stats for a word\n"
        "  find <w> [<w>...]  Pages containing all words (AND)\n"
        "  help               This message\n"
        "  quit / exit        Leave the shell"
    )


def run_interactive(
    index_path: Path | None = None,
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
) -> None:
    shell = SearchShell(index_path=index_path)
    output_fn("Search engine tool. Type 'help' for commands.")
    while True:
        try:
            line = input_fn("> ").strip()
        except EOFError:
            output_fn("")
            break
        if not line:
            continue
        try:
            parts = shlex.split(line)
        except ValueError as exc:
            output_fn(f"Parse error: {exc}")
            continue
        result = shell.dispatch(parts)
        if result == "__EXIT__":
            break
        if result:
            output_fn(result)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Quotes search engine (coursework CLI).")
    parser.add_argument(
        "-i",
        "--index",
        type=Path,
        default=None,
        help="Path to index JSON (default: ./data/index.json)",
    )
    parser.add_argument(
        "-c",
        "--command",
        default=None,
        help="Run one command non-interactively then exit (e.g. 'load' or 'print good')",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose logging (includes informational crawler messages)",
    )
    args = parser.parse_args(argv)

    _configure_logging(args.verbose)

    index_path = args.index or default_index_path()
    if args.command is not None:
        shell = SearchShell(index_path=index_path)
        try:
            parts = shlex.split(args.command)
        except ValueError as exc:
            print(f"Parse error: {exc}", file=sys.stderr)
            return 2
        out = shell.dispatch(parts)
        if out == "__EXIT__":
            return 0
        if out:
            print(out)
        return 0

    run_interactive(index_path=index_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
