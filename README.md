# Coursework 2: Search Engine Tool (XJCO3011 / COMP3011)

Python command-line search tool for [quotes.toscrape.com](https://quotes.toscrape.com/): crawl with a **≥6 second** politeness window, build a case-insensitive **inverted index** (per-word frequency and token positions per page), then query it with **`print`** and **`find`**.

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
```

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

## Notes for your video / submission

- Declare any GenAI use honestly; the brief requires a **critical reflection** segment in the video.
- After `build`, submit the generated **`data/index.json`** (or the path you passed to `--index`) along with your GitHub URL and video link on Minerva.
- Verify your video link in a private/incognito window before submitting.
