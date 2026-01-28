"""
Tavily Search Tool for Mindrian
Web research capabilities for Larry and workshop bots
"""

import os
from tavily import TavilyClient
from typing import Optional, List, Dict

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# Startup diagnostic
if TAVILY_API_KEY:
    print(f"[TAVILY] API key loaded: {TAVILY_API_KEY[:8]}...{TAVILY_API_KEY[-4:]} ({len(TAVILY_API_KEY)} chars)")
else:
    print("[TAVILY] WARNING: TAVILY_API_KEY not found in environment!")


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
        print("[TAVILY] search_web called but API key is missing!")
        return {
            "error": "Tavily API key not configured. Set TAVILY_API_KEY in environment.",
            "results": []
        }

    try:
        print(f"[TAVILY] Searching: '{query[:80]}' (depth={search_depth}, max={max_results})")
        client = TavilyClient(api_key=TAVILY_API_KEY)

        response = client.search(
            query=query,
            search_depth=search_depth,
            max_results=max_results,
            include_domains=include_domains or [],
            exclude_domains=exclude_domains or []
        )

        result_count = len(response.get("results", []))
        print(f"[TAVILY] Got {result_count} results for: '{query[:50]}'")

        return {
            "query": query,
            "results": response.get("results", []),
            "answer": response.get("answer", ""),
        }

    except Exception as e:
        print(f"[TAVILY] ERROR for '{query[:50]}': {type(e).__name__}: {e}")
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


# === New Agent-Specific Research Functions ===

def research_six_hats(topic: str, hat_color: str) -> Dict:
    """
    Research for BONO Master - Six Thinking Hats perspective.

    Args:
        topic: The topic being analyzed
        hat_color: white, red, black, yellow, green, or blue

    Returns:
        Dictionary with hat-specific research
    """
    hat_queries = {
        "white": f"{topic} statistics data facts evidence numbers research",
        "red": f"{topic} user sentiment emotions feelings reactions opinions",
        "black": f"{topic} risks problems failures challenges criticism concerns",
        "yellow": f"{topic} benefits advantages opportunities success potential",
        "green": f"{topic} innovations alternatives creative solutions new approaches",
        "blue": f"{topic} strategic framework analysis methodology synthesis",
    }

    query = hat_queries.get(hat_color.lower(), f"{topic} analysis")

    results = search_web(
        query=query,
        search_depth="advanced",
        max_results=5
    )

    return {
        "topic": topic,
        "hat": hat_color,
        "findings": results.get("results", []),
        "summary": results.get("answer", ""),
    }


def research_unknowns(topic: str, quadrant: str) -> Dict:
    """
    Research for Known-Unknowns - Rumsfeld Matrix quadrant.

    Args:
        topic: The topic being analyzed
        quadrant: known_knowns, known_unknowns, or unknown_unknowns

    Returns:
        Dictionary with quadrant-specific research
    """
    quadrant_queries = {
        "known_knowns": f"{topic} established facts proven statistics verified data",
        "known_unknowns": f"{topic} unanswered questions uncertainties unknowns research gaps",
        "unknown_unknowns": f"{topic} unexpected disruptions black swan surprises blind spots emerging risks",
    }

    query = quadrant_queries.get(quadrant.lower(), f"{topic} analysis")

    results = search_web(
        query=query,
        search_depth="advanced",
        max_results=5
    )

    return {
        "topic": topic,
        "quadrant": quadrant,
        "findings": results.get("results", []),
        "summary": results.get("answer", ""),
    }


def research_domain_exhaustive(topic: str, domains: List[str] = None) -> Dict:
    """
    Exhaustive multi-domain research for Domain Explorer.

    Args:
        topic: The topic to research exhaustively
        domains: Optional list of specific domains to focus on

    Returns:
        Dictionary with comprehensive multi-domain findings
    """
    if domains is None:
        domains = ["technical", "market", "regulatory", "academic", "competitor"]

    all_findings = {}

    domain_queries = {
        "technical": f"{topic} technology implementation technical challenges solutions",
        "market": f"{topic} market size growth trends TAM SAM investment funding",
        "regulatory": f"{topic} regulation policy compliance legal requirements barriers",
        "academic": f"{topic} research paper study findings scientific evidence",
        "competitor": f"{topic} competitors landscape alternatives comparison market share",
        "failures": f"{topic} failures post-mortem what went wrong lessons learned",
        "success": f"{topic} success case study best practices winning strategies",
        "emerging": f"{topic} emerging trends future forecast predictions 2025 2026",
    }

    for domain in domains:
        query = domain_queries.get(domain, f"{topic} {domain} analysis")
        results = search_web(
            query=query,
            search_depth="advanced",
            max_results=4
        )
        all_findings[domain] = {
            "results": results.get("results", []),
            "summary": results.get("answer", ""),
        }

    return {
        "topic": topic,
        "domains_researched": domains,
        "findings": all_findings,
        "total_sources": sum(len(f["results"]) for f in all_findings.values()),
    }


