"""
PWS Consultant Pipeline - Background intelligence for the PWS Consultant agent.

Orchestrates:
1. LangExtract (instant + background) for real-time signal detection
2. GraphRAG hybrid retrieval: context extraction -> text2cypher -> cypher2text -> LLM context
3. FileSearch for PWS course materials (lectures, frameworks, worksheets)
4. Domain/Subdomain discovery from user context
5. BONO expert-builder pipeline for domain-specific consulting panel

All designed for low latency:
- instant_extract() runs synchronously (<5ms)
- GraphRAG lazy cache (~2MB, sub-100ms)
- Neo4j queries with 3s circuit breaker
- FileSearch async with caching
- Expert building runs as fire-and-forget background task
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# Lazy imports (graceful degradation if tools unavailable)
# ═══════════════════════════════════════════════════════════════════════════════

try:
    from tools.langextract import instant_extract, get_extraction_hint, background_extract_pws
    LANGEXTRACT_ENABLED = True
except ImportError:
    LANGEXTRACT_ENABLED = False
    def instant_extract(text): return {"signals": {}, "counts": {}, "quality_signals": {}, "content_type": "general"}
    def get_extraction_hint(signals, turn_count=0): return None
    async def background_extract_pws(text, context="", extract_type="general"): return {}

try:
    from tools.graphrag_lite import (
        enrich_for_bot, light_context, query_neo4j,
        lazy_concept_lookup, lazy_multi_concept_context,
        get_related_frameworks, get_problem_context,
        should_retrieve, get_retrieval_type,
    )
    GRAPHRAG_ENABLED = True
except ImportError:
    GRAPHRAG_ENABLED = False
    def enrich_for_bot(msg, turn, bot_id="larry"): return None
    def light_context(query, context_type="auto"): return ("", {})
    def query_neo4j(cypher, params=None): return []
    def lazy_concept_lookup(query, limit=5): return []
    def lazy_multi_concept_context(keywords): return ("", {})
    def get_related_frameworks(topic, limit=3): return []
    def get_problem_context(desc): return {}
    def should_retrieve(msg, turn=0): return False
    def get_retrieval_type(msg): return "none"

try:
    from tools.graph_router import graph_score_agents, classify_and_route, has_problem_language
    GRAPH_ROUTER_ENABLED = True
except ImportError:
    GRAPH_ROUTER_ENABLED = False
    def graph_score_agents(text, bot): return ({}, {})
    def classify_and_route(text, bot): return ({}, {})
    def has_problem_language(text): return False


# ═══════════════════════════════════════════════════════════════════════════════
# 1. INSTANT ANALYSIS (synchronous, <5ms)
# ═══════════════════════════════════════════════════════════════════════════════

def instant_analyze(user_message: str, turn_count: int = 0) -> Dict:
    """
    Zero-latency analysis of user message.
    Combines LangExtract signals with GraphRAG retrieval type detection.

    Returns:
        {
            "signals": dict (from instant_extract),
            "hint": str or None (coaching hint for system prompt),
            "retrieval_type": str ("concept" | "framework" | "problem" | "none"),
            "has_problem_language": bool,
            "content_type": str,
            "ms": float
        }
    """
    start = time.time()

    signals = instant_extract(user_message)
    hint = get_extraction_hint(signals, turn_count)
    retrieval_type = get_retrieval_type(user_message) if GRAPHRAG_ENABLED else "none"
    problem_lang = has_problem_language(user_message) if GRAPH_ROUTER_ENABLED else False

    elapsed = (time.time() - start) * 1000

    return {
        "signals": signals,
        "hint": hint,
        "retrieval_type": retrieval_type,
        "has_problem_language": problem_lang,
        "content_type": signals.get("content_type", "general"),
        "ms": round(elapsed, 1),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 2. HYBRID RETRIEVAL: Text -> Cypher -> Text -> Context
# ═══════════════════════════════════════════════════════════════════════════════

def text_to_cypher_queries(user_message: str, signals: dict = None) -> List[Dict]:
    """
    Convert user text + extracted signals into targeted Cypher queries.

    This is the text2cypher step: we don't use LLM to generate Cypher.
    Instead, we use pattern matching on extracted signals to select
    pre-built Cypher templates. Fast and deterministic.

    Returns list of: [{"name": str, "cypher": str, "params": dict}]
    """
    queries = []
    text_lower = user_message.lower()

    # Extract keywords for concept lookup
    keywords = []
    if signals and signals.get("signals"):
        # Use LangExtract-detected entities
        samples = signals.get("samples", {})
        for key in ["problems", "assumptions", "statistics"]:
            keywords.extend(samples.get(key, [])[:2])

    # 1. Framework discovery from concepts
    if keywords or len(text_lower.split()) > 3:
        search_terms = " ".join(keywords[:3]) if keywords else user_message[:200]
        queries.append({
            "name": "related_frameworks",
            "cypher": """
                CALL db.index.fulltext.queryNodes('framework_ecosystem_search', $query, {limit: 5})
                YIELD node, score
                WHERE score > 0.5
                RETURN node.name AS framework,
                       node.description AS description,
                       node.hint AS hint,
                       score
                ORDER BY score DESC
                LIMIT 5
            """,
            "params": {"query": search_terms},
        })

    # 2. Problem type classification from graph
    if signals and signals.get("has_problem_language", has_problem_language(user_message)):
        queries.append({
            "name": "problem_types",
            "cypher": """
                CALL db.index.fulltext.queryNodes('entity_fulltext', $query, {limit: 3})
                YIELD node, score
                WHERE 'ProblemType' IN labels(node) AND score > 0.3
                RETURN node.name AS problem_type,
                       node.description AS description,
                       node.recommended_approach AS approach,
                       score
                ORDER BY score DESC
                LIMIT 3
            """,
            "params": {"query": user_message[:300]},
        })

    # 3. Domain discovery
    queries.append({
        "name": "domain_discovery",
        "cypher": """
            CALL db.index.fulltext.queryNodes('entity_fulltext', $query, {limit: 5})
            YIELD node, score
            WHERE ('Domain' IN labels(node) OR 'Concept' IN labels(node))
              AND score > 0.3
            RETURN labels(node) AS types,
                   node.name AS name,
                   node.description AS description,
                   score
            ORDER BY score DESC
            LIMIT 5
        """,
        "params": {"query": user_message[:300]},
    })

    # 4. Technique lookup based on problem context
    quality = signals.get("quality_signals", {}) if signals else {}
    if quality.get("has_pws_elements") or quality.get("has_data"):
        queries.append({
            "name": "techniques",
            "cypher": """
                CALL db.index.fulltext.queryNodes('entity_fulltext', $query, {limit: 5})
                YIELD node, score
                WHERE 'Technique' IN labels(node) AND score > 0.3
                RETURN node.name AS technique,
                       node.description AS description,
                       score
                ORDER BY score DESC
                LIMIT 3
            """,
            "params": {"query": user_message[:200]},
        })

    # 5. Concept co-occurrence (LazyGraphRAG fast path)
    # This uses the lazy cache, not a direct Cypher query
    queries.append({
        "name": "concept_cooccurrence",
        "cypher": "__LAZY_LOOKUP__",  # Special marker: use lazy_multi_concept_context
        "params": {"keywords": text_lower.split()[:8]},
    })

    return queries


def execute_cypher_queries(queries: List[Dict]) -> Dict[str, any]:
    """
    Execute Cypher queries and return structured results.

    The cypher2text step: convert raw Neo4j results into
    structured context that can be injected into the LLM prompt.

    Returns:
        {
            "frameworks": [{"name": str, "description": str, "hint": str}],
            "problem_types": [{"name": str, "description": str, "approach": str}],
            "domains": [{"name": str, "type": str, "description": str}],
            "techniques": [{"name": str, "description": str}],
            "concept_hint": str,
            "trace": {"queries_run": int, "total_ms": float, "errors": [str]}
        }
    """
    if not GRAPHRAG_ENABLED:
        return {
            "frameworks": [], "problem_types": [], "domains": [],
            "techniques": [], "concept_hint": "",
            "trace": {"queries_run": 0, "total_ms": 0, "errors": ["GraphRAG not available"]},
        }

    start = time.time()
    results = {
        "frameworks": [],
        "problem_types": [],
        "domains": [],
        "techniques": [],
        "concept_hint": "",
        "trace": {"queries_run": 0, "total_ms": 0, "errors": []},
    }

    for q in queries:
        try:
            if q["cypher"] == "__LAZY_LOOKUP__":
                # Use lazy concept co-occurrence (cached, fast)
                hint, trace = lazy_multi_concept_context(q["params"]["keywords"])
                results["concept_hint"] = hint or ""
                results["trace"]["queries_run"] += 1
                continue

            rows = query_neo4j(q["cypher"], q["params"])
            results["trace"]["queries_run"] += 1

            if q["name"] == "related_frameworks":
                results["frameworks"] = [
                    {"name": r.get("framework", ""), "description": r.get("description", ""), "hint": r.get("hint", "")}
                    for r in rows
                ]
            elif q["name"] == "problem_types":
                results["problem_types"] = [
                    {"name": r.get("problem_type", ""), "description": r.get("description", ""), "approach": r.get("approach", "")}
                    for r in rows
                ]
            elif q["name"] == "domain_discovery":
                results["domains"] = [
                    {
                        "name": r.get("name", ""),
                        "type": r.get("types", ["Unknown"])[0] if r.get("types") else "Unknown",
                        "description": r.get("description", ""),
                    }
                    for r in rows
                ]
            elif q["name"] == "techniques":
                results["techniques"] = [
                    {"name": r.get("technique", ""), "description": r.get("description", "")}
                    for r in rows
                ]

        except Exception as e:
            results["trace"]["errors"].append(f"{q['name']}: {str(e)[:100]}")
            logger.debug("Cypher query '%s' failed: %s", q["name"], e)

    results["trace"]["total_ms"] = round((time.time() - start) * 1000, 1)
    return results


def cypher_results_to_context(results: Dict) -> str:
    """
    Convert structured Cypher results into natural language context
    for injection into the LLM system prompt.

    The cypher2text -> LLM context step.
    """
    parts = []

    if results.get("frameworks"):
        fw_names = [f["name"] for f in results["frameworks"][:4]]
        parts.append(f"Related PWS frameworks: {', '.join(fw_names)}")
        # Include hints for top 2
        for fw in results["frameworks"][:2]:
            if fw.get("hint"):
                parts.append(f"  - {fw['name']}: {fw['hint']}")

    if results.get("problem_types"):
        pt_info = results["problem_types"][0]
        parts.append(f"Graph-detected problem pattern: {pt_info['name']}")
        if pt_info.get("approach"):
            parts.append(f"  Recommended approach: {pt_info['approach']}")

    if results.get("domains"):
        domain_names = [d["name"] for d in results["domains"][:3]]
        parts.append(f"Relevant domains: {', '.join(domain_names)}")

    if results.get("techniques"):
        tech_names = [t["name"] for t in results["techniques"][:3]]
        parts.append(f"Applicable techniques: {', '.join(tech_names)}")

    if results.get("concept_hint"):
        parts.append(f"Knowledge graph context: {results['concept_hint']}")

    if not parts:
        return ""

    return "[Hybrid retrieval context]\n" + "\n".join(parts)


# ═══════════════════════════════════════════════════════════════════════════════
# 3. FULL HYBRID RETRIEVAL PIPELINE (combines all steps)
# ═══════════════════════════════════════════════════════════════════════════════

def hybrid_retrieve(user_message: str, signals: dict = None) -> Tuple[str, Dict]:
    """
    Full hybrid retrieval pipeline:
    Context Extraction -> Text-to-Cypher -> Cypher Execution -> Cypher-to-Text

    This runs synchronously and targets <500ms total.

    Args:
        user_message: The user's input text
        signals: Pre-computed LangExtract signals (optional, will compute if None)

    Returns:
        (context_string, trace_dict)
    """
    start = time.time()

    # Step 1: Extract signals if not provided
    if signals is None:
        signals = instant_extract(user_message)

    # Step 2: Generate Cypher queries from text + signals
    cypher_queries = text_to_cypher_queries(user_message, signals)

    # Step 3: Execute queries against Neo4j
    results = execute_cypher_queries(cypher_queries)

    # Step 4: Convert results to LLM context
    context = cypher_results_to_context(results)

    # Also get GraphRAG bot enrichment (for additional hints)
    graphrag_hint = enrich_for_bot(user_message, 1, bot_id="pws_consultant") if GRAPHRAG_ENABLED else None
    if graphrag_hint and graphrag_hint not in context:
        context += f"\n{graphrag_hint}"

    elapsed = (time.time() - start) * 1000

    trace = {
        "pipeline": "hybrid_retrieve",
        "total_ms": round(elapsed, 1),
        "cypher_queries": len(cypher_queries),
        "cypher_trace": results.get("trace", {}),
        "frameworks_found": len(results.get("frameworks", [])),
        "domains_found": len(results.get("domains", [])),
        "has_graphrag_hint": bool(graphrag_hint),
    }

    return context, trace


# ═══════════════════════════════════════════════════════════════════════════════
# 4. DOMAIN DISCOVERY PIPELINE (background, async)
# ═══════════════════════════════════════════════════════════════════════════════

async def discover_domain_and_subdomains(
    user_message: str,
    conversation_context: str = "",
    cypher_results: dict = None,
) -> Dict:
    """
    Discover the user's domain and subdomains from their challenge description.

    Uses a combination of:
    - Neo4j domain nodes (from cypher_results if available)
    - LLM classification for subdomain extraction
    - Concept co-occurrence for related fields

    Returns:
        {
            "domain": str,
            "subdomains": [str],
            "confidence": float,
            "source": "graph" | "llm" | "hybrid"
        }
    """
    domain = ""
    subdomains = []
    source = "default"

    # Try graph-based domain detection first (fast)
    if cypher_results and cypher_results.get("domains"):
        domains = cypher_results["domains"]
        if domains:
            domain = domains[0]["name"]
            subdomains = [d["name"] for d in domains[1:4]]
            source = "graph"

    # If no graph result, try concept lookup
    if not domain and GRAPHRAG_ENABLED:
        try:
            concepts = lazy_concept_lookup(user_message[:200], limit=5)
            if concepts:
                # Use top concept's community peers as domain indicators
                top_concept = concepts[0]["name"]
                domain = top_concept
                subdomains = [c["name"] for c in concepts[1:4]]
                source = "concept"
        except Exception as e:
            logger.debug("Concept lookup for domain failed: %s", e)

    # LLM-based domain extraction as fallback (uses Gemini)
    if not domain:
        try:
            from google import genai
            import os

            client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=f"""Extract the primary domain and 3-4 subdomains from this challenge description.
