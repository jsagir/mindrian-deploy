"""
Lightweight GraphRAG for Conversational Chat
============================================

Designed for Larry's coaching style:
- Only retrieves when needed
- Returns hints, not lectures
- Helps Larry ask better questions

Two retrieval layers:
1. LazyGraphRAG (~8K concepts, 39 communities, ~123K co-occurrence edges)
   - Bounded cache: community map + PWS terms only (~2MB)
   - CO_OCCURS edges fetched on-demand per query concept
   - Circuit breaker: falls back gracefully if Neo4j slow
2. Entity/Framework layer (legacy)
   - Fulltext search over Framework, Concept, Person, etc.
   - Structural relationships (HAS_COMPONENT, REQUIRES, etc.)

Memory strategy (safe for 512MB Render):
- Cache: 39 communities + top concepts per community (~2MB)
- Cache: ~100 PWS terms for fast matching (~10KB)
- On-demand: CO_OCCURS neighbors fetched per query (~1 Cypher call)
- Never load all 123K edges into Python memory
"""

import os
import re
import time
import logging
from typing import Optional, Dict, List, Set

logger = logging.getLogger("graphrag_lite")

_neo4j_driver = None

# === Bounded Cache ===
_cache = None
_cache_loaded_at = 0.0
_CACHE_TTL = 3600  # Refresh every hour
_NEO4J_TIMEOUT = 3.0  # Circuit breaker: 3s max per query
_MIN_COMMUNITY_SIZE = 5  # Exclude micro-communities from retrieval


class _LazyCache:
    """Bounded in-memory cache. ~2MB total, safe for 512MB instances."""

    __slots__ = (
        'pws_terms', 'concept_to_community', 'community_top_concepts',
        'community_sizes', 'ready',
    )

    def __init__(self):
        self.pws_terms: Set[str] = set()  # ~100 PWS terms
        self.concept_to_community: Dict[str, int] = {}  # concept name -> community_id
        self.community_top_concepts: Dict[int, List[str]] = {}  # community -> top 10 names
        self.community_sizes: Dict[int, int] = {}  # community -> member count
        self.ready = False

    def is_valid_community(self, community_id: Optional[int]) -> bool:
        """Exclude micro-communities unless query explicitly matches."""
        if community_id is None:
            return False
        return self.community_sizes.get(community_id, 0) >= _MIN_COMMUNITY_SIZE


def _get_neo4j():
    """Get or create Neo4j driver."""
    global _neo4j_driver
    if _neo4j_driver is None:
        from neo4j import GraphDatabase
        uri = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USER")
        password = os.getenv("NEO4J_PASSWORD")
        if all([uri, user, password]):
            _neo4j_driver = GraphDatabase.driver(uri, auth=(user, password))
    return _neo4j_driver


def _get_cache() -> _LazyCache:
    """Get or warm the bounded cache. Thread-safe enough for single-process."""
    global _cache, _cache_loaded_at

    now = time.monotonic()
    if _cache and _cache.ready and (now - _cache_loaded_at) < _CACHE_TTL:
        return _cache

    driver = _get_neo4j()
    if not driver:
        return _LazyCache()

    cache = _LazyCache()
    try:
        t0 = time.monotonic()
        with driver.session() as session:
            # Load concept -> community mapping (~8K entries, ~500KB)
            result = session.run("""
                MATCH (c:LazyGraphConcept)
                WHERE c.community_id IS NOT NULL
                RETURN c.name AS name, c.community_id AS cid
            """)
            for r in result:
                cache.concept_to_community[r["name"]] = r["cid"]

            # Load community sizes + top 10 concepts per community
            result = session.run("""
                MATCH (c:LazyGraphConcept)
                WHERE c.community_id IS NOT NULL
                WITH c.community_id AS cid, c.name AS name, c.chunk_count AS freq
                ORDER BY cid, freq DESC
                WITH cid, collect(name) AS all_names, count(*) AS size
                RETURN cid, size, all_names[0..10] AS top
            """)
            for r in result:
                cache.community_top_concepts[r["cid"]] = r["top"]
                cache.community_sizes[r["cid"]] = r["size"]

            # PWS terms: concepts with chunk_count >= 5 (frequent = meaningful)
            result = session.run("""
                MATCH (c:LazyGraphConcept)
                WHERE c.chunk_count >= 5
                RETURN c.name AS name
            """)
            cache.pws_terms = {r["name"] for r in result}

        elapsed = time.monotonic() - t0
        cache.ready = True
        _cache = cache
        _cache_loaded_at = now
        logger.info(
            "LazyGraphRAG cache warmed: %d concepts, %d communities (%d valid), %d PWS terms [%.1fs]",
            len(cache.concept_to_community),
            len(cache.community_sizes),
            sum(1 for s in cache.community_sizes.values() if s >= _MIN_COMMUNITY_SIZE),
            len(cache.pws_terms),
            elapsed,
        )
    except Exception as e:
        logger.error("LazyGraphRAG cache warm error: %s", e)

    return cache


