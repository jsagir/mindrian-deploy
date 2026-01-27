"""
Tool Dispatcher — Maps Neo4j MCPTool nodes to actual callable Python functions.

The Neo4j graph contains MCPTool nodes with SUPPORTS/ORCHESTRATES_MCP relationships
that describe *what each tool is good at*. This module bridges graph intelligence
to actual execution by mapping tool names to Python callables.

Architecture:
    Neo4j MCPTool node → TOOL_REGISTRY → Python function → Result

Available tools in Mindrian runtime:
    - Neo4j (graphrag_lite) — framework discovery, concept lookup, community context
    - Tavily (tavily_search) — web search, trend research, assumption validation
    - Gemini (google.genai) — LLM reasoning, synthesis

NOT available (graph has nodes, but no runtime):
    - ArXiv MCP Server — no API key / client configured
    - Octagon Deep Research — no API key / client configured
    - Google Patents MCP — no API key / client configured
    - Sequential Thinking MCP — no server running
    - Notion — no server running
    - n8n-mcp — no runtime integration
    - pinecone — available via MCP but not wired to dispatcher yet
"""

import logging
import time
from typing import Dict, List, Optional, Any, Callable

logger = logging.getLogger("tool_dispatcher")


# ── Tool Registry ────────────────────────────────────────────────────────────
# Maps Neo4j MCPTool.name variants → (callable, category, description)
# Lazy imports inside callables to avoid import errors when tools unavailable.

def _neo4j_framework_lookup(query: str, **kwargs) -> Dict:
    """Query Neo4j for frameworks related to the query."""
    from tools.graphrag_lite import get_related_frameworks
    frameworks = get_related_frameworks(query, limit=kwargs.get("limit", 5))
    return {"tool": "neo4j", "action": "framework_lookup", "results": frameworks}


def _neo4j_concept_lookup(query: str, **kwargs) -> Dict:
    """Query Neo4j for concept connections."""
    from tools.graphrag_lite import get_concept_connections
    connections = get_concept_connections(query)
    return {"tool": "neo4j", "action": "concept_lookup", "results": connections}


def _neo4j_problem_context(query: str, **kwargs) -> Dict:
    """Query Neo4j for problem type classification."""
    from tools.graphrag_lite import get_problem_context
    context = get_problem_context(query)
    return {"tool": "neo4j", "action": "problem_context", "results": context}


def _neo4j_lazy_concepts(query: str, **kwargs) -> Dict:
    """Query Neo4j LazyGraphRAG for concept co-occurrence."""
    from tools.graphrag_lite import lazy_concept_lookup, lazy_community_context
    concepts = lazy_concept_lookup(query, limit=kwargs.get("limit", 5))
    neighbors = {}
    if concepts:
        neighbors = lazy_community_context(concepts[0]["name"], limit=6)
    return {"tool": "neo4j", "action": "lazy_concepts", "concepts": concepts, "neighbors": neighbors}


def _neo4j_cypher(query: str, **kwargs) -> Dict:
    """Execute raw Cypher query against Neo4j."""
    from tools.graphrag_lite import _get_neo4j
    driver = _get_neo4j()
    if not driver:
        return {"tool": "neo4j", "action": "cypher", "error": "no_driver"}
    try:
        cypher = kwargs.get("cypher", query)
        params = kwargs.get("params", {})
        with driver.session() as session:
            result = session.run(cypher, **params)
            records = [dict(r) for r in result]
        return {"tool": "neo4j", "action": "cypher", "records": records}
    except Exception as e:
        return {"tool": "neo4j", "action": "cypher", "error": str(e)}


def _tavily_search(query: str, **kwargs) -> Dict:
    """Web search via Tavily API."""
    from tools.tavily_search import search_web
    return search_web(
        query=query,
        search_depth=kwargs.get("search_depth", "advanced"),
        max_results=kwargs.get("max_results", 5),
    )


def _tavily_context(query: str, **kwargs) -> Dict:
    """RAG-optimized search context via Tavily."""
    from tools.tavily_search import get_search_context
    context = get_search_context(query, max_results=kwargs.get("max_results", 5))
    return {"tool": "tavily", "action": "context", "context": context}


