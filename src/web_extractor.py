"""Readable-content extraction for research URLs."""

from __future__ import annotations

import requests
import trafilatura
from bs4 import BeautifulSoup

from src.config import MIN_CONTENT_LENGTH, USER_AGENT


def clean_text(text: str) -> str:
    """Collapse noisy whitespace into readable line-separated text."""
    return "\n".join(
        line.strip()
        for line in (text or "").splitlines()
        if line.strip()
    )


def extract_with_trafilatura(url: str) -> str | None:
    """Try the article/document oriented extraction path first."""
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        return None

    extracted_text = trafilatura.extract(downloaded)
    if not extracted_text:
        return None

    cleaned_text = clean_text(extracted_text)
    if len(cleaned_text) < MIN_CONTENT_LENGTH:
        return None

    return cleaned_text


def extract_with_requests(url: str) -> str | None:
    """Fallback to direct HTML fetching and text extraction."""
    response = requests.get(
        url,
        headers={"User-Agent": USER_AGENT},
        timeout=30,
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()

    cleaned_text = clean_text(soup.get_text(separator="\n"))
    if len(cleaned_text) < MIN_CONTENT_LENGTH:
        return None

    return cleaned_text


def extract_content(url: str, title: str = "", snippet: str = "") -> dict:
    """Return normalized extracted content and the method that produced it."""
    extracted_text = extract_with_trafilatura(url)
    if extracted_text:
        return {
            "title": title,
            "url": url,
            "snippet": snippet,
            "content": extracted_text,
            "extraction_method": "trafilatura",
        }

    extracted_text = extract_with_requests(url)
    if extracted_text:
        return {
            "title": title,
            "url": url,
            "snippet": snippet,
            "content": extracted_text,
            "extraction_method": "requests_bs4",
        }

    return {
        "title": title,
        "url": url,
        "snippet": snippet,
        "content": None,
        "extraction_method": None,
    }
