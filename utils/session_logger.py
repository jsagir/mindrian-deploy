"""
Session Event Logger for Recursive Intelligence

Logs session events (agent switches, phase completions, reactions) to Supabase
for the learning loop. Fire-and-forget async writes - does NOT block main flow.

Phase 1 of Recursive Intelligence implementation.
"""

import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime
from collections import deque
from utils.storage import get_supabase_client

# ============================================
# In-Memory Cache (2GB RAM optimization)
# ============================================
# Keep recent events in memory for fast pattern detection
# Flush to Supabase async - no blocking

_event_buffer: deque = deque(maxlen=1000)  # Last 1000 events in memory
_summary_cache: Dict[str, Dict] = {}  # session_id -> summary (LRU would be better)
_agents_used_tracker: Dict[str, List[str]] = {}  # session_id -> [agents used]

# Stats for monitoring
_stats = {
    "events_logged": 0,
    "events_failed": 0,
    "summaries_logged": 0,
    "summaries_failed": 0,
}


def get_logger_stats() -> Dict[str, int]:
    """Get logging statistics for monitoring."""
    return _stats.copy()


# ============================================
# Event Logging
# ============================================

async def log_session_event(
    session_id: str,
    event_type: str,
    agent: Optional[str] = None,
    from_agent: Optional[str] = None,
    to_agent: Optional[str] = None,
    phase_name: Optional[str] = None,
    signal_type: Optional[str] = None,
    user_initiated: Optional[bool] = None,
    turn_count: Optional[int] = None,
    metadata: Optional[dict] = None
) -> None:
    """
    Log a session event. Fire-and-forget - does NOT block main flow.

    Event types:
    - 'agent_switch': User or system switched bots
    - 'phase_completion': Workshop phase completed
    - 'reaction': User reaction classified (positive/negative/redirect/neutral)

    Args:
        session_id: UUID of the session
        event_type: Type of event
        agent: Current bot ID
        from_agent: For agent_switch - previous bot
        to_agent: For agent_switch - new bot
        phase_name: For phase_completion - name of completed phase
        signal_type: For reaction - positive/negative/redirect/neutral
        user_initiated: Whether user triggered this (vs system/router)
        turn_count: Current turn number in conversation
        metadata: Additional JSON metadata
    """
    event = {
        "session_id": session_id,
        "event_type": event_type,
        "agent": agent,
        "from_agent": from_agent,
        "to_agent": to_agent,
        "phase_name": phase_name,
        "signal_type": signal_type,
        "user_initiated": user_initiated,
        "turn_count": turn_count,
        "metadata": metadata or {},
        "created_at": datetime.utcnow().isoformat()
    }

    # Add to in-memory buffer (instant)
    _event_buffer.append(event)

    # Track agents used per session
    if event_type == "agent_switch" and to_agent:
        if session_id not in _agents_used_tracker:
            _agents_used_tracker[session_id] = []
        if to_agent not in _agents_used_tracker[session_id]:
            _agents_used_tracker[session_id].append(to_agent)

    # Async write to Supabase (non-blocking)
    asyncio.create_task(_write_event_to_supabase(event))


async def _write_event_to_supabase(event: Dict[str, Any]) -> None:
    """Write event to Supabase. Runs in background."""
    try:
        supabase = get_supabase_client()
        if not supabase:
            _stats["events_failed"] += 1
            return

        # Use sync client in thread to avoid blocking
        await asyncio.to_thread(
            lambda: supabase.table("session_events").insert(event).execute()
        )
        _stats["events_logged"] += 1

    except Exception as e:
        _stats["events_failed"] += 1
        print(f"[SessionLogger] Event write failed: {e}")


# ============================================
# Session Summary
# ============================================

