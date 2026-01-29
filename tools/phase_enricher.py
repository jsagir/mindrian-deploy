"""
Phase Enricher - LazyGraph/Neo4j + News/Trends context enrichment
==================================================================

Enriches workshop phases with:
1. Neo4j knowledge graph - frameworks, case studies, concepts
2. NewsMesh news - current articles relevant to domain
3. Google Trends - trend data for uncertainties and driving forces
"""

import os
from typing import Dict, List, Any, Optional

# Import research tools
try:
    from tools.news_search import search_news, format_news_markdown
    NEWS_AVAILABLE = True
except ImportError:
    NEWS_AVAILABLE = False

try:
    from tools.trends_search import search_trends, search_related_queries, format_trends_markdown
    TRENDS_AVAILABLE = True
except ImportError:
    TRENDS_AVAILABLE = False

# Neo4j connection
NEO4J_URI = os.getenv("NEO4J_URI", "")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")

_driver = None


def get_neo4j_driver():
    """Get or create Neo4j driver."""
    global _driver
    if _driver is None and NEO4J_URI:
        try:
            from neo4j import GraphDatabase
            _driver = GraphDatabase.driver(
                NEO4J_URI,
                auth=(NEO4J_USER, NEO4J_PASSWORD)
            )
        except Exception as e:
            print(f"Neo4j connection error: {e}")
            return None
    return _driver


def query_neo4j(query: str, params: dict = None) -> List[dict]:
    """
    Execute a Cypher query and return results.

    Args:
        query: Cypher query string
        params: Query parameters

    Returns:
        List of record dictionaries
    """
    driver = get_neo4j_driver()
    if not driver:
        return []

    try:
        with driver.session() as session:
            result = session.run(query, params or {})
            return [dict(record) for record in result]
    except Exception as e:
        print(f"Neo4j query error: {e}")
        return []


def enrich_phase_context(
    phase_config: dict,
    user_context: dict = None,
    bot_id: str = "scenario"
) -> Dict[str, Any]:
    """
    Query Neo4j for phase-relevant frameworks, examples, and guidance.

    Args:
        phase_config: Phase definition with neo4j_queries
        user_context: Extracted user data (domain, focal_question, etc.)
        bot_id: Current bot identifier

    Returns:
        Dict with frameworks, case_studies, tips, related_concepts
    """
    enriched = {
        "frameworks": [],
        "case_studies": [],
        "tips": [],
        "related_concepts": []
    }

    queries = phase_config.get("neo4j_queries", {})
    user_context = user_context or {}

    for query_name, cypher in queries.items():
        if not cypher or not cypher.strip():
            continue

        # Build params from user context
        params = {
            "domain": user_context.get("domain", ""),
            "focal_question": user_context.get("focal_question", ""),
            "bot_id": bot_id
        }

        try:
            records = query_neo4j(cypher, params)

            # Categorize results based on query name
            if "case" in query_name.lower():
                enriched["case_studies"].extend(records)
            elif "framework" in query_name.lower() or "context" in query_name.lower():
                enriched["frameworks"].extend(records)
            elif "tip" in query_name.lower() or "warning" in query_name.lower():
                enriched["tips"].extend(records)
            else:
                enriched["related_concepts"].extend(records)

        except Exception as e:
            print(f"Enrichment query '{query_name}' error: {e}")

    return enriched


def format_enrichment_for_display(enriched: Dict[str, Any], max_items: int = 3) -> str:
    """
    Format enriched context for user-friendly display.

    Args:
        enriched: Dict from enrich_phase_context
        max_items: Maximum items per category

    Returns:
        Formatted markdown string
    """
    parts = []

    # Frameworks
    if enriched.get("frameworks"):
        parts.append("**Relevant Frameworks:**")
        for f in enriched["frameworks"][:max_items]:
            name = (f.get("framework") or f.get("name") or
                    f.get("f.name") or "Framework")
            components = f.get("components", [])
            if components:
                parts.append(f"- {name}: {', '.join(components[:3])}")
            else:
                desc = f.get("description", "")[:80]
                parts.append(f"- {name}" + (f": {desc}..." if desc else ""))

    # Case Studies
    if enriched.get("case_studies"):
        parts.append("\n**Case Studies:**")
        for cs in enriched["case_studies"][:max_items]:
            name = (cs.get("case_study") or cs.get("name") or
                    cs.get("cs.name") or "Case Study")
            summary = (cs.get("summary") or cs.get("cs.summary") or "")[:100]
            parts.append(f"- {name}" + (f": {summary}..." if summary else ""))

    # Tips
    if enriched.get("tips"):
        parts.append("\n**Tips:**")
        for tip in enriched["tips"][:max_items]:
            text = tip.get("tip") or tip.get("text") or tip.get("description", "")
            if text:
                parts.append(f"- {text[:100]}")

    # Related Concepts
    if enriched.get("related_concepts"):
        concepts = enriched["related_concepts"][:max_items]
        concept_names = []
        for c in concepts:
            name = (c.get("concept") or c.get("name") or
                    c.get("trend") or c.get("c.name"))
            if name:
                concept_names.append(name)
        if concept_names:
            parts.append(f"\n**Related:** {', '.join(concept_names)}")

    return "\n".join(parts) if parts else ""


