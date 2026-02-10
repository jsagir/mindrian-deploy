"""
PWS Navigator - Cross-Domain Bridge Detection
==============================================

Inspired by Austin Granmoe's "Large Scale Networks for Idea Generation":
uses knowledge graph topology to find innovation bridges between domains.

Core idea: concepts that connect different communities (modularity classes)
are the most fertile ground for cross-domain innovation.

Functions:
- explore_domain(query) - Map a query to domains and related concepts
- find_bridges(domain1, domain2) - Find concepts bridging two domains
- cross_domain_discovery(query) - Full pipeline: query → domains → bridges → opportunities
- get_domain_landscape() - Overview of all domains (for demo)

Design principles (same as graphrag_lite):
- Bounded queries (always LIMIT, never unbounded)
- Circuit breaker: 5s max per Neo4j call
- Graceful degradation if Neo4j unavailable
- Memory-safe for 512MB Render instances
"""

import os
import time
import logging
from typing import Optional, Dict, List, Tuple

logger = logging.getLogger("pws_navigator")

_NEO4J_TIMEOUT = 5.0


def _get_neo4j():
    """Reuse graphrag_lite's Neo4j driver."""
    try:
        from tools.graphrag_lite import _get_neo4j as get_driver
        return get_driver()
    except ImportError:
        from neo4j import GraphDatabase
        uri = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USER")
        password = os.getenv("NEO4J_PASSWORD")
        if all([uri, user, password]):
            return GraphDatabase.driver(uri, auth=(user, password))
    return None


def _run_cypher(query: str, params: dict = None, timeout: float = _NEO4J_TIMEOUT) -> List[Dict]:
    """Execute Cypher with timeout guard."""
    driver = _get_neo4j()
    if not driver:
        return []

    params = params or {}
    t0 = time.monotonic()
    try:
        with driver.session() as session:
            records = session.run(query, params)
            results = [dict(r) for r in records]
        elapsed = time.monotonic() - t0
        if elapsed > timeout:
            logger.warning("PWS Navigator slow query (%.1fs): %s", elapsed, query[:80])
        return results
    except Exception as e:
        logger.error("PWS Navigator Cypher error: %s", e)
        return []


# ═══════════════════════════════════════════════════════════════════════════════
# Domain Exploration
# ═══════════════════════════════════════════════════════════════════════════════

def explore_domain(query: str, limit: int = 10) -> Dict:
    """
    Map a user query to domains and their key concepts.

    Returns:
        {
            "query": str,
            "domains": [{"name": str, "concept_count": int, "top_concepts": [...]}],
            "matched_concepts": [{"name": str, "community": int, "freq": int}],
        }
    """
    result = {"query": query, "domains": [], "matched_concepts": []}

    # Step 1: Find matching concepts via fulltext
    concepts = _run_cypher("""
        CALL db.index.fulltext.queryNodes('lazy_concept_search', $q)
        YIELD node, score
        WHERE score > 0.3
        RETURN node.name AS name,
               node.community_id AS community,
               node.chunk_count AS freq,
               node.degree AS degree,
               score
        ORDER BY score DESC
        LIMIT $limit
    """, {"q": query, "limit": limit})

    if not concepts:
        # Fallback: CONTAINS match
        concepts = _run_cypher("""
            MATCH (c:LazyGraphConcept)
            WHERE toLower(c.name) CONTAINS toLower($q)
            RETURN c.name AS name,
                   c.community_id AS community,
                   c.chunk_count AS freq,
                   c.degree AS degree,
                   1.0 AS score
            ORDER BY c.chunk_count DESC
            LIMIT $limit
        """, {"q": query, "limit": limit})

    result["matched_concepts"] = concepts

    # Step 2: Get community info for matched concepts
    communities = set(c["community"] for c in concepts if c.get("community") is not None)
    if communities:
        domain_info = _run_cypher("""
            MATCH (c:LazyGraphConcept)
            WHERE c.community_id IN $cids
            WITH c.community_id AS cid, c.name AS name, c.chunk_count AS freq
            ORDER BY cid, freq DESC
            WITH cid, collect(name) AS all_names, count(*) AS size
            RETURN cid AS community_id, size AS concept_count, all_names[0..8] AS top_concepts
            ORDER BY size DESC
        """, {"cids": list(communities)})

        result["domains"] = domain_info

    return result


