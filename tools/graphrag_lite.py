"""
Lightweight GraphRAG for Conversational Chat
============================================

Designed for Larry's coaching style:
- Only retrieves when needed
- Returns hints, not lectures
- Helps Larry ask better questions

Graph's value: Understanding relationships between concepts,
not delivering paragraphs of content.
"""

import os
from typing import Optional, Dict, List

_neo4j_driver = None


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


def get_concept_connections(concept: str) -> Dict:
    """
    Get a concept and its immediate connections.
    Returns hints, not full documents.

    Use when Larry needs to understand how concepts relate.

    Example:
        >>> get_concept_connections("JTBD")
        {
            "name": "Jobs to Be Done",
            "description": "Framework for understanding...",
            "connections": [
                {"relation": "HAS_COMPONENT", "name": "Milkshake Example", "type": "Concept"},
                {"relation": "REQUIRES", "name": "Customer Interviews", "type": "Tool"},
            ]
        }
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
        print(f"Graph lookup error: {e}")

    return {"concept": concept, "connections": []}


def get_related_frameworks(topic: str, limit: int = 3) -> List[Dict]:
    """
    Find frameworks related to a topic.
    Returns names and one-liners, not full explanations.

    Use when Larry is considering which framework might help.
    """
    driver = _get_neo4j()
    if not driver:
        return []

    try:
        with driver.session() as session:
            # Try full-text search first (using framework_ecosystem_search index)
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
        print(f"Framework lookup error: {e}")
        return []


def get_problem_context(problem_description: str) -> Dict:
    """
    Given a problem description, find relevant problem types and approaches.

    Helps Larry understand what kind of problem this is.
    """
    driver = _get_neo4j()
    if not driver:
        return {}

    try:
        with driver.session() as session:
            # Use entity_fulltext index for broader search
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
        print(f"Problem context error: {e}")

    return {}


# === Decision Logic ===

def should_retrieve(message: str, turn_count: int) -> bool:
    """
    Decide if this turn needs retrieval.
    Most conversational turns don't need it.

    Args:
        message: User's message
        turn_count: Number of conversation turns so far

    Returns:
        True if retrieval would help, False otherwise
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

    # Direct concept questions
    if any(phrase in message_lower for phrase in ["what is", "what's", "explain", "tell me about"]):
        return "concept"

    # Looking for frameworks
    if any(phrase in message_lower for phrase in ["framework", "approach", "method", "tool for"]):
        return "framework"

    # Describing a problem/situation
    problem_indicators = ["struggling with", "stuck on", "problem is", "challenge is", "issue is"]
    if any(phrase in message_lower for phrase in problem_indicators):
        return "problem"

    return "none"


# === Main Interface ===

def light_context(query: str, context_type: str = "auto") -> str:
    """
    Get light context for a query.
    Returns 2-3 sentences max, not a lecture.

    Args:
        query: The user's query or topic
        context_type: 'concept', 'framework', 'problem', or 'auto'

    Returns:
        Brief contextual hint for Larry to use
    """
    if context_type == "auto":
        context_type = get_retrieval_type(query)

    if context_type == "concept":
        connections = get_concept_connections(query)
        if connections.get("connections"):
            related = [c["name"] for c in connections["connections"][:4]]
            name = connections.get("name", query)
            return f"{name} connects to: {', '.join(related)}"
        elif connections.get("description"):
            return connections["description"]

    elif context_type == "framework":
        frameworks = get_related_frameworks(query, limit=2)
        if frameworks:
            hints = [f"{f['name']}" for f in frameworks]
            return f"Relevant frameworks: {', '.join(hints)}"

    elif context_type == "problem":
        context = get_problem_context(query)
        if context.get("problem_type"):
            result = f"This sounds like: {context['problem_type']}"
            if context.get("approaches"):
                result += f". Consider: {', '.join(context['approaches'][:2])}"
            return result

    return ""


def enrich_for_larry(user_message: str, turn_count: int) -> Optional[str]:
    """
    Main entry point: decide if and how to enrich Larry's context.

    Args:
        user_message: What the user said
        turn_count: How many turns into the conversation

    Returns:
        Context hint string if helpful, None otherwise

    Usage in mindrian_chat.py:
        context_hint = enrich_for_larry(message.content, turn_count)
        if context_hint:
            # Add to system prompt or as invisible context
    """
    if not should_retrieve(user_message, turn_count):
        return None

    context = light_context(user_message)
    return context if context else None