# === LazyGraphRAG Layer ===

def lazy_concept_lookup(query: str, limit: int = 5) -> List[Dict]:
    """
    Find LazyGraphConcept nodes matching the query.
    Uses fulltext index first, falls back to CONTAINS match.
    """
    driver = _get_neo4j()
    if not driver:
        return []

    try:
        t0 = time.monotonic()
        with driver.session() as session:
            # Try fulltext index (lazy_concept_search)
            result = session.run("""
                CALL db.index.fulltext.queryNodes('lazy_concept_search', $query)
                YIELD node, score
                WHERE score > 0.5
                RETURN node.name AS name,
                       node.community_id AS community,
                       node.chunk_count AS freq,
                       node.degree AS degree,
                       score
                ORDER BY score DESC
                LIMIT $limit
            """, query=query, limit=limit)

            concepts = [dict(r) for r in result]

            if not concepts:
                # Fallback: CONTAINS match
                result = session.run("""
                    MATCH (c:LazyGraphConcept)
                    WHERE toLower(c.name) CONTAINS toLower($query)
                    RETURN c.name AS name,
                           c.community_id AS community,
                           c.chunk_count AS freq,
                           c.degree AS degree,
                           1.0 AS score
                    ORDER BY c.chunk_count DESC
                    LIMIT $limit
                """, query=query, limit=limit)
                concepts = [dict(r) for r in result]

        elapsed = time.monotonic() - t0
        if elapsed > _NEO4J_TIMEOUT:
            logger.warning("LazyGraphRAG slow: concept_lookup('%s') took %.1fs", query, elapsed)

        return concepts
    except Exception as e:
        logger.error("LazyGraphRAG lookup error: %s", e)
        return []


def lazy_community_context(concept_name: str, limit: int = 8) -> Dict:
    """
    Get a concept's CO_OCCURS neighbors on demand (not cached).
    Returns the conceptual neighborhood around a topic.
    Bounded: always top-K by weight, never unbounded expansion.
    """
    driver = _get_neo4j()
    if not driver:
        return {}

    try:
        t0 = time.monotonic()
        with driver.session() as session:
            result = session.run("""
                MATCH (c:LazyGraphConcept {name: $name})-[r:CO_OCCURS]-(neighbor:LazyGraphConcept)
                WITH neighbor, r.weight AS weight, c.community_id AS src_community
                ORDER BY weight DESC
                LIMIT $limit
                RETURN collect({
                    name: neighbor.name,
                    weight: weight,
                    community: neighbor.community_id,
                    same_community: neighbor.community_id = src_community
                }) AS neighbors,
                src_community AS community
            """, name=concept_name, limit=limit)

            elapsed = time.monotonic() - t0
            if elapsed > _NEO4J_TIMEOUT:
                logger.warning("LazyGraphRAG slow: community_context('%s') took %.1fs", concept_name, elapsed)

            record = result.single()
            if record:
                return {
                    "concept": concept_name,
                    "community": record["community"],
                    "neighbors": record["neighbors"],
                }
    except Exception as e:
        logger.error("Community context error: %s", e)

    return {}