Return ONLY a JSON object like: {{"domain": "...", "subdomains": ["...", "..."]}}

Challenge: {user_message[:500]}
{f'Context: {conversation_context[:300]}' if conversation_context else ''}""",
            )
            import json
            text = response.text.strip()
            # Clean markdown code block if present
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            parsed = json.loads(text.strip())
            domain = parsed.get("domain", "")
            subdomains = parsed.get("subdomains", [])
            source = "llm"
        except Exception as e:
            logger.debug("LLM domain extraction failed: %s", e)
            domain = "General Innovation"
            subdomains = ["Strategy", "Technology", "Market"]
            source = "default"

    return {
        "domain": domain,
        "subdomains": subdomains[:5],
        "confidence": 0.8 if source in ("graph", "concept") else 0.6,
        "source": source,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 5. EXPERT BUILDER PIPELINE (background, async)
# ═══════════════════════════════════════════════════════════════════════════════

async def build_expert_panel(
    user_message: str,
    problem_type_key: str = "undefined",
    conversation_context: str = "",
    cypher_results: dict = None,
) -> Dict:
    """
    Full background pipeline that:
    1. Discovers domain/subdomains
    2. Builds domain-specific experts
    3. Returns ready-to-render expert panel

    This is the fire-and-forget task that runs while the user
    is answering diagnostic questions.

    Returns:
        {
            "domain": str,
            "subdomains": [str],
            "experts": [expert_dict],
            "problem_type": str,
            "trace": dict
        }
    """
    start = time.time()

    # Step 1: Discover domain
    domain_result = await discover_domain_and_subdomains(
        user_message, conversation_context, cypher_results
    )

    # Step 2: Build experts
    from prompts.pws_consultant import build_expert_specs
    experts = build_expert_specs(
        domain=domain_result["domain"],
        subdomains=domain_result["subdomains"],
        problem_type_key=problem_type_key,
    )

    elapsed = (time.time() - start) * 1000

    return {
        "domain": domain_result["domain"],
        "subdomains": domain_result["subdomains"],
        "experts": experts,
        "problem_type": problem_type_key,
        "trace": {
            "domain_source": domain_result["source"],
            "domain_confidence": domain_result["confidence"],
            "experts_built": len(experts),
            "total_ms": round(elapsed, 1),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 6. FILE SEARCH INTEGRATION (PWS course materials)
# ═══════════════════════════════════════════════════════════════════════════════

async def search_pws_materials(
    query: str,
    problem_type_key: str = None,
    store_id: str = "fileSearchStores/pwsknowledgebase-a4rnz3u41lsn",
) -> Optional[str]:
    """
    Search PWS FileSearch store for relevant course materials.

    Enriches the query with problem-type context for better retrieval.

    Returns formatted context string or None.
    """
    try:
        from google import genai
        import os

        client = genai.Client(api_key=os.environ.get("GOOGLE_FILESEARCH_API_KEY") or os.environ.get("GOOGLE_API_KEY"))

        # Enrich query with problem type context
        enriched_query = query
        if problem_type_key:
            from prompts.pws_consultant import get_problem_type
            pt = get_problem_type(problem_type_key)
            enriched_query = f"{query} (Problem type: {pt['name']}. Frameworks: {', '.join(pt['frameworks'][:3])})"

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=enriched_query[:500],
            config={
                "tools": [{"google_search": {"file_search_store": store_id}}],
                "temperature": 0.3,
                "max_output_tokens": 500,
            },
        )

        if response and response.text:
            return f"[PWS Course Material]\n{response.text[:800]}"

    except Exception as e:
        logger.debug("FileSearch retrieval failed: %s", e)

    return None


# ═══════════════════════════════════════════════════════════════════════════════
# 7. FULL TURN PIPELINE (called each message in PWS Consultant)
# ═══════════════════════════════════════════════════════════════════════════════

async def process_consultant_turn(
    user_message: str,
    turn_count: int = 0,
    phase: str = "intro",
    conversation_context: str = "",
    problem_type_key: str = None,
    session=None,
) -> Dict:
    """
    Main pipeline called each turn in the PWS Consultant.

    Orchestrates all retrieval and background tasks:
    1. Instant analysis (sync, <5ms)
    2. Hybrid retrieval: text->cypher->text (sync, <500ms target)
    3. FileSearch for PWS materials (async)
    4. Background expert building (async, fire-and-forget)

    Returns:
        {
            "system_context": str,     # Inject into system prompt
            "signals": dict,           # LangExtract signals
            "hybrid_context": str,     # From graph retrieval
            "filesearch_context": str, # From PWS materials
            "recommended_tools": list, # Context-aware tool buttons
            "expert_panel_task": Task, # Background task (check later)
            "trace": dict,
        }
    """
    start = time.time()

    # 1. Instant analysis
    instant = instant_analyze(user_message, turn_count)

    # 2. Hybrid retrieval (synchronous, fast)
    hybrid_context, hybrid_trace = hybrid_retrieve(user_message, instant["signals"])

    # 3. FileSearch (async, non-blocking)
    filesearch_context = None
    if phase in ("consulting", "diagnostic") and turn_count > 1:
        try:
            filesearch_context = await asyncio.wait_for(
                search_pws_materials(user_message, problem_type_key),
                timeout=3.0,
            )
        except asyncio.TimeoutError:
            logger.debug("FileSearch timed out")
        except Exception as e:
            logger.debug("FileSearch error: %s", e)

    # 4. Expert building (background, fire-and-forget in intro/diagnostic phase)
    expert_task = None
    if phase in ("intro", "diagnostic") and session is not None:
        try:
            expert_task = asyncio.create_task(
                build_expert_panel(
                    user_message,
                    problem_type_key=problem_type_key or "undefined",
                    conversation_context=conversation_context,
                    cypher_results=hybrid_trace.get("cypher_trace"),
                )
            )
        except Exception as e:
            logger.debug("Expert panel task failed to start: %s", e)

    # 5. Context-aware tool recommendations
    from prompts.pws_consultant import get_recommended_tools
    tools = []
    if problem_type_key:
        tools = get_recommended_tools(problem_type_key, instant["signals"])

    # 6. Assemble system context
    context_parts = []
    if instant.get("hint"):
        context_parts.append(instant["hint"])
    if hybrid_context:
        context_parts.append(hybrid_context)
    if filesearch_context:
        context_parts.append(filesearch_context)

    system_context = "\n\n".join(context_parts) if context_parts else ""

    elapsed = (time.time() - start) * 1000

    return {
        "system_context": system_context,
        "signals": instant["signals"],
        "hybrid_context": hybrid_context,
        "filesearch_context": filesearch_context,
        "recommended_tools": tools,
        "expert_panel_task": expert_task,
        "trace": {
            "pipeline": "process_consultant_turn",
            "phase": phase,
            "turn": turn_count,
            "instant_ms": instant["ms"],
            "hybrid_ms": hybrid_trace.get("total_ms", 0),
            "total_ms": round(elapsed, 1),
            "has_filesearch": bool(filesearch_context),
            "has_expert_task": bool(expert_task),
        },
    }