def get_domain_landscape(min_size: int = 5, limit: int = 20) -> List[Dict]:
    """
    Overview of all communities/domains in the graph.
    Great for demos - shows the breadth of the knowledge base.

    Returns list of domains with their top concepts and sizes.
    """
    return _run_cypher("""
        MATCH (c:LazyGraphConcept)
        WHERE c.community_id IS NOT NULL
        WITH c.community_id AS cid, c.name AS name, c.chunk_count AS freq
        ORDER BY cid, freq DESC
        WITH cid, collect(name) AS all_names, count(*) AS size
        WHERE size >= $min_size
        RETURN cid AS community_id,
               size AS concept_count,
               all_names[0..6] AS top_concepts,
               all_names[0] AS domain_label
        ORDER BY size DESC
        LIMIT $limit
    """, {"min_size": min_size, "limit": limit})


# ═══════════════════════════════════════════════════════════════════════════════
# Bridge Detection (the core innovation from Granmoe's paper)
# ═══════════════════════════════════════════════════════════════════════════════

def find_bridges(community1: int, community2: int, limit: int = 10) -> List[Dict]:
    """
    Find concepts that bridge two communities (cross-domain connectors).

    These are the "interclass edges" from Granmoe's paper - concepts that
    have strong CO_OCCURS relationships with concepts in BOTH communities.
    These bridging nodes are the most fertile ground for innovation.

    Returns list of bridge concepts with their connection strengths.
    """
    return _run_cypher("""
        MATCH (a:LazyGraphConcept)-[r1:CO_OCCURS]-(bridge:LazyGraphConcept)-[r2:CO_OCCURS]-(b:LazyGraphConcept)
        WHERE a.community_id = $cid1
          AND b.community_id = $cid2
          AND bridge.community_id IN [$cid1, $cid2]
        WITH bridge,
             sum(CASE WHEN a.community_id = $cid1 THEN r1.weight ELSE 0 END) AS strength_to_c1,
             sum(CASE WHEN b.community_id = $cid2 THEN r2.weight ELSE 0 END) AS strength_to_c2,
             collect(DISTINCT a.name)[0..3] AS c1_connections,
             collect(DISTINCT b.name)[0..3] AS c2_connections
        WITH bridge, strength_to_c1, strength_to_c2, c1_connections, c2_connections,
             (strength_to_c1 * strength_to_c2) AS bridge_score
        WHERE bridge_score > 0
        RETURN bridge.name AS name,
               bridge.community_id AS home_community,
               bridge.degree AS degree,
               bridge_score,
               strength_to_c1,
               strength_to_c2,
               c1_connections,
               c2_connections
        ORDER BY bridge_score DESC
        LIMIT $limit
    """, {"cid1": community1, "cid2": community2, "limit": limit})


