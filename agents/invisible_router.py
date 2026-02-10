"""
Invisible Agent Router — LangGraph StateGraph
===============================================

Replaces the agent dropdown with transparent methodology injection.
User stays in one conversation; the system detects when a PWS methodology
would help and injects it into Larry's base prompt.

Architecture:
    fast_classify (regex, <5ms)
        → graph_enrich (Neo4j, ~50ms)
            → [confidence >= 0.7] → cooldown_check → prompt_compose
            → [confidence < 0.7]  → llm_classify (~500ms) → cooldown_check → prompt_compose

Public API:
    route_and_inject()          — Run the router, return injection + attribution
    build_invisible_router()    — Graph factory
    InvisibleRouterState        — State TypedDict
"""

import os
import re
import json
import logging
import time
from typing import TypedDict, List, Optional, Dict, Any, Literal

from langgraph.graph import StateGraph, END

logger = logging.getLogger("invisible_router")


# ============================================================================
# State Definition
# ============================================================================

class MethodologyAttribution(TypedDict):
    """Tracks which methodology was active for a given turn."""
    methodology_id: str
    methodology_label: str
    confidence: float
    explicit: bool
    turn_index: int


class InvisibleRouterState(TypedDict, total=False):
    """State for the invisible routing graph."""
    # Input
    user_message: str
    conversation_history: list
    turn_count: int

    # Session context
    current_mode: str            # "working" or "classroom"
    base_bot_id: str             # "lawrence" or "larry_playground"

    # Router output
    detected_methodology: Optional[str]
    methodology_confidence: float
    methodology_label: str
    explicit_request: bool
    should_suggest: bool

    # Methodology state (persisted across turns via session)
    methodology_cooldowns: dict        # {methodology_id: last_applied_turn}
    methodology_history: list          # List[MethodologyAttribution]

    # Generation control
    methodology_injection: str         # Prompt injection text
    methodology_attribution_tag: str   # e.g., "[analyzing future trends]"

    # Timing
    router_latency_ms: int


# ============================================================================
# Methodology Injection Templates
# ============================================================================

METHODOLOGY_INJECTIONS = {
    "tta": """METHODOLOGY ACTIVE: Trending to the Absurd
Apply future-trend extrapolation to the user's topic. Identify current trends,
extrapolate them to logical extremes, and surface emerging problems/opportunities.
Do NOT announce you are using TTA. Weave the analysis naturally into your response.
Keep Larry's conversational voice.""",

    "redteam": """METHODOLOGY ACTIVE: Red Team / Stress Testing
Challenge the user's assumptions. Identify the 2-3 biggest assumptions in their
thinking and probe them. Ask what evidence supports each assumption.
Frame challenges constructively: "One thing worth pressure-testing is..."
Do NOT announce you are red-teaming. Keep Larry's conversational voice.""",

    "jtbd": """METHODOLOGY ACTIVE: Jobs to Be Done
Analyze the user's topic through the lens of customer jobs. What functional,
emotional, and social jobs are customers trying to accomplish? What are they
currently "hiring" to do the job? Where are the gaps?
Weave this naturally into conversation. Keep Larry's conversational voice.""",

    "scurve": """METHODOLOGY ACTIVE: S-Curve / Technology Timing
Assess where the relevant technology sits on its adoption curve. Is this
Era of Ferment (many approaches, no dominant design) or Era of Incremental
Change (optimization within standard)? What does timing suggest?
Weave naturally. Keep Larry's conversational voice.""",

    "ackoff": """METHODOLOGY ACTIVE: Ackoff's DIKW Pyramid
Ground the user's claims in the Data-Information-Knowledge-Wisdom hierarchy.
Which of their statements are data (observable)? Which are interpretation?
Apply the Camera Test where relevant. Push toward evidence-based reasoning.
Keep Larry's conversational voice.""",

    "scenario": """METHODOLOGY ACTIVE: Scenario Analysis
Help the user think about multiple plausible futures rather than a single
prediction. Identify the 2 key uncertainties and sketch the resulting 2x2
matrix of scenarios. Which scenario does their strategy assume?
Keep Larry's conversational voice.""",

    "bono": """METHODOLOGY ACTIVE: Six Thinking Hats / Parallel Thinking
Guide the user to separate different thinking modes: facts (white), feelings (red),
caution (black), optimism (yellow), creativity (green), process (blue).
Apply the relevant hat(s) to the current discussion naturally.
Keep Larry's conversational voice.""",

    "nested_hierarchies": """METHODOLOGY ACTIVE: Nested Hierarchies / Systems Analysis
Identify the system levels relevant to the user's problem. Where are the leverage
points? What are the reverse salients holding back progress? Consider cascading effects.
Keep Larry's conversational voice.""",
}

