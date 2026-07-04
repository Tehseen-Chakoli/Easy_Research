"""Helpers for parsing mixed research input into queries and URLs."""

from __future__ import annotations

import re
from urllib.parse import urlparse


def is_youtube_url(url: str) -> bool:
    """Return whether a URL points to a supported YouTube host."""
    lower_url = (url or "").lower()
    return "youtube.com" in lower_url or "youtu.be" in lower_url


def is_url(text: str) -> bool:
    """Validate whether a value is an HTTP or HTTPS URL."""
    try:
        parsed = urlparse(text)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    except Exception:
        return False


def extract_urls_and_queries(source_input: str) -> tuple[list[str], str]:
    """Split mixed user input into unique URLs and a remaining search query."""
    if not source_input:
        return [], ""

    url_pattern = r"https?://[^\s,]+"
    urls = re.findall(url_pattern, source_input)

    query_text = re.sub(url_pattern, " ", source_input)
    query_lines = [
        line.strip(" ,")
        for line in query_text.splitlines()
        if line.strip(" ,")
    ]
    google_query = " ".join(query_lines).strip()

    seen = set()
    clean_urls = []
    for url in urls:
        clean_url = url.strip().rstrip(").,]")
        if clean_url and clean_url not in seen and is_url(clean_url):
            clean_urls.append(clean_url)
            seen.add(clean_url)

    return clean_urls, google_query