def find_bridges_by_name(domain1_query: str, domain2_query: str, limit: int = 8) -> Dict:
    """
    User-friendly bridge detection: takes two topic names, resolves to communities,
    then finds bridges.

    Returns:
        {
            "domain1": {"query": str, "community": int, "top_concepts": [...]},
            "domain2": {"query": str, "community": int, "top_concepts": [...]},
            "bridges": [{"name": str, "bridge_score": float, ...}],
            "innovation_prompts": [str]  -- generated questions for exploration
        }
    """
    result = {
        "domain1": {"query": domain1_query},
        "domain2": {"query": domain2_query},
        "bridges": [],
        "innovation_prompts": [],
    }

    # Resolve domain1
    d1_concepts = _run_cypher("""
        CALL db.index.fulltext.queryNodes('lazy_concept_search', $q)
        YIELD node, score
        WHERE score > 0.3 AND node.community_id IS NOT NULL
        RETURN node.name AS name, node.community_id AS community, score
        ORDER BY score DESC
        LIMIT 3
    """, {"q": domain1_query})

    # Resolve domain2
    d2_concepts = _run_cypher("""
        CALL db.index.fulltext.queryNodes('lazy_concept_search', $q)
        YIELD node, score
        WHERE score > 0.3 AND node.community_id IS NOT NULL
        RETURN node.name AS name, node.community_id AS community, score
        ORDER BY score DESC
        LIMIT 3
    """, {"q": domain2_query})

    if not d1_concepts or not d2_concepts:
        return result

    cid1 = d1_concepts[0]["community"]
    cid2 = d2_concepts[0]["community"]

    # Get community context
    for domain_key, cid in [("domain1", cid1), ("domain2", cid2)]:
        ctx = _run_cypher("""
            MATCH (c:LazyGraphConcept {community_id: $cid})
            RETURN c.name AS name, c.chunk_count AS freq
            ORDER BY c.chunk_count DESC
            LIMIT 6
        """, {"cid": cid})
        result[domain_key]["community"] = cid
        result[domain_key]["top_concepts"] = [c["name"] for c in ctx]

    if cid1 == cid2:
        result["bridges"] = [{"note": "Same community - these topics are already closely related"}]
        return result

    # Find bridges
    bridges = find_bridges(cid1, cid2, limit=limit)
    result["bridges"] = bridges

    # Generate innovation prompts from bridges
    for bridge in bridges[:3]:
        name = bridge["name"]
        c1_links = bridge.get("c1_connections", [])
        c2_links = bridge.get("c2_connections", [])
        d1_label = result["domain1"]["top_concepts"][0] if result["domain1"]["top_concepts"] else domain1_query
        d2_label = result["domain2"]["top_concepts"][0] if result["domain2"]["top_concepts"] else domain2_query

        prompt = (
            f"How might '{name}' (which connects to {', '.join(c1_links[:2])} in {d1_label}'s domain "
            f"and {', '.join(c2_links[:2])} in {d2_label}'s domain) inspire a new approach?"
        )
        result["innovation_prompts"].append(prompt)

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# Cross-Domain Discovery (Full Pipeline)
# ═══════════════════════════════════════════════════════════════════════════════