METHODOLOGY_LABELS = {
    "tta": "exploring future trends",
    "redteam": "stress-testing assumptions",
    "jtbd": "analyzing customer needs",
    "scurve": "assessing technology timing",
    "ackoff": "grounding in evidence",
    "scenario": "exploring multiple futures",
    "bono": "parallel thinking perspectives",
    "nested_hierarchies": "systems-level analysis",
    "domain": "domain selection",
    "investment": "investment analysis",
    "knowns": "mapping unknowns",
    "validation": "multi-perspective validation",
    "beautiful_question": "questioning deeper",
}


# ============================================================================
# Explicit Request Patterns (user says "stress-test this", "explore trends")
# ============================================================================

EXPLICIT_PATTERNS = {
    "tta": [
        r"trending to the absurd", r"extrapolate this trend",
        r"what happens in \d+ years", r"future of\b",
        r"what will .* look like", r"project this forward",
    ],
    "redteam": [
        r"stress[- ]?test", r"challenge (this|my|these|that)",
        r"devil'?s advocate", r"poke holes", r"what could go wrong",
        r"attack (this|my)", r"find the flaw",
    ],
    "jtbd": [
        r"jobs? to be done", r"what job .* hiring",
        r"customer (jobs?|needs?|motivations?)",
        r"why (do|would) (people|customers|users) (buy|use|choose)",
    ],
    "scurve": [
        r"s[- ]?curve", r"technology timing", r"too early or too late",
        r"dominant design", r"era of (ferment|incremental)",
    ],
    "ackoff": [
        r"dikw", r"ackoff", r"camera test",
        r"ground.* in (evidence|data)", r"validate with data",
    ],
    "scenario": [
        r"scenario analysis", r"multiple futures",
        r"2x2 (matrix|scenario)", r"plausible futures",
        r"what are the scenarios",
    ],
}


# ============================================================================
# Node 1: FAST CLASSIFY (pattern matching, <5ms)
# ============================================================================

def fast_classify(state: InvisibleRouterState) -> dict:
    """Pattern-based methodology detection. No LLM call."""
    start = time.time()
    message = state.get("user_message", "").lower()
    turn_count = state.get("turn_count", 0)

    # Don't route on first 2 turns — let conversation develop
    if turn_count < 2:
        return {
            "detected_methodology": None,
            "methodology_confidence": 0.0,
            "explicit_request": False,
            "should_suggest": False,
        }

    # Check explicit requests first (highest confidence)
    for method_id, patterns in EXPLICIT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, message):
                logger.info("Fast classify: explicit %s (pattern: %s)", method_id, pattern)
                return {
                    "detected_methodology": method_id,
                    "methodology_confidence": 0.95,
                    "explicit_request": True,
                    "should_suggest": False,
                }

    # Implicit detection: keyword scoring from conversation context
    # Import AGENT_TRIGGERS lazily to avoid circular imports
    try:
        from mindrian_chat import AGENT_TRIGGERS
    except ImportError:
        AGENT_TRIGGERS = {}

    history_text = " ".join(
        m.get("content", "") for m in state.get("conversation_history", [])[-6:]
    ).lower()

    # Combine current message + recent history for scoring
    combined = f"{message} {history_text}"

    scores = {}
    for agent_id, triggers in AGENT_TRIGGERS.items():
        keywords = triggers.get("keywords", [])
        score = sum(1 for kw in keywords if kw.lower() in combined)
        if score >= 2:  # Require 2+ keyword matches for implicit detection
            scores[agent_id] = score

    if scores:
        best_id = max(scores, key=scores.get)
        best_score = scores[best_id]
        confidence = min(best_score / 4.0, 0.85)  # Cap at 0.85 for implicit

        return {
            "detected_methodology": best_id,
            "methodology_confidence": confidence,
            "explicit_request": False,
            "should_suggest": confidence < 0.7,
            "router_latency_ms": int((time.time() - start) * 1000),
        }

    return {
        "detected_methodology": None,
        "methodology_confidence": 0.0,
        "explicit_request": False,
        "should_suggest": False,
        "router_latency_ms": int((time.time() - start) * 1000),
    }


