"""
Google Patents Search for Mindrian
====================================

Uses SerpApi Google Patents endpoint if SERPAPI_KEY is set.
Falls back to google-patent-scraper or direct scraping.

pip install google-search-results  (for SerpApi)
pip install google-patent-scraper  (for fallback)
"""

import os
import logging
from typing import Dict, List, Optional

logger = logging.getLogger("patent_search")

SERPAPI_KEY = os.getenv("SERPAPI_KEY") or os.getenv("SERPAPI_API_KEY")


def search_patents(
    query: str,
    max_results: int = 5,
    country: Optional[str] = None,
    status: Optional[str] = None,
) -> Dict:
    """
    Search Google Patents for patents related to a query.

    Args:
        query: Search terms (semicolons separate multiple terms)
        max_results: Number of results (max 10 without pagination)
        country: ISO country code filter (e.g., "US", "DE")
        status: "GRANT" or "APPLICATION"

    Returns:
        {"query": str, "patents": [...], "count": int}
    """
    if SERPAPI_KEY:
        return _search_serpapi(query, max_results, country, status)
    else:
        return _search_scraper(query, max_results)


def _search_serpapi(
    query: str,
    max_results: int = 5,
    country: Optional[str] = None,
    status: Optional[str] = None,
) -> Dict:
    """Search using SerpApi Google Patents API."""
    try:
        from serpapi import GoogleSearch

        params = {
            "engine": "google_patents",
            "q": query,
            "api_key": SERPAPI_KEY,
            "num": min(max_results, 10),
        }
        if country:
            params["country"] = country
        if status:
            params["status"] = status

        search = GoogleSearch(params)
        results = search.get_dict()

        patents = []
        for item in results.get("organic_results", [])[:max_results]:
            patents.append({
                "title": item.get("title", ""),
                "patent_id": item.get("patent_id", ""),
                "inventor": item.get("inventor", ""),
                "assignee": item.get("assignee", ""),
                "publication_date": item.get("publication_date", ""),
                "priority_date": item.get("priority_date", ""),
                "snippet": item.get("snippet", "")[:300],
                "url": item.get("pdf", item.get("link", "")),
                "grant_date": item.get("grant_date", ""),
                "filing_date": item.get("filing_date", ""),
            })

        logger.info("SerpApi patent search: '%s' → %d patents", query[:60], len(patents))
        return {"query": query, "patents": patents, "count": len(patents), "source": "serpapi"}

    except ImportError:
        logger.warning("serpapi package not installed. Run: pip install google-search-results")
        return _search_scraper(query, max_results)
    except Exception as e:
        logger.error("SerpApi patent search error: %s", e)
        return {"query": query, "patents": [], "error": str(e), "source": "serpapi"}


def _search_scraper(query: str, max_results: int = 5) -> Dict:
    """Fallback: search using google-patent-scraper or Tavily."""
    # Try google-patent-scraper
    try:
        from google_patent_scraper import scraper_class

        scraper = scraper_class()
        # The scraper works with patent IDs, not queries.
        # For query-based search, fall through to Tavily.
        pass
    except ImportError:
        pass

    # Final fallback: use Tavily to search Google Patents site
    try:
        from tools.tavily_search import search_web

        results = search_web(
            query=f"site:patents.google.com {query}",
            search_depth="advanced",
            max_results=max_results,
        )

        patents = []
        for item in results.get("results", []):
            patents.append({
                "title": item.get("title", ""),
                "snippet": item.get("content", "")[:300],
                "url": item.get("url", ""),
                "patent_id": _extract_patent_id(item.get("url", "")),
                "inventor": "",
                "assignee": "",
                "publication_date": "",
            })

        logger.info("Tavily patent search (fallback): '%s' → %d patents", query[:60], len(patents))
        return {"query": query, "patents": patents, "count": len(patents), "source": "tavily_fallback"}

    except Exception as e:
        logger.error("Patent search fallback error: %s", e)
        return {"query": query, "patents": [], "error": str(e), "source": "fallback_failed"}


def _extract_patent_id(url: str) -> str:
    """Extract patent ID from a Google Patents URL."""
    # https://patents.google.com/patent/US12345678B2
    if "patents.google.com/patent/" in url:
        parts = url.split("patents.google.com/patent/")
        if len(parts) > 1:
            return parts[1].split("/")[0].split("?")[0]
    return ""


def search_innovation_landscape(
    technology: str,
    max_results: int = 8,
) -> Dict:
    """
    Search for patents in a technology area to map the innovation landscape.
    Useful for S-Curve analysis and TTA workshops.
    """
    results = search_patents(technology, max_results=max_results)

    # Add landscape-oriented metadata
    results["landscape_query"] = technology
    results["analysis_type"] = "innovation_landscape"

    return results


def search_prior_art(
    invention: str,
    max_results: int = 5,
) -> Dict:
    """
    Search for prior art related to an invention.
    Useful for Red Teaming ("has this been done before?").
    """
    results = search_patents(
        f"{invention} prior art",
        max_results=max_results,
    )
    results["analysis_type"] = "prior_art"
    return results


def format_patents_markdown(results: Dict) -> str:
    """Format patent search results as readable markdown."""
    patents = results.get("patents", [])
    if not patents:
        return f"No patents found for: {results.get('query', '')}"

    source = results.get("source", "unknown")
    lines = [f"**Google Patents: {len(patents)} results** (via {source})\n"]

    for i, p in enumerate(patents, 1):
        lines.append(f"**{i}. {p.get('title', 'Untitled')}**")
        if p.get("patent_id"):
            lines.append(f"   Patent: {p['patent_id']}")
        if p.get("assignee"):
            lines.append(f"   Assignee: {p['assignee']}")
        if p.get("inventor"):
            lines.append(f"   Inventor: {p['inventor']}")
        if p.get("publication_date"):
            lines.append(f"   Published: {p['publication_date']}")
        if p.get("snippet"):
            lines.append(f"   {p['snippet'][:200]}...")
        if p.get("url"):
            lines.append(f"   [{p['url']}]({p['url']})")
        lines.append("")

    return "\n".join(lines)