def cross_domain_discovery(query: str, max_domains: int = 4, max_bridges: int = 5) -> Dict:
    """
    Full discovery pipeline: given a topic, find what OTHER domains it connects to
    and surface the bridge concepts for innovation.

    This is the "PWS Navigator" feature - starting from a user's topic,
    it discovers unexpected cross-domain connections.

    Returns:
        {
            "query": str,
            "home_domain": {"community": int, "top_concepts": [...]},
            "cross_domain_bridges": [
                {
                    "target_domain": {"community": int, "top_concepts": [...]},
                    "bridges": [{"name": str, ...}],
                    "innovation_prompts": [str]
                }
            ],
            "reverse_salients": [{"name": str, ...}],  -- constraints/bottlenecks
        }
    """
    result = {
        "query": query,
        "home_domain": {},
        "cross_domain_bridges": [],
        "reverse_salients": [],
    }

    # Step 1: Find the user's starting concept and its home community
    home_concepts = _run_cypher("""
        CALL db.index.fulltext.queryNodes('lazy_concept_search', $q)
        YIELD node, score
        WHERE score > 0.3 AND node.community_id IS NOT NULL
        RETURN node.name AS name, node.community_id AS community,
               node.chunk_count AS freq, node.degree AS degree, score
        ORDER BY score DESC
        LIMIT 3
    """, {"q": query})

    if not home_concepts:
        return result

    home_cid = home_concepts[0]["community"]

    # Get home domain context
    home_ctx = _run_cypher("""
        MATCH (c:LazyGraphConcept {community_id: $cid})
        RETURN c.name AS name, c.chunk_count AS freq
        ORDER BY c.chunk_count DESC
        LIMIT 8
    """, {"cid": home_cid})

    result["home_domain"] = {
        "community": home_cid,
        "matched_concept": home_concepts[0]["name"],
        "top_concepts": [c["name"] for c in home_ctx],
    }

    # Step 2: Find concepts that bridge OUT from this community to others
    cross_links = _run_cypher("""
        MATCH (home:LazyGraphConcept {community_id: $cid})-[r:CO_OCCURS]-(other:LazyGraphConcept)
        WHERE other.community_id IS NOT NULL
          AND other.community_id <> $cid
        WITH other.community_id AS target_cid,
             count(*) AS edge_count,
             sum(r.weight) AS total_weight,
             collect(DISTINCT other.name)[0..4] AS sample_concepts,
             collect(DISTINCT home.name)[0..4] AS home_connectors
        WHERE edge_count >= 2
        RETURN target_cid, edge_count, total_weight, sample_concepts, home_connectors
        ORDER BY total_weight DESC
        LIMIT $max_domains
    """, {"cid": home_cid, "max_domains": max_domains})

    # Step 3: For each cross-domain connection, find the best bridges
    for link in cross_links:
        target_cid = link["target_cid"]

        # Get target domain context
        target_ctx = _run_cypher("""
            MATCH (c:LazyGraphConcept {community_id: $cid})
            RETURN c.name AS name, c.chunk_count AS freq
            ORDER BY c.chunk_count DESC
            LIMIT 6
        """, {"cid": target_cid})

        target_label = target_ctx[0]["name"] if target_ctx else f"Community {target_cid}"

        # Find the actual bridge concepts
        bridges = find_bridges(home_cid, target_cid, limit=max_bridges)

        # Generate innovation prompts
        prompts = []
        home_label = result["home_domain"]["top_concepts"][0] if result["home_domain"]["top_concepts"] else query
        for b in bridges[:2]:
            c1 = b.get("c1_connections", [])
            c2 = b.get("c2_connections", [])
            prompts.append(
                f"How might '{b['name']}' connect {home_label} with {target_label}? "
                f"(It links {', '.join(c1[:2])} ↔ {', '.join(c2[:2])})"
            )

        result["cross_domain_bridges"].append({
            "target_domain": {
                "community": target_cid,
                "label": target_label,
                "top_concepts": [c["name"] for c in target_ctx],
                "edge_count": link["edge_count"],
                "total_weight": link["total_weight"],
            },
            "bridges": bridges,
            "home_connectors": link["home_connectors"],
            "target_connectors": link["sample_concepts"],
            "innovation_prompts": prompts,
        })

    # Step 4: Find reverse salients (bottlenecks/constraints) near the query
    result["reverse_salients"] = _run_cypher("""
        MATCH (rs:ReverseSalient)
        WHERE toLower(rs.name) CONTAINS toLower($q)
           OR toLower(rs.description) CONTAINS toLower($q)
        RETURN rs.name AS name, rs.description AS description
        LIMIT 5
    """, {"q": query})

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# Formatting for Chat Display
# ═══════════════════════════════════════════════════════════════════════════════

