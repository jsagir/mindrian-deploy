"""
Session Distiller for Recursive Intelligence

Processes completed sessions to extract and store insights.
Runs at session end or as a batch job.

Phase 3 of Recursive Intelligence implementation.
"""

import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from utils.insight_extractor import (
    extract_from_conversation,
    extract_dead_ends,
    extract_cross_connections,
    store_extraction,
    SessionExtraction,
    ExtractedInsight,
    InsightType,
    Confidence
)
from utils.session_logger import log_session_summary, get_agents_used


async def distill_session(
    session_id: str,
    history: List[dict],
    agents_used: Optional[List[str]] = None,
    current_agent: str = "lawrence",
    completed: bool = True
) -> Dict[str, Any]:
    """
    Distill a session into structured insights and summary.

    This is the main entry point for session processing.
    Call at session end or when user leaves.

    Args:
        session_id: UUID of the session
        history: Conversation history
        agents_used: List of agents used (auto-detected if None)
        current_agent: Current/last agent
        completed: Whether session completed normally

    Returns:
        Dict with extraction results and stats
    """
    results = {
        "session_id": session_id,
        "success": False,
        "insights_extracted": 0,
        "frameworks_detected": [],
        "problem_type": None,
        "dead_ends_found": 0,
        "cross_connections_found": 0,
    }

    try:
        # Get agents used if not provided
        if agents_used is None:
            agents_used = get_agents_used(session_id) or [current_agent]

        # Main extraction
        extraction = extract_from_conversation(
            history=history,
            session_id=session_id,
            current_agent=current_agent
        )

        # Add dead-end extraction
        dead_ends = extract_dead_ends(history, current_agent)
        extraction.insights.extend(dead_ends)

        # Add cross-connection extraction
        connections = extract_cross_connections(history, current_agent)
        extraction.insights.extend(connections)

        # Store insights to Supabase
        stored = await store_extraction(extraction)

        # Log session summary
        await log_session_summary(
            session_id=session_id,
            agents_used=agents_used,
            total_turns=len(history),
            completed=completed,
            frameworks_applied=extraction.frameworks_used,
            problem_type=extraction.problem_type,
        )

        # Build results
        results["success"] = stored
        results["insights_extracted"] = len(extraction.insights)
        results["frameworks_detected"] = extraction.frameworks_used
        results["problem_type"] = extraction.problem_type
        results["dead_ends_found"] = len(dead_ends)
        results["cross_connections_found"] = len(connections)

        print(f"[SessionDistiller] Distilled session {session_id}: "
              f"{len(extraction.insights)} insights, "
              f"{len(extraction.frameworks_used)} frameworks")

    except Exception as e:
        print(f"[SessionDistiller] Error distilling {session_id}: {e}")
        results["error"] = str(e)

    return results


async def batch_distill_pending_sessions(limit: int = 50) -> Dict[str, Any]:
    """
    Process pending sessions that haven't been distilled yet.

    This can be run as a scheduled job (e.g., daily).

    Args:
        limit: Max sessions to process in one batch

    Returns:
        Summary of batch processing
    """
    try:
        from utils.storage import get_supabase_client

        supabase = get_supabase_client()
        if not supabase:
            return {"success": False, "error": "Supabase not configured"}

        # Find sessions with events but no insights yet
        # This is a simple heuristic - sessions with reactions but no extracted insights
        result = await asyncio.to_thread(
            lambda: supabase.rpc(
                "get_undistilled_sessions",
                {"limit_count": limit}
            ).execute()
        )

        sessions = result.data if result.data else []

        processed = 0
        errors = 0

        for session in sessions:
            try:
                # Fetch session history from thread storage
                # Note: This requires the conversation to be stored
                session_id = session.get("session_id")

                # For now, log that we found it
                # Full implementation would fetch history from Chainlit storage
                print(f"[BatchDistill] Would process session {session_id}")
                processed += 1

            except Exception as e:
                print(f"[BatchDistill] Error: {e}")
                errors += 1

        return {
            "success": True,
            "sessions_found": len(sessions),
            "processed": processed,
            "errors": errors,
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================
# Integration Helper for mindrian_chat.py
# ============================================

async def on_session_end(session_id: str, history: List[dict], bot_id: str):
    """
    Call this when a session ends (user leaves, timeout, etc.).

    Fire-and-forget - doesn't block user experience.
    """
    # Run distillation in background
    asyncio.create_task(
        distill_session(
            session_id=session_id,
            history=history,
            current_agent=bot_id,
            completed=True
        )
    )


async def on_significant_turn(
    session_id: str,
    history: List[dict],
    bot_id: str,
    turn_count: int
) -> Optional[str]:
    """
    Check for insights at significant conversation milestones.

    Call this every N turns (e.g., every 5 turns) to catch insights
    without waiting for session end.

    Returns:
        Optional hint for the system (e.g., "user_struggling")
    """
    # Only process at milestones
    if turn_count < 5 or turn_count % 5 != 0:
        return None

    try:
        # Quick dead-end check
        dead_ends = extract_dead_ends(history[-10:], bot_id)  # Last 10 messages

        if len(dead_ends) >= 2:
            return "user_struggling"  # Signal to offer help

        # Check for framework switch patterns
        extraction = extract_from_conversation(
            history=history[-10:],
            session_id=session_id,
            current_agent=bot_id
        )

        if len(extraction.frameworks_used) >= 2:
            return "framework_hopping"  # Signal to ground in one approach

    except Exception as e:
        print(f"[SignificantTurn] Error (non-critical): {e}")

    return None


# ============================================
# SQL Function for Batch Processing
# ============================================

GET_UNDISTILLED_SESSIONS_SQL = """
-- Create this function in Supabase if batch processing is needed:
CREATE OR REPLACE FUNCTION get_undistilled_sessions(limit_count INT DEFAULT 50)
RETURNS TABLE(session_id UUID) AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT se.session_id
    FROM session_events se
    WHERE se.event_type = 'reaction'
      AND NOT EXISTS (
          SELECT 1 FROM session_insights si
          WHERE si.session_id = se.session_id
      )
    ORDER BY se.session_id
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;
"""


if __name__ == "__main__":
    # Test distillation
    import asyncio

    test_history = [
        {"role": "user", "content": "I want to validate my startup idea for a food delivery app"},
        {"role": "model", "content": "Let's use Triple Validation to assess this. First, Is it Real?"},
        {"role": "user", "content": "I think so, but I realize my assumption about customer willingness to pay is untested"},
        {"role": "model", "content": "That's a critical insight! Untested assumptions are risky."},
        {"role": "user", "content": "The feature comparison approach was a dead end"},
        {"role": "model", "content": "Good to recognize that. What if we use JTBD instead?"},
        {"role": "user", "content": "Yes! JTBD connects to the progress customers want, not features"},
        {"role": "model", "content": "Exactly. What progress are they trying to make?"},
    ]

    async def test():
        result = await distill_session(
            session_id="test-session-123",
            history=test_history,
            current_agent="validation",
            completed=True
        )
        print("\nDistillation Results:")
        print("=" * 60)
        for k, v in result.items():
            print(f"  {k}: {v}")

    asyncio.run(test())