def research_investment_question(company_or_opportunity: str, question_number: int) -> Dict:
    """
    Research for PWS Investment - Ten Questions validation.

    Args:
        company_or_opportunity: The startup or opportunity being evaluated
        question_number: 1-10 corresponding to the Ten Questions

    Returns:
        Dictionary with question-specific validation research
    """
    question_queries = {
        1: f"{company_or_opportunity} problem market need pain point evidence",
        2: f"{company_or_opportunity} user impact customer testimonials reviews",
        3: f"{company_or_opportunity} pricing revenue willingness to pay customers",
        4: f"{company_or_opportunity} technology differentiation patents innovation",
        5: f"{company_or_opportunity} traction growth metrics users revenue MRR",
        6: f"{company_or_opportunity} roadmap vision strategy future plans",
        7: f"{company_or_opportunity} team resources funding requirements",
        8: f"{company_or_opportunity} founders team background experience track record",
        9: f"{company_or_opportunity} funding raised valuation investors capital",
        10: f"{company_or_opportunity} valuation multiples comparable deals M&A",
    }

    question_names = {
        1: "Is the problem real?",
        2: "How is it impacting users?",
        3: "Will they pay?",
        4: "Solving it differently?",
        5: "Any momentum?",
        6: "Current vs future state clear?",
        7: "What's needed to implement?",
        8: "Why this team?",
        9: "How much to get it done?",
        10: "Sound valuation?",
    }

    query = question_queries.get(question_number, f"{company_or_opportunity} analysis")

    results = search_web(
        query=query,
        search_depth="advanced",
        max_results=5
    )

    return {
        "company": company_or_opportunity,
        "question_number": question_number,
        "question": question_names.get(question_number, "Unknown"),
        "findings": results.get("results", []),
        "summary": results.get("answer", ""),
    }


# === Enhanced Tavily Methods for Matrix-Based Research ===

def get_search_context(
    query: str,
    search_depth: str = "advanced",
    max_results: int = 5,
    max_tokens: int = 4000
) -> str:
    """
    Get optimized search context for RAG applications.
    Uses Tavily's get_search_context() for precise, fact-based context.

    Args:
        query: Search query
        search_depth: "basic" or "advanced"
        max_results: Number of results to consider
        max_tokens: Max tokens in returned context

    Returns:
        Optimized context string for RAG
    """
    if not TAVILY_API_KEY:
        return "Error: Tavily API key not configured"

    try:
        client = TavilyClient(api_key=TAVILY_API_KEY)
        context = client.get_search_context(
            query=query,
            search_depth=search_depth,
            max_results=max_results,
            max_tokens=max_tokens
        )
        return context
    except Exception as e:
        return f"Error: {str(e)}"


def qna_search(query: str, search_depth: str = "advanced") -> Dict:
    """
    Get direct answer to a question using Tavily's QnA search.
    Perfect for specific questions that need concise answers.

    Args:
        query: Question to answer
        search_depth: "basic" or "advanced"

    Returns:
        Dictionary with answer and sources
    """
    if not TAVILY_API_KEY:
        return {"error": "Tavily API key not configured", "answer": "", "sources": []}

    try:
        client = TavilyClient(api_key=TAVILY_API_KEY)
        answer = client.qna_search(query=query, search_depth=search_depth)
        return {
            "query": query,
            "answer": answer,
            "sources": []  # QnA returns just the answer
        }
    except Exception as e:
        return {"error": str(e), "answer": "", "sources": []}


def batch_search(queries: List[Dict], max_concurrent: int = 5) -> List[Dict]:
    """
    Execute multiple searches efficiently.

    Args:
        queries: List of dicts with 'query', 'category', 'consolidation_group' keys
        max_concurrent: Max parallel requests (Tavily handles this internally)

    Returns:
        List of search results with metadata
    """
    if not TAVILY_API_KEY:
        return [{"error": "Tavily API key not configured"} for _ in queries]

    client = TavilyClient(api_key=TAVILY_API_KEY)
    results = []

    for q in queries:
        query_text = q.get("query", "")
        category = q.get("category", "general")
        group = q.get("consolidation_group", "default")

        try:
            response = client.search(
                query=query_text,
                search_depth="advanced",
                max_results=5,
                include_answer=True
            )

            results.append({
                "query": query_text,
                "category": category,
                "consolidation_group": group,
                "results": response.get("results", []),
                "answer": response.get("answer", ""),
                "source_count": len(response.get("results", []))
            })
        except Exception as e:
            results.append({
                "query": query_text,
                "category": category,
                "consolidation_group": group,
                "error": str(e),
                "results": [],
                "answer": ""
            })

    return results