def format_discovery_as_markdown(discovery: Dict) -> str:
    """Format cross_domain_discovery output as rich Markdown for Chainlit."""
    if not discovery.get("home_domain") or not discovery.get("home_domain", {}).get("top_concepts"):
        return f"No graph data found for **{discovery.get('query', '?')}**. Try a different topic."

    lines = []
    home = discovery["home_domain"]
    query = discovery["query"]

    lines.append(f"## PWS Navigator: {query}")
    lines.append("")
    lines.append(f"**Home Domain** (Community {home['community']}): "
                 f"{', '.join(home['top_concepts'][:5])}")
    lines.append("")

    bridges = discovery.get("cross_domain_bridges", [])
    if bridges:
        lines.append(f"### Cross-Domain Connections ({len(bridges)} domains found)")
        lines.append("")

        for i, xd in enumerate(bridges, 1):
            target = xd["target_domain"]
            lines.append(f"#### {i}. {target['label']}")
            lines.append(f"*{target['edge_count']} connections, "
                         f"strength: {target['total_weight']:.0f}*")
            lines.append(f"Key concepts: {', '.join(target['top_concepts'][:4])}")
            lines.append("")

            bridge_list = xd.get("bridges", [])
            if bridge_list:
                lines.append("**Bridge Concepts:**")
                for b in bridge_list[:3]:
                    c1 = b.get("c1_connections", [])
                    c2 = b.get("c2_connections", [])
                    lines.append(f"- **{b['name']}** (score: {b.get('bridge_score', 0):.0f}) "
                                 f"→ connects {', '.join(c1[:2])} ↔ {', '.join(c2[:2])}")
                lines.append("")

            prompts = xd.get("innovation_prompts", [])
            if prompts:
                lines.append("**Innovation Questions:**")
                for p in prompts:
                    lines.append(f"> {p}")
                lines.append("")
    else:
        lines.append("*No strong cross-domain connections found. "
                     "This topic may be well-contained within a single domain.*")
        lines.append("")

    rs = discovery.get("reverse_salients", [])
    if rs:
        lines.append("### Bottlenecks & Constraints")
        for r in rs:
            desc = r.get("description", "")[:120]
            lines.append(f"- **{r['name']}**: {desc}")
        lines.append("")

    return "\n".join(lines)


def format_landscape_as_markdown(domains: List[Dict]) -> str:
    """Format domain landscape for demo display."""
    if not domains:
        return "No domains found in the knowledge graph."

    lines = ["## PWS Knowledge Landscape", ""]
    lines.append(f"**{len(domains)} active domains** across the innovation knowledge base:")
    lines.append("")

    for i, d in enumerate(domains, 1):
        concepts = d.get("top_concepts", [])
        label = concepts[0] if concepts else f"Domain {d['community_id']}"
        count = d.get("concept_count", 0)
        others = ", ".join(concepts[1:4]) if len(concepts) > 1 else ""
        lines.append(f"{i}. **{label}** ({count} concepts) — {others}")

    lines.append("")
    lines.append("*Click 'Explore Bridges' to find cross-domain innovation opportunities.*")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# Mermaid Diagram Generation
# ═══════════════════════════════════════════════════════════════════════════════

def discovery_to_mermaid(discovery: Dict) -> str:
    """Generate a Mermaid mindmap from cross-domain discovery results."""
    home = discovery.get("home_domain", {})
    query = discovery.get("query", "Topic")
    bridges = discovery.get("cross_domain_bridges", [])

    if not home.get("top_concepts"):
        return ""

    # Sanitize text for Mermaid (no special chars)
    def safe(text: str) -> str:
        return text.replace("(", "").replace(")", "").replace("[", "").replace("]", "").replace('"', "'").replace("\n", " ")[:40]

    lines = ["mindmap", f"  root(({safe(query)}))", f"    {safe(home['top_concepts'][0])}"]

    for c in home["top_concepts"][1:4]:
        lines.append(f"      {safe(c)}")

    for xd in bridges[:3]:
        target = xd["target_domain"]
        label = safe(target.get("label", "Unknown"))
        lines.append(f"    {label}")

        for b in xd.get("bridges", [])[:2]:
            lines.append(f"      {safe(b['name'])}")

        for c in target.get("top_concepts", [])[:2]:
            lines.append(f"      {safe(c)}")

    return "\n".join(lines)
