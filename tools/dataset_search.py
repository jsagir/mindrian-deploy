"""
Unified Dataset Search for Mindrian
=====================================

Searches two complementary sources:
  - Kaggle: curated ML/research datasets (CSV, JSON, SQLite)
  - Socrata: 80K+ government open datasets (cities, states, federal)

Kaggle auth: KAGGLE_USERNAME + KAGGLE_KEY env vars
Socrata: no auth required (app token optional via SOCRATA_APP_TOKEN)
"""

import logging
import os
from typing import Dict, List, Optional

import requests

from tools.research_cache import cached_call

logger = logging.getLogger("dataset_search")


# ---------------------------------------------------------------------------
# Kaggle
# ---------------------------------------------------------------------------

def search_kaggle(query: str, max_results: int = 5) -> Dict:
    """
    Search Kaggle datasets by keyword via REST API.

    Requires KAGGLE_USERNAME and KAGGLE_KEY environment variables.
    """
    username = os.getenv("KAGGLE_USERNAME")
    key = os.getenv("KAGGLE_KEY")

    if not username or not key:
        return {"source": "Kaggle", "query": query, "datasets": [], "error": "KAGGLE_USERNAME/KAGGLE_KEY not set"}

    def _fetch():
        try:
            resp = requests.get(
                "https://www.kaggle.com/api/v1/datasets/list",
                params={
                    "search": query,
                    "sortBy": "votes",
                    "filetype": "csv",
                    "page": 1,
                },
                auth=(username, key),
                timeout=15,
            )
            if resp.status_code != 200:
                return {"source": "Kaggle", "query": query, "datasets": [], "error": f"HTTP {resp.status_code}"}

            raw = resp.json()
            datasets = []
            for ds in raw[:max_results]:
                datasets.append({
                    "title": ds.get("title", ""),
                    "ref": ds.get("ref", ""),
                    "url": f"https://www.kaggle.com/datasets/{ds.get('ref', '')}",
                    "size": _human_size(ds.get("totalBytes", 0)),
                    "votes": ds.get("totalVotes", 0),
                    "downloads": ds.get("totalDownloads", 0),
                    "description": (ds.get("subtitle") or "")[:200],
                })

            return {"source": "Kaggle", "query": query, "datasets": datasets, "error": None}

        except Exception as e:
            logger.error("Kaggle search error: %s", e)
            return {"source": "Kaggle", "query": query, "datasets": [], "error": str(e)}

    return cached_call("kaggle", query, _fetch, ttl=600)


# ---------------------------------------------------------------------------
# Socrata (Open Data Network / Discovery API)
# ---------------------------------------------------------------------------

def search_socrata(query: str, max_results: int = 5) -> Dict:
    """
    Search Socrata open data catalog via Discovery API.

    No auth required. Optional SOCRATA_APP_TOKEN for higher rate limits.
    """
    def _fetch():
        try:
            params = {
                "q": query,
                "limit": max_results,
                "only": "datasets",
            }
            token = os.getenv("SOCRATA_APP_TOKEN")
            headers = {}
            if token:
                headers["X-App-Token"] = token

            resp = requests.get(
                "https://api.us.socrata.com/api/catalog/v1",
                params=params,
                headers=headers,
                timeout=15,
            )
            if resp.status_code != 200:
                return {"source": "Socrata", "query": query, "datasets": [], "error": f"HTTP {resp.status_code}"}

            raw = resp.json()
            results = raw.get("results", [])

            datasets = []
            for item in results[:max_results]:
                resource = item.get("resource", {})
                link = item.get("link", "")
                metadata = item.get("metadata", {})
                domain = metadata.get("domain", "")

                datasets.append({
                    "title": resource.get("name", ""),
                    "description": (resource.get("description") or "")[:200],
                    "url": link,
                    "domain": domain,
                    "type": resource.get("type", "dataset"),
                    "updated": resource.get("updatedAt", "")[:10],
                    "columns": resource.get("columns_name", [])[:8],
                    "row_count": resource.get("page_views", {}).get("page_views_total", 0),
                })

            return {"source": "Socrata", "query": query, "datasets": datasets, "error": None}

        except Exception as e:
            logger.error("Socrata search error: %s", e)
            return {"source": "Socrata", "query": query, "datasets": [], "error": str(e)}

    return cached_call("socrata", query, _fetch, ttl=600)


# ---------------------------------------------------------------------------
# Unified search + formatter
# ---------------------------------------------------------------------------

def search_datasets(query: str, sources: Optional[List[str]] = None) -> Dict:
    """
    Search across Kaggle and Socrata for datasets.

    Args:
        query: Search terms
        sources: Optional list of sources ('kaggle', 'socrata'). Default: both.
    """
    if sources is None:
        sources = ["kaggle", "socrata"]

    results = {}
    for src in sources:
        if src == "kaggle":
            results["kaggle"] = search_kaggle(query)
        elif src == "socrata":
            results["socrata"] = search_socrata(query)

    return {"query": query, "sources": sources, "results": results}


def format_datasets_markdown(results: Dict) -> str:
    """Format unified dataset search results as readable markdown."""
    parts = [f"**📊 Dataset Search: {results.get('query', '')}**\n"]

    for source_key, data in results.get("results", {}).items():
        if data.get("error"):
            parts.append(f"**{data['source']}:** {data['error']}\n")
            continue

        datasets = data.get("datasets", [])
        if not datasets:
            parts.append(f"**{data['source']}:** No datasets found.\n")
            continue

        source_label = data["source"]
        parts.append(f"### {source_label} ({len(datasets)} results)\n")

        for i, ds in enumerate(datasets, 1):
            title = ds.get("title", "Untitled")
            url = ds.get("url", "")
            desc = ds.get("description", "")

            parts.append(f"**{i}. [{title}]({url})**")

            details = []
            if ds.get("size"):
                details.append(ds["size"])
            if ds.get("votes"):
                details.append(f"⭐ {ds['votes']}")
            if ds.get("downloads"):
                details.append(f"⬇️ {ds['downloads']:,}")
            if ds.get("domain"):
                details.append(f"📍 {ds['domain']}")
            if ds.get("updated"):
                details.append(f"Updated: {ds['updated']}")

            if details:
                parts.append(f"   {' · '.join(details)}")
            if desc:
                parts.append(f"   {desc}")

            # Show column names for Socrata datasets
            cols = ds.get("columns", [])
            if cols:
                parts.append(f"   Columns: {', '.join(cols[:6])}{'...' if len(cols) > 6 else ''}")

            parts.append("")

    if len(parts) <= 1:
        parts.append("No datasets found for this query.")

    return "\n".join(parts)


def _human_size(nbytes: int) -> str:
    """Convert bytes to human-readable size."""
    if nbytes == 0:
        return "0 B"
    for unit in ["B", "KB", "MB", "GB"]:
        if nbytes < 1024:
            return f"{nbytes:.1f} {unit}"
        nbytes /= 1024
    return f"{nbytes:.1f} TB"
