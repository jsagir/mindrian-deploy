"""
LightRAG-Enhanced Bank of Opportunities
=======================================

Integrates the Bank of Opportunities with LightRAG for:
1. Entity extraction from opportunities (domains, relevancy)
2. Knowledge graph relationships via LightRAG API
3. Per-user opportunity linking (via user_lazygraph.py)

Graph Schema:
  (:Opportunity {id, name, problem, value_potential})
      -[:IN_DOMAIN]-> (:Domain {name})
      -[:RELEVANT_TO]-> (:Topic {name})
      -[:FOUND_BY]-> (:User {id})
      -[:DISCOVERED_IN]-> (:Session {id})
      -[:USED_FRAMEWORK]-> (:Framework {name})
      -[:CO_OCCURS_WITH]-> (:Opportunity {id})  # LightRAG relationship

Uses LightRAG at mondrian-ts.onrender.com (same Neo4j as Mindrian)
"""

import os
import json
import hashlib
import logging
import requests
from typing import Optional, Dict, List, Any
from datetime import datetime
from dataclasses import dataclass, asdict, field

logger = logging.getLogger("opportunity_bank_lightrag")

# === Configuration ===
LIGHTRAG_URL = os.getenv("LIGHTRAG_URL", "https://mondrian-ts.onrender.com")
LIGHTRAG_USERNAME = os.getenv("LIGHTRAG_USERNAME", "jsagir")
LIGHTRAG_PASSWORD = os.getenv("LIGHTRAG_PASSWORD", "12345678")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Import existing opportunity bank
from tools.opportunity_bank import (
    Opportunity,
    OpportunityType,
    ValuePotential,
    store_opportunity,
    extract_opportunities,
    generate_opportunity_id,
    get_supabase_client,
)

# Import user lazygraph
from tools.user_lazygraph import (
    _get_neo4j,
    store_insight,
    UserInsight,
)


# === LightRAG Session ===

_lightrag_token = None
_lightrag_session = None


def _get_lightrag_session() -> Optional[requests.Session]:
    """Get authenticated LightRAG session."""
    global _lightrag_token, _lightrag_session

    try:
        if _lightrag_session is None:
            _lightrag_session = requests.Session()

        if not _lightrag_token:
            resp = requests.post(
                f"{LIGHTRAG_URL}/login",
                data={"username": LIGHTRAG_USERNAME, "password": LIGHTRAG_PASSWORD},
                timeout=15
            )
            if resp.status_code == 200:
                _lightrag_token = resp.json().get("access_token")
                _lightrag_session.headers.update({"Authorization": f"Bearer {_lightrag_token}"})
            else:
                logger.warning(f"LightRAG login failed: {resp.status_code}")
                return None

        return _lightrag_session

    except Exception as e:
        logger.warning(f"LightRAG session error: {e}")
        return None


# === LightRAG Entity Operations ===