def lazy_multi_concept_context(keywords: List[str]) -> tuple:
    """
    Given keywords from user message, find matching LazyGraphConcepts
    and their top co-occurring neighbors.

    Returns:
        (hint_string, trace_dict) — hint for Larry, trace for logging.

    Uses cache for fast concept matching, on-demand for CO_OCCURS edges.
    """
    trace = {
        "keywords": keywords,
        "matched_concepts": [],
        "community_ids": [],
        "neighbors_fetched": 0,
        "cross_domain": False,
        "source": "lazy_graphrag",
    }

    cache = _get_cache()

    # Fast path: check cache for direct PWS term matches first
    direct_matches = []
    for kw in keywords[:4]:
        kw_title = kw.title()
        if kw_title in cache.pws_terms:
            cid = cache.concept_to_community.get(kw_title)
            direct_matches.append({"name": kw_title, "community": cid, "freq": 99, "score": 2.0})

    # Slow path: fulltext search for unmatched keywords
    all_concepts = list(direct_matches)
    matched_names = {m["name"].lower() for m in direct_matches}
    for kw in keywords[:4]:
        if kw.lower() not in matched_names and kw.title() not in matched_names:
            matches = lazy_concept_lookup(kw, limit=2)
            all_concepts.extend(matches)

    if not all_concepts:
        return "", trace

    # Deduplicate, keep highest-scoring
    seen = {}
    for c in all_concepts:
        name = c["name"]
        if name not in seen or c.get("score", 0) > seen[name].get("score", 0):
            seen[name] = c

    top_concepts = sorted(seen.values(), key=lambda x: x.get("freq", 0), reverse=True)[:3]
    trace["matched_concepts"] = [c["name"] for c in top_concepts]
    trace["community_ids"] = [c.get("community") for c in top_concepts]

    # Get CO_OCCURS neighbors for the top concept (on-demand, bounded to limit=6)
    neighbor_names = []
    if top_concepts:
        ctx = lazy_community_context(top_concepts[0]["name"], limit=6)
        neighbors = ctx.get("neighbors", [])
        neighbor_names = [n["name"] for n in neighbors if n.get("name")]
        trace["neighbors_fetched"] = len(neighbor_names)

    # Build hint
    concept_names = [c["name"] for c in top_concepts]
    parts = []
    if concept_names:
        parts.append(f"Key concepts: {', '.join(concept_names)}")
    if neighbor_names:
        parts.append(f"Related: {', '.join(neighbor_names[:5])}")

    # Cross-domain signal: concepts span multiple valid communities
    communities = set(
        c.get("community") for c in top_concepts
        if c.get("community") is not None and cache.is_valid_community(c.get("community"))
    )
    if len(communities) > 1:
        parts.append("(cross-domain topic)")
        trace["cross_domain"] = True

    # Community context: show what else is in the main community
    # Only use communities above the minimum size threshold
    if top_concepts and top_concepts[0].get("community") is not None:
        cid = top_concepts[0]["community"]
        if cache.is_valid_community(cid):
            community_peers = cache.community_top_concepts.get(cid, [])
            mentioned = set(concept_names + neighbor_names)
            extras = [p for p in community_peers if p not in mentioned][:3]
            if extras:
                parts.append(f"Also in this domain: {', '.join(extras)}")

    return ". ".join(parts), trace


