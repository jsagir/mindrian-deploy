"""
Intelligence Tools — LangChain @tool Functions
===============================================
Specialized tools for Oracle prediction markets and Text2Cypher.
"""

from .oracle_tools import (
    create_prediction_market,
    get_open_markets,
    get_research_brief,
    get_hsi_surprises,
    place_prediction,
    get_market_predictions,
    resolve_market,
    get_user_calibration,
    get_leaderboard,
    ALL_ORACLE_TOOLS,
)

from .text2cypher import (
    query_knowledge_graph,
    explain_cypher_query,
    text_to_cypher_query,
    store_market_in_neo4j,
    store_market_outcome_in_neo4j,
    MINDRIAN_SCHEMA,
)

__all__ = [
    # Oracle Tools
    "create_prediction_market",
    "get_open_markets",
    "get_research_brief",
    "get_hsi_surprises",
    "place_prediction",
    "get_market_predictions",
    "resolve_market",
    "get_user_calibration",
    "get_leaderboard",
    "ALL_ORACLE_TOOLS",
    # Text2Cypher
    "query_knowledge_graph",
    "explain_cypher_query",
    "text_to_cypher_query",
    "store_market_in_neo4j",
    "store_market_outcome_in_neo4j",
    "MINDRIAN_SCHEMA",
]
