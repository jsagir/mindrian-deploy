"""
Chat Integration - Hooks for mindrian_chat.py

This module provides integration points for the A2A orchestration system
with the existing Chainlit-based mindrian_chat.py.

Key Principle: Layer on top, don't rewrite. These hooks are optional
and can be enabled/disabled via feature flag.
"""

import logging
from typing import Any, Dict, Optional, Callable
from datetime import datetime

try:
    import chainlit as cl
    CHAINLIT_AVAILABLE = True
except ImportError:
    CHAINLIT_AVAILABLE = False

from .orchestrator import A2AOrchestrator, AgentInput, AgentOutput
from .context_manager import ContextManager, Artifact
from .phase_manager import PhaseManager, Phase
from .classifier import classify, get_routing_recommendation

logger = logging.getLogger(__name__)

# Feature flag - set to True to enable orchestration
A2A_ORCHESTRATION_ENABLED = False  # Start disabled, enable when ready


# === Session State Keys ===

SESSION_KEYS = {
    "orchestrator": "a2a_orchestrator",
    "context_manager": "a2a_context",
    "phase_manager": "a2a_phases",
    "classification": "a2a_classification",
    "routing": "a2a_routing",
}


# === Initialization Hooks ===

async def init_a2a_session(session_id: str) -> Optional[A2AOrchestrator]:
    """
    Initialize A2A orchestration for a new session.

    Call this from on_chat_start() in mindrian_chat.py:

    ```python
    from protocols.chat_integration import init_a2a_session, A2A_ORCHESTRATION_ENABLED

    @cl.on_chat_start
    async def on_chat_start():
        # ... existing code ...

        if A2A_ORCHESTRATION_ENABLED:
            orchestrator = await init_a2a_session(session_id)
            cl.user_session.set("a2a_orchestrator", orchestrator)
    ```
    """
    if not A2A_ORCHESTRATION_ENABLED:
        return None

    orchestrator = A2AOrchestrator(session_id)

    logger.info(f"A2A orchestration initialized for session {session_id}")

    return orchestrator


async def restore_a2a_session(session_id: str) -> Optional[A2AOrchestrator]:
    """
    Restore A2A orchestration for a resumed session.

    Call this from on_chat_resume() in mindrian_chat.py.
    """
    if not A2A_ORCHESTRATION_ENABLED:
        return None

    try:
        orchestrator = A2AOrchestrator.load(session_id)
        logger.info(f"A2A orchestration restored for session {session_id}")
        return orchestrator
    except Exception as e:
        logger.error(f"Failed to restore A2A session: {e}")
        return A2AOrchestrator(session_id)


# === Message Processing Hooks ===

async def pre_process_message(
    message: str,
    orchestrator: Optional[A2AOrchestrator],
    bot_id: str
) -> Dict[str, Any]:
    """
    Pre-process a message before sending to the bot.

    Call this at the start of on_message() in mindrian_chat.py:

    ```python
    @cl.on_message
    async def on_message(message: cl.Message):
        orchestrator = cl.user_session.get("a2a_orchestrator")

        if orchestrator:
            pre_result = await pre_process_message(
                message.content,
                orchestrator,
                bot_id
            )

            # Use classification for context enrichment
            if pre_result.get("classification"):
                # Add to context or modify bot behavior
                pass
    ```

    Returns:
        Dict with classification, routing recommendation, and any context updates
    """
    if orchestrator is None:
        return {"enabled": False}

    # Classify the message
    classification = await classify(message)
    routing = get_routing_recommendation(classification)

    # Add user input as artifact
    orchestrator.context.create_artifact(
        content=message,
        source="user",
        artifact_type="user_input"
    )

    # Store classification
    orchestrator.classification = classification
    orchestrator.routing = routing

    return {
        "enabled": True,
        "classification": classification.to_dict(),
        "routing": routing,
        "current_phase": orchestrator.phases.current_phase.value,
        "suggested_agent": routing.get("primary_agent"),
        "red_team_frequency": routing.get("red_team_frequency"),
        "context_hint": _build_context_hint(orchestrator, classification)
    }


def _build_context_hint(orchestrator: A2AOrchestrator, classification) -> str:
    """Build a context hint to inject into the bot's context."""
    hints = []

    # Classification context
    hints.append(f"[Cynefin: {classification.cynefin}, PWS: {classification.pws}]")

    # Phase context
    phase = orchestrator.phases.current_phase
    hints.append(f"[Phase: {phase.value}]")

    # Recent artifacts (last 3)
    artifacts = orchestrator.context.get_all_artifacts()[-3:]
    if artifacts:
        artifact_summary = ", ".join(a.content[:30] for a in artifacts)
        hints.append(f"[Recent context: {artifact_summary}]")

    return " ".join(hints)