# ============================================================================
# Node 2: GRAPH ENRICH (Neo4j signals, ~50ms)
# ============================================================================

def graph_enrich(state: InvisibleRouterState) -> dict:
    """Enrich with Neo4j graph scores. Advisory — boosts or confirms."""
    detected = state.get("detected_methodology")
    confidence = state.get("methodology_confidence", 0.0)

    try:
        from tools.graph_router import graph_score_agents, classify_and_route, has_problem_language
    except ImportError:
        return {}  # Graph router not available — keep existing classification

    message = state.get("user_message", "")
    history_text = " ".join(
        m.get("content", "") for m in state.get("conversation_history", [])[-6:]
    )
    combined = f"{message} {history_text}"

    try:
        graph_scores, _ = graph_score_agents(combined[:200], state.get("base_bot_id", "lawrence"))

        if has_problem_language(combined):
            problem_scores, _ = classify_and_route(combined[:200], state.get("base_bot_id", "lawrence"))
            for bot_id, ps in problem_scores.items():
                graph_scores[bot_id] = graph_scores.get(bot_id, 0) + ps

        if not graph_scores:
            return {}

        # If fast_classify found something, boost or suppress with graph evidence
        if detected and detected in graph_scores:
            return {"methodology_confidence": min(confidence + 0.15, 1.0)}

        if detected and graph_scores:
            graph_best = max(graph_scores, key=graph_scores.get)
            if graph_scores[graph_best] > 2.0 and graph_best != detected:
                return {"methodology_confidence": confidence * 0.7}

        # If fast_classify found nothing, use graph signal
        if not detected and graph_scores:
            graph_best = max(graph_scores, key=graph_scores.get)
            if graph_scores[graph_best] > 1.5:
                return {
                    "detected_methodology": graph_best,
                    "methodology_confidence": min(graph_scores[graph_best] / 5.0, 0.75),
                    "should_suggest": True,
                }

    except Exception as e:
        logger.debug("Graph enrich failed: %s", e)

    return {}


# ============================================================================
# Node 3: LLM CLASSIFY (only for ambiguous, ~500ms)
# ============================================================================

async def llm_classify(state: InvisibleRouterState) -> dict:
    """LLM classification for ambiguous cases. Uses Gemini Flash for speed."""
    message = state.get("user_message", "")
    recent = state.get("conversation_history", [])[-4:]

    prompt = f"""Analyze this message and determine if a specific PWS methodology should be applied.

MESSAGE: {message}

RECENT CONTEXT:
{json.dumps(recent[-3:], default=str)[:1000]}

METHODOLOGIES:
- tta: Future trends (when discussing future, trends, disruption)
- jtbd: Customer jobs (when discussing customers, needs, motivations)
- scurve: Technology timing (when discussing tech adoption, market timing)
- redteam: Challenge assumptions (when claims need stress-testing)
- ackoff: Evidence validation (when claims need data grounding)
- scenario: Multiple futures (when facing strategic uncertainty)
- none: No specific methodology needed

Return ONLY JSON:
{{"methodology": "tta|jtbd|scurve|redteam|ackoff|scenario|none", "confidence": 0.0-1.0, "label": "human-readable action"}}"""

    try:
        from utils.llm_router import get_gemini_client
        client = get_gemini_client()

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config={"temperature": 0.1, "max_output_tokens": 100},
        )

        text = response.text.strip() if response.text else ""
        # Parse JSON from response
        json_match = re.search(r'\{[^}]+\}', text)
        if json_match:
            result = json.loads(json_match.group())
            if result.get("methodology", "none") != "none":
                return {
                    "detected_methodology": result["methodology"],
                    "methodology_confidence": result.get("confidence", 0.6),
                    "methodology_label": result.get("label", ""),
                    "should_suggest": result.get("confidence", 0.6) < 0.8,
                }
    except Exception as e:
        logger.debug("LLM classify failed: %s", e)

    return {}


