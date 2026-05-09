"""Unit tests for the crawler (mocked HTTP; no live network required)."""

from __future__ import annotations

from unittest.mock import MagicMock

from src.crawler import (
    Crawler,
    DEFAULT_BASE_URL,
    POLITENESS_SECONDS,
    discover_links,
    extract_visible_text,
)


def test_extract_visible_text_strips_scripts() -> None:
    html = "<html><body><script>x</script><p>Hello</p></body></html>"
    assert extract_visible_text(html) == "Hello"


def test_discover_links_same_origin_only() -> None:
    html = """
    <a href="/page/1/">one</a>
    <a href="https://quotes.toscrape.com/tag/life/">tag</a>
    <a href="https://evil.example/">no</a>
    """
    links = discover_links(html, "https://quotes.toscrape.com/", "quotes.toscrape.com")
    assert "https://quotes.toscrape.com/page/1" in links or "https://quotes.toscrape.com/page/1/" in links
    assert any("tag" in u for u in links)
    assert not any("evil.example" in u for u in links)


def test_politeness_sleep_between_requests() -> None:
    sleeps: list[float] = []

    def fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)

    session = MagicMock()
    session.get.return_value.text = "<html><body></body></html>"
    session.get.return_value.raise_for_status = MagicMock()

    crawler = Crawler(
        base_url=DEFAULT_BASE_URL,
        politeness_seconds=POLITENESS_SECONDS,
        session=session,
        sleeper=fake_sleep,
    )
    crawler.fetch("https://quotes.toscrape.com/")
    crawler.fetch("https://quotes.toscrape.com/page/2/")
    assert session.get.call_count == 2
    # Second fetch should wait until politeness window elapsed
    assert sleeps, "expected at least one politeness sleep before the second request"
    assert max(sleeps) >= POLITENESS_SECONDS * 0.99


def test_crawl_bfs_uses_fetch_and_collects_pages() -> None:
    html_home = """
    <html><body>
    <p>alpha beta</p>
    <a href="https://quotes.toscrape.com/page/2/">next</a>
    </body></html>
    """
    html_page2 = "<html><body><p>gamma</p></body></html>"

    def norm(u: str) -> str:
        return u.rstrip("/")

    responses = {
        norm("https://quotes.toscrape.com/"): html_home,
        norm("https://quotes.toscrape.com/page/2/"): html_page2,
    }

    session = MagicMock()

    def fake_get(url: str, **_kwargs):
        text = responses.get(norm(url))
        if text is None:
            raise AssertionError(f"unexpected URL {url!r}")
        resp = MagicMock()
        resp.text = text
        resp.raise_for_status = MagicMock()
        return resp

    session.get.side_effect = fake_get

    crawler = Crawler(session=session, sleeper=lambda _: None)
    docs = crawler.crawl()
    urls = {d.url for d in docs}
    assert "https://quotes.toscrape.com/" in urls
    assert any("page/2" in u for u in urls)
    joined = " ".join(d.text for d in docs)
    assert "alpha" in joined and "gamma" in joined