def push_opportunity_to_lightrag(opportunity: Opportunity) -> bool:
    """
    Push opportunity as entity to LightRAG graph.

    Creates:
    - Opportunity entity with PWS properties
    - Domain relationship
    - Framework relationships
    """
    session = _get_lightrag_session()
    if not session:
        return False

    try:
        # Create Opportunity entity
        entity_data = {
            "entity_name": opportunity.name,
            "entity_data": {
                "entity_type": "OPPORTUNITY",
                "description": opportunity.description[:500] if opportunity.description else "",
                "problem": opportunity.problem[:300] if opportunity.problem else "",
                "value_potential": opportunity.value_potential,
                "domain": opportunity.domain,
                "job_to_be_done": opportunity.job_to_be_done[:200] if opportunity.job_to_be_done else "",
                "created_at": opportunity.created_at,
                "created_by": opportunity.created_by,
            }
        }

        resp = session.post(
            f"{LIGHTRAG_URL}/graph/entity/create",
            json=entity_data,
            timeout=15
        )

        if resp.status_code not in [200, 409]:  # 409 = already exists
            logger.warning(f"LightRAG entity create failed: {resp.status_code} - {resp.text[:100]}")
            return False

        # Create Domain entity and relationship
        if opportunity.domain:
            # Create domain entity
            session.post(
                f"{LIGHTRAG_URL}/graph/entity/create",
                json={
                    "entity_name": opportunity.domain,
                    "entity_data": {"entity_type": "DOMAIN", "description": f"Domain: {opportunity.domain}"}
                },
                timeout=10
            )

            # Create IN_DOMAIN relationship
            session.post(
                f"{LIGHTRAG_URL}/graph/relation/create",
                json={
                    "source_entity": opportunity.name,
                    "target_entity": opportunity.domain,
                    "relation_data": {
                        "description": "is in domain",
                        "keywords": "domain, category, field",
                        "weight": 1.0,
                    }
                },
                timeout=10
            )

        # Create Framework relationships
        for framework in opportunity.frameworks_applied:
            session.post(
                f"{LIGHTRAG_URL}/graph/entity/create",
                json={
                    "entity_name": framework,
                    "entity_data": {"entity_type": "FRAMEWORK", "description": f"PWS Framework: {framework}"}
                },
                timeout=10
            )

            session.post(
                f"{LIGHTRAG_URL}/graph/relation/create",
                json={
                    "source_entity": opportunity.name,
                    "target_entity": framework,
                    "relation_data": {
                        "description": "used framework",
                        "keywords": "methodology, analysis",
                        "weight": 0.8,
                    }
                },
                timeout=10
            )

        logger.info(f"LightRAG: Pushed opportunity '{opportunity.name}' with domain '{opportunity.domain}'")
        return True

    except Exception as e:
        logger.error(f"LightRAG push error: {e}")
        return False


def link_opportunities_in_lightrag(opp1_name: str, opp2_name: str, relevancy: float = 0.5) -> bool:
    """
    Create CO_OCCURS relationship between opportunities in LightRAG.

    This enables "related opportunities" queries.
    """
    session = _get_lightrag_session()
    if not session:
        return False

    try:
        resp = session.post(
            f"{LIGHTRAG_URL}/graph/relation/create",
            json={
                "source_entity": opp1_name,
                "target_entity": opp2_name,
                "relation_data": {
                    "description": "co-occurs with",
                    "keywords": "related, similar, connected",
                    "weight": relevancy,
                }
            },
            timeout=10
        )

        return resp.status_code in [200, 409]

    except Exception as e:
        logger.warning(f"LightRAG link error: {e}")
        return False


def query_related_opportunities_lightrag(opportunity_name: str, limit: int = 5) -> List[Dict]:
    """
    Query LightRAG for opportunities related to a given one.

    Uses LightRAG's graph traversal to find connected opportunities.
    """
    session = _get_lightrag_session()
    if not session:
        return []

    try:
        # Query LightRAG graph
        resp = session.get(
            f"{LIGHTRAG_URL}/graph/entity/neighbors",
            params={"entity_name": opportunity_name, "limit": limit},
            timeout=10
        )

        if resp.status_code != 200:
            return []

        neighbors = resp.json()
        opportunities = [
            n for n in neighbors
            if n.get("entity_type") == "OPPORTUNITY"
        ]

        return opportunities

    except Exception as e:
        logger.warning(f"LightRAG query error: {e}")
        return []


def query_opportunities_by_domain_lightrag(domain: str, limit: int = 10) -> List[Dict]:
    """
    Query LightRAG for all opportunities in a domain.
    """
    session = _get_lightrag_session()
    if not session:
        return []

    try:
        # Use LightRAG query API
        resp = session.post(
            f"{LIGHTRAG_URL}/query",
            json={
                "query": f"opportunities in {domain} domain",
                "mode": "local",  # Fast local search
            },
            timeout=15
        )

        if resp.status_code != 200:
            return []

        result = resp.json()
        # Parse response for opportunity entities
        return result.get("entities", [])[:limit]

    except Exception as e:
        logger.warning(f"LightRAG domain query error: {e}")
        return []


# === Enhanced Extraction with Domain/Relevancy ===

