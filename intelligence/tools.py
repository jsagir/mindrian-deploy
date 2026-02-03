"""
LangChain Tools for Mindrian Intelligence Layer
================================================
@tool wrapped functions for agent composition and reasoning.

Usage:
    from intelligence.tools import search_web_tavily, query_neo4j_concepts

    # Use directly
    result = search_web_tavily.invoke({"query": "AI in healthcare"})

    # Or compose into agent
    from langchain.agents import create_tool_calling_agent
    agent = create_tool_calling_agent(llm, [search_web_tavily, query_neo4j_concepts])
"""

import os
import json
from typing import Optional, List, Dict, Any
from langchain_core.tools import tool
from pydantic import BaseModel, Field

# =============================================================================
# PYDANTIC SCHEMAS FOR STRUCTURED INPUT
# =============================================================================

class WebSearchInput(BaseModel):
    """Input schema for web search."""
    query: str = Field(description="Search query")
    search_depth: str = Field(default="basic", description="'basic' for fast, 'advanced' for thorough")
    max_results: int = Field(default=5, description="Number of results (1-10)")


class ValidationInput(BaseModel):
    """Input schema for assumption validation."""
    assumption: str = Field(description="The assumption or claim to validate")


class Neo4jQueryInput(BaseModel):
    """Input schema for Neo4j queries."""
    topic: str = Field(description="Topic or concept to search for")
    limit: int = Field(default=5, description="Maximum results to return")


class ExtractionInput(BaseModel):
    """Input schema for structured extraction."""
    text: str = Field(description="Text to extract structured data from")


# =============================================================================
# RESEARCH TOOLS - Web & Specialized Search
# =============================================================================

@tool("search_web", args_schema=WebSearchInput)
def search_web_tavily(query: str, search_depth: str = "basic", max_results: int = 5) -> str:
    """
    Search the web for current information using Tavily.

    Use for:
    - Finding recent data and statistics
    - Market research and trends
    - Validating claims with evidence
    - Discovering expert opinions

    Returns formatted search results with titles, snippets, and URLs.
    """
    from tools.tavily_search import search_web as tavily_search

    result = tavily_search(
        query=query,
        search_depth=search_depth,
        max_results=max_results
    )

    if result.get("error"):
        return f"Search error: {result['error']}"

    # Format results for agent consumption
    formatted = []
    for r in result.get("results", []):
        formatted.append(f"**{r.get('title', 'Untitled')}**\n{r.get('content', '')[:300]}\nURL: {r.get('url', '')}")

    return "\n\n---\n\n".join(formatted) if formatted else "No results found."


@tool("search_arxiv")
def search_arxiv(query: str, max_results: int = 5) -> str:
    """
    Search ArXiv for academic papers and research.

    Use for:
    - Finding peer-reviewed research
    - Understanding theoretical foundations
    - Citing academic sources
    - Discovering cutting-edge research

    Best for: AI/ML, physics, mathematics, computer science topics.
    """
    from tools.tavily_search import search_web as tavily_search

    result = tavily_search(
        query=f"site:arxiv.org {query}",
        search_depth="advanced",
        max_results=max_results,
        include_domains=["arxiv.org"]
    )

    if result.get("error"):
        return f"ArXiv search error: {result['error']}"

    formatted = []
    for r in result.get("results", []):
        formatted.append(f"**{r.get('title', 'Untitled')}**\n{r.get('content', '')[:400]}\nURL: {r.get('url', '')}")

    return "\n\n---\n\n".join(formatted) if formatted else "No ArXiv papers found."


@tool("search_patents")
def search_patents(query: str, max_results: int = 5) -> str:
    """
    Search patent databases for innovations and prior art.

    Use for:
    - Competitive intelligence
    - Understanding technical solutions
    - Identifying IP landscape
    - Finding prior art for new ideas

    Searches Google Patents and USPTO.
    """
    from tools.tavily_search import search_web as tavily_search

    result = tavily_search(
        query=f"patent {query}",
        search_depth="advanced",
        max_results=max_results,
        include_domains=["patents.google.com", "uspto.gov"]
    )

    if result.get("error"):
        return f"Patent search error: {result['error']}"

    formatted = []
    for r in result.get("results", []):
        formatted.append(f"**{r.get('title', 'Untitled')}**\n{r.get('content', '')[:400]}\nURL: {r.get('url', '')}")

    return "\n\n---\n\n".join(formatted) if formatted else "No patents found."


