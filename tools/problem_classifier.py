"""
Problem Classifier Tool
========================
Neo4j-powered problem classification and recommendation engine.

Queries the ProblemType taxonomy + CynefinDomain + Framework graph
to provide structured classification and next-step recommendations.

Usage:
    from tools.problem_classifier import classify_problem, get_problem_taxonomy

    # Get the full taxonomy for context injection
    taxonomy = get_problem_taxonomy()

    # Classify a problem and get recommendations
    result = classify_problem("ill-defined")
"""

import os
import logging
from typing import Optional

logger = logging.getLogger("problem_classifier")

_NEO4J_TIMEOUT = 3.0  # seconds — circuit breaker


def _get_driver():
    """Get Neo4j driver (lazy import)."""
    from neo4j import GraphDatabase
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")
    if not all([uri, user, password]):
        return None
    return GraphDatabase.driver(uri, auth=(user, password))


def get_problem_taxonomy() -> Optional[str]:
    """
    Fetch the full ProblemType taxonomy from Neo4j.
    Returns a formatted string for context injection.
    """
    driver = _get_driver()
    if not driver:
        return None

    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (pt:ProblemType)
                OPTIONAL MATCH (pt)-[:PART_OF]->(cd:CynefinDomain)
                RETURN pt.name AS name,
                       pt.description AS description,
                       pt.clarity_level AS clarity,
                       pt.complexity_level AS complexity,
                       pt.recommended_approach AS approach,
                       cd.name AS cynefin_domain
                ORDER BY pt.name
            """)

            lines = ["## Problem Type Taxonomy (from Knowledge Graph)\n"]
            for r in result:
                lines.append(f"**{r['name']}** — {r['description'] or 'No description'}")
                if r['cynefin_domain']:
                    lines.append(f"  Cynefin: {r['cynefin_domain']} | Clarity: {r['clarity'] or '?'} | Complexity: {r['complexity'] or '?'}")
                if r['approach']:
                    lines.append(f"  Recommended: {r['approach']}")
                lines.append("")

            return "\n".join(lines) if len(lines) > 1 else None
    except Exception as e:
        logger.warning(f"problem_classifier taxonomy fetch failed: {e}")
        return None
    finally:
        driver.close()


def classify_problem(problem_type: str) -> Optional[str]:
    """
    Given a classified problem type, fetch graph context:
    - Matching ProblemType node + Cynefin domain
    - Frameworks that address this problem type
    - Related ReverseSalients
    - Recommended next steps

    Args:
        problem_type: One of "well-defined", "ill-defined", "undefined", "wicked", "tame"

    Returns:
        Formatted context string or None
    """
    driver = _get_driver()
    if not driver:
        return None

    # Normalize input to match graph names
    type_map = {
        "well-defined": "Well-Defined Problem",
        "well defined": "Well-Defined Problem",
        "ill-defined": "Ill-Defined Problem",
        "ill defined": "Ill-Defined Problem",
        "undefined": "Undefined Problem",
        "un-defined": "Undefined Problem",
        "wicked": "Wicked Problem",
        "tame": "Tame Problem",
    }
    canonical = type_map.get(problem_type.lower().strip(), problem_type)

    try:
        with driver.session() as session:
            # 1. Get ProblemType + Cynefin
            pt_result = session.run("""
                MATCH (pt:ProblemType {name: $name})
                OPTIONAL MATCH (pt)-[:PART_OF]->(cd:CynefinDomain)
                RETURN pt.name AS name, pt.description AS desc,
                       pt.recommended_approach AS approach,
                       cd.name AS cynefin
            """, name=canonical)
            pt = pt_result.single()

            if not pt:
                return None

            lines = [
                f"**Classification: {pt['name']}**",
                f"Description: {pt['desc']}",
                f"Cynefin Domain: {pt['cynefin'] or 'Unknown'}",
                f"Recommended Approach: {pt['approach'] or 'See taxonomy'}",
                "",
            ]

            # 2. Frameworks addressing this problem type
            fw_result = session.run("""
                MATCH (pt:ProblemType {name: $name})<-[:ADDRESSES_PROBLEM_TYPE]-(fw)
                RETURN DISTINCT fw.name AS name, labels(fw)[0] AS label
                LIMIT 10
            """, name=canonical)
            frameworks = [r["name"] for r in fw_result]
            if frameworks:
                lines.append(f"Frameworks that address this: {', '.join(frameworks)}")

            # 3. Also check RELATES_TO edges (migrated from cleanup)
            rel_result = session.run("""
                MATCH (pt:ProblemType {name: $name})-[r:RELATES_TO]-(x)
                WHERE r.original_type = 'ADDRESSES_PROBLEM_TYPE'
                RETURN DISTINCT x.name AS name
                LIMIT 10
            """, name=canonical)
            related = [r["name"] for r in rel_result if r["name"] not in frameworks]
            if related:
                lines.append(f"Related resources: {', '.join(related[:5])}")

            # 4. Nearby ReverseSalients
            rs_result = session.run("""
                MATCH (pt:ProblemType {name: $name})-[*1..2]-(rs:ReverseSalient)
                RETURN DISTINCT rs.name AS name
                LIMIT 5
            """, name=canonical)
            salients = [r["name"] for r in rs_result]
            if salients:
                lines.append(f"Related bottlenecks: {', '.join(salients)}")

            return "\n".join(lines)
    except Exception as e:
        logger.warning(f"problem_classifier classify failed: {e}")
        return None
    finally:
        driver.close()


def get_classification_context(user_message: str) -> Optional[str]:
    """
    High-level entry point: fetch taxonomy + any detected problem type context.
    Called from mindrian_chat.py when Problem Classifier bot is active.

    Returns formatted context string for system prompt injection.
    """
    taxonomy = get_problem_taxonomy()
    if not taxonomy:
        return None
    return taxonomy
