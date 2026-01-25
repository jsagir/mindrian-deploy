"""
PWS Brain - Neo4j-Powered Knowledge Discovery

Connects to the PWS knowledge graph to:
1. Discover relevant frameworks for challenges
2. Find related concepts and methodologies
3. Build research orchestration plans

Uses Neo4j MCP tools internally - hidden from end users.
"""

import os
from typing import List, Dict, Optional, Any
from tools.neo4j_framework_discovery import (
    FrameworkRecommendation,
    categorize_framework,
    get_category_role,
    extract_challenge_keywords,
    build_framework_recommendations
)


async def query_neo4j_for_frameworks(
    keywords: List[str],
    limit: int = 8
) -> List[FrameworkRecommendation]:
    """
    Query Neo4j knowledge graph for relevant PWS frameworks.

    This function is called by the research planning system.
    Uses Neo4j MCP tools internally.

    Args:
        keywords: Challenge keywords to match against frameworks
        limit: Maximum frameworks to return

    Returns:
        List of FrameworkRecommendation objects
    """
    # Build cypher query to find matching frameworks
    keyword_pattern = "|".join(keywords[:10])  # Max 10 keywords for query

    query = f"""
    MATCH (f:Framework)
    WHERE toLower(f.name) =~ '.*({keyword_pattern.lower()}).*'
    WITH f.name AS name,
         CASE
           WHEN toLower(f.name) CONTAINS 'question' THEN 'questioning'
           WHEN toLower(f.name) CONTAINS 'problem' THEN 'problem_solving'
           WHEN toLower(f.name) CONTAINS 'innovation' THEN 'innovation'
           WHEN toLower(f.name) CONTAINS 'system' THEN 'systems'
           WHEN toLower(f.name) CONTAINS 'trend' THEN 'trends'
           WHEN toLower(f.name) CONTAINS 'scenario' THEN 'trends'
           WHEN toLower(f.name) CONTAINS 'valid' THEN 'validation'
           WHEN toLower(f.name) CONTAINS 'pyramid' THEN 'synthesis'
           WHEN toLower(f.name) CONTAINS 'minto' THEN 'synthesis'
           ELSE 'general'
         END AS category
    RETURN DISTINCT name, category
    LIMIT {limit}
    """

    # This will be called via the MCP integration
    # For now, return empty list - actual Neo4j query happens via MCP
    return []


async def query_neo4j_framework_relationships(
    framework_name: str
) -> Dict[str, Any]:
    """
    Get detailed relationships for a specific framework.

    Args:
        framework_name: Name of the framework to explore

    Returns:
        Dictionary with related concepts, tools, and examples
    """
    query = f"""
    MATCH (f:Framework {{name: $name}})-[r]->(related)
    RETURN type(r) AS relationship,
           labels(related)[0] AS related_type,
           related.name AS related_name,
           related.description AS description
    LIMIT 20
    """

    # Will be implemented via MCP
    return {
        "framework": framework_name,
        "relationships": []
    }


async def discover_framework_examples(
    framework_name: str,
    limit: int = 3
) -> List[Dict]:
    """
    Find examples and case studies for a framework.

    Args:
        framework_name: Framework to find examples for
        limit: Max examples to return

    Returns:
        List of example dictionaries
    """
    query = """
    MATCH (f:Framework {name: $name})-[:HAS_EXAMPLE|APPLIED_IN|ILLUSTRATED_BY]->(example)
    RETURN example.name AS name,
           example.description AS description,
           labels(example)[0] AS type
    LIMIT $limit
    """

    return []


def generate_framework_cypher_query(keywords: List[str], limit: int = 10) -> str:
    """
    Generate a Cypher query to discover relevant frameworks.

    Returns the query string that can be executed via MCP.
    """
    # Build keyword matching condition
    conditions = []
    for kw in keywords[:10]:
        conditions.append(f"toLower(f.name) CONTAINS '{kw.lower()}'")

    condition_str = " OR ".join(conditions) if conditions else "true"

    return f"""
    MATCH (f:Framework)
    WHERE {condition_str}
    WITH f,
         CASE
           WHEN toLower(f.name) CONTAINS 'question' THEN 'questioning'
           WHEN toLower(f.name) CONTAINS 'problem' THEN 'problem_solving'
           WHEN toLower(f.name) CONTAINS 'innovation' THEN 'innovation'
           WHEN toLower(f.name) CONTAINS 'system' THEN 'systems'
           WHEN toLower(f.name) CONTAINS 'trend' OR toLower(f.name) CONTAINS 'scenario' THEN 'trends'
           WHEN toLower(f.name) CONTAINS 'valid' OR toLower(f.name) CONTAINS 'test' THEN 'validation'
           WHEN toLower(f.name) CONTAINS 'pyramid' OR toLower(f.name) CONTAINS 'minto' OR toLower(f.name) CONTAINS 'synthesis' THEN 'synthesis'
           ELSE 'general'
         END AS category
    RETURN DISTINCT f.name AS name, category
    ORDER BY
      CASE category
        WHEN 'questioning' THEN 1
        WHEN 'problem_solving' THEN 2
        WHEN 'validation' THEN 3
        WHEN 'innovation' THEN 4
        WHEN 'trends' THEN 5
        WHEN 'systems' THEN 6
        WHEN 'synthesis' THEN 7
        ELSE 8
      END
    LIMIT {limit}
    """


# Pre-built queries for common research scenarios
RESEARCH_SCENARIO_QUERIES = {
    "innovation_opportunity": """
        MATCH (f:Framework)
        WHERE toLower(f.name) CONTAINS 'innovation'
           OR toLower(f.name) CONTAINS 'opportunity'
           OR toLower(f.name) CONTAINS 'disrupt'
        RETURN f.name AS name
        LIMIT 5
    """,

    "problem_definition": """
        MATCH (f:Framework)
        WHERE toLower(f.name) CONTAINS 'problem'
           OR toLower(f.name) CONTAINS 'wicked'
           OR toLower(f.name) CONTAINS 'defined'
        RETURN f.name AS name
        LIMIT 5
    """,

    "trend_analysis": """
        MATCH (f:Framework)
        WHERE toLower(f.name) CONTAINS 'trend'
           OR toLower(f.name) CONTAINS 'scenario'
           OR toLower(f.name) CONTAINS 'future'
        RETURN f.name AS name
        LIMIT 5
    """,

    "validation": """
        MATCH (f:Framework)
        WHERE toLower(f.name) CONTAINS 'valid'
           OR toLower(f.name) CONTAINS 'test'
           OR toLower(f.name) CONTAINS 'hypothesis'
           OR toLower(f.name) CONTAINS 'camera'
        RETURN f.name AS name
        LIMIT 5
    """,

    "systems_thinking": """
        MATCH (f:Framework)
        WHERE toLower(f.name) CONTAINS 'system'
           OR toLower(f.name) CONTAINS 'complex'
           OR toLower(f.name) CONTAINS 'cynefin'
        RETURN f.name AS name
        LIMIT 5
    """
}


def get_scenario_query(scenario: str) -> str:
    """Get a pre-built query for a research scenario."""
    return RESEARCH_SCENARIO_QUERIES.get(scenario, "")
