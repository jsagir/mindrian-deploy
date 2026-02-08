"""
Text2Cypher — Natural Language to Neo4j Cypher Query Tool
==========================================================
Converts natural language questions into Cypher queries and executes them
against the Neo4j knowledge graph.

Features:
- Schema-aware query generation (knows your node types, relationships)
- Safe query validation (read-only by default)
- Automatic result formatting
- Query explanation for transparency
- Caching for repeated queries

Integration:
- LangChain @tool decorator for agent composition
- LangGraph node for pipeline integration
- Direct API for programmatic use

Security:
- Read-only mode by default
- Query validation before execution
- Configurable query patterns
- Parameterized queries to prevent injection
"""

import os
import json
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from functools import lru_cache
from datetime import datetime

# Google Gemini
from google import genai
from google.genai import types

# Neo4j
try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    print("Neo4j driver not available")

# LangChain
from langchain_core.tools import tool

# Lazy-initialized Gemini client (avoids import-time errors when API key is missing)
_client = None

def _get_client():
    """Get or create Gemini client (lazy initialization)."""
    global _client
    if _client is None:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY environment variable not set")
        _client = genai.Client(api_key=api_key)
    return _client

# Neo4j configuration
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")


# =============================================================================
# SCHEMA DEFINITIONS — Your Knowledge Graph Structure
# =============================================================================

MINDRIAN_SCHEMA = """
## Mindrian Knowledge Graph Schema

### Core Node Types

**Concept** — PWS methodology concepts
- Properties: name (string), description (text), category (string)
- Example: (:Concept {name: "Camera Test", category: "validation"})

**Framework** — Structured thinking frameworks
- Properties: name (string), description (text), when_to_use (text), steps (list)
- Example: (:Framework {name: "Jobs to Be Done", when_to_use: "customer research"})

**Problem** — Problem types and patterns
- Properties: name (string), description (text), domain (string)
- Example: (:Problem {name: "Adoption barrier", domain: "technology"})

**ReverseSalient** — Cross-domain breakthrough opportunities (Hughes theory)
- Properties: name (string), description (text), source_domain (string), target_domain (string)
- Example: (:ReverseSalient {name: "Battery density", source_domain: "EVs"})

**CaseStudy** — Real-world examples and outcomes
- Properties: name (string), company (string), outcome (string), year (int)
- Example: (:CaseStudy {name: "Airbnb pivot", company: "Airbnb", outcome: "success"})

**Bot** — Mindrian agent definitions
- Properties: bot_id (string), name (string), methodology (string)
- Example: (:Bot {bot_id: "tta", name: "Trending to the Absurd"})

**PredictionMarket** — Oracle agent markets
- Properties: id (string), question (text), status (string), outcome (string)
- Example: (:PredictionMarket {question: "Will X succeed?", status: "open"})

**MarketOutcome** — Resolved prediction outcomes
- Properties: result (string), actual_value (float), lesson (text)

**ForecastPattern** — Learned prediction patterns
- Properties: concept (string), avg_accuracy (float), bias_direction (string)

### Key Relationships

**ADDRESSES_PROBLEM_TYPE** — Framework → Problem
**RELATED_TO** — Concept ↔ Concept
**APPLIES_FRAMEWORK** — CaseStudy → Framework
**DEMONSTRATES** — CaseStudy → Concept
**BOTTLENECK_IN** — ReverseSalient → Problem
**SOLVED_BY** — ReverseSalient → Framework
**FORECASTS_ABOUT** — PredictionMarket → Concept
**INFORMED_BY_SURPRISE** — PredictionMarket → ReverseSalient
**RESOLVED_AS** — PredictionMarket → MarketOutcome
**SPECIALIZES_IN** — Bot → Framework
**USES_TOOL** — Framework → ResearchTool

### Common Query Patterns

1. Find frameworks for a problem type:
   MATCH (f:Framework)-[:ADDRESSES_PROBLEM_TYPE]->(p:Problem)
   WHERE p.name CONTAINS 'adoption'
   RETURN f.name, f.description

2. Get related concepts:
   MATCH (c1:Concept)-[:RELATED_TO]-(c2:Concept)
   WHERE c1.name = 'Camera Test'
   RETURN c2.name, c2.description

3. Find reverse salients in a domain:
   MATCH (rs:ReverseSalient)
   WHERE rs.source_domain CONTAINS 'healthcare'
   RETURN rs.name, rs.description, rs.target_domain

4. Get case studies for a framework:
   MATCH (cs:CaseStudy)-[:APPLIES_FRAMEWORK]->(f:Framework)
   WHERE f.name CONTAINS 'JTBD'
   RETURN cs.name, cs.company, cs.outcome

5. Find prediction patterns for a concept:
   MATCH (fp:ForecastPattern)
   WHERE fp.concept CONTAINS 'technology'
   RETURN fp.concept, fp.avg_accuracy, fp.bias_direction
"""

