"""
ArXiv Academic Search for Mindrian
===================================

Free API — no key required.
Uses the arxiv.py library for structured search over 2M+ papers.

pip install arxiv
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger("arxiv_search")


def search_papers(
    query: str,
    max_results: int = 5,
    sort_by: str = "relevance",
) -> Dict:
    """
    Search ArXiv for academic papers.

    Args:
        query: Search query (supports ArXiv query syntax)
        max_results: Number of papers to return (1-20)
        sort_by: "relevance" or "submitted" (latest first)

    Returns:
        {"query": str, "papers": [...], "count": int}
    """
    try:
        import arxiv

        sort_criterion = (
            arxiv.SortCriterion.Relevance
            if sort_by == "relevance"
            else arxiv.SortCriterion.SubmittedDate
        )

        client = arxiv.Client()
        search = arxiv.Search(
            query=query,
            max_results=min(max_results, 20),
            sort_by=sort_criterion,
        )

        papers = []
        for result in client.results(search):
            papers.append({
                "title": result.title,
                "authors": [a.name for a in result.authors[:5]],
                "summary": result.summary[:400],
                "published": result.published.strftime("%Y-%m-%d") if result.published else None,
                "url": result.entry_id,
                "pdf_url": result.pdf_url,
                "categories": result.categories[:3],
            })

        logger.info("ArXiv search: '%s' → %d papers", query[:60], len(papers))
        return {"query": query, "papers": papers, "count": len(papers)}

    except ImportError:
        logger.error("arxiv package not installed. Run: pip install arxiv")
        return {"query": query, "papers": [], "error": "arxiv package not installed"}
    except Exception as e:
        logger.error("ArXiv search error: %s", e)
        return {"query": query, "papers": [], "error": str(e)}


def search_by_topic(
    topic: str,
    max_results: int = 5,
) -> Dict:
    """
    Search ArXiv using title + abstract matching.
    Better for broad topic searches.
    """
    # ArXiv query syntax: ti=title, abs=abstract
    query = f'ti:"{topic}" OR abs:"{topic}"'
    return search_papers(query, max_results=max_results, sort_by="relevance")


def search_recent(
    topic: str,
    max_results: int = 5,
) -> Dict:
    """Search for most recent papers on a topic."""
    return search_papers(topic, max_results=max_results, sort_by="submitted")


def search_for_validation(
    claim: str,
    max_results: int = 5,
) -> Dict:
    """
    Search ArXiv for papers that could validate or challenge a claim.
    Useful for Red Teaming and Ackoff (DIKW grounding).
    """
    results = search_papers(claim, max_results=max_results)

    # Add validation-oriented summaries
    for paper in results.get("papers", []):
        paper["relevance_to_claim"] = claim[:100]

    return results


def format_papers_markdown(results: Dict) -> str:
    """Format search results as readable markdown."""
    papers = results.get("papers", [])
    if not papers:
        return f"No papers found for: {results.get('query', '')}"

    lines = [f"**ArXiv: {len(papers)} papers found**\n"]
    for i, p in enumerate(papers, 1):
        authors = ", ".join(p["authors"][:3])
        if len(p["authors"]) > 3:
            authors += f" et al."
        lines.append(f"**{i}. {p['title']}**")
        lines.append(f"   {authors} ({p.get('published', 'n/d')})")
        lines.append(f"   {p['summary'][:200]}...")
        lines.append(f"   [{p['url']}]({p['url']})")
        lines.append("")

    return "\n".join(lines)
