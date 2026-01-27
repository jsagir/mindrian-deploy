"""
Graph-Driven Bot Routing for Mindrian
======================================

Advisory only — adds weight to keyword scoring, never overrides.
Returns (scores_dict, trace_dict) on success, ({}, {}) on any failure.
"""

import os
import time
from typing import Dict, Tuple

_neo4j_driver = None


def _get_neo4j():
    global _neo4j_driver
    if _neo4j_driver is None:
        from neo4j import GraphDatabase
        uri = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USER")
        password = os.getenv("NEO4J_PASSWORD")
        if all([uri, user, password]):
            _neo4j_driver = GraphDatabase.driver(uri, auth=(user, password))
    return _neo4j_driver


# Framework substring -> bot_id mapping
FRAMEWORK_TO_BOT: Dict[str, str] = {
    "trending to the absurd": "tta",
    "tta": "tta",
    "s-curve": "scurve",
    "s curve": "scurve",
    "technology lifecycle": "scurve",
    "dominant design": "scurve",
    "jobs to be done": "jtbd",
    "jtbd": "jtbd",
    "customer job": "jtbd",
    "hire": "jtbd",
    "red team": "redteam",
    "devil's advocate": "redteam",
    "stress test": "redteam",
    "assumption testing": "redteam",
    "de bono": "redteam",
    "six thinking hats": "redteam",
    "minto": "larry",
    "scqa": "larry",
    "pyramid principle": "larry",
}

# Problem-language triggers for classify_and_route
_PROBLEM_TRIGGERS = [
    "struggling", "stuck", "problem", "challenge", "issue",
    "debate", "disagree", "can't decide", "pivot", "failing",
    "not working", "confused", "unsure", "uncertain",
]


def graph_score_agents(
    recent_text: str, current_bot: str
) -> Tuple[Dict[str, float], Dict]:
    """
    Score bots by matching recent_text against framework nodes in Neo4j.

    Returns:
        (scores_dict, trace_dict) — scores are additive weights, not overrides.
        ({}, {}) on any failure.
    """
    t0 = time.time()
    trace: Dict = {
        "source": "graph_score_agents",
        "query": recent_text[:120],
        "frameworks": [],
        "mapped_bots": {},
        "ms": 0,
    }

    driver = _get_neo4j()
    if not driver:
        trace["error"] = "no_driver"
        return {}, trace

    try:
        with driver.session() as session:
            result = session.run(
                """
                CALL db.index.fulltext.queryNodes(
                    'framework_ecosystem_search', $text
                )
                YIELD node, score
                WHERE score > 0.3
                RETURN node.name AS name, score
                ORDER BY score DESC
                LIMIT 5
                """,
                text=recent_text,
            )
            records = list(result)

        scores: Dict[str, float] = {}
        fw_names = []

        for rec in records:
            fw_name = rec["name"]
            fw_score = rec["score"]
            fw_names.append(fw_name)
            name_lower = fw_name.lower()

            for substring, bot_id in FRAMEWORK_TO_BOT.items():
                if substring in name_lower:
                    scores[bot_id] = scores.get(bot_id, 0) + fw_score
                    trace["mapped_bots"].setdefault(bot_id, []).append(fw_name)
                    break

        trace["frameworks"] = fw_names
        trace["ms"] = round((time.time() - t0) * 1000)
        return scores, trace

    except Exception as e:
        trace["error"] = str(e)
        trace["ms"] = round((time.time() - t0) * 1000)
        return {}, trace


def classify_and_route(
    problem_text: str, current_bot: str
) -> Tuple[Dict[str, float], Dict]:
    """
    Score bots via ProblemType nodes when problem-like language is detected.

    Only call when problem language is present (use has_problem_language()).
    Returns ({}, {}) on any failure.
    """
    t0 = time.time()
    trace: Dict = {
        "source": "classify_and_route",
        "query": problem_text[:120],
        "problem_type": None,
        "recommended_approach": None,
        "mapped_bots": {},
        "ms": 0,
    }

    driver = _get_neo4j()
    if not driver:
        trace["error"] = "no_driver"
        return {}, trace

    try:
        with driver.session() as session:
            result = session.run(
                """
                CALL db.index.fulltext.queryNodes(
                    'entity_fulltext', $text
                )
                YIELD node, score
                WHERE 'ProblemType' IN labels(node) AND score > 0.3
                RETURN node.name AS name,
                       node.recommended_approach AS recommended_approach,
                       score
                ORDER BY score DESC
                LIMIT 1
                """,
                text=problem_text,
            )
            rec = result.single()

        if not rec:
            trace["ms"] = round((time.time() - t0) * 1000)
            return {}, trace

        trace["problem_type"] = rec["name"]
        approach = rec["recommended_approach"] or ""
        trace["recommended_approach"] = approach

        scores: Dict[str, float] = {}
        approach_lower = approach.lower()
        for substring, bot_id in FRAMEWORK_TO_BOT.items():
            if substring in approach_lower:
                scores[bot_id] = scores.get(bot_id, 0) + rec["score"]
                trace["mapped_bots"].setdefault(bot_id, []).append(substring)

        trace["ms"] = round((time.time() - t0) * 1000)
        return scores, trace

    except Exception as e:
        trace["error"] = str(e)
        trace["ms"] = round((time.time() - t0) * 1000)
        return {}, trace


def has_problem_language(text: str) -> bool:
    """Check if text contains problem-like language."""
    text_lower = text.lower()
    return any(trigger in text_lower for trigger in _PROBLEM_TRIGGERS)
