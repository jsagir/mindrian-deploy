"""
Session Memory Integration
===========================

Lightweight integration layer that connects:
- User LazyGraph (per-user memory across sessions)
- LightRAG Opportunity Bank (domain/relevancy tracking)
- Mindrian Chat (main conversation handler)

This module provides simple hooks to call from mindrian_chat.py
without adding complexity to the main file.

Usage in mindrian_chat.py:
    from tools.session_memory import (
        on_session_start,
        on_message_processed,
        on_session_end,
        get_user_context,
    )

    # In on_chat_start:
    await on_session_start(user_id, session_id, bot_id)

    # After each message:
    await on_message_processed(user_id, session_id, conversation, bot_id, phase)

    # When session ends:
    await on_session_end(user_id, session_id)
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional

logger = logging.getLogger("session_memory")

# Track which sessions have been processed to avoid duplicates
_processed_turns = {}  # session_id -> last_turn_count
_PROCESS_INTERVAL = 5  # Process memory every N turns


async def on_session_start(
    user_id: str,
    session_id: str,
    bot_id: str = ""
) -> Optional[str]:
    """
    Called when a new chat session starts.

    Returns user context string if returning user, None if new user.
    """
    if not user_id:
        return None

    try:
        from tools.user_lazygraph import load_user_memory, store_session, UserSession

        # Store session start
        await store_session(UserSession(
            session_id=session_id,
            user_id=user_id,
            started_at="",
            bot_id=bot_id,
            turn_count=0,
        ))

        # Load user memory for context
        memory = await load_user_memory(user_id)

        if not memory.sessions or len(memory.sessions) <= 1:
            logger.info(f"New user started session: {user_id}")
            return None

        # Build context for returning user
        parts = []
        parts.append(f"Returning user ({len(memory.sessions)} sessions)")

        if memory.problems:
            recent_probs = [p.name for p in memory.problems[:3]]
            parts.append(f"Previously explored: {', '.join(recent_probs)}")

        if memory.frameworks_used:
            parts.append(f"Familiar with: {', '.join(memory.frameworks_used[:5])}")

        if memory.domains_explored:
            parts.append(f"Domains: {', '.join(memory.domains_explored[:3])}")

        # Check for untested assumptions
        untested = [a for a in memory.assumptions if a.status == "untested"]
        if untested:
            parts.append(f"Has {len(untested)} untested assumptions")

        context = ". ".join(parts)
        logger.info(f"Returning user: {user_id} - {context}")
        return context

    except ImportError:
        logger.debug("user_lazygraph not available")
        return None
    except Exception as e:
        logger.warning(f"Session start error: {e}")
        return None


async def on_message_processed(
    user_id: str,
    session_id: str,
    conversation: List[Dict[str, str]],
    bot_id: str = "",
    phase: str = "",
    force: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Called after a message is processed.

    Extracts entities and updates user graph every N turns.
    Set force=True to process immediately (e.g., on important messages).

    Returns extraction result if processing occurred, None otherwise.
    """
    if not user_id or not session_id:
        return None

    turn_count = len(conversation)
    last_processed = _processed_turns.get(session_id, 0)

    # Only process every N turns (unless forced)
    if not force and (turn_count - last_processed) < _PROCESS_INTERVAL:
        return None

    try:
        from tools.user_lazygraph import process_conversation_turn

        result = await process_conversation_turn(
            user_id=user_id,
            session_id=session_id,
            conversation=conversation,
            bot_id=bot_id,
            phase=phase,
        )

        _processed_turns[session_id] = turn_count

        if result.get("stored", {}).get("problems", 0) > 0:
            logger.info(
                f"User graph updated: {user_id} - "
                f"probs={result['stored']['problems']}, "
                f"assums={result['stored']['assumptions']}, "
                f"insights={result['stored']['insights']}"
            )

        return result

    except ImportError:
        logger.debug("user_lazygraph not available")
        return None
    except Exception as e:
        logger.warning(f"Message processing error: {e}")
        return None