def _tavily_qna(query: str, **kwargs) -> Dict:
    """Direct Q&A via Tavily."""
    from tools.tavily_search import qna_search
    return qna_search(query)


def _tavily_trend_research(query: str, **kwargs) -> Dict:
    """Trend research for TTA workshop."""
    from tools.tavily_search import research_trend
    return research_trend(query)


def _tavily_validate_assumption(query: str, **kwargs) -> Dict:
    """Assumption validation for Red Teaming."""
    from tools.tavily_search import validate_assumption
    return validate_assumption(query)


def _tavily_batch(query: str, **kwargs) -> Dict:
    """Batch search across multiple queries."""
    from tools.tavily_search import batch_search
    queries = kwargs.get("queries", [{"query": query, "category": "general"}])
    return {"tool": "tavily", "action": "batch", "results": batch_search(queries)}


def _not_available(query: str, **kwargs) -> Dict:
    """Placeholder for tools that exist in the graph but have no runtime."""
    tool_name = kwargs.get("_tool_name", "unknown")
    return {
        "tool": tool_name,
        "action": "not_available",
        "error": f"Tool '{tool_name}' exists in the graph but has no runtime in Mindrian",
        "fallback": "Use tavily_search or neo4j for similar capability",
    }


# ── Registry: Neo4j MCPTool.name → (function, category) ─────────────────────

TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {
    # Neo4j tools (all map to graphrag_lite functions)
    "Neo4j MCP":            {"fn": _neo4j_framework_lookup, "category": "neo4j", "available": True},
    "neo4j-mcp":            {"fn": _neo4j_cypher,           "category": "neo4j", "available": True},
    "Neo4j Graph Analysis":  {"fn": _neo4j_lazy_concepts,   "category": "neo4j", "available": True},

    # Tavily tools (all map to tavily_search functions)
    "Tavily MCP":            {"fn": _tavily_search,    "category": "tavily", "available": True},
    "tavily-mcp":            {"fn": _tavily_search,    "category": "tavily", "available": True},
    "Tavily Search":         {"fn": _tavily_search,    "category": "tavily", "available": True},
    "Tavily Web Research":   {"fn": _tavily_search,    "category": "tavily", "available": True},
    "Tavily Advanced Research Scanner": {"fn": _tavily_context, "category": "tavily", "available": True},

    # Web search (maps to Tavily as well)
    "Web Search":            {"fn": _tavily_search,    "category": "web",    "available": True},
    "Web Search for Unknown Unknowns": {"fn": _tavily_search, "category": "web", "available": True},

    # NOT AVAILABLE — graph nodes exist but no runtime
    "ArXiv MCP Server":      {"fn": _not_available, "category": "arxiv",   "available": False},
    "ArXiv Research":        {"fn": _not_available, "category": "arxiv",   "available": False},
    "ArXiv Academic Search":  {"fn": _not_available, "category": "arxiv",   "available": False},
    "Octagon Deep Research":  {"fn": _not_available, "category": "octagon", "available": False},
    "Octagon Deep Research MCP": {"fn": _not_available, "category": "octagon", "available": False},
    "Google Patents MCP":    {"fn": _not_available, "category": "patents", "available": False},
    "Google Patents Search":  {"fn": _not_available, "category": "patents", "available": False},
    "Sequential Thinking":   {"fn": _not_available, "category": "thinking", "available": False},
    "Sequential Thinking Analyzer": {"fn": _not_available, "category": "thinking", "available": False},
    "think-tool":            {"fn": _not_available, "category": "thinking", "available": False},
    "sequential-thinking":   {"fn": _not_available, "category": "thinking", "available": False},
    "Think Tool Synthesizer": {"fn": _not_available, "category": "thinking", "available": False},
    "mindmap-mermaid":       {"fn": _not_available, "category": "viz",     "available": False},
    "mindmap":               {"fn": _not_available, "category": "viz",     "available": False},
    "n8n-mcp":               {"fn": _not_available, "category": "n8n",     "available": False},
    "pinecone":              {"fn": _not_available, "category": "pinecone", "available": False},
    "Notion":                {"fn": _not_available, "category": "notion",  "available": False},
    "NLP Processing Engine":  {"fn": _not_available, "category": "nlp",    "available": False},
    "PWS Research Validator": {"fn": _not_available, "category": "custom",  "available": False},
}