# Forbidden query patterns (safety)
FORBIDDEN_PATTERNS = [
    "DELETE", "DETACH DELETE", "REMOVE", "SET",
    "CREATE", "MERGE", "DROP", "CALL db.",
    "CALL apoc.periodic", "CALL apoc.trigger"
]


# =============================================================================
# QUERY GENERATION
# =============================================================================

def generate_cypher_query(
    question: str,
    schema: str = MINDRIAN_SCHEMA,
    allow_writes: bool = False
) -> Tuple[str, str]:
    """
    Generate a Cypher query from natural language.

    Args:
        question: Natural language question
        schema: Graph schema description
        allow_writes: Whether to allow write operations (default False)

    Returns:
        Tuple of (cypher_query, explanation)
    """
    write_mode = "You may use CREATE, MERGE, SET if the user explicitly asks to add data." if allow_writes else "ONLY generate READ queries (MATCH, RETURN, WITH, WHERE, ORDER BY, LIMIT). Never DELETE, CREATE, MERGE, SET, or REMOVE."

    prompt = f"""You are a Cypher query generator for a Neo4j knowledge graph.

{schema}

USER QUESTION: {question}

RULES:
1. {write_mode}
2. Use parameterized queries where possible (e.g., $keyword instead of hardcoded strings)
3. Add LIMIT to prevent massive result sets
4. Use CONTAINS for fuzzy text matching, not exact equals
5. Return only relevant properties, not entire nodes
6. Explain what the query does

OUTPUT FORMAT (JSON):
{{
    "cypher": "MATCH ... RETURN ...",
    "explanation": "This query finds...",
    "parameters": {{"keyword": "value"}},
    "is_safe": true
}}

If the question cannot be answered from this graph, return:
{{
    "cypher": null,
    "explanation": "Cannot answer because...",
    "parameters": {{}},
    "is_safe": true
}}"""

    try:
        client = _get_client()
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=1000,
                response_mime_type="application/json"
            )
        )

        result = json.loads(response.text.strip())

        cypher = result.get("cypher")
        explanation = result.get("explanation", "Query generated")
        parameters = result.get("parameters", {})

        if cypher:
            # Validate safety
            if not allow_writes:
                cypher_upper = cypher.upper()
                for pattern in FORBIDDEN_PATTERNS:
                    if pattern in cypher_upper:
                        return None, f"Query blocked: contains forbidden pattern '{pattern}'"

        return cypher, explanation, parameters

    except Exception as e:
        return None, f"Query generation failed: {str(e)}", {}


def validate_cypher_query(query: str, allow_writes: bool = False) -> Tuple[bool, str]:
    """
    Validate a Cypher query for safety.

    Args:
        query: Cypher query string
        allow_writes: Whether writes are allowed

    Returns:
        Tuple of (is_valid, reason)
    """
    if not query:
        return False, "Empty query"

    query_upper = query.upper().strip()

    # Check for forbidden patterns
    if not allow_writes:
        for pattern in FORBIDDEN_PATTERNS:
            if pattern in query_upper:
                return False, f"Query contains forbidden pattern: {pattern}"

    # Basic syntax checks
    if not query_upper.startswith(("MATCH", "RETURN", "WITH", "OPTIONAL", "CALL")):
        if not allow_writes:
            return False, "Query must start with MATCH, RETURN, WITH, OPTIONAL, or CALL"

    # Check for LIMIT (prevent unbounded results)
    if "RETURN" in query_upper and "LIMIT" not in query_upper:
        # Auto-add reasonable limit
        pass  # We'll handle this in execution

    return True, "Valid"


# =============================================================================
# QUERY EXECUTION
# =============================================================================

def execute_cypher_query(
    query: str,
    parameters: Dict[str, Any] = None,
    limit: int = 50
) -> Tuple[List[Dict], Optional[str]]:
    """
    Execute a Cypher query against Neo4j.

    Args:
        query: Cypher query string
        parameters: Query parameters
        limit: Maximum results (auto-added if not in query)

    Returns:
        Tuple of (results, error_message)
    """
    if not NEO4J_AVAILABLE:
        return [], "Neo4j driver not available"

    if not NEO4J_URI or not NEO4J_PASSWORD:
        return [], "Neo4j not configured"

    # Validate
    is_valid, reason = validate_cypher_query(query)
    if not is_valid:
        return [], reason

    # Auto-add LIMIT if not present
    query_upper = query.upper()
    if "RETURN" in query_upper and "LIMIT" not in query_upper:
        query = query.rstrip(";") + f" LIMIT {limit}"

    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

        with driver.session() as session:
            result = session.run(query, parameters or {})
            records = [dict(record) for record in result]

        driver.close()

        return records, None

    except Exception as e:
        return [], f"Query execution failed: {str(e)}"