# ============================================================================
# Node 4: COOLDOWN CHECK (prevent methodology spam)
# ============================================================================

def cooldown_check(state: InvisibleRouterState) -> dict:
    """Prevent applying same methodology too frequently. 5-turn cooldown."""
    detected = state.get("detected_methodology")
    if not detected or state.get("explicit_request", False):
        return {}  # No cooldown for explicit requests

    cooldowns = state.get("methodology_cooldowns", {})
    last_applied = cooldowns.get(detected, -999)
    current_turn = state.get("turn_count", 0)

    if current_turn - last_applied < 5:
        if state.get("methodology_confidence", 0) < 0.9:
            logger.info("Cooldown: suppressing %s (last applied turn %d, now %d)",
                       detected, last_applied, current_turn)
            return {
                "detected_methodology": None,
                "methodology_confidence": 0.0,
                "should_suggest": False,
            }

    return {}


# ============================================================================
# Node 5: PROMPT COMPOSE (build methodology injection)
# ============================================================================

def prompt_compose(state: InvisibleRouterState) -> dict:
    """Layer methodology guidance onto the base Larry prompt."""
    detected = state.get("detected_methodology")

    if not detected:
        return {
            "methodology_injection": "",
            "methodology_attribution_tag": "",
        }

    injection = METHODOLOGY_INJECTIONS.get(detected, "")
    label = state.get("methodology_label") or METHODOLOGY_LABELS.get(detected, "")

    # Update cooldowns
    cooldowns = dict(state.get("methodology_cooldowns", {}))
    cooldowns[detected] = state.get("turn_count", 0)

    # Track attribution
    history = list(state.get("methodology_history", []))
    history.append({
        "methodology_id": detected,
        "methodology_label": label,
        "confidence": state.get("methodology_confidence", 0.0),
        "explicit": state.get("explicit_request", False),
        "turn_index": state.get("turn_count", 0),
    })

    logger.info("Prompt compose: %s (confidence: %.2f, explicit: %s)",
               detected, state.get("methodology_confidence", 0), state.get("explicit_request", False))

    return {
        "methodology_injection": injection,
        "methodology_attribution_tag": f"[{label}]" if label else "",
        "methodology_cooldowns": cooldowns,
        "methodology_history": history,
    }


# ============================================================================
# Conditional Edge: needs LLM?
# ============================================================================

def needs_llm_classification(state: InvisibleRouterState) -> str:
    """Decide whether to call LLM for ambiguous cases."""
    if state.get("explicit_request", False):
        return "cooldown_check"
    if state.get("methodology_confidence", 0) >= 0.7:
        return "cooldown_check"
    if state.get("detected_methodology") is None and state.get("methodology_confidence", 0) == 0.0:
        return "cooldown_check"  # Nothing found — just use Larry
    return "llm_classify"  # Ambiguous — need LLM


# ============================================================================
# Graph Builder
# ============================================================================