async def log_session_summary(
    session_id: str,
    agents_used: Optional[List[str]] = None,
    total_turns: int = 0,
    completed: bool = False,
    frameworks_applied: Optional[List[str]] = None,
    problem_type: Optional[str] = None,
    venture_id: Optional[str] = None,
    user_id: Optional[str] = None
) -> None:
    """
    Log session summary at session end.

    Args:
        session_id: UUID of the session
        agents_used: List of bot IDs used in session
        total_turns: Total conversation turns
        completed: Whether session completed normally
        frameworks_applied: List of frameworks used
        problem_type: Classified problem type (for routing learning)
        venture_id: Optional venture/project ID
        user_id: Optional user ID for cross-session patterns
    """
    # Use tracked agents if not provided
    if agents_used is None:
        agents_used = _agents_used_tracker.get(session_id, [])

    summary = {
        "session_id": session_id,
        "agents_used": agents_used,
        "frameworks_applied": frameworks_applied or [],
        "problem_type": problem_type,
        "total_turns": total_turns,
        "completed": completed,
        "venture_id": venture_id,
        "user_id": user_id,
        "created_at": datetime.utcnow().isoformat()
    }

    # Cache in memory
    _summary_cache[session_id] = summary

    # Async write to Supabase
    asyncio.create_task(_write_summary_to_supabase(summary))

    # Cleanup tracker
    if session_id in _agents_used_tracker:
        del _agents_used_tracker[session_id]


async def _write_summary_to_supabase(summary: Dict[str, Any]) -> None:
    """Write summary to Supabase. Runs in background."""
    try:
        supabase = get_supabase_client()
        if not supabase:
            _stats["summaries_failed"] += 1
            return

        await asyncio.to_thread(
            lambda: supabase.table("session_summaries").upsert(summary).execute()
        )
        _stats["summaries_logged"] += 1

    except Exception as e:
        _stats["summaries_failed"] += 1
        print(f"[SessionLogger] Summary write failed: {e}")


# ============================================
# Helper Functions
# ============================================

def track_agent_start(session_id: str, agent: str) -> None:
    """
    Track initial agent for a session.
    Call this at session start.
    """
    if session_id not in _agents_used_tracker:
        _agents_used_tracker[session_id] = []
    if agent not in _agents_used_tracker[session_id]:
        _agents_used_tracker[session_id].append(agent)


def get_agents_used(session_id: str) -> List[str]:
    """Get list of agents used in a session."""
    return _agents_used_tracker.get(session_id, []).copy()


def get_recent_events(
    session_id: Optional[str] = None,
    event_type: Optional[str] = None,
    limit: int = 100
) -> List[Dict]:
    """
    Get recent events from in-memory buffer.
    Fast - no Supabase query needed.

    Args:
        session_id: Filter by session (optional)
        event_type: Filter by event type (optional)
        limit: Max events to return

    Returns:
        List of event dicts (newest first)
    """
    events = list(_event_buffer)

    if session_id:
        events = [e for e in events if e.get("session_id") == session_id]

    if event_type:
        events = [e for e in events if e.get("event_type") == event_type]

    # Return newest first
    return list(reversed(events))[:limit]


def get_session_summary(session_id: str) -> Optional[Dict]:
    """Get cached session summary (if available)."""
    return _summary_cache.get(session_id)


# ============================================
# Batch Operations (for 2GB optimization)
# ============================================

async def flush_event_buffer() -> int:
    """
    Flush all buffered events to Supabase.
    Call this periodically or on shutdown.

    Returns:
        Number of events flushed
    """
    if not _event_buffer:
        return 0

    events = list(_event_buffer)
    _event_buffer.clear()

    try:
        supabase = get_supabase_client()
        if not supabase:
            return 0

        # Batch insert
        await asyncio.to_thread(
            lambda: supabase.table("session_events").insert(events).execute()
        )
        return len(events)

    except Exception as e:
        print(f"[SessionLogger] Batch flush failed: {e}")
        # Put events back in buffer
        _event_buffer.extend(events)
        return 0


def clear_caches() -> None:
    """Clear all in-memory caches. Call on shutdown."""
    _event_buffer.clear()
    _summary_cache.clear()
    _agents_used_tracker.clear()
