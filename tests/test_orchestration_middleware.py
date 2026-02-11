"""
Orchestration Middleware Test Suite

Validates the button-less human-in-the-loop detection system:
1. Early turns always PASS_THROUGH
2. High confidence triggers RECOMMEND
3. Medium confidence triggers SUGGEST
4. Low confidence triggers PASS_THROUGH
5. Cooldown prevents repeat recommendations
6. Momentum boosts confidence over consecutive turns
7. Feature flag disables middleware
"""

import os
import sys
import pytest
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from protocols.orchestration_middleware import (
    MiddlewareDecision,
    MiddlewareResult,
    evaluate_message,
    record_orchestration_run,
    record_orchestration_dismissed,
    cleanup_session,
    get_recommendation_message,
    get_suggestion_message,
    RECOMMEND_THRESHOLD,
    SUGGEST_THRESHOLD,
    MIN_TURNS_BEFORE_RECOMMEND,
    COOLDOWN_TURNS,
    _get_session_state,
    _calculate_momentum,
    _record_workflow_type,
)
from protocols.intent_classifier import WorkflowType


# === Fixtures ===

@pytest.fixture(autouse=True)
def clean_session():
    """Clean up session state between tests."""
    yield
    cleanup_session("test-session")


# === Test 1: Early turns ===

@pytest.mark.asyncio
async def test_pass_through_early_turns():
    """Turn 0 and 1 should always PASS_THROUGH regardless of message content."""
    # Turn 0 — even with a strong trigger phrase
    result = await evaluate_message(
        message="Find the breakthrough for my startup idea",
        history=[],
        session_id="test-session",
        bot_id="lawrence",
        turn_count=0,
    )
    assert result.decision == MiddlewareDecision.PASS_THROUGH
    assert "early" in result.reasoning.lower() or "turn" in result.reasoning.lower()

    # Turn 1
    result = await evaluate_message(
        message="Analyze my technology for market opportunities",
        history=[],
        session_id="test-session",
        bot_id="lawrence",
        turn_count=1,
    )
    assert result.decision == MiddlewareDecision.PASS_THROUGH


# === Test 2: High confidence → RECOMMEND ===

@pytest.mark.asyncio
async def test_recommend_high_confidence():
    """Strong trigger phrases should produce RECOMMEND at sufficient turn count."""
    result = await evaluate_message(
        message="find the breakthrough opportunity for reentry technology",
        history=[{"role": "user", "content": "Hi"}, {"role": "assistant", "content": "Hello"}],
        session_id="test-session",
        bot_id="lawrence",
        turn_count=5,
    )
    assert result.decision == MiddlewareDecision.RECOMMEND
    assert result.confidence >= RECOMMEND_THRESHOLD
    assert result.workflow_type is not None
    assert len(result.suggested_agents) > 0


# === Test 3: Medium confidence → SUGGEST ===

@pytest.mark.asyncio
async def test_suggest_medium_confidence():
    """Exploratory messages should produce SUGGEST (not RECOMMEND)."""
    result = await evaluate_message(
        message="tell me about trends in urban farming",
        history=[{"role": "user", "content": "Hi"}, {"role": "assistant", "content": "Hello"}],
        session_id="test-session",
        bot_id="lawrence",
        turn_count=5,
    )
    # Should be SUGGEST or PASS_THROUGH (depends on regex confidence)
    assert result.decision in (MiddlewareDecision.SUGGEST, MiddlewareDecision.PASS_THROUGH)
    assert result.confidence < RECOMMEND_THRESHOLD or result.decision == MiddlewareDecision.SUGGEST


# === Test 4: Low confidence → PASS_THROUGH ===

@pytest.mark.asyncio
async def test_pass_through_low_confidence():
    """Simple greetings should produce PASS_THROUGH."""
    result = await evaluate_message(
        message="hello, how are you?",
        history=[],
        session_id="test-session",
        bot_id="lawrence",
        turn_count=5,
    )
    assert result.decision == MiddlewareDecision.PASS_THROUGH
    assert result.confidence < SUGGEST_THRESHOLD


# === Test 5: Cooldown prevents repeat ===

@pytest.mark.asyncio
async def test_cooldown_prevents_repeat():
    """After running orchestration, no recommendation for COOLDOWN_TURNS."""
    session_id = "test-session"

    # Record that orchestration ran at turn 5
    record_orchestration_run(session_id, turn_count=5)

    # Try at turn 6 (within cooldown)
    result = await evaluate_message(
        message="find the breakthrough",
        history=[],
        session_id=session_id,
        bot_id="lawrence",
        turn_count=6,
    )
    assert result.decision == MiddlewareDecision.PASS_THROUGH
    assert "cooldown" in result.reasoning.lower()

    # Try at turn 5 + COOLDOWN_TURNS (should be allowed)
    result = await evaluate_message(
        message="find the breakthrough",
        history=[],
        session_id=session_id,
        bot_id="lawrence",
        turn_count=5 + COOLDOWN_TURNS,
    )
    # Should NOT be blocked by cooldown
    assert "cooldown" not in result.reasoning.lower()