# =============================================================================
# HIGH-LEVEL API
# =============================================================================

async def text_to_cypher_query(
    question: str,
    execute: bool = True,
    limit: int = 25
) -> Dict[str, Any]:
    """
    Convert natural language to Cypher and optionally execute.

    Args:
        question: Natural language question
        execute: Whether to execute the query
        limit: Result limit

    Returns:
        Dict with query, explanation, results, and error
    """
    # Generate query
    cypher, explanation, parameters = generate_cypher_query(question)

    result = {
        "question": question,
        "cypher": cypher,
        "explanation": explanation,
        "parameters": parameters,
        "results": [],
        "error": None
    }

    if not cypher:
        result["error"] = explanation
        return result

    if execute:
        records, error = execute_cypher_query(cypher, parameters, limit)
        result["results"] = records
        result["error"] = error

    return result


def format_query_results(results: List[Dict], max_items: int = 10) -> str:
    """Format query results for display."""
    if not results:
        return "No results found."

    formatted = []
    for i, record in enumerate(results[:max_items], 1):
        parts = []
        for key, value in record.items():
            if value is not None:
                if isinstance(value, str) and len(value) > 200:
                    value = value[:200] + "..."
                parts.append(f"**{key}**: {value}")
        formatted.append(f"{i}. " + " | ".join(parts))

    output = "\n".join(formatted)

    if len(results) > max_items:
        output += f"\n\n*...and {len(results) - max_items} more results*"

    return output


# =============================================================================
# LANGCHAIN TOOL
# =============================================================================

@tool
def query_knowledge_graph(question: str) -> str:
    """
    Query the Mindrian knowledge graph using natural language.

    Use this tool when you need to:
    - Find frameworks for a specific problem type
    - Get related concepts to a PWS methodology
    - Find case studies and real-world examples
    - Discover cross-domain connections (reverse salients)
    - Look up prediction market patterns

    Args:
        question: Natural language question about the knowledge graph

    Returns:
        Formatted results from the graph query
    """
    import asyncio

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    result = loop.run_until_complete(text_to_cypher_query(question, execute=True))

    if result.get("error"):
        return f"Query error: {result['error']}\n\nGenerated Cypher: {result.get('cypher', 'None')}"

    if not result.get("results"):
        return f"No results found.\n\nCypher used: {result.get('cypher', 'None')}\n\nExplanation: {result.get('explanation', '')}"

    formatted = format_query_results(result["results"])

    return f"""## Knowledge Graph Results

**Question**: {question}
**Cypher**: `{result.get('cypher', '')}`

### Results
{formatted}

*{result.get('explanation', '')}*"""


@tool
def explain_cypher_query(question: str) -> str:
    """
    Generate and explain a Cypher query WITHOUT executing it.

    Use this to understand what query would be generated for a question,
    or to get the Cypher for manual execution.

    Args:
        question: Natural language question

    Returns:
        Generated Cypher query with explanation
    """
    cypher, explanation, parameters = generate_cypher_query(question)

    if not cypher:
        return f"Could not generate query: {explanation}"

    params_str = json.dumps(parameters, indent=2) if parameters else "{}"

    return f"""## Generated Cypher Query

**Question**: {question}

**Cypher**:
```cypher
{cypher}
```

**Parameters**:
```json
{params_str}
```

**Explanation**: {explanation}

*This query has NOT been executed. Use `query_knowledge_graph` to execute.*"""


# =============================================================================
# SPECIALIZED QUERY FUNCTIONS
# =============================================================================

async def find_frameworks_for_problem(problem_description: str) -> List[Dict]:
    """Find frameworks that address a problem type."""
    result = await text_to_cypher_query(
        f"What frameworks address problems like: {problem_description}"
    )
    return result.get("results", [])


async def find_reverse_salients(domain: str) -> List[Dict]:
    """Find reverse salients (cross-domain opportunities) for a domain."""
    result = await text_to_cypher_query(
        f"Find reverse salients related to {domain}"
    )
    return result.get("results", [])


async def get_related_concepts(concept_name: str) -> List[Dict]:
    """Get concepts related to a given concept."""
    result = await text_to_cypher_query(
        f"What concepts are related to {concept_name}?"
    )
    return result.get("results", [])


async def get_case_studies_for_framework(framework_name: str) -> List[Dict]:
    """Get case studies that applied a framework."""
    result = await text_to_cypher_query(
        f"Show case studies that used the {framework_name} framework"
    )
    return result.get("results", [])


