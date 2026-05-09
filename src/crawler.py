"""HTTP crawler for quotes.toscrape.com with a mandatory politeness window."""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from typing import Callable
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

DEFAULT_BASE_URL = "https://quotes.toscrape.com"
POLITENESS_SECONDS = 6.0
REQUEST_TIMEOUT = 30


@dataclass(frozen=True)
class PageDocument:
    """One crawled page: canonical URL and plain text used for indexing."""

    url: str
    text: str


def _same_site(url: str, allowed_netloc: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False
    netloc = parsed.netloc.lower()
    if netloc == allowed_netloc:
        return True
    if netloc.startswith("www.") and netloc[4:] == allowed_netloc:
        return True
    if allowed_netloc.startswith("www.") and netloc == allowed_netloc[4:]:
        return True
    return netloc == allowed_netloc


def _normalize_url(url: str) -> str:
    """Drop fragments; keep path/query for distinct pages."""
    p = urlparse(url)
    return p._replace(fragment="").geturl()


def discover_links(html: str, page_url: str, allowed_netloc: str) -> set[str]:
    soup = BeautifulSoup(html, "html.parser")
    found: set[str] = set()
    for tag in soup.find_all("a", href=True):
        absolute = urljoin(page_url, tag["href"])
        absolute = _normalize_url(absolute)
        if _same_site(absolute, allowed_netloc):
            found.add(absolute.rstrip("/") or absolute)
    # Normalise trailing slash consistency for root
    return {_canonical_quotes_url(u) for u in found}


def _canonical_quotes_url(url: str) -> str:
    """Normalise scheme (https), netloc casing, drop fragments."""
    p = urlparse(_normalize_url(url))
    netloc = p.netloc.lower()
    scheme = "https"
    path = p.path or "/"
    rebuilt = p._replace(scheme=scheme, netloc=netloc, path=path, fragment="")
    url_out = rebuilt.geturl()
    if path in ("", "/"):
        return f"{scheme}://{netloc}/"
    return url_out


def extract_visible_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return soup.get_text(separator=" ", strip=True)


class Crawler:
    """Breadth-first crawler respecting a delay between network requests."""

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        politeness_seconds: float = POLITENESS_SECONDS,
        session: requests.Session | None = None,
        sleeper: Callable[[float], None] | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/") + "/" if not base_url.endswith("/") else base_url
        parsed = urlparse(self.base_url)
        self._allowed_netloc = parsed.netloc.lower()
        self.politeness_seconds = politeness_seconds
        self._session = session or requests.Session()
        self._session.headers.setdefault(
            "User-Agent",
            "XJCO3011-Coursework2-SearchTool/1.0 (+educational)",
        )
        self._sleeper = sleeper or time.sleep
        self._last_request_monotonic: float | None = None

    def _wait_politeness(self) -> None:
        if self._last_request_monotonic is None:
            return
        elapsed = time.monotonic() - self._last_request_monotonic
        remaining = self.politeness_seconds - elapsed
        if remaining > 0:
            self._sleeper(remaining)

    def fetch(self, url: str) -> str:
        self._wait_politeness()
        try:
            response = self._session.get(url, timeout=REQUEST_TIMEOUT)
            self._last_request_monotonic = time.monotonic()
            response.raise_for_status()
        except requests.RequestException:
            self._last_request_monotonic = time.monotonic()
            raise
        return response.text

    def crawl(
        self,
        progress: Callable[[str, int, int], None] | None = None,
    ) -> list[PageDocument]:
        """
        Crawl all reachable on-site HTML pages starting from the base URL.

        If ``progress`` is set, it is called after each successful fetch as
        ``progress(url, pages_fetched_so_far, queue_size)`` so UIs can show activity.
        """
        start = _canonical_quotes_url(_normalize_url(self.base_url))
        visited: set[str] = set()
        queue: deque[str] = deque([start])
        documents: list[PageDocument] = []

        while queue:
            url = queue.popleft()
            if url in visited:
                continue
            visited.add(url)

            try:
                html = self.fetch(url)
            except requests.RequestException:
                continue

            text = extract_visible_text(html)
            documents.append(PageDocument(url=url, text=text))
            if progress is not None:
                progress(url, len(documents), len(queue))

            for link in discover_links(html, url, self._allowed_netloc):
                if link not in visited:
                    queue.append(link)

        documents.sort(key=lambda d: d.url)
        return documents