@tool("search_trends")
def search_trends(query: str) -> str:
    """
    Search for trend data and market trajectory information.

    Use for:
    - Understanding market direction
    - Identifying growth patterns
    - Finding inflection points
    - Trending to the Absurd analysis

    Searches trend reports, market analysis, and forecasts.
    """
    from tools.tavily_search import search_web as tavily_search

    result = tavily_search(
        query=f"{query} trend forecast growth statistics 2024 2025",
        search_depth="advanced",
        max_results=5
    )

    if result.get("error"):
        return f"Trends search error: {result['error']}"

    formatted = []
    for r in result.get("results", []):
        formatted.append(f"**{r.get('title', 'Untitled')}**\n{r.get('content', '')[:400]}\nURL: {r.get('url', '')}")

    return "\n\n---\n\n".join(formatted) if formatted else "No trend data found."


@tool("search_govdata")
def search_govdata(query: str, max_results: int = 5) -> str:
    """
    Search US government data sources (BLS, FRED, Census, data.gov).

    Use for:
    - Official statistics and metrics
    - Economic indicators
    - Demographic data
    - Policy and regulatory information

    Most authoritative source for US economic and social data.
    """
    from tools.tavily_search import search_web as tavily_search

    result = tavily_search(
        query=f"{query} statistics data",
        search_depth="advanced",
        max_results=max_results,
        include_domains=["bls.gov", "census.gov", "fred.stlouisfed.org", "data.gov"]
    )

    if result.get("error"):
        return f"Gov data search error: {result['error']}"

    formatted = []
    for r in result.get("results", []):
        formatted.append(f"**{r.get('title', 'Untitled')}**\n{r.get('content', '')[:400]}\nURL: {r.get('url', '')}")

    return "\n\n---\n\n".join(formatted) if formatted else "No government data found."


@tool("search_datasets")
def search_datasets(query: str, max_results: int = 5) -> str:
    """
    Search for datasets on Kaggle, Socrata, and other data repositories.

    Use for:
    - Finding raw data for analysis
    - Identifying data sources for validation
    - Discovering benchmark datasets
    - Supporting quantitative research
    """
    from tools.tavily_search import search_web as tavily_search

    result = tavily_search(
        query=f"dataset {query}",
        search_depth="advanced",
        max_results=max_results,
        include_domains=["kaggle.com", "data.world", "socrata.com", "huggingface.co/datasets"]
    )

    if result.get("error"):
        return f"Dataset search error: {result['error']}"

    formatted = []
    for r in result.get("results", []):
        formatted.append(f"**{r.get('title', 'Untitled')}**\n{r.get('content', '')[:400]}\nURL: {r.get('url', '')}")

    return "\n\n---\n\n".join(formatted) if formatted else "No datasets found."


@tool("search_news")
def search_news(query: str, max_results: int = 5) -> str:
    """
    Search for recent news articles and current events.

    Use for:
    - Current market developments
    - Recent announcements and launches
    - Industry news and updates
    - Real-time information
    """
    from tools.tavily_search import search_web as tavily_search

    result = tavily_search(
        query=f"{query} news",
        search_depth="basic",
        max_results=max_results,
        include_domains=["reuters.com", "bloomberg.com", "techcrunch.com", "nytimes.com", "wsj.com"]
    )

    if result.get("error"):
        return f"News search error: {result['error']}"

    formatted = []
    for r in result.get("results", []):
        formatted.append(f"**{r.get('title', 'Untitled')}**\n{r.get('content', '')[:300]}\nURL: {r.get('url', '')}")

    return "\n\n---\n\n".join(formatted) if formatted else "No news found."