async def get_prediction_patterns(concept: str) -> List[Dict]:
    """Get learned prediction patterns for a concept area."""
    result = await text_to_cypher_query(
        f"What prediction patterns exist for {concept}?"
    )
    return result.get("results", [])


# =============================================================================
# NEO4J WRITE OPERATIONS (for Oracle integration)
# =============================================================================

def store_market_in_neo4j(market_data: Dict[str, Any]) -> Optional[str]:
    """
    Store a prediction market in Neo4j and connect to relevant concepts.

    Args:
        market_data: Market data dict with question, category, etc.

    Returns:
        Neo4j node ID or None on error
    """
    if not NEO4J_AVAILABLE or not NEO4J_URI or not NEO4J_PASSWORD:
        return None

    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

        with driver.session() as session:
            # Create market node
            result = session.run("""
                CREATE (m:PredictionMarket {
                    id: $id,
                    question: $question,
                    category: $category,
                    status: 'open',
                    created_at: datetime()
                })
                RETURN elementId(m) AS node_id
            """, {
                "id": market_data.get("id"),
                "question": market_data.get("question"),
                "category": market_data.get("category", "custom")
            })

            record = result.single()
            node_id = record["node_id"] if record else None

            # Try to connect to relevant concepts
            keywords = market_data.get("question", "").split()[:5]
            for keyword in keywords:
                if len(keyword) > 3:  # Skip short words
                    session.run("""
                        MATCH (m:PredictionMarket {id: $market_id})
                        MATCH (c:Concept)
                        WHERE c.name CONTAINS $keyword OR c.description CONTAINS $keyword
                        MERGE (m)-[:FORECASTS_ABOUT]->(c)
                    """, {"market_id": market_data.get("id"), "keyword": keyword})

        driver.close()
        return node_id

    except Exception as e:
        print(f"Neo4j market storage error: {e}")
        return None


def store_market_outcome_in_neo4j(
    market_id: str,
    outcome: Dict[str, Any],
    retrospective: Dict[str, Any]
) -> bool:
    """
    Store market outcome and lessons in Neo4j.

    Args:
        market_id: The market ID
        outcome: Resolution outcome data
        retrospective: Retrospective analysis

    Returns:
        Success boolean
    """
    if not NEO4J_AVAILABLE or not NEO4J_URI or not NEO4J_PASSWORD:
        return False

    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

        with driver.session() as session:
            # Update market status
            session.run("""
                MATCH (m:PredictionMarket {id: $market_id})
                SET m.status = 'resolved',
                    m.resolved_at = datetime()
            """, {"market_id": market_id})

            # Create outcome node
            session.run("""
                MATCH (m:PredictionMarket {id: $market_id})
                CREATE (o:MarketOutcome {
                    result: $result,
                    actual_value: $actual_value,
                    crowd_accuracy: $crowd_accuracy,
                    crux: $crux,
                    lesson: $lesson
                })
                MERGE (m)-[:RESOLVED_AS]->(o)
            """, {
                "market_id": market_id,
                "result": outcome.get("outcome"),
                "actual_value": outcome.get("actual_value", 0.5),
                "crowd_accuracy": retrospective.get("crowd_accuracy", 0.5),
                "crux": retrospective.get("crux_disagreement", ""),
                "lesson": retrospective.get("lesson_learned", "")
            })

            # Store pattern if extracted
            pattern = retrospective.get("pattern_extracted")
            if pattern:
                session.run("""
                    MERGE (fp:ForecastPattern {
                        pattern_text: $pattern
                    })
                    ON CREATE SET
                        fp.created_at = datetime(),
                        fp.confidence = 0.5,
                        fp.sample_size = 1
                    ON MATCH SET
                        fp.sample_size = fp.sample_size + 1,
                        fp.confidence = fp.confidence + 0.1
                """, {"pattern": pattern})

        driver.close()
        return True

    except Exception as e:
        print(f"Neo4j outcome storage error: {e}")
        return False


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Core functions
    "generate_cypher_query",
    "validate_cypher_query",
    "execute_cypher_query",
    "text_to_cypher_query",
    "format_query_results",
    # LangChain tools
    "query_knowledge_graph",
    "explain_cypher_query",
    # Specialized queries
    "find_frameworks_for_problem",
    "find_reverse_salients",
    "get_related_concepts",
    "get_case_studies_for_framework",
    "get_prediction_patterns",
    # Neo4j writes (Oracle)
    "store_market_in_neo4j",
    "store_market_outcome_in_neo4j",
    # Schema
    "MINDRIAN_SCHEMA",
]
