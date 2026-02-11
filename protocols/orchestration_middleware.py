"""
Orchestration Middleware - Button-less Human-in-the-Loop Detection
=================================================================

Called on every message (after context enrichment, before Gemini call).
Evaluates whether multi-agent orchestration would help the user.

Core Principle: DETECT → RECOMMEND → CONFIRM → EXECUTE
Never auto-executes. The user always decides.

Decision types:
- RECOMMEND (≥0.80): Show recommendation BEFORE normal response, with accept/dismiss
- SUGGEST (0.60-0.79): Show suggestion AFTER normal response, lighter UI
- PASS_THROUGH (<0.60): Nothing shown
"""

import os
import time
import logging
from enum import Enum
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

from .intent_classifier import (
    classify_intent,
    should_auto_orchestrate,
    ClassificationResult,
    WorkflowType,
    get_workflow_description,
)
from .workflow_recipes import WORKFLOWS, get_workflow

logger = logging.getLogger("mindrian")

# Feature flag
ORCHESTRATION_MIDDLEWARE_ENABLED = os.getenv("ORCHESTRATION_MIDDLEWARE_ENABLED", "true").lower() in ("true", "1", "yes")

# Thresholds (conservative — false positives are worse than false negatives)
RECOMMEND_THRESHOLD = 0.80
SUGGEST_THRESHOLD = 0.60

# Guards
MIN_TURNS_BEFORE_RECOMMEND = 2  # Skip first 2 turns (let conversation develop)
COOLDOWN_TURNS = 8  # No re-recommendation within 8 turns of last orchestration
MOMENTUM_WINDOW = 4  # Look at last N turns for momentum
MOMENTUM_BOOST = 0.10  # Boost confidence when momentum detected


class MiddlewareDecision(Enum):
    """What the middleware recommends."""
    RECOMMEND = "recommend"    # High confidence — show before response
    SUGGEST = "suggest"        # Medium confidence — show after response
    PASS_THROUGH = "pass_through"  # Low confidence — nothing shown


@dataclass
class MiddlewareResult:
    """Full result from middleware evaluation."""
    decision: MiddlewareDecision
    classification: Optional[ClassificationResult] = None
    workflow_type: Optional[str] = None
    workflow_name: Optional[str] = None
    confidence: float = 0.0
    suggested_agents: List[str] = field(default_factory=list)
    reasoning: str = ""
    estimated_seconds: int = 0
    evaluation_ms: float = 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# Session State Management
# ═══════════════════════════════════════════════════════════════════════════════

# Per-session state (keyed by session_id)
_session_state: Dict[str, Dict[str, Any]] = {}


def _get_session_state(session_id: str) -> Dict[str, Any]:
    """Get or create session state for middleware."""
    if session_id not in _session_state:
        _session_state[session_id] = {
            "last_orchestration_turn": -COOLDOWN_TURNS - 1,  # Allow first recommendation
            "recent_workflow_types": [],  # Last N detected workflow types for momentum
            "orchestration_count": 0,
            "dismissed_count": 0,
        }
    return _session_state[session_id]


def record_orchestration_run(session_id: str, turn_count: int):
    """Record that orchestration was run (for cooldown tracking)."""
    state = _get_session_state(session_id)
    state["last_orchestration_turn"] = turn_count
    state["orchestration_count"] += 1


def record_orchestration_dismissed(session_id: str):
    """Record that user dismissed a recommendation."""
    state = _get_session_state(session_id)
    state["dismissed_count"] += 1


def cleanup_session(session_id: str):
    """Clean up session state when session ends."""
    _session_state.pop(session_id, None)


# ═══════════════════════════════════════════════════════════════════════════════
# Momentum Detection
# ═══════════════════════════════════════════════════════════════════════════════

def _calculate_momentum(
    current_workflow: WorkflowType,
    session_id: str,
) -> float:
    """
    Calculate momentum boost if recent turns build toward the same workflow.

    If the last 3-4 turns all point to the same workflow type,
    the user is likely building up to something — boost confidence.
    """
    state = _get_session_state(session_id)
    recent = state["recent_workflow_types"]

    if len(recent) < 2:
        return 0.0

    # Check how many of the recent turns match current workflow
    matches = sum(1 for wt in recent[-MOMENTUM_WINDOW:] if wt == current_workflow.value)
    total = min(len(recent), MOMENTUM_WINDOW)

    if total >= 2 and matches >= 2:
        # At least 2 of the last N turns had the same workflow type
        ratio = matches / total
        return MOMENTUM_BOOST * ratio

    return 0.0


def _record_workflow_type(session_id: str, workflow_type: WorkflowType):
    """Record detected workflow type for momentum tracking."""
    state = _get_session_state(session_id)
    state["recent_workflow_types"].append(workflow_type.value)
    # Keep only last MOMENTUM_WINDOW * 2 entries
    if len(state["recent_workflow_types"]) > MOMENTUM_WINDOW * 2:
        state["recent_workflow_types"] = state["recent_workflow_types"][-MOMENTUM_WINDOW * 2:]


# ═══════════════════════════════════════════════════════════════════════════════
# Main Evaluation
# ═══════════════════════════════════════════════════════════════════════════════

