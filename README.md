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
  test_indexer.py
  test_search.py
data/
  index.json    # produced by `build` (submit this with your coursework)
```

## Tests

```bash
pytest
```

Tests use mocks and **do not** hit the network.

## Notes for your video / submission

- Declare any GenAI use honestly; the brief requires a **critical reflection** segment in the video.
- After `build`, submit the generated **`data/index.json`** (or the path you passed to `--index`) along with your GitHub URL and video link on Minerva.
- Verify your video link in a private/incognito window before submitting.
