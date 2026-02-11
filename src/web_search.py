"""Web search via DuckDuckGo — free, no API key needed."""

import logging

from ddgs import DDGS

logger = logging.getLogger(__name__)


def search(query: str, max_results: int = 3) -> list[dict]:
    """Search the web and return top results.

    Returns list of {"title": ..., "url": ..., "snippet": ...}
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        logger.info("Search '%s' → %d results", query, len(results))
        return [
            {
                "title": r.get("title", ""),
                "url": r.get("href", ""),
                "snippet": r.get("body", ""),
            }
            for r in results
        ]
    except Exception as e:
        logger.error("Search failed: %s", e)
        return []


def format_results(results: list[dict]) -> str:
    """Format search results into a readable string for the AI."""
    if not results:
        return "No results found."
    parts = []
    for r in results:
        parts.append(f"• {r['title']}\n  {r['snippet']}\n  {r['url']}")
    return "\n\n".join(parts)