def get_phase_transition_context(
    from_phase: dict,
    to_phase: dict,
    user_context: dict = None,
    extracted_deliverables: dict = None,
    include_research: bool = True
) -> str:
    """
    Generate intelligent transition message between phases.

    Summarizes completed work, explains next phase, provides
    relevant context from Neo4j + News + Trends, and gives opening prompt.

    Args:
        from_phase: Completed phase config
        to_phase: Next phase config
        user_context: Accumulated user context (domain, etc.)
        extracted_deliverables: What was extracted from completed phase
        include_research: Whether to include news/trends research

    Returns:
        Formatted transition message
    """
    user_context = user_context or {}
    extracted_deliverables = extracted_deliverables or {}

    transition = []

    # --- Section 1: Summarize completed phase ---
    from_name = from_phase.get("name", "Previous Phase")
    transition.append(f"**{from_name}**")

    if extracted_deliverables:
        transition.append("You've established:")
        for key, value in extracted_deliverables.items():
            if value and value != "[discussed but not explicitly stated]":
                clean_key = key.replace("_", " ").title()
                display_value = str(value)[:80]
                if len(str(value)) > 80:
                    display_value += "..."
                transition.append(f"  - {clean_key}: {display_value}")
    transition.append("")

    # --- Section 2: Introduce next phase ---
    to_name = to_phase.get("name", "Next Phase")
    to_desc = to_phase.get("description", "")
    transition.append(f"**{to_name}**")
    if to_desc:
        transition.append(f"*{to_desc}*")
    transition.append("")

    # --- Section 3: Clear instructions ---
    instructions = to_phase.get("instructions", [])
    if instructions:
        transition.append("**What to do:**")
        for inst in instructions[:4]:
            transition.append(f"- {inst}")
        transition.append("")

    # --- Section 4: Full enrichment (Neo4j + News + Trends) ---
    if include_research:
        enriched = enrich_phase_with_research(
            to_phase,
            user_context,
            include_news=NEWS_AVAILABLE,
            include_trends=TRENDS_AVAILABLE
        )
        enriched_text = format_full_enrichment(enriched, max_items=2)
    else:
        enriched = enrich_phase_context(to_phase, user_context)
        enriched_text = format_enrichment_for_display(enriched, max_items=2)

    if enriched_text:
        transition.append(enriched_text)
        transition.append("")

    # --- Section 5: Opening prompt ---
    prompt = to_phase.get("prompt", "What would you like to explore?")

    # Substitute user context variables in prompt
    for key, value in user_context.items():
        if value and isinstance(value, str):
            prompt = prompt.replace(f"{{{key}}}", value)

    transition.append(f"**Let's begin:** {prompt}")

    return "\n".join(transition)


def get_quick_context_hint(phase_config: dict, user_context: dict = None) -> str:
    """
    Get a quick one-line context hint for a phase.

    Args:
        phase_config: Phase definition
        user_context: User context dict

    Returns:
        Short hint string or empty string
    """
    enriched = enrich_phase_context(phase_config, user_context)

    # Try to get one relevant piece of context
    if enriched.get("case_studies"):
        cs = enriched["case_studies"][0]
        name = cs.get("name") or cs.get("case_study", "")
        if name:
            return f"(See how {name} approached this)"

    if enriched.get("frameworks"):
        f = enriched["frameworks"][0]
        name = f.get("framework") or f.get("name", "")
        if name:
            return f"(Uses {name} methodology)"

    return ""


# ============================================================
# NEWS & TRENDS ENRICHMENT
# ============================================================

def fetch_domain_news(domain: str, max_results: int = 3) -> Dict[str, Any]:
    """
    Fetch recent news articles relevant to a domain.

    Args:
        domain: The domain/industry to search for
        max_results: Maximum number of articles

    Returns:
        Dict with articles list and formatted markdown
    """
    if not NEWS_AVAILABLE:
        return {"articles": [], "markdown": "", "error": "NewsMesh not available"}

    if not domain:
        return {"articles": [], "markdown": "", "error": "No domain specified"}

    try:
        # Search for domain news in business/technology categories
        results = search_news(
            query=domain,
            max_results=max_results,
            category="business",
            sort_by="relevant"
        )

        articles = results.get("articles", [])
        markdown = ""

        if articles:
            markdown = f"**Recent News ({domain}):**\n"
            for i, a in enumerate(articles[:max_results], 1):
                title = a.get("title", "")[:60]
                source = a.get("source", "")
                markdown += f"- {title} ({source})\n"

        return {
            "articles": articles,
            "markdown": markdown,
            "error": results.get("error")
        }

    except Exception as e:
        return {"articles": [], "markdown": "", "error": str(e)}


