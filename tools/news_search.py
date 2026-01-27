"""
NewsMesh News Search for Mindrian
===================================

Structured news search via NewsMesh API.
Returns articles with category, topics, people — richer than Tavily for news.

Base URL: https://api.newsmesh.co/v1
Auth: NEWSMESH_API_KEY env var (free tier: 50/day, 7-day history)

Categories: politics, technology, business, health, entertainment,
            sports, science, lifestyle, environment, world
"""

import logging
import os
from typing import Dict, List, Optional

import requests

from tools.research_cache import cached_call

logger = logging.getLogger("news_search")

BASE_URL = "https://api.newsmesh.co/v1"


def search_news(
    query: str,
    max_results: int = 5,
    category: Optional[str] = None,
    sort_by: str = "relevant",
) -> Dict:
    """
    Search NewsMesh for news articles.

    Args:
        query: Search query (supports phrases, AND/OR, exclusions with -)
        max_results: Number of articles (max 25)
        category: Optional filter — politics, technology, business, health,
                  entertainment, sports, science, lifestyle, environment, world
        sort_by: 'relevant', 'date_descending', 'date_ascending'
    """
    api_key = os.getenv("NEWSMESH_API_KEY")
    if not api_key:
        return {"source": "NewsMesh", "query": query, "articles": [], "error": "NEWSMESH_API_KEY not set"}

    def _fetch():
        try:
            params = {
                "apiKey": api_key,
                "q": query,
                "limit": min(max_results, 25),
                "sortBy": sort_by,
            }
            if category:
                params["category"] = category

            resp = requests.get(f"{BASE_URL}/search", params=params, timeout=15)

            if resp.status_code != 200:
                err = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
                return {"source": "NewsMesh", "query": query, "articles": [],
                        "error": err.get("message", f"HTTP {resp.status_code}")}

            data = resp.json()
            articles = []
            for item in data.get("articles", [])[:max_results]:
                articles.append({
                    "title": item.get("title", ""),
                    "description": (item.get("description") or "")[:250],
                    "url": item.get("link", ""),
                    "source": item.get("source", ""),
                    "published": (item.get("published_date") or "")[:10],
                    "category": item.get("category", ""),
                    "topics": item.get("topics", [])[:5],
                    "people": item.get("people", [])[:3],
                })

            logger.info("NewsMesh: '%s' → %d articles", query[:40], len(articles))
            return {"source": "NewsMesh", "query": query, "articles": articles, "error": None}

        except Exception as e:
            logger.error("NewsMesh error: %s", e)
            return {"source": "NewsMesh", "query": query, "articles": [], "error": str(e)}

    return cached_call("newsmesh", query, _fetch, ttl=900)  # 15 min cache (news changes)


def get_trending(max_results: int = 5) -> Dict:
    """Get trending news articles."""
    api_key = os.getenv("NEWSMESH_API_KEY")
    if not api_key:
        return {"source": "NewsMesh", "query": "trending", "articles": [], "error": "NEWSMESH_API_KEY not set"}

    def _fetch():
        try:
            resp = requests.get(
                f"{BASE_URL}/trending",
                params={"apiKey": api_key, "limit": min(max_results, 25)},
                timeout=15,
            )
            if resp.status_code != 200:
                return {"source": "NewsMesh", "query": "trending", "articles": [], "error": f"HTTP {resp.status_code}"}

            data = resp.json()
            articles = []
            for item in data.get("articles", [])[:max_results]:
                articles.append({
                    "title": item.get("title", ""),
                    "description": (item.get("description") or "")[:250],
                    "url": item.get("link", ""),
                    "source": item.get("source", ""),
                    "published": (item.get("published_date") or "")[:10],
                    "category": item.get("category", ""),
                    "topics": item.get("topics", [])[:5],
                    "people": item.get("people", [])[:3],
                })

            return {"source": "NewsMesh", "query": "trending", "articles": articles, "error": None}

        except Exception as e:
            return {"source": "NewsMesh", "query": "trending", "articles": [], "error": str(e)}

    return cached_call("newsmesh", "trending", _fetch, ttl=600)


def format_news_markdown(results: Dict) -> str:
    """Format news search results as readable markdown."""
    articles = results.get("articles", [])
    if results.get("error"):
        return f"**News error:** {results['error']}"

    if not articles:
        return f"No news found for: {results.get('query', '')}"

    lines = [f"**📰 News: {len(articles)} articles**\n"]

    for i, a in enumerate(articles, 1):
        lines.append(f"**{i}. {a['title']}**")
        meta = []
        if a.get("source"):
            meta.append(a["source"])
        if a.get("published"):
            meta.append(a["published"])
        if a.get("category"):
            meta.append(a["category"])
        if meta:
            lines.append(f"   {' · '.join(meta)}")
        if a.get("description"):
            lines.append(f"   {a['description']}")
        if a.get("topics"):
            lines.append(f"   Topics: {', '.join(a['topics'])}")
        if a.get("people"):
            lines.append(f"   People: {', '.join(a['people'])}")
        if a.get("url"):
            lines.append(f"   [{a['url']}]({a['url']})")
        lines.append("")

    return "\n".join(lines)
