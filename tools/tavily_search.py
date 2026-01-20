"""
Tavily Search Tool for Mindrian
Web research capabilities for Larry and workshop bots
"""

import os
from tavily import TavilyClient
from typing import Optional, List, Dict

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")


def search_web(
    query: str,
    search_depth: str = "basic",
    max_results: int = 5,
    include_domains: Optional[List[str]] = None,
    exclude_domains: Optional[List[str]] = None
) -> Dict:
    """
    Search the web using Tavily API.

    Args:
        query: Search query
        search_depth: "basic" or "advanced"
        max_results: Number of results to return
        include_domains: Only search these domains
        exclude_domains: Exclude these domains

    Returns:
        Dictionary with search results
    """
    if not TAVILY_API_KEY:
        return {
            "error": "Tavily API key not configured",
            "results": []
        }

    try:
        client = TavilyClient(api_key=TAVILY_API_KEY)

        response = client.search(
            query=query,
            search_depth=search_depth,
            max_results=max_results,
            include_domains=include_domains or [],
            exclude_domains=exclude_domains or []
        )

        return {
            "query": query,
            "results": response.get("results", []),
            "answer": response.get("answer", ""),
        }

    except Exception as e:
        return {
            "error": str(e),
            "results": []
        }


def research_trend(trend_topic: str) -> Dict:
    """
    Research a trend for Trending to the Absurd workshop.

    Args:
        trend_topic: The trend to research

    Returns:
        Dictionary with research findings
    """
    # Search for recent news and data
    news_results = search_web(
        query=f"{trend_topic} trend statistics data 2024 2025",
        search_depth="advanced",
        max_results=5
    )

    # Search for expert analysis
    analysis_results = search_web(
        query=f"{trend_topic} analysis forecast future implications",
        search_depth="advanced",
        max_results=5
    )

    return {
        "trend": trend_topic,
        "news_and_data": news_results.get("results", []),
        "expert_analysis": analysis_results.get("results", []),
        "summary": news_results.get("answer", "") + "\n\n" + analysis_results.get("answer", "")
    }


def validate_assumption(assumption: str) -> Dict:
    """
    Research to validate or challenge an assumption (for Red Teaming).

    Args:
        assumption: The assumption to validate

    Returns:
        Dictionary with supporting and contradicting evidence
    """
    # Search for supporting evidence
    supporting = search_web(
        query=f"{assumption} evidence support data",
        search_depth="advanced",
        max_results=3
    )

    # Search for contradicting evidence
    contradicting = search_web(
        query=f"{assumption} challenges problems failures criticism",
        search_depth="advanced",
        max_results=3
    )

    return {
        "assumption": assumption,
        "supporting_evidence": supporting.get("results", []),
        "contradicting_evidence": contradicting.get("results", []),
    }