@tool("validate_assumption", args_schema=ValidationInput)
def validate_assumption(assumption: str) -> str:
    """
    Find both supporting AND contradicting evidence for an assumption.

    Use for:
    - Red Teaming and devil's advocate
    - Camera Test validation
    - Stress-testing hypotheses
    - Finding blind spots

    Returns evidence from both perspectives to enable balanced assessment.
    """
    from tools.tavily_search import search_web as tavily_search

    # Search for supporting evidence
    supporting = tavily_search(
        query=f"{assumption} evidence support data research",
        search_depth="advanced",
        max_results=3
    )

    # Search for contradicting evidence
    contradicting = tavily_search(
        query=f"{assumption} challenges problems criticism failures counterexample",
        search_depth="advanced",
        max_results=3
    )

    output = ["## Supporting Evidence"]
    for r in supporting.get("results", []):
        output.append(f"- **{r.get('title', '')}**: {r.get('content', '')[:200]}")

    output.append("\n## Contradicting Evidence")
    for r in contradicting.get("results", []):
        output.append(f"- **{r.get('title', '')}**: {r.get('content', '')[:200]}")

    return "\n".join(output)


@tool("research_trend")
def research_trend(trend_topic: str) -> str:
    """
    Comprehensive research on a trend for Trending to the Absurd.

    Gathers:
    - Current statistics and data
    - Expert analysis and forecasts
    - Growth trajectory
    - Potential disruptions

    Use when exploring a trend to extrapolate to absurd extremes.
    """
    from tools.tavily_search import research_trend as tavily_research_trend

    result = tavily_research_trend(trend_topic)

    output = [f"## Trend Research: {trend_topic}"]

    output.append("\n### News & Data")
    for r in result.get("news_and_data", [])[:3]:
        output.append(f"- **{r.get('title', '')}**: {r.get('content', '')[:200]}")

    output.append("\n### Expert Analysis")
    for r in result.get("expert_analysis", [])[:3]:
        output.append(f"- **{r.get('title', '')}**: {r.get('content', '')[:200]}")

    if result.get("summary"):
        output.append(f"\n### Summary\n{result['summary'][:500]}")

    return "\n".join(output)


# =============================================================================
# KNOWLEDGE TOOLS - Neo4j GraphRAG
# =============================================================================

@tool("query_concepts", args_schema=Neo4jQueryInput)
def query_neo4j_concepts(topic: str, limit: int = 5) -> str:
    """
    Query the PWS knowledge graph for concept relationships.

    Use for:
    - Understanding how concepts connect
    - Finding related methodologies
    - Discovering adjacent ideas
    - Building context for coaching

    Returns concept connections from the Neo4j knowledge graph.
    """
    try:
        from tools.graphrag_lite import get_concept_connections

        result = get_concept_connections(topic)

        if not result.get("connections"):
            return f"No connections found for '{topic}' in knowledge graph."

        output = [f"## {result.get('name', topic)} ({result.get('type', 'Concept')})"]

        if result.get("description"):
            output.append(f"\n{result['description'][:300]}")

        output.append("\n### Connections:")
        for conn in result.get("connections", [])[:limit]:
            output.append(f"- **{conn.get('name', '')}** ({conn.get('type', '')}) via {conn.get('relation', '')}")

        return "\n".join(output)

    except Exception as e:
        return f"Knowledge graph query error: {str(e)}"


@tool("query_frameworks", args_schema=Neo4jQueryInput)
def query_neo4j_frameworks(topic: str, limit: int = 3) -> str:
    """
    Find PWS frameworks relevant to a topic.

    Use for:
    - Recommending methodologies
    - Finding applicable tools
    - Grounding advice in PWS methodology
    - Workshop guidance

    Returns frameworks like JTBD, TTA, S-Curve, etc. with hints.
    """
    try:
        from tools.graphrag_lite import get_related_frameworks

        frameworks = get_related_frameworks(topic, limit=limit)

        if not frameworks:
            return f"No frameworks found for '{topic}'."

        output = [f"## Relevant Frameworks for: {topic}"]
        for fw in frameworks:
            output.append(f"\n### {fw.get('name', 'Unknown')}")
            output.append(f"Type: {fw.get('type', 'Framework')}")
            if fw.get("hint"):
                output.append(f"Hint: {fw['hint']}")

        return "\n".join(output)

    except Exception as e:
        return f"Framework query error: {str(e)}"