def build_invisible_router():
    """
    Build the LangGraph StateGraph for invisible routing.

    Flow:
        fast_classify → graph_enrich
            → [confidence >= 0.7] → cooldown_check → prompt_compose → END
            → [confidence < 0.7]  → llm_classify → cooldown_check → prompt_compose → END
    """
    workflow = StateGraph(InvisibleRouterState)

    workflow.add_node("fast_classify", fast_classify)
    workflow.add_node("graph_enrich", graph_enrich)
    workflow.add_node("llm_classify", llm_classify)
    workflow.add_node("cooldown_check", cooldown_check)
    workflow.add_node("prompt_compose", prompt_compose)

    workflow.set_entry_point("fast_classify")
    workflow.add_edge("fast_classify", "graph_enrich")

    workflow.add_conditional_edges(
        "graph_enrich",
        needs_llm_classification,
        {
            "cooldown_check": "cooldown_check",
            "llm_classify": "llm_classify",
        },
    )

    workflow.add_edge("llm_classify", "cooldown_check")
    workflow.add_edge("cooldown_check", "prompt_compose")
    workflow.add_edge("prompt_compose", END)

    return workflow.compile()


# ============================================================================
# Public API
# ============================================================================

# Module-level compiled graph (built once)
_router_graph = None


def _get_router():
    """Lazy-init the router graph."""
    global _router_graph
    if _router_graph is None:
        _router_graph = build_invisible_router()
    return _router_graph


async def route_and_inject(
    user_message: str,
    conversation_history: list,
    turn_count: int,
    base_bot_id: str = "lawrence",
    mode: str = "working",
    methodology_cooldowns: dict = None,
    methodology_history: list = None,
) -> dict:
    """
    Run the invisible router and return methodology injection + attribution.

    Args:
        user_message: Current user message
        conversation_history: Full chat history
        turn_count: Current turn number
        base_bot_id: Base bot ("lawrence" or "larry_playground")
        mode: "working" (invisible routing) or "classroom" (skip routing)
        methodology_cooldowns: {methodology_id: last_applied_turn}
        methodology_history: List of MethodologyAttribution dicts

    Returns:
        {
            "methodology_injection": str,        # Inject into system prompt
            "methodology_attribution_tag": str,   # e.g., "[exploring future trends]"
            "detected_methodology": str or None,
            "methodology_confidence": float,
            "explicit_request": bool,
            "should_suggest": bool,
            "methodology_cooldowns": dict,        # Updated cooldowns
            "methodology_history": list,          # Updated history
            "methodology_label": str,             # Human-readable label
            "router_latency_ms": int,
        }
    """
    # Classroom mode: skip routing entirely
    if mode == "classroom":
        return {
            "methodology_injection": "",
            "methodology_attribution_tag": "",
            "detected_methodology": None,
            "methodology_confidence": 0.0,
            "explicit_request": False,
            "should_suggest": False,
            "methodology_cooldowns": methodology_cooldowns or {},
            "methodology_history": methodology_history or [],
            "methodology_label": "",
            "router_latency_ms": 0,
        }

    start = time.time()

    initial_state = {
        "user_message": user_message,
        "conversation_history": conversation_history,
        "turn_count": turn_count,
        "current_mode": mode,
        "base_bot_id": base_bot_id,
        "detected_methodology": None,
        "methodology_confidence": 0.0,
        "methodology_label": "",
        "explicit_request": False,
        "should_suggest": False,
        "methodology_cooldowns": methodology_cooldowns or {},
        "methodology_history": methodology_history or [],
        "methodology_injection": "",
        "methodology_attribution_tag": "",
        "router_latency_ms": 0,
    }

    try:
        router = _get_router()
        result = await router.ainvoke(initial_state)

        total_ms = int((time.time() - start) * 1000)
        result["router_latency_ms"] = total_ms

        if result.get("detected_methodology"):
            logger.info(
                "Router: %s (confidence: %.2f, explicit: %s, latency: %dms)",
                result["detected_methodology"],
                result.get("methodology_confidence", 0),
                result.get("explicit_request", False),
                total_ms,
            )

        return result

    except Exception as e:
        logger.error("Invisible router failed: %s", e)
        return {
            "methodology_injection": "",
            "methodology_attribution_tag": "",
            "detected_methodology": None,
            "methodology_confidence": 0.0,
            "explicit_request": False,
            "should_suggest": False,
            "methodology_cooldowns": methodology_cooldowns or {},
            "methodology_history": methodology_history or [],
            "methodology_label": "",
            "router_latency_ms": int((time.time() - start) * 1000),
        }
