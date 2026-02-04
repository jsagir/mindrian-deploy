"""
Mindrian Memory Module
======================

Conductor-style persistent memory management combining:
- Neo4j: User journey graph (relationships, frameworks, insights)
- Supabase: Artifacts storage (specs, extractions, evidence)
- PostgreSQL: LangGraph checkpoints (conversation state)

Usage:
    from memory import JourneyStore, get_journey_context

    # Create/load user journey
    store = JourneyStore(user_id="user_123")
    journey = await store.get_or_create_journey(problem="How can AI improve education?")

    # Get context for agent prompts
    context = await store.get_journey_context()

    # Update after pipeline completion
    await store.update_phase("tta", insights=[...])
"""

from .user_journey import (
    UserJourney,
    JourneyStore,
    get_journey_context,
    get_postgres_checkpointer,
)

from .checkpointer import (
    get_shared_checkpointer,
    create_thread_id,
)

__all__ = [
    "UserJourney",
    "JourneyStore",
    "get_journey_context",
    "get_postgres_checkpointer",
    "get_shared_checkpointer",
    "create_thread_id",
]