async def evaluate_message(
    message: str,
    history: List[Dict],
    session_id: str,
    bot_id: str,
    turn_count: int,
    has_document: bool = False,
) -> MiddlewareResult:
    """
    Evaluate a message for orchestration opportunity.

    Called on every message after context enrichment, before Gemini call.
    Pure detection — never runs orchestration itself.

    Args:
        message: User's message text
        history: Conversation history
        session_id: Session identifier
        bot_id: Current bot ID
        turn_count: Number of turns in conversation
        has_document: Whether a document is attached

    Returns:
        MiddlewareResult with decision, classification, and metadata
    """
    start = time.monotonic()

    # === Guard: Feature flag ===
    if not ORCHESTRATION_MIDDLEWARE_ENABLED:
        return MiddlewareResult(
            decision=MiddlewareDecision.PASS_THROUGH,
            reasoning="Middleware disabled by feature flag",
            evaluation_ms=(time.monotonic() - start) * 1000,
        )

    # === Guard: Early turns ===
    if turn_count < MIN_TURNS_BEFORE_RECOMMEND:
        return MiddlewareResult(
            decision=MiddlewareDecision.PASS_THROUGH,
            reasoning=f"Too early (turn {turn_count} < {MIN_TURNS_BEFORE_RECOMMEND})",
            evaluation_ms=(time.monotonic() - start) * 1000,
        )

    # === Guard: Cooldown ===
    state = _get_session_state(session_id)
    turns_since_last = turn_count - state["last_orchestration_turn"]
    if turns_since_last < COOLDOWN_TURNS:
        return MiddlewareResult(
            decision=MiddlewareDecision.PASS_THROUGH,
            reasoning=f"Cooldown ({turns_since_last} turns since last orchestration, need {COOLDOWN_TURNS})",
            evaluation_ms=(time.monotonic() - start) * 1000,
        )

    # === Fast path: Trigger phrases ===
    if should_auto_orchestrate(message):
        classification = classify_intent(message, has_document=has_document)
        workflow = _resolve_workflow(classification)
        _record_workflow_type(session_id, classification.workflow_type)

        elapsed = (time.monotonic() - start) * 1000
        logger.info(f"[MIDDLEWARE] Fast path trigger: {classification.workflow_type.value} "
                     f"(confidence={classification.confidence:.2f}, {elapsed:.1f}ms)")

        return MiddlewareResult(
            decision=MiddlewareDecision.RECOMMEND,
            classification=classification,
            workflow_type=classification.workflow_type.value,
            workflow_name=workflow["name"] if workflow else get_workflow_description(classification.workflow_type),
            confidence=min(classification.confidence + 0.05, 1.0),  # Small boost for explicit triggers
            suggested_agents=classification.recommended_agents,
            reasoning=classification.reasoning,
            estimated_seconds=workflow["estimated_seconds"] if workflow else 120,
            evaluation_ms=elapsed,
        )

    # === Standard path: classify_intent + momentum ===
    classification = classify_intent(message, has_document=has_document)

    # Calculate momentum boost
    momentum = _calculate_momentum(classification.workflow_type, session_id)
    adjusted_confidence = min(classification.confidence + momentum, 1.0)

    # Record for future momentum
    _record_workflow_type(session_id, classification.workflow_type)

    # Resolve workflow
    workflow = _resolve_workflow(classification)

    # Make decision
    if adjusted_confidence >= RECOMMEND_THRESHOLD:
        decision = MiddlewareDecision.RECOMMEND
    elif adjusted_confidence >= SUGGEST_THRESHOLD:
        decision = MiddlewareDecision.SUGGEST
    else:
        decision = MiddlewareDecision.PASS_THROUGH

    elapsed = (time.monotonic() - start) * 1000
    logger.info(f"[MIDDLEWARE] {decision.value}: {classification.workflow_type.value} "
                 f"(base={classification.confidence:.2f}, momentum={momentum:.2f}, "
                 f"adjusted={adjusted_confidence:.2f}, {elapsed:.1f}ms)")

    return MiddlewareResult(
        decision=decision,
        classification=classification,
        workflow_type=classification.workflow_type.value,
        workflow_name=workflow["name"] if workflow else get_workflow_description(classification.workflow_type),
        confidence=adjusted_confidence,
        suggested_agents=classification.recommended_agents,
        reasoning=classification.reasoning,
        estimated_seconds=workflow["estimated_seconds"] if workflow else 120,
        evaluation_ms=elapsed,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _resolve_workflow(classification: ClassificationResult) -> Optional[Dict]:
    """Resolve a workflow recipe from classification."""
    workflow_id = classification.workflow_type.value
    if workflow_id in WORKFLOWS:
        return WORKFLOWS[workflow_id]
    return WORKFLOWS.get("full_analysis")


def get_recommendation_message(result: MiddlewareResult) -> str:
    """Build the recommendation message shown to the user."""
    agents_str = ", ".join(
        _agent_display_name(a) for a in result.suggested_agents[:4]
    )
    minutes = max(1, result.estimated_seconds // 60)

    return (
        f"This sounds like it needs a **{result.workflow_name}** analysis. "
        f"I can run {agents_str} together for a deeper synthesis (~{minutes} min)."
    )


def get_suggestion_message(result: MiddlewareResult) -> str:
    """Build the suggestion message shown after normal response."""
    agents_str = ", ".join(
        _agent_display_name(a) for a in result.suggested_agents[:3]
    )

    return (
        f"I could also run a deeper **{result.workflow_name}** analysis "
        f"with {agents_str}."
    )


def _agent_display_name(agent_id: str) -> str:
    """Get display name for an agent ID."""
    names = {
        "tta": "TTA",
        "jtbd": "JTBD",
        "redteam": "Red Team",
        "ackoff": "Ackoff",
        "scurve": "S-Curve",
        "research": "Research",
        "validation": "Validation",
        "knowns": "Known-Unknowns",
        "larry": "Lawrence",
    }
    return names.get(agent_id, agent_id.title())