def _extract_keywords(message: str) -> List[str]:
    """Extract meaningful keywords from user message for graph lookup."""
    # Remove common question prefixes
    cleaned = re.sub(
        r'^(what is|what are|what\'s|how does|how do|how can|explain|tell me about|describe|teach me|show me)\s+',
        '', message.lower()
    )
    # Remove stopwords
    stopwords = {
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'can', 'shall', 'to', 'of', 'in', 'for',
        'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through', 'during',
        'before', 'after', 'above', 'below', 'between', 'and', 'but', 'or',
        'not', 'no', 'so', 'if', 'than', 'too', 'very', 'just', 'about',
        'this', 'that', 'these', 'those', 'it', 'its', 'i', 'me', 'my',
        'we', 'our', 'you', 'your', 'they', 'them', 'their', 'some', 'any',
        'all', 'each', 'every', 'both', 'few', 'more', 'most', 'other',
        'up', 'out', 'also', 'use', 'using', 'used', 'think', 'want',
    }
    words = re.findall(r'\b[a-z][\w-]+\b', cleaned)
    keywords = [w for w in words if w not in stopwords and len(w) > 2]

    # Also check for multi-word PWS terms
    pws_terms = [
        'jobs to be done', 'trending to the absurd', 's-curve', 's curve',
        'reverse salient', 'red teaming', 'minto pyramid', 'problem worth solving',
        'six thinking hats', 'beautiful question', 'design thinking',
        'systems thinking', 'lean startup', 'customer discovery',
        'value proposition', 'first principles', 'ackoff pyramid',
    ]
    msg_lower = message.lower()
    for term in pws_terms:
        if term in msg_lower:
            keywords.insert(0, term)

    return keywords[:6]


# === Legacy Entity/Framework Layer ===

