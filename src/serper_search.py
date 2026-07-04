import requests
from urllib.parse import urlparse

from src.config import (
    SERPER_API_KEY,
    DEFAULT_NUM_RESULTS,
    BLOCKED_DOMAINS
)


def is_blocked_url(url: str) -> bool:
    """
    Check whether URL belongs to blocked domains.
    """
    hostname = (urlparse(url).hostname or "").lower()

    for domain in BLOCKED_DOMAINS:
        blocked_domain = domain.lower()
        if hostname == blocked_domain or hostname.endswith(f".{blocked_domain}"):
            return True

    return False


def search_serper(
    query: str,
    num_results: int = DEFAULT_NUM_RESULTS
):
    """
    Search using Serper API and return filtered organic results.
    """
    if not SERPER_API_KEY:
        raise ValueError("SERPER_API_KEY is missing.")

    url = "https://google.serper.dev/search"

    payload = {
        "q": query,
        "num": num_results
    }

    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    organic_results = data.get("organic", [])

    filtered_results = []

    for item in organic_results:

        result_url = item.get("link", "")

        if not result_url:
            continue

        if is_blocked_url(result_url):
            print(f"Skipping blocked domain: {result_url}")
            continue

        filtered_results.append({
            "title": item.get("title", ""),
            "link": result_url,
            "snippet": item.get("snippet", "")
        })

    return filtered_results