@tool("query_problem_context", args_schema=Neo4jQueryInput)
def query_neo4j_problems(topic: str, limit: int = 3) -> str:
    """
    Get problem classification and recommended approaches from knowledge graph.

    Use for:
    - Understanding problem types (simple, complicated, complex, wicked)
    - Finding applicable solution approaches
    - Routing to appropriate methodology
    - Cynefin-aware guidance

    Returns problem type classification with suggested approaches.
    """
    try:
        from tools.graphrag_lite import get_problem_context

        context = get_problem_context(topic)

        if not context.get("problem_type"):
            return f"Could not classify problem type for '{topic}'."

        output = [f"## Problem Analysis: {topic}"]
        output.append(f"\n**Problem Type:** {context.get('problem_type', 'Unknown')}")

        if context.get("description"):
            output.append(f"\n**Description:** {context['description'][:200]}")

        if context.get("approaches"):
            output.append("\n**Recommended Approaches:**")
            for approach in context.get("approaches", [])[:limit]:
                output.append(f"- {approach}")

        return "\n".join(output)

    except Exception as e:
        return f"Problem context error: {str(e)}"


# =============================================================================
# EXTRACTION TOOLS - LangExtract
# =============================================================================

@tool("extract_instant", args_schema=ExtractionInput)
def extract_instant(text: str) -> str:
    """
    Fast regex-based extraction of PWS signals (<5ms).

    Extracts:
    - Statistics (percentages, money, numbers)
    - Assumptions (explicit and implicit)
    - Problems and solutions mentioned
    - Questions raised
    - Certainty/uncertainty markers

    Use for quick analysis without API calls.
    """
    try:
        from tools.langextract import instant_extract, format_instant_extraction

        signals = instant_extract(text)
        return format_instant_extraction(signals)

    except Exception as e:
        return f"Extraction error: {str(e)}"


@tool("extract_deep", args_schema=ExtractionInput)
def extract_deep(text: str) -> str:
    """
    Deep LLM-based extraction for comprehensive PWS analysis.

    Extracts:
    - Core problem statement
    - Sub-problems and aspects
    - Stated and hidden assumptions
    - Key facts with confidence levels
    - Statistics with sources
    - Open questions
    - PWS quality scores (problem clarity, data grounding, assumption awareness)

    Use for thorough analysis (takes longer, uses API).
    Note: This is async - returns cached result or triggers background extraction.
    """
    try:
        from tools.langextract import instant_extract, get_cached_extraction

        # Check cache first
        cached = get_cached_extraction(text, "deep")
        if cached:
            from tools.langextract import format_deep_extraction
            return format_deep_extraction(cached)

        # Fall back to instant if not cached
        signals = instant_extract(text)
        return f"Deep extraction not cached. Instant analysis:\n\n{format_instant_extraction(signals)}\n\n(Use background_extract_pws for full analysis)"

    except Exception as e:
        return f"Deep extraction error: {str(e)}"


# =============================================================================
# TOOL COLLECTIONS FOR AGENT COMPOSITION
# =============================================================================

ALL_RESEARCH_TOOLS = [
    search_web_tavily,
    search_arxiv,
    search_patents,
    search_trends,
    search_govdata,
    search_datasets,
    search_news,
    validate_assumption,
    research_trend,
]

ALL_KNOWLEDGE_TOOLS = [
    query_neo4j_concepts,
    query_neo4j_frameworks,
    query_neo4j_problems,
]

ALL_EXTRACTION_TOOLS = [
    extract_instant,
    extract_deep,
]

ALL_TOOLS = ALL_RESEARCH_TOOLS + ALL_KNOWLEDGE_TOOLS + ALL_EXTRACTION_TOOLS