DOMAIN_RELEVANCY_PROMPT = """Analyze this opportunity and extract domain/relevancy information.

OPPORTUNITY:
Name: {name}
Description: {description}
Problem: {problem}

Return JSON:
{{
  "primary_domain": "Main industry or field (e.g., Healthcare, Education, FinTech)",
  "secondary_domains": ["Other relevant domains"],
  "topics": ["Specific topics this relates to"],
  "relevancy_keywords": ["Keywords for semantic matching"],
  "target_industries": ["Industries that would benefit"],
  "related_frameworks": ["PWS frameworks that apply (TTA, JTBD, S-Curve, etc.)"]
}}

Be specific with domains (not just "Technology" but "EdTech" or "HealthTech").
"""


async def extract_domain_relevancy(opportunity: Opportunity) -> Dict[str, Any]:
    """
    Use Gemini to extract detailed domain and relevancy info for an opportunity.
    """
    if not GOOGLE_API_KEY:
        return {}

    try:
        from google import genai

        client = genai.Client(api_key=GOOGLE_API_KEY)
        prompt = DOMAIN_RELEVANCY_PROMPT.format(
            name=opportunity.name,
            description=opportunity.description,
            problem=opportunity.problem,
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "temperature": 0.1,
            }
        )

        return json.loads(response.text)

    except Exception as e:
        logger.warning(f"Domain extraction error: {e}")
        return {}


# === Neo4j Direct Storage (Enhanced) ===

async def store_opportunity_with_lightrag(
    opportunity: Opportunity,
    user_id: str = "",
    session_id: str = ""
) -> Dict[str, Any]:
    """
    Store opportunity in all backends with LightRAG enhancement.

    1. Extract domain/relevancy using Gemini
    2. Store in Supabase table + Neo4j (existing)
    3. Push to LightRAG graph
    4. Link to user graph if user_id provided
    5. Create relevancy relationships

    Returns status dict.
    """
    result = {
        "supabase": False,
        "neo4j": False,
        "lightrag": False,
        "user_linked": False,
        "domain_extracted": False,
        "relevancy_links": 0,
    }

    # Step 1: Extract domain/relevancy
    domain_info = await extract_domain_relevancy(opportunity)
    if domain_info:
        result["domain_extracted"] = True

        # Update opportunity with extracted info
        if domain_info.get("primary_domain") and not opportunity.domain:
            opportunity.domain = domain_info["primary_domain"]

        if domain_info.get("relevancy_keywords"):
            opportunity.tags = list(set(opportunity.tags + domain_info["relevancy_keywords"]))

        if domain_info.get("related_frameworks"):
            opportunity.frameworks_applied = list(set(
                opportunity.frameworks_applied + domain_info["related_frameworks"]
            ))

    # Step 2: Store in existing backends (Supabase + Neo4j)
    storage_result = await store_opportunity(opportunity, generate_embedding=True)
    result["supabase"] = bool(storage_result.get("supabase_table"))
    result["neo4j"] = storage_result.get("neo4j", False)

    # Step 3: Push to LightRAG
    lightrag_ok = push_opportunity_to_lightrag(opportunity)
    result["lightrag"] = lightrag_ok

    # Step 4: Link to user graph
    if user_id and session_id:
        driver = _get_neo4j()
        if driver:
            try:
                with driver.session() as db_session:
                    db_session.run("""
                        MATCH (u:User {id: $user_id})
                        MATCH (o:Opportunity {id: $opp_id})
                        MERGE (u)-[:FOUND_OPPORTUNITY]->(o)

                        WITH o
                        MATCH (s:Session {id: $session_id})
                        MERGE (o)-[:DISCOVERED_IN]->(s)
                    """, {
                        "user_id": user_id,
                        "opp_id": opportunity.id,
                        "session_id": session_id,
                    })

                result["user_linked"] = True

                # Also store as insight for the user
                await store_insight(user_id, UserInsight(
                    id="",
                    text=f"Opportunity discovered: {opportunity.name}",
                    source="opportunity_bank",
                    confidence=opportunity.extraction_confidence,
                    session_id=session_id,
                ))

            except Exception as e:
                logger.warning(f"User link error: {e}")

    # Step 5: Create relevancy links in LightRAG
    if lightrag_ok and domain_info.get("topics"):
        for topic in domain_info["topics"][:5]:
            # Create topic entity
            session = _get_lightrag_session()
            if session:
                session.post(
                    f"{LIGHTRAG_URL}/graph/entity/create",
                    json={
                        "entity_name": topic,
                        "entity_data": {"entity_type": "TOPIC", "description": f"Topic: {topic}"}
                    },
                    timeout=10
                )

                # Create RELEVANT_TO relationship
                resp = session.post(
                    f"{LIGHTRAG_URL}/graph/relation/create",
                    json={
                        "source_entity": opportunity.name,
                        "target_entity": topic,
                        "relation_data": {
                            "description": "is relevant to",
                            "keywords": "relevancy, topic, related",
                            "weight": 0.7,
                        }
                    },
                    timeout=10
                )

                if resp.status_code in [200, 409]:
                    result["relevancy_links"] += 1

    logger.info(f"Stored opportunity '{opportunity.name}' - {result}")
    return result


