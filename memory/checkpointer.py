"""
Centralized Checkpointer Management
===================================

Provides a shared PostgreSQL checkpointer for all LangGraph pipelines.
Ensures consistent state persistence across the application.
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Global checkpointer instance (singleton pattern)
_shared_checkpointer = None
_checkpointer_initialized = False


async def get_shared_checkpointer():
    """
    Get the shared PostgreSQL checkpointer for all pipelines.

    Uses singleton pattern to avoid multiple connections.
    Falls back to MemorySaver if Postgres is unavailable.
    """
    global _shared_checkpointer, _checkpointer_initialized

    if _checkpointer_initialized:
        return _shared_checkpointer

    try:
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

        database_url = os.getenv("DATABASE_URL") or os.getenv("CHAINLIT_DATABASE_URL")

        if not database_url:
            logger.warning("DATABASE_URL not found - using in-memory checkpointer")
            from langgraph.checkpoint.memory import MemorySaver
            _shared_checkpointer = MemorySaver()
            _checkpointer_initialized = True
            return _shared_checkpointer

        # Create PostgreSQL checkpointer
        _shared_checkpointer = AsyncPostgresSaver.from_conn_string(database_url)
        await _shared_checkpointer.setup()

        logger.info("✅ Shared PostgreSQL checkpointer initialized")
        _checkpointer_initialized = True
        return _shared_checkpointer

    except ImportError as e:
        logger.warning(f"PostgreSQL checkpointer not available: {e}")
        from langgraph.checkpoint.memory import MemorySaver
        _shared_checkpointer = MemorySaver()
        _checkpointer_initialized = True
        return _shared_checkpointer

    except Exception as e:
        logger.error(f"Checkpointer initialization failed: {e}")
        from langgraph.checkpoint.memory import MemorySaver
        _shared_checkpointer = MemorySaver()
        _checkpointer_initialized = True
        return _shared_checkpointer


def create_thread_id(
    user_id: str,
    pipeline: str = "default",
    journey_id: str = None,
    session_id: str = None
) -> str:
    """
    Create a consistent thread ID for LangGraph checkpointing.

    Thread IDs determine checkpoint scope:
    - Same thread_id = resume from previous state
    - Different thread_id = fresh start

    Format: {pipeline}_{user_id}_{journey_id}_{session_id}

    Args:
        user_id: User identifier
        pipeline: Pipeline name (minto, bono, grading, etc.)
        journey_id: Optional journey ID for journey-scoped state
        session_id: Optional session ID for session-scoped state

    Returns:
        Consistent thread ID string
    """
    parts = [pipeline, user_id]

    if journey_id:
        parts.append(journey_id)
    if session_id:
        parts.append(session_id[:12])  # Truncate session ID

    return "_".join(parts)


async def get_checkpoint_state(thread_id: str) -> Optional[dict]:
    """
    Retrieve the latest checkpoint state for a thread.

    Useful for inspecting what state was saved.
    """
    checkpointer = await get_shared_checkpointer()

    if not checkpointer:
        return None

    try:
        config = {"configurable": {"thread_id": thread_id}}
        state = await checkpointer.aget(config)
        return state
    except Exception as e:
        logger.error(f"Failed to get checkpoint state: {e}")
        return None


async def list_thread_checkpoints(thread_id: str, limit: int = 10) -> list:
    """
    List recent checkpoints for a thread.

    Useful for implementing time-travel / revert functionality.
    """
    checkpointer = await get_shared_checkpointer()

    if not checkpointer:
        return []

    try:
        config = {"configurable": {"thread_id": thread_id}}
        checkpoints = []

        async for checkpoint in checkpointer.alist(config, limit=limit):
            checkpoints.append({
                "id": checkpoint.config.get("configurable", {}).get("checkpoint_id"),
                "thread_id": thread_id,
                "ts": checkpoint.checkpoint.get("ts"),
            })

        return checkpoints
    except Exception as e:
        logger.error(f"Failed to list checkpoints: {e}")
        return []


async def reset_checkpointer():
    """Reset the shared checkpointer (useful for testing)."""
    global _shared_checkpointer, _checkpointer_initialized
    _shared_checkpointer = None
    _checkpointer_initialized = False
