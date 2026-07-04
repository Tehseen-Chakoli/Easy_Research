"""Search integration for Easy Research using the Serper API."""

from __future__ import annotations

import requests

from src.config import SERPER_API_KEY, SERPER_SEARCH_URL


def search_serper(query: str, num_results: int = 5) -> list[dict]:
    """Run a Serper search and return normalized organic results."""
    if not SERPER_API_KEY:
        raise ValueError("SERPER_API_KEY is missing.")

    normalized_query = (query or "").strip()
    if not normalized_query:
        raise ValueError("Search query cannot be empty.")

    response = requests.post(
        SERPER_SEARCH_URL,
        headers={
            "X-API-KEY": SERPER_API_KEY,
            "Content-Type": "application/json",
        },
        json={
            "q": normalized_query,
            "num": int(num_results),
        },
        timeout=30,
    )
    response.raise_for_status()

    payload = response.json()
    organic_results = payload.get("organic", [])

    return [
        {
            "title": item.get("title", "").strip(),
            "link": item.get("link", "").strip(),
            "snippet": item.get("snippet", "").strip(),
        }
        for item in organic_results
        if item.get("link")
    ]
