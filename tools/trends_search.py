"""
Google Trends Search for Mindrian
==================================

Uses SerpAPI Google Trends engine for real-time trend data.
Requires SERPAPI_API_KEY environment variable.

pip install google-search-results
"""

import logging
import os
from typing import Dict, List, Optional

logger = logging.getLogger("trends_search")


def search_trends(
    query: str,
    data_type: str = "TIMESERIES",
    date: str = "today 12-m",
    geo: str = "",
) -> Dict:
    """
    Search Google Trends via SerpAPI.

    Args:
        query: Search term(s), comma-separated for comparisons (max 5).
        data_type: TIMESERIES | RELATED_QUERIES | RELATED_TOPICS | GEO_MAP
        date: Time range — 'now 1-H', 'now 4-H', 'now 1-d', 'now 7-d',
              'today 1-m', 'today 3-m', 'today 12-m', 'today 5-y', 'all'
        geo: Country code (e.g. 'US'). Empty = worldwide.

    Returns:
        {"query": str, "data_type": str, "data": ..., "error": str|None}
    """
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        return {"query": query, "data_type": data_type, "data": None, "error": "SERPAPI_API_KEY not set"}

    try:
        from serpapi import GoogleSearch

        params = {
            "engine": "google_trends",
            "q": query,
            "data_type": data_type,
            "date": date,
            "api_key": api_key,
        }
        if geo:
            params["geo"] = geo

        search = GoogleSearch(params)
        results = search.get_dict()

        if "error" in results:
            return {"query": query, "data_type": data_type, "data": None, "error": results["error"]}

        logger.info("Google Trends: '%s' (%s) → success", query[:40], data_type)
        return {"query": query, "data_type": data_type, "data": results, "error": None}

    except ImportError:
        logger.error("google-search-results package not installed. Run: pip install google-search-results")
        return {"query": query, "data_type": data_type, "data": None, "error": "google-search-results not installed"}
    except Exception as e:
        logger.error("Google Trends error: %s", e)
        return {"query": query, "data_type": data_type, "data": None, "error": str(e)}


def search_related_queries(query: str, geo: str = "") -> Dict:
    """Get rising and top related queries for a term."""
    return search_trends(query, data_type="RELATED_QUERIES", geo=geo)


def search_interest_over_time(query: str, date: str = "today 12-m", geo: str = "") -> Dict:
    """Get interest-over-time timeseries for a term."""
    return search_trends(query, data_type="TIMESERIES", date=date, geo=geo)


def format_trends_markdown(results: Dict) -> str:
    """Format Google Trends results as readable markdown."""
    if results.get("error"):
        return f"**Trends error:** {results['error']}"

    data = results.get("data", {})
    data_type = results.get("data_type", "TIMESERIES")
    query = results.get("query", "")
    lines = [f"**Google Trends: {query}**\n"]

    if data_type == "TIMESERIES":
        timeline = data.get("interest_over_time", {}).get("timeline_data", [])
        if not timeline:
            return f"No trend data found for: {query}"

        # Show summary: first, peak, latest
        values = []
        for point in timeline:
            for v in point.get("values", []):
                values.append((point.get("date", ""), v.get("extracted_value", 0)))

        if values:
            peak = max(values, key=lambda x: x[1])
            latest = values[-1]
            first = values[0]
            lines.append(f"**12-month trend summary:**")
            lines.append(f"- Start: {first[0]} — interest **{first[1]}**")
            lines.append(f"- Peak: {peak[0]} — interest **{peak[1]}**")
            lines.append(f"- Latest: {latest[0]} — interest **{latest[1]}**")

            # Direction
            if len(values) >= 4:
                recent_avg = sum(v[1] for v in values[-4:]) / 4
                early_avg = sum(v[1] for v in values[:4]) / 4
                if recent_avg > early_avg * 1.2:
                    lines.append(f"- 📈 **Rising trend** (recent avg {recent_avg:.0f} vs early {early_avg:.0f})")
                elif recent_avg < early_avg * 0.8:
                    lines.append(f"- 📉 **Declining trend** (recent avg {recent_avg:.0f} vs early {early_avg:.0f})")
                else:
                    lines.append(f"- ➡️ **Stable trend** (recent avg {recent_avg:.0f} vs early {early_avg:.0f})")

    elif data_type == "RELATED_QUERIES":
        related = data.get("related_queries", {})
        rising = related.get("rising", [])
        top = related.get("top", [])

        if rising:
            lines.append("**🚀 Rising queries:**")
            for item in rising[:5]:
                q = item.get("query", "")
                val = item.get("value", "")
                lines.append(f"- {q} ({val})")
            lines.append("")

        if top:
            lines.append("**🔝 Top related queries:**")
            for item in top[:5]:
                q = item.get("query", "")
                val = item.get("value", "")
                lines.append(f"- {q} ({val})")

        if not rising and not top:
            lines.append("No related queries found.")

    elif data_type == "RELATED_TOPICS":
        related = data.get("related_topics", {})
        rising = related.get("rising", [])
        top = related.get("top", [])

        if rising:
            lines.append("**🚀 Rising topics:**")
            for item in rising[:5]:
                topic = item.get("topic", {}).get("title", "Unknown")
                val = item.get("value", "")
                lines.append(f"- {topic} ({val})")

        if top:
            lines.append("**🔝 Top topics:**")
            for item in top[:5]:
                topic = item.get("topic", {}).get("title", "Unknown")
                val = item.get("value", "")
                lines.append(f"- {topic} ({val})")

    if len(lines) == 1:
        lines.append("No trend data available for this query.")

    return "\n".join(lines)
