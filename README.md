# Coursework 2: Search Engine Tool (XJCO3011 / COMP3011)

Python command-line search tool for [quotes.toscrape.com](https://quotes.toscrape.com/): crawl with a **≥6 second** politeness window, build a case-insensitive **inverted index** (per-word frequency and token positions per page), then query it with **`print`** and **`find`**.

## Architecture overview

End-to-end data flow:

1. **`crawler`** — Breadth-first traversal of on-site links only (`urllib.parse` + same-host checks). Each page is fetched with **Requests**; **Beautiful Soup** strips `script` / `style` / `noscript` and extracts visible text so varied HTML layouts still yield plain text.
2. **`indexer`** — Tokenises text with a single regex (letters/digits; apostrophes inside words). Builds an **inverted index**: `token → { page_url → { frequency, positions[] } }`, wrapped as JSON with a **`version`** field for forward compatibility.
3. **`search`** — `print` formats postings for one token; `find` performs **conjunctive (AND)** queries by intersecting URL sets per token.
4. **`main`** — Interactive or `-c` “one-shot” CLI; persists the index as **one JSON file** (default `data/index.json`).

```text
HTTP pages  →  PageDocument(url, text)  →  tokens per page
                                                ↓
                         inverted index on disk (JSON)  ←  build / load
                                                ↓
                                        print / find
```

## Design rationale

| Decision | Why |
|----------|-----|
| **Dict-based inverted index** | Average-case **O(1)** lookup per token for `find`; intersecting **small URL sets** per AND-term is efficient for this dataset. Alternatives (e.g. on-disk BM25 engines) are unnecessary for coursework scale. |
| **Store `positions` not only counts** | Satisfies the brief’s “position, etc.” requirement and supports debugging; enables future extensions (proximity, phrase-like checks) without re-crawling. |
| **JSON index file** | Human-readable for marking/debugging; trivial `build` / `load`; trade-off: larger file than a binary format — acceptable here. |
| **AND semantics for multi-word `find`** | Matches the brief example (“pages containing the words **good** **and** **friends**”). |
| **6 s politeness delay** | Enforced with monotonic clocks between successful request timestamps so the gap holds even after slow responses. |
| **`INDEX_FORMAT_VERSION` in `load_index`** | Rejects incompatible files early with a clear error instead of failing mysteriously during search. |

## Error handling and robustness

- **Network / HTTP**: Failed fetches log a **warning** (visible at default logging level), increment a **per-run failure counter**, and the crawler **continues** with remaining URLs so one bad link does not abort the crawl.
- **HTML extraction**: If text extraction raises unexpectedly, the page is indexed with **empty text** rather than crashing the whole `build`.
- **Index file**: `load` validates **JSON**, **`version`**, presence of **`inverted`**, and that **`inverted` is an object** before use.
- **CLI**: `load` / `build` failures return **user-facing strings**; `shlex` errors in interactive mode are caught and reported without exiting the shell.

## Code style

Source follows **PEP 8** naming and layout, type hints on public components, and split modules (`crawler` / `indexer` / `search` / `main`) to keep responsibilities separated.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run the tool

From the repository root:

```bash
python -m src.main
```

Optional flags:

```bash
python -m src.main --index path\to\my_index.json
python -m src.main -c "load"
python -m src.main -c "print good"
python -m src.main -v -c "build"
```

`-v` / `--verbose` lowers the logging threshold so you see more detail during a crawl (default still shows **warnings**, e.g. failed URLs).

### Commands (interactive `>` shell)

| Command | Description |
|--------|-------------|
| `build` | Crawl the site, build the inverted index, save to `data/index.json` (default). **Takes several minutes** because of the 6-second delay between HTTP requests. |
| `load` | Load a previously saved index from disk into memory. |
| `print <word>` | Show stored statistics for one token (lowercased): URLs, frequency, word positions in that page’s token list. |
| `find <w> [<w> ...]` | **AND** search: list URLs whose page contains **every** given word at least once. |
| `help` | Short help. |
| `quit` / `exit` | Leave the shell. |

### Examples

```
> build
> load
> print nonsense
> find indifference
> find good friends
```

## Project layout

```
src/
  crawler.py    # HTTP crawl + politeness + HTML text extraction
  indexer.py    # Tokenise pages and build/save/load JSON inverted index
  search.py     # print / find logic
  main.py       # Interactive CLI
tests/
  test_crawler.py
  test_crawler_edges.py
  test_indexer.py
  test_search.py
  test_main_shell.py
  test_main_dispatch.py
  test_integration_pipeline.py
  test_performance_search.py
  test_cli_integration.py
data/
  index.json    # produced by `build` (submit this with your coursework)
```

## Tests

The suite is split into:

- **Unit tests**: crawler/indexer/search parsing, URL rules, shell command dispatch, mocked `build`, error paths.
- **Integration tests**: mocked crawl → save index → new shell `load` → `find`/`print`; subprocess smoke tests for `python -m src.main`.
- **Performance tests**: repeated `find` on a large synthetic index with a loose latency bound (regression guard).

Run all tests (no live crawling):

```bash
pytest
```

Coverage report (requires `pytest-cov`, listed in `requirements.txt`):

```bash
pytest --cov=src --cov-report=term-missing
```

Typical overall line coverage for `src/` is **above 95%** (only rare branches such as duplicate-queue edge cases or the `__main__` entry shim may remain unhit when importing the package).