async def post_process_response(
    response: str,
    orchestrator: Optional[A2AOrchestrator],
    bot_id: str
) -> Dict[str, Any]:
    """
    Post-process a response after the bot generates it.

    Call this after getting the bot's response in on_message():

    ```python
    # After bot generates response
    if orchestrator:
        post_result = await post_process_response(
            response_text,
            orchestrator,
            bot_id
        )

        if post_result.get("needs_validation"):
            # Show Red Team feedback
            pass

        if post_result.get("suggested_transition"):
            # Offer phase transition
            pass
    ```

    Returns:
        Dict with validation results and suggested actions
    """
    if orchestrator is None:
        return {"enabled": False}

    # Determine if we should validate
    should_validate = _should_validate_response(
        orchestrator,
        bot_id,
        response
    )

    validation_result = None
    if should_validate:
        validation_result = await orchestrator.red_team.validate(
            claim=response,
            evidence=orchestrator.context.get_all_artifacts(),
            stage=orchestrator.phases.current_phase,
            agent=bot_id
        )

    # Check for phase transition signals
    transition_signal = _detect_transition_signal(response, orchestrator)

    # Add response as frame (not artifact - it's bot speculation until validated)
    orchestrator.context.add_frame(
        agent=bot_id,
        content=response[:500],  # Truncate for storage
        frame_type="working_model",
        confidence=0.6
    )

    return {
        "enabled": True,
        "needs_validation": should_validate and validation_result and not validation_result.passed,
        "validation_result": validation_result.__dict__ if validation_result else None,
        "suggested_transition": transition_signal,
        "current_phase": orchestrator.phases.current_phase.value
    }


def _should_validate_response(
    orchestrator: A2AOrchestrator,
    bot_id: str,
    response: str
) -> bool:
    """Determine if response should go through Red Team validation."""
    routing = orchestrator.routing or {}
    frequency = routing.get("red_team_frequency", "on_transitions")

    if frequency == "none":
        return False
    elif frequency == "every_output":
        return True
    elif frequency == "intensive":
        return True
    elif frequency == "on_transitions":
        # Validate if phase might transition
        return orchestrator.phases.current_phase in [
            Phase.FRAMING, Phase.DEFINING, Phase.VALIDATING
        ]
    elif frequency == "periodic":
        # Validate every 5th response (placeholder logic)
        return orchestrator.context.get_summary()["artifact_count"] % 5 == 0
    elif frequency == "final_only":
        return orchestrator.phases.current_phase == Phase.VALIDATING

    return False


def _detect_transition_signal(response: str, orchestrator: A2AOrchestrator) -> Optional[Dict]:
    """Detect if response signals a phase transition."""
    response_lower = response.lower()

    # Transition keywords
    transition_signals = {
        Phase.FRAMING: ["identified the problem", "opportunity is", "the real issue"],
        Phase.DEFINING: ["problem statement", "how might we", "specifically"],
        Phase.SOLVING: ["solution", "approach", "implementation"],
        Phase.VALIDATING: ["validate", "test", "verify", "check"],
    }

    current = orchestrator.phases.current_phase
    allowed = orchestrator.phases.get_allowed_transitions()

    for target_phase in allowed:
        keywords = transition_signals.get(target_phase, [])
        if any(kw in response_lower for kw in keywords):
            return {
                "suggested_phase": target_phase.value,
                "reason": f"Response contains transition keywords for {target_phase.value}",
                "current_phase": current.value
            }

    return None


# === UI Enhancement Hooks ===

async def get_phase_indicator(orchestrator: Optional[A2AOrchestrator]) -> Optional[str]:
    """
    Get a phase indicator to show in the UI.

    Can be used to show current phase in the chat header or sidebar.
    """
    if orchestrator is None:
        return None

    phase = orchestrator.phases.current_phase
    phase_icons = {
        Phase.EXPLORING: "🔭",
        Phase.FRAMING: "🎯",
        Phase.DEFINING: "📋",
        Phase.SOLVING: "🔧",
        Phase.VALIDATING: "✅",
        Phase.COMPLETE: "🎉",
        Phase.STUCK: "🚧",
    }

    icon = phase_icons.get(phase, "📍")
    return f"{icon} {phase.value.title()}"


async def get_classification_badge(orchestrator: Optional[A2AOrchestrator]) -> Optional[Dict]:
    """
    Get classification info for a UI badge.
    """
    if orchestrator is None or orchestrator.classification is None:
        return None

    c = orchestrator.classification
    return {
        "cynefin": c.cynefin,
        "pws": c.pws,
        "confidence": min(c.cynefin_confidence, c.pws_confidence),
        "label": f"{c.cynefin.title()} / {c.pws.replace('-', ' ').title()}"
    }