def get_concept_connections(concept: str) -> Dict:
    """
    Get a concept and its immediate connections from the entity layer.
    Returns hints, not full documents.
    """
    driver = _get_neo4j()
    if not driver:
        return {"concept": concept, "connections": []}

    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (n)
                WHERE toLower(n.name) CONTAINS toLower($concept)
                   OR toLower(n.description) CONTAINS toLower($concept)
                WITH n LIMIT 1

                OPTIONAL MATCH (n)-[r]-(related)
                WHERE related:Framework OR related:Concept OR related:Tool
                   OR related:ProcessStep OR related:Problem

                RETURN
                    n.name AS name,
                    labels(n)[0] AS type,
                    n.description AS description,
                    collect(DISTINCT {
                        relation: type(r),
                        name: related.name,
                        type: labels(related)[0]
                    })[0..6] AS connections
            """, concept=concept)

            record = result.single()
            if record:
                return {
                    "name": record["name"],
                    "type": record["type"],
                    "description": record["description"][:200] if record["description"] else None,
                    "connections": [c for c in record["connections"] if c.get("name")]
                }
    except Exception as e:
        logger.error("Graph lookup error: %s", e)

    return {"concept": concept, "connections": []}


def get_related_frameworks(topic: str, limit: int = 3) -> List[Dict]:
    """
    Find frameworks related to a topic.
    Returns names and one-liners, not full explanations.
    """
    driver = _get_neo4j()
    if not driver:
        return []

    try:
        with driver.session() as session:
            result = session.run("""
                CALL db.index.fulltext.queryNodes('framework_ecosystem_search', $topic)
                YIELD node, score
                WHERE score > 0.3
                RETURN
                    node.name AS name,
                    labels(node)[0] AS type,
                    node.description AS description,
                    score
                ORDER BY score DESC
                LIMIT $limit
            """, topic=topic, limit=limit)

            frameworks = []
            for record in result:
                desc = record["description"][:100] if record["description"] else ""
                frameworks.append({
                    "name": record["name"],
                    "type": record["type"],
                    "hint": desc,
                })

            if frameworks:
                return frameworks

            # Fallback: simple text match
            result = session.run("""
                MATCH (n:Framework)
                WHERE toLower(n.name) CONTAINS toLower($topic)
                   OR toLower(n.description) CONTAINS toLower($topic)
                RETURN n.name AS name, n.description AS description
                LIMIT $limit
            """, topic=topic, limit=limit)

            for record in result:
                desc = record["description"][:100] if record["description"] else ""
                frameworks.append({
                    "name": record["name"],
                    "type": "Framework",
                    "hint": desc,
                })

            return frameworks

    except Exception as e:
        logger.error("Framework lookup error: %s", e)
        return []


def get_problem_context(problem_description: str) -> Dict:
    """
    Given a problem description, find relevant problem types and approaches.
    """
    driver = _get_neo4j()
    if not driver:
        return {}

    try:
        with driver.session() as session:
            result = session.run("""
                CALL db.index.fulltext.queryNodes('entity_fulltext', $problem)
                YIELD node, score
                WITH node, score
                WHERE score > 0.3
                ORDER BY score DESC
                LIMIT 3

                OPTIONAL MATCH (node)-[:REQUIRES|HAS_TOOL|SOLVED_BY|HAS_METHOD]->(solution)

                RETURN
                    node.name AS problemType,
                    labels(node)[0] AS nodeType,
                    node.description AS description,
                    collect(DISTINCT solution.name)[0..3] AS approaches
            """, problem=problem_description)

            records = list(result)
            if records:
                record = records[0]
                return {
                    "problem_type": record["problemType"],
                    "description": record["description"][:150] if record["description"] else None,
                    "approaches": [a for a in record["approaches"] if a],
                }
    except Exception as e:
        logger.error("Problem context error: %s", e)

    return {}


# === Decision Logic ===

def should_retrieve(message: str, turn_count: int) -> bool:
    """
    Decide if this turn needs retrieval.
    Most conversational turns don't need it.
    """
    message_lower = message.lower()

    # Explicit knowledge requests - always retrieve
    explicit_triggers = [
        "what is", "what's", "what are",
        "explain", "tell me about", "describe",
        "how does", "how do", "how can",
        "walk me through", "give me a framework",
        "teach me", "show me",
    ]
    if any(phrase in message_lower for phrase in explicit_triggers):
        return True

    # Framework/methodology mentions after some conversation
    if turn_count >= 2:
        methodology_words = [
            "framework", "tool", "method", "approach",
            "technique", "model", "process", "methodology",
            "jtbd", "jobs to be done", "minto", "scqa",
            "s-curve", "s curve", "validation", "scorecard",
            "trending", "absurd", "reverse salient", "ackoff",
            "cynefin", "red team", "beautiful question",
            "problem worth solving", "innovation",
        ]
        if any(word in message_lower for word in methodology_words):
            return True

    # User asking for next steps or homework
    action_triggers = [
        "what should i", "what do i", "next step",
        "homework", "exercise", "assignment",
        "where do i start", "how do i begin",
    ]
    if any(phrase in message_lower for phrase in action_triggers):
        return True

    return False


def get_retrieval_type(message: str) -> str:
    """
    Determine what type of retrieval would be most helpful.

    Returns:
        'concept' - user asking about a specific concept
        'framework' - user needs a framework recommendation
        'problem' - user describing a problem situation
        'none' - no retrieval needed
    """
    message_lower = message.lower()

    if any(phrase in message_lower for phrase in ["what is", "what's", "explain", "tell me about"]):
        return "concept"

    if any(phrase in message_lower for phrase in ["framework", "approach", "method", "tool for"]):
        return "framework"

    problem_indicators = ["struggling with", "stuck on", "problem is", "challenge is", "issue is"]
    if any(phrase in message_lower for phrase in problem_indicators):
        return "problem"

    return "none"


# === Main Interface ===

def light_context(query: str, context_type: str = "auto") -> tuple:
    """
    Get light context for a query.
    Returns 2-3 sentences max, not a lecture.

    Uses LazyGraphRAG first (fast, broad coverage), then falls back
    to the entity/framework layer for structured relationships.

    Returns:
        (hint_string, trace_dict) for traceability.
    """
    t0 = time.monotonic()

    if context_type == "auto":
        context_type = get_retrieval_type(query)

    trace = {
        "query": query[:100],
        "retrieval_type": context_type,
        "lazy_trace": None,
        "entity_layer_used": False,
        "total_ms": 0,
    }

    # Layer 1: LazyGraphRAG — keyword-based concept co-occurrence
    keywords = _extract_keywords(query)
    lazy_hint = ""
    if keywords:
        lazy_hint, lazy_trace = lazy_multi_concept_context(keywords)
        trace["lazy_trace"] = lazy_trace

    # Layer 2: Entity/Framework layer — structured relationships
    entity_hint = ""
    if context_type == "concept":
        connections = get_concept_connections(query)
        if connections.get("connections"):
            related = [c["name"] for c in connections["connections"][:4]]
            name = connections.get("name", query)
            entity_hint = f"{name} connects to: {', '.join(related)}"
            trace["entity_layer_used"] = True
        elif connections.get("description"):
            entity_hint = connections["description"]
            trace["entity_layer_used"] = True

    elif context_type == "framework":
        frameworks = get_related_frameworks(query, limit=2)
        if frameworks:
            hints = [f["name"] for f in frameworks]
            entity_hint = f"Relevant frameworks: {', '.join(hints)}"
            trace["entity_layer_used"] = True

    elif context_type == "problem":
        context = get_problem_context(query)
        if context.get("problem_type"):
            entity_hint = f"This sounds like: {context['problem_type']}"
            if context.get("approaches"):
                entity_hint += f". Consider: {', '.join(context['approaches'][:2])}"
            trace["entity_layer_used"] = True

    elapsed_ms = (time.monotonic() - t0) * 1000
    trace["total_ms"] = round(elapsed_ms, 1)

    # Merge both layers
    if lazy_hint and entity_hint:
        hint = f"{lazy_hint}. {entity_hint}"
    else:
        hint = lazy_hint or entity_hint or ""

    return hint, trace


_BOT_HINT_PREFIX: Dict[str, str] = {
    "larry": "[GraphRAG context for larry - use to ask better questions, not to lecture: ",
    "tta": "[GraphRAG context for tta - use to guide trend exploration: ",
    "jtbd": "[GraphRAG context for jtbd - use to deepen customer job analysis: ",
    "scurve": "[GraphRAG context for scurve - use to ground technology timing: ",
    "redteam": "[GraphRAG context for redteam - use to sharpen assumption challenges: ",
    "ackoff": "[GraphRAG context for ackoff - use to ground DIKW validation: ",
    "bono": "[GraphRAG context for bono - use to enrich perspective analysis: ",
}


def enrich_for_bot(user_message: str, turn_count: int, bot_id: str = "larry") -> Optional[str]:
    """
    Enrich any bot's context with graph hints.

    Args:
        user_message: What the user said
        turn_count: How many turns into the conversation
        bot_id: Which bot is active (e.g. 'larry', 'tta', 'jtbd')

    Returns:
        Context hint string with bot-specific prefix if helpful, None otherwise
    """
    if not should_retrieve(user_message, turn_count):
        return None

    try:
        t0 = time.monotonic()
        hint, trace = light_context(user_message)
        elapsed = time.monotonic() - t0

        if hint:
            logger.info(
                "GraphRAG enrichment [%dms] bot=%s: concepts=%s, communities=%s, cross_domain=%s, entity_layer=%s",
                trace.get("total_ms", 0),
                bot_id,
                trace.get("lazy_trace", {}).get("matched_concepts", []) if trace.get("lazy_trace") else [],
                trace.get("lazy_trace", {}).get("community_ids", []) if trace.get("lazy_trace") else [],
                trace.get("lazy_trace", {}).get("cross_domain", False) if trace.get("lazy_trace") else False,
                trace.get("entity_layer_used", False),
            )
            prefix = _BOT_HINT_PREFIX.get(bot_id, f"[GraphRAG context for {bot_id} - ")
            return f"{prefix}{hint}]"

        if elapsed > _NEO4J_TIMEOUT:
            logger.warning("GraphRAG timeout: %.1fs for '%s...'", elapsed, user_message[:50])

    except Exception as e:
        logger.error("GraphRAG enrichment failed (graceful fallback): %s", e)

    return None


def enrich_for_larry(user_message: str, turn_count: int) -> Optional[str]:
    """Backward-compatible wrapper around enrich_for_bot."""
    return enrich_for_bot(user_message, turn_count, bot_id="larry")