async def on_opportunity_found(
    opportunity_data: Dict[str, Any],
    user_id: str = "",
    session_id: str = ""
) -> Optional[Dict[str, Any]]:
    """
    Called when an opportunity is identified.

    Stores with LightRAG enhancement (domain/relevancy extraction).
    """
    try:
        from tools.opportunity_bank import Opportunity
        from tools.opportunity_bank_lightrag import store_opportunity_with_lightrag

        # Build opportunity from data
        opp = Opportunity(
            id=opportunity_data.get("id", ""),
            name=opportunity_data.get("name", opportunity_data.get("title", "")),
            description=opportunity_data.get("description", ""),
            problem=opportunity_data.get("problem", ""),
            value_potential=opportunity_data.get("value_potential", "medium"),
            domain=opportunity_data.get("domain", ""),
            job_to_be_done=opportunity_data.get("job_to_be_done", ""),
            frameworks_applied=opportunity_data.get("frameworks_applied", []),
            tags=opportunity_data.get("tags", []),
            source_bot=opportunity_data.get("source_bot", ""),
        )

        result = await store_opportunity_with_lightrag(
            opportunity=opp,
            user_id=user_id,
            session_id=session_id,
        )

        logger.info(f"Opportunity stored with LightRAG: {opp.name}")
        return result

    except ImportError:
        logger.debug("opportunity_bank_lightrag not available")
        return None
    except Exception as e:
        logger.warning(f"Opportunity storage error: {e}")
        return None


async def on_session_end(
    user_id: str,
    session_id: str,
    conversation: List[Dict[str, str]] = None
) -> Optional[Dict[str, Any]]:
    """
    Called when a session ends.

    Does final extraction and updates session turn count.
    """
    if not user_id or not session_id:
        return None

    try:
        from tools.user_lazygraph import store_session, UserSession

        # Final processing of any remaining messages
        if conversation:
            await on_message_processed(
                user_id=user_id,
                session_id=session_id,
                conversation=conversation,
                force=True,  # Force final extraction
            )

        # Update session with final turn count
        await store_session(UserSession(
            session_id=session_id,
            user_id=user_id,
            started_at="",
            turn_count=len(conversation) if conversation else 0,
        ))

        # Clean up tracking
        if session_id in _processed_turns:
            del _processed_turns[session_id]

        logger.info(f"Session ended: {user_id}/{session_id}")
        return {"success": True}

    except ImportError:
        return None
    except Exception as e:
        logger.warning(f"Session end error: {e}")
        return None


async def get_user_context(user_id: str) -> str:
    """
    Get a concise context string about the user for injection into prompts.

    Returns empty string for new users.
    """
    if not user_id:
        return ""

    try:
        from tools.user_lazygraph import get_user_context_for_llm
        return await get_user_context_for_llm(user_id, max_items=5)

    except ImportError:
        return ""
    except Exception as e:
        logger.warning(f"Get user context error: {e}")
        return ""


async def extract_opportunities_with_lightrag(
    conversation: List[Dict[str, str]],
    bot_id: str = "unknown",
    methodology: str = "",
    phase: str = "",
    conversation_id: str = "",
    user_id: str = ""
) -> Dict[str, Any]:
    """
    Extract and store opportunities using LightRAG enhancement.

    Call this instead of extract_and_store_opportunities for full integration.
    """
    try:
        from tools.opportunity_bank_lightrag import extract_and_store_with_lightrag

        return await extract_and_store_with_lightrag(
            conversation=conversation,
            bot_id=bot_id,
            methodology=methodology,
            phase=phase,
            conversation_id=conversation_id,
            user_id=user_id,
        )

    except ImportError:
        # Fall back to basic opportunity extraction
        try:
            from tools.opportunity_bank import extract_and_store_opportunities
            opps, summary = await extract_and_store_opportunities(
                conversation=conversation,
                bot_id=bot_id,
                methodology=methodology,
                phase=phase,
                conversation_id=conversation_id,
                user_id=user_id,
            )
            return summary
        except ImportError:
            return {"extracted": 0, "stored": 0}

    except Exception as e:
        logger.warning(f"Opportunity extraction error: {e}")
        return {"extracted": 0, "stored": 0}


def get_memory_stats() -> Dict[str, Any]:
    """
    Get statistics about the session memory system.
    """
    stats = {
        "active_sessions": len(_processed_turns),
        "process_interval": _PROCESS_INTERVAL,
    }

    try:
        from tools.user_lazygraph import get_cache_stats
        stats["user_cache"] = get_cache_stats()
    except ImportError:
        pass

    return stats
