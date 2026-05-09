"""Extra crawler edge coverage (URL policies and HTTP failures)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
import requests

from src.crawler import Crawler, _same_site


def test_same_site_rejects_non_http_scheme() -> None:
    assert _same_site("ftp://quotes.toscrape.com/path", "quotes.toscrape.com") is False


def test_same_site_accepts_www_variant() -> None:
    assert (
        _same_site("https://www.quotes.toscrape.com/page/1", "quotes.toscrape.com") is True
    )


def test_same_site_when_allowed_netloc_includes_www_prefix() -> None:
    assert (
        _same_site("https://quotes.toscrape.com/", "www.quotes.toscrape.com") is True
    )


def test_fetch_records_time_then_raises() -> None:
    session = MagicMock()
    session.get.side_effect = requests.ConnectionError("boom")
    crawler = Crawler(session=session, sleeper=lambda _: None)
    with pytest.raises(requests.ConnectionError):
        crawler.fetch("https://quotes.toscrape.com/")
    assert session.get.call_count == 1


def test_crawl_skips_failed_fetch_but_keeps_going() -> None:
    """If first fetch fails completely, crawler returns no documents (queue may drain empty)."""
    session = MagicMock()
    session.get.side_effect = requests.Timeout("timeout")
    crawler = Crawler(session=session, sleeper=lambda _: None)
    assert crawler.crawl() == []


def test_crawl_invokes_progress_per_page() -> None:
    html = "<html><body>Hi <a href='/next/'>x</a></body></html>"
    session = MagicMock()

    def responses(url, **_kwargs):
        resp = MagicMock()
        if url.endswith("quotes.toscrape.com/") or url.endswith("quotes.toscrape.com"):
            resp.text = html
        else:
            resp.text = "<html><body>end</body></html>"
        resp.raise_for_status = MagicMock()
        return resp

    session.get.side_effect = responses
    events: list[tuple[int, int]] = []

    def progress(_url: str, n: int, qsize: int) -> None:
        events.append((n, qsize))

    crawler = Crawler(session=session, sleeper=lambda _: None)
    crawler.crawl(progress=progress)
    assert events and events[0][0] == 1