def fetch_domain_trends(domain: str, uncertainties: List[str] = None) -> Dict[str, Any]:
    """
    Fetch Google Trends data for domain and key uncertainties.

    Args:
        domain: The domain/industry to analyze
        uncertainties: List of uncertainty terms to check trends for

    Returns:
        Dict with trend data and formatted markdown
    """
    if not TRENDS_AVAILABLE:
        return {"trends": [], "markdown": "", "error": "Google Trends not available"}

    if not domain:
        return {"trends": [], "markdown": "", "error": "No domain specified"}

    try:
        trends_data = []
        markdown_parts = []

        # Get trends for main domain
        domain_trends = search_trends(domain, data_type="TIMESERIES", date="today 12-m")
        if not domain_trends.get("error"):
            trends_data.append({"term": domain, "data": domain_trends})

            # Extract trend direction
            data = domain_trends.get("data", {})
            timeline = data.get("interest_over_time", {}).get("timeline_data", [])
            if timeline:
                values = []
                for point in timeline:
                    for v in point.get("values", []):
                        values.append(v.get("extracted_value", 0))
                if len(values) >= 4:
                    recent = sum(values[-4:]) / 4
                    early = sum(values[:4]) / 4
                    if recent > early * 1.2:
                        markdown_parts.append(f"**{domain}**: 📈 Rising trend")
                    elif recent < early * 0.8:
                        markdown_parts.append(f"**{domain}**: 📉 Declining trend")
                    else:
                        markdown_parts.append(f"**{domain}**: ➡️ Stable trend")

        # Get related queries for inspiration
        related = search_related_queries(domain)
        if not related.get("error"):
            rising = related.get("data", {}).get("related_queries", {}).get("rising", [])
            if rising:
                rising_terms = [r.get("query", "") for r in rising[:3]]
                markdown_parts.append(f"**Rising related:** {', '.join(rising_terms)}")

        # Check trends for specific uncertainties
        if uncertainties:
            for term in uncertainties[:2]:  # Limit API calls
                term_trends = search_trends(term, data_type="TIMESERIES", date="today 12-m")
                if not term_trends.get("error"):
                    trends_data.append({"term": term, "data": term_trends})

        markdown = "\n".join(markdown_parts) if markdown_parts else ""

        return {
            "trends": trends_data,
            "markdown": markdown,
            "error": None
        }

    except Exception as e:
        return {"trends": [], "markdown": "", "error": str(e)}


def enrich_phase_with_research(
    phase_config: dict,
    user_context: dict = None,
    include_news: bool = True,
    include_trends: bool = True
) -> Dict[str, Any]:
    """
    Full enrichment combining Neo4j + News + Trends.

    Args:
        phase_config: Phase definition
        user_context: User context with domain, uncertainties, etc.
        include_news: Whether to fetch news
        include_trends: Whether to fetch trends

    Returns:
        Combined enrichment dict
    """
    user_context = user_context or {}
    domain = user_context.get("domain", "")

    # Start with Neo4j enrichment
    enriched = enrich_phase_context(phase_config, user_context)

    # Add news if relevant phase
    phase_name = phase_config.get("name", "").lower()
    news_phases = ["driving forces", "narratives", "synthesis"]

    if include_news and any(p in phase_name for p in news_phases):
        news = fetch_domain_news(domain, max_results=3)
        enriched["news"] = news
        if news.get("markdown"):
            enriched["news_markdown"] = news["markdown"]

    # Add trends if relevant phase
    trends_phases = ["driving forces", "uncertainty", "narratives"]

    if include_trends and any(p in phase_name for p in trends_phases):
        uncertainties = []
        if user_context.get("top_uncertainties"):
            uncertainties = user_context["top_uncertainties"].split(",")[:2]

        trends = fetch_domain_trends(domain, uncertainties)
        enriched["trends"] = trends
        if trends.get("markdown"):
            enriched["trends_markdown"] = trends["markdown"]

    return enriched


def format_full_enrichment(enriched: Dict[str, Any], max_items: int = 3) -> str:
    """
    Format full enrichment (Neo4j + News + Trends) for display.

    Args:
        enriched: Full enrichment dict from enrich_phase_with_research
        max_items: Max items per category

    Returns:
        Formatted markdown string
    """
    parts = []

    # Neo4j content
    neo4j_content = format_enrichment_for_display(enriched, max_items)
    if neo4j_content:
        parts.append(neo4j_content)

    # Trends
    if enriched.get("trends_markdown"):
        parts.append("\n**Current Trends:**")
        parts.append(enriched["trends_markdown"])

    # News
    if enriched.get("news_markdown"):
        parts.append("\n" + enriched["news_markdown"])

    return "\n".join(parts) if parts else ""


__all__ = [
    "get_neo4j_driver",
    "query_neo4j",
    "enrich_phase_context",
    "format_enrichment_for_display",
    "get_phase_transition_context",
    "get_quick_context_hint",
    "fetch_domain_news",
    "fetch_domain_trends",
    "enrich_phase_with_research",
    "format_full_enrichment",
    "NEWS_AVAILABLE",
    "TRENDS_AVAILABLE",
]