# Category-level fallback: if an unknown tool name matches a category keyword
CATEGORY_FALLBACK: Dict[str, Callable] = {
    "neo4j":   _neo4j_framework_lookup,
    "tavily":  _tavily_search,
    "web":     _tavily_search,
    "search":  _tavily_search,
}


# ── Public API ───────────────────────────────────────────────────────────────

def resolve_tool(tool_name: str) -> Dict[str, Any]:
    """
    Resolve a Neo4j MCPTool node name to its registry entry.

    Returns:
        {"fn": callable, "category": str, "available": bool}
        or a not_available entry for unknown tools.
    """
    if tool_name in TOOL_REGISTRY:
        return TOOL_REGISTRY[tool_name]

    # Fuzzy match: check if any registry key is a substring
    tool_lower = tool_name.lower()
    for key, entry in TOOL_REGISTRY.items():
        if key.lower() in tool_lower or tool_lower in key.lower():
            return entry

    # Category fallback
    for cat_keyword, fn in CATEGORY_FALLBACK.items():
        if cat_keyword in tool_lower:
            return {"fn": fn, "category": cat_keyword, "available": True}

    return {"fn": _not_available, "category": "unknown", "available": False}


def execute_tool(tool_name: str, query: str, **kwargs) -> Dict:
    """
    Execute a tool by its Neo4j MCPTool node name.

    Args:
        tool_name: The MCPTool.name from Neo4j
        query: The query/input to pass
        **kwargs: Additional parameters

    Returns:
        Tool result dict with timing trace.
    """
    t0 = time.time()
    entry = resolve_tool(tool_name)
    kwargs["_tool_name"] = tool_name

    try:
        result = entry["fn"](query, **kwargs)
    except Exception as e:
        result = {"tool": tool_name, "error": str(e)}

    elapsed_ms = round((time.time() - t0) * 1000)
    result["_trace"] = {
        "tool_name": tool_name,
        "category": entry.get("category", "unknown"),
        "available": entry.get("available", False),
        "ms": elapsed_ms,
    }
    logger.info("tool_dispatch: %s [%dms] available=%s", tool_name, elapsed_ms, entry.get("available"))
    return result


def get_available_tools() -> List[str]:
    """Return names of tools that have actual runtime callables."""
    return [name for name, entry in TOOL_REGISTRY.items() if entry["available"]]


def get_unavailable_tools() -> List[str]:
    """Return names of tools that exist in graph but lack runtime."""
    return [name for name, entry in TOOL_REGISTRY.items() if not entry["available"]]


def execute_pipeline(tool_names: List[str], query: str, pass_context: bool = True) -> List[Dict]:
    """
    Execute a sequence of tools, optionally passing context forward.

    Args:
        tool_names: Ordered list of MCPTool node names
        query: Initial query
        pass_context: If True, append prior results as context to subsequent queries

    Returns:
        List of tool results in execution order.
    """
    results = []
    context_parts = []

    for tool_name in tool_names:
        entry = resolve_tool(tool_name)
        if not entry["available"]:
            logger.warning("Pipeline skipping unavailable tool: %s", tool_name)
            results.append(execute_tool(tool_name, query))
            continue

        enriched_query = query
        if pass_context and context_parts:
            enriched_query = f"{query}\n\nPrior findings: {'; '.join(context_parts[-3:])}"

        result = execute_tool(tool_name, enriched_query)
        results.append(result)

        # Extract context for next step
        if result.get("results"):
            if isinstance(result["results"], list):
                for r in result["results"][:2]:
                    if isinstance(r, dict):
                        context_parts.append(r.get("name", r.get("title", str(r)[:100])))
                    else:
                        context_parts.append(str(r)[:100])
            elif isinstance(result["results"], dict):
                context_parts.append(str(result["results"])[:200])
        elif result.get("answer"):
            context_parts.append(result["answer"][:200])
        elif result.get("context"):
            context_parts.append(str(result["context"])[:200])

    return results