def research_matrix_execution(
    why_queries: List[str],
    what_if_queries: List[str],
    how_queries: List[str],
    validation_queries: List[str],
    challenge_queries: List[str]
) -> Dict:
    """
    Execute a full research matrix with categorized queries.
    Optimized for Beautiful Questions + Sequential Thinking workflow.

    Args:
        why_queries: Queries for WHY questions (root causes)
        what_if_queries: Queries for WHAT IF questions (possibilities)
        how_queries: Queries for HOW questions (implementation)
        validation_queries: Camera Test queries (observable evidence)
        challenge_queries: Devil's Advocate queries (counter-evidence)

    Returns:
        Comprehensive research results organized by category
    """
    all_results = {
        "why": {"queries": [], "results": [], "context": "", "source_count": 0},
        "what_if": {"queries": [], "results": [], "context": "", "source_count": 0},
        "how": {"queries": [], "results": [], "context": "", "source_count": 0},
        "validation": {"queries": [], "results": [], "context": "", "source_count": 0},
        "challenge": {"queries": [], "results": [], "context": "", "source_count": 0},
    }

    def execute_category(queries: List[str], category: str):
        category_results = []
        for query in queries:
            # Use get_search_context for RAG-optimized results
            context = get_search_context(query, max_results=4, max_tokens=2000)

            # Also get structured results
            search_result = search_web(query, search_depth="advanced", max_results=4)

            category_results.append({
                "query": query,
                "context": context,
                "results": search_result.get("results", []),
                "answer": search_result.get("answer", "")
            })

        return category_results

    # Execute each category
    if why_queries:
        results = execute_category(why_queries, "why")
        all_results["why"]["queries"] = why_queries
        all_results["why"]["results"] = results
        all_results["why"]["source_count"] = sum(len(r.get("results", [])) for r in results)
        all_results["why"]["context"] = "\n\n".join([r.get("context", "") for r in results if r.get("context")])

    if what_if_queries:
        results = execute_category(what_if_queries, "what_if")
        all_results["what_if"]["queries"] = what_if_queries
        all_results["what_if"]["results"] = results
        all_results["what_if"]["source_count"] = sum(len(r.get("results", [])) for r in results)
        all_results["what_if"]["context"] = "\n\n".join([r.get("context", "") for r in results if r.get("context")])

    if how_queries:
        results = execute_category(how_queries, "how")
        all_results["how"]["queries"] = how_queries
        all_results["how"]["results"] = results
        all_results["how"]["source_count"] = sum(len(r.get("results", [])) for r in results)
        all_results["how"]["context"] = "\n\n".join([r.get("context", "") for r in results if r.get("context")])

    if validation_queries:
        results = execute_category(validation_queries, "validation")
        all_results["validation"]["queries"] = validation_queries
        all_results["validation"]["results"] = results
        all_results["validation"]["source_count"] = sum(len(r.get("results", [])) for r in results)
        all_results["validation"]["context"] = "\n\n".join([r.get("context", "") for r in results if r.get("context")])

    if challenge_queries:
        results = execute_category(challenge_queries, "challenge")
        all_results["challenge"]["queries"] = challenge_queries
        all_results["challenge"]["results"] = results
        all_results["challenge"]["source_count"] = sum(len(r.get("results", [])) for r in results)
        all_results["challenge"]["context"] = "\n\n".join([r.get("context", "") for r in results if r.get("context")])

    # Calculate totals
    total_sources = sum(cat["source_count"] for cat in all_results.values())
    total_queries = sum(len(cat["queries"]) for cat in all_results.values())

    return {
        "categories": all_results,
        "total_queries_executed": total_queries,
        "total_sources_found": total_sources,
        "summary": {
            "why_sources": all_results["why"]["source_count"],
            "what_if_sources": all_results["what_if"]["source_count"],
            "how_sources": all_results["how"]["source_count"],
            "validation_sources": all_results["validation"]["source_count"],
            "challenge_sources": all_results["challenge"]["source_count"],
        }
    }