# === Query Functions ===

async def search_opportunities_by_relevancy(
    query: str,
    limit: int = 10
) -> List[Dict]:
    """
    Search opportunities using LightRAG's semantic search.

    Returns opportunities ranked by relevancy to the query.
    """
    session = _get_lightrag_session()
    if not session:
        # Fallback to existing search
        from tools.opportunity_bank import search_opportunities
        return await search_opportunities(query, limit)

    try:
        # Use LightRAG hybrid search
        resp = session.post(
            f"{LIGHTRAG_URL}/query",
            json={
                "query": query,
                "mode": "hybrid",  # Combines local + global search
            },
            timeout=20
        )

        if resp.status_code != 200:
            from tools.opportunity_bank import search_opportunities
            return await search_opportunities(query, limit)

        result = resp.json()

        # Filter for opportunity entities
        opportunities = []
        for entity in result.get("entities", []):
            if entity.get("entity_type") == "OPPORTUNITY":
                opportunities.append({
                    "name": entity.get("entity_name"),
                    "description": entity.get("description", ""),
                    "domain": entity.get("domain", ""),
                    "value_potential": entity.get("value_potential", "medium"),
                    "relevancy_score": entity.get("score", 0.5),
                })

        return opportunities[:limit]

    except Exception as e:
        logger.warning(f"LightRAG search error: {e}")
        from tools.opportunity_bank import search_opportunities
        return await search_opportunities(query, limit)


async def get_user_opportunities(user_id: str, limit: int = 20) -> List[Dict]:
    """
    Get all opportunities found by a specific user.
    """
    driver = _get_neo4j()
    if not driver:
        return []

    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (u:User {id: $user_id})-[:FOUND_OPPORTUNITY]->(o:Opportunity)
                OPTIONAL MATCH (o)-[:IN_DOMAIN]->(d:Domain)
                RETURN o.id AS id, o.name AS name, o.description AS description,
                       o.value_potential AS value_potential, o.problem AS problem,
                       d.name AS domain, o.created_at AS created_at
                ORDER BY o.created_at DESC
                LIMIT $limit
            """, {"user_id": user_id, "limit": limit})

            return [dict(r) for r in result]

    except Exception as e:
        logger.error(f"Get user opportunities error: {e}")
        return []


async def get_domain_opportunity_map(limit_per_domain: int = 5) -> Dict[str, List[Dict]]:
    """
    Get a map of domains to their opportunities.

    Returns:
        {
            "EdTech": [{"name": "...", "value_potential": "high"}, ...],
            "HealthTech": [...],
        }
    """
    driver = _get_neo4j()
    if not driver:
        return {}

    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (o:Opportunity)-[:IN_DOMAIN]->(d:Domain)
                WITH d.name AS domain, o
                ORDER BY o.value_potential DESC, o.created_at DESC
                WITH domain, collect({
                    id: o.id,
                    name: o.name,
                    value_potential: o.value_potential,
                    problem: o.problem
                })[0..$limit] AS opps
                RETURN domain, opps
            """, {"limit": limit_per_domain})

            return {r["domain"]: r["opps"] for r in result}

    except Exception as e:
        logger.error(f"Domain map error: {e}")
        return {}