async def get_journey_summary(orchestrator: Optional[A2AOrchestrator]) -> Optional[Dict]:
    """
    Get journey summary for UI display.
    """
    if orchestrator is None:
        return None

    journey = orchestrator.get_journey()

    return {
        "current_phase": journey.current_phase.value,
        "agents_visited": journey.agents_visited,
        "time_in_phase_minutes": journey.time_in_phase / 60,
        "key_decisions": journey.key_decisions[-3:],  # Last 3
        "friction_points": journey.friction_points
    }


# === Action Handlers ===

async def handle_phase_transition_request(
    orchestrator: Optional[A2AOrchestrator],
    target_phase: str,
    reason: str = "User requested"
) -> Dict[str, Any]:
    """
    Handle a user request to transition phases.

    Can be triggered by a button click in the UI.
    """
    if orchestrator is None:
        return {"success": False, "message": "Orchestration not enabled"}

    try:
        target = Phase(target_phase)
    except ValueError:
        return {"success": False, "message": f"Invalid phase: {target_phase}"}

    success, message = orchestrator.phases.transition(
        target,
        reason,
        triggered_by="user"
    )

    return {
        "success": success,
        "message": message,
        "new_phase": orchestrator.phases.current_phase.value,
        "allowed_next": [p.value for p in orchestrator.phases.get_allowed_transitions()]
    }


async def handle_promote_insight(
    orchestrator: Optional[A2AOrchestrator],
    frame_id: str,
    validation_source: str = "user_confirmed"
) -> Dict[str, Any]:
    """
    Handle a user promoting a frame to an artifact.

    This is called when user confirms an insight as valid.
    """
    if orchestrator is None:
        return {"success": False, "message": "Orchestration not enabled"}

    if orchestrator.current_agent is None:
        return {"success": False, "message": "No current agent"}

    try:
        artifact_id = orchestrator.context.promote_frame_to_artifact(
            orchestrator.current_agent,
            frame_id,
            validation_source
        )
        return {
            "success": True,
            "artifact_id": artifact_id,
            "message": "Insight promoted to validated artifact"
        }
    except ValueError as e:
        return {"success": False, "message": str(e)}


# === Persistence Hooks ===

async def save_a2a_state(orchestrator: Optional[A2AOrchestrator]):
    """
    Save A2A state. Call this periodically or on session end.
    """
    if orchestrator is None:
        return

    try:
        orchestrator.save_state()
        logger.info(f"A2A state saved for session {orchestrator.session_id}")
    except Exception as e:
        logger.error(f"Failed to save A2A state: {e}")


# === Example Integration Code ===

INTEGRATION_EXAMPLE = '''
# In mindrian_chat.py, add these integrations:

from protocols.chat_integration import (
    A2A_ORCHESTRATION_ENABLED,
    init_a2a_session,
    restore_a2a_session,
    pre_process_message,
    post_process_response,
    get_phase_indicator,
    save_a2a_state,
)

@cl.on_chat_start
async def on_chat_start():
    # ... existing initialization code ...

    # Initialize A2A orchestration (if enabled)
    if A2A_ORCHESTRATION_ENABLED:
        session_id = cl.user_session.get("id")
        orchestrator = await init_a2a_session(session_id)
        cl.user_session.set("a2a_orchestrator", orchestrator)


@cl.on_chat_resume
async def on_chat_resume(thread):
    # ... existing resume code ...

    if A2A_ORCHESTRATION_ENABLED:
        session_id = thread["id"]
        orchestrator = await restore_a2a_session(session_id)
        cl.user_session.set("a2a_orchestrator", orchestrator)


@cl.on_message
async def on_message(message: cl.Message):
    orchestrator = cl.user_session.get("a2a_orchestrator")

    # Pre-process with A2A (classification, context)
    if orchestrator:
        pre_result = await pre_process_message(
            message.content,
            orchestrator,
            bot_id
        )

        # Optionally inject context hint into system prompt
        if pre_result.get("context_hint"):
            enriched_context = pre_result["context_hint"]
            # Add to messages or system prompt

    # ... existing bot response generation ...

    # Post-process with A2A (validation, transitions)
    if orchestrator:
        post_result = await post_process_response(
            response_text,
            orchestrator,
            bot_id
        )

        # Show Red Team feedback if needed
        if post_result.get("needs_validation"):
            feedback = post_result["validation_result"]["feedback"]
            await cl.Message(
                content=f"🔴 **Red Team Feedback:** {feedback}",
                author="Red Team"
            ).send()

        # Offer phase transition if suggested
        if post_result.get("suggested_transition"):
            transition = post_result["suggested_transition"]
            # Show transition button/message


@cl.on_stop
async def on_stop():
    orchestrator = cl.user_session.get("a2a_orchestrator")
    await save_a2a_state(orchestrator)
'''