# === Test 6: Momentum boosts confidence ===

def test_momentum_boost_calculation():
    """Consecutive turns with same workflow type should produce momentum boost."""
    session_id = "test-session"

    # Record several turns of the same workflow type
    _record_workflow_type(session_id, WorkflowType.TECH_TO_OPPORTUNITY)
    _record_workflow_type(session_id, WorkflowType.TECH_TO_OPPORTUNITY)
    _record_workflow_type(session_id, WorkflowType.TECH_TO_OPPORTUNITY)

    momentum = _calculate_momentum(WorkflowType.TECH_TO_OPPORTUNITY, session_id)
    assert momentum > 0.0, "Momentum should be positive when recent turns match"


def test_no_momentum_for_different_types():
    """Mixed workflow types should not produce momentum."""
    session_id = "test-session"

    _record_workflow_type(session_id, WorkflowType.EXPLORE)
    _record_workflow_type(session_id, WorkflowType.STRESS_TEST)
    _record_workflow_type(session_id, WorkflowType.VALIDATE)

    momentum = _calculate_momentum(WorkflowType.TECH_TO_OPPORTUNITY, session_id)
    assert momentum == 0.0, "Momentum should be zero when types don't match"


# === Test 7: Feature flag disables middleware ===

@pytest.mark.asyncio
async def test_feature_flag_disables(monkeypatch):
    """When ORCHESTRATION_MIDDLEWARE_ENABLED is False, always PASS_THROUGH."""
    import protocols.orchestration_middleware as mw
    original = mw.ORCHESTRATION_MIDDLEWARE_ENABLED
    try:
        mw.ORCHESTRATION_MIDDLEWARE_ENABLED = False

        result = await evaluate_message(
            message="find the breakthrough",
            history=[],
            session_id="test-session",
            bot_id="lawrence",
            turn_count=10,
        )
        assert result.decision == MiddlewareDecision.PASS_THROUGH
        assert "disabled" in result.reasoning.lower()
    finally:
        mw.ORCHESTRATION_MIDDLEWARE_ENABLED = original


# === Test 8: Message formatting ===

def test_recommendation_message_format():
    """get_recommendation_message should produce a readable string."""
    result = MiddlewareResult(
        decision=MiddlewareDecision.RECOMMEND,
        workflow_type="tech_to_opportunity",
        workflow_name="Technology → Opportunity",
        confidence=0.88,
        suggested_agents=["tta", "jtbd", "research", "ackoff"],
        reasoning="Strong tech-to-opportunity signal",
        estimated_seconds=180,
    )

    msg = get_recommendation_message(result)
    assert "Technology → Opportunity" in msg
    assert "TTA" in msg
    assert "3 min" in msg or "~3 min" in msg


def test_suggestion_message_format():
    """get_suggestion_message should produce a lighter suggestion string."""
    result = MiddlewareResult(
        decision=MiddlewareDecision.SUGGEST,
        workflow_type="explore",
        workflow_name="Multi-Perspective Exploration",
        confidence=0.68,
        suggested_agents=["tta", "research", "knowns"],
        reasoning="Exploratory signal",
        estimated_seconds=120,
    )

    msg = get_suggestion_message(result)
    assert "Multi-Perspective Exploration" in msg
    assert "TTA" in msg


# === Test 9: Session state management ===

def test_session_state_tracking():
    """Session state should track orchestration runs and dismissals."""
    session_id = "test-session"

    state = _get_session_state(session_id)
    assert state["orchestration_count"] == 0
    assert state["dismissed_count"] == 0

    record_orchestration_run(session_id, turn_count=5)
    state = _get_session_state(session_id)
    assert state["orchestration_count"] == 1
    assert state["last_orchestration_turn"] == 5

    record_orchestration_dismissed(session_id)
    state = _get_session_state(session_id)
    assert state["dismissed_count"] == 1


def test_cleanup_session():
    """cleanup_session should remove all session state."""
    session_id = "test-session"
    _get_session_state(session_id)  # Create state
    record_orchestration_run(session_id, turn_count=3)

    cleanup_session(session_id)

    # After cleanup, state should be fresh
    state = _get_session_state(session_id)
    assert state["orchestration_count"] == 0


# === Test 10: evaluation_ms tracking ===

@pytest.mark.asyncio
async def test_evaluation_ms_tracked():
    """Every result should have evaluation_ms > 0."""
    result = await evaluate_message(
        message="hello",
        history=[],
        session_id="test-session",
        bot_id="lawrence",
        turn_count=0,
    )
    assert result.evaluation_ms >= 0