async def get_opportunity_network(opportunity_id: str) -> Dict[str, Any]:
    """
    Get the network around an opportunity (domains, frameworks, related opps).
    """
    driver = _get_neo4j()
    if not driver:
        return {}

    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (o:Opportunity {id: $id})
                OPTIONAL MATCH (o)-[:IN_DOMAIN]->(d:Domain)
                OPTIONAL MATCH (o)-[:USED_FRAMEWORK]->(f:Framework)
                OPTIONAL MATCH (o)-[:RELEVANT_TO]->(t:Topic)
                OPTIONAL MATCH (o)-[:CO_OCCURS_WITH]-(related:Opportunity)
                RETURN o.name AS name,
                       o.description AS description,
                       o.value_potential AS value_potential,
                       collect(DISTINCT d.name) AS domains,
                       collect(DISTINCT f.name) AS frameworks,
                       collect(DISTINCT t.name) AS topics,
                       collect(DISTINCT {name: related.name, id: related.id})[0..5] AS related
            """, {"id": opportunity_id})

            record = result.single()
            if record:
                return dict(record)

    except Exception as e:
        logger.error(f"Opportunity network error: {e}")

    return {}


# === Batch Operations ===

async def sync_existing_opportunities_to_lightrag(batch_size: int = 20) -> Dict[str, int]:
    """
    Sync existing opportunities from Supabase to LightRAG.

    Call this to backfill the LightRAG graph with historical data.
    """
    from tools.opportunity_bank import get_opportunities_from_table

    result = {"synced": 0, "failed": 0, "total": 0}

    try:
        opportunities = await get_opportunities_from_table(limit=batch_size)
        result["total"] = len(opportunities)

        for opp_data in opportunities:
            try:
                # Convert to Opportunity object
                opp = Opportunity(
                    id=opp_data.get("id", ""),
                    name=opp_data.get("name", ""),
                    description=opp_data.get("description", ""),
                    problem=opp_data.get("problem", ""),
                    value_potential=opp_data.get("value_potential", "medium"),
                    domain=opp_data.get("domain", ""),
                    frameworks_applied=opp_data.get("frameworks_applied", []),
                    tags=opp_data.get("tags", []),
                    created_at=opp_data.get("created_at", ""),
                    created_by=opp_data.get("created_by", ""),
                )

                if push_opportunity_to_lightrag(opp):
                    result["synced"] += 1
                else:
                    result["failed"] += 1

            except Exception as e:
                logger.warning(f"Sync error for {opp_data.get('name')}: {e}")
                result["failed"] += 1

    except Exception as e:
        logger.error(f"Batch sync error: {e}")

    logger.info(f"LightRAG sync complete: {result}")
    return result


# === Main Entry Points ===

async def extract_and_store_with_lightrag(
    conversation: List[Dict[str, str]],
    bot_id: str = "unknown",
    methodology: str = "",
    phase: str = "",
    conversation_id: str = "",
    user_id: str = ""
) -> Dict[str, Any]:
    """
    Full pipeline: Extract opportunities from conversation and store with LightRAG.

    This is the enhanced version of extract_and_store_opportunities.
    """
    # Extract using existing function
    opportunities = await extract_opportunities(
        conversation=conversation,
        bot_id=bot_id,
        methodology=methodology,
        phase=phase,
        conversation_id=conversation_id,
        user_id=user_id,
    )

    if not opportunities:
        return {"extracted": 0, "stored": 0, "lightrag_synced": 0}

    results = []
    for opp in opportunities:
        result = await store_opportunity_with_lightrag(
            opportunity=opp,
            user_id=user_id,
            session_id=conversation_id,
        )
        results.append(result)

    return {
        "extracted": len(opportunities),
        "stored": sum(1 for r in results if r.get("supabase") or r.get("neo4j")),
        "lightrag_synced": sum(1 for r in results if r.get("lightrag")),
        "domains_extracted": sum(1 for r in results if r.get("domain_extracted")),
        "relevancy_links_created": sum(r.get("relevancy_links", 0) for r in results),
        "opportunities": [opp.to_dict() for opp in opportunities],
    }
