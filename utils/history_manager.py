"""
Conversation History Manager
============================

Implements bounded conversation history with:
- Sliding window (max 50 messages by default)
- Optional context summarization for older messages
- Memory-safe for 512MB instances

Usage:
    from utils.history_manager import (
        add_to_history,
        get_bounded_history,
        compact_history_if_needed,
        MAX_HISTORY_LENGTH,
    )

    # In message handlers:
    history = cl.user_session.get("history", [])
    history = add_to_history(history, role="user", content=message)
    cl.user_session.set("history", history)
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("history_manager")

# Configuration
MAX_HISTORY_LENGTH = 50  # Keep last 50 messages
COMPACT_THRESHOLD = 60   # Start compaction when history exceeds this
SUMMARY_OLDER_THAN = 30  # Messages older than this get summarized

# Token limits for context building
MAX_CONTEXT_TOKENS_ESTIMATE = 30000  # ~30K chars for Gemini context
CHARS_PER_MESSAGE_LIMIT = 2000  # Truncate individual messages


def add_to_history(
    history: List[Dict[str, str]],
    role: str,
    content: str,
    max_length: int = MAX_HISTORY_LENGTH,
    truncate_content: bool = True,
) -> List[Dict[str, str]]:
    """
    Add a message to history while enforcing bounds.

    Args:
        history: Current conversation history
        role: Message role ("user", "model", "assistant")
        content: Message content
        max_length: Maximum history length (default: 50)
        truncate_content: Whether to truncate long messages

    Returns:
        Updated history list (bounded)
    """
    # Truncate content if too long
    if truncate_content and len(content) > CHARS_PER_MESSAGE_LIMIT:
        content = content[:CHARS_PER_MESSAGE_LIMIT] + "..."
        logger.debug("Truncated message content (was %d chars)", len(content))

    # Add the new message
    history.append({"role": role, "content": content})

    # Enforce sliding window
    if len(history) > max_length:
        removed_count = len(history) - max_length
        history = history[-max_length:]
        logger.debug("Sliding window: removed %d old messages", removed_count)

    return history


def get_bounded_history(
    history: List[Dict[str, str]],
    max_length: int = MAX_HISTORY_LENGTH,
    max_total_chars: int = MAX_CONTEXT_TOKENS_ESTIMATE,
) -> List[Dict[str, str]]:
    """
    Get a bounded view of history for LLM context.

    Args:
        history: Full conversation history
        max_length: Maximum number of messages
        max_total_chars: Maximum total character count

    Returns:
        Bounded history list
    """
    if not history:
        return []

    # First bound by count
    bounded = history[-max_length:] if len(history) > max_length else history

    # Then bound by total characters
    total_chars = sum(len(m.get("content", "")) for m in bounded)

    if total_chars > max_total_chars:
        # Remove oldest messages until under limit
        while bounded and total_chars > max_total_chars:
            removed = bounded.pop(0)
            total_chars -= len(removed.get("content", ""))

    return bounded


def compact_history_if_needed(
    history: List[Dict[str, str]],
    threshold: int = COMPACT_THRESHOLD,
    keep_recent: int = 30,
) -> List[Dict[str, str]]:
    """
    Compact history by removing/summarizing old messages if over threshold.

    This is a simple approach that keeps recent messages and drops older ones.
    For advanced use, consider adding LLM summarization.

    Args:
        history: Current history
        threshold: Trigger compaction when history exceeds this
        keep_recent: Number of recent messages to keep

    Returns:
        Compacted history
    """
    if len(history) <= threshold:
        return history

    logger.info("Compacting history: %d -> %d messages", len(history), keep_recent)

    # Keep only recent messages
    return history[-keep_recent:]


def estimate_history_tokens(history: List[Dict[str, str]]) -> int:
    """
    Estimate token count for history (rough approximation).

    Uses ~4 chars per token as a rough estimate.

    Args:
        history: Conversation history

    Returns:
        Estimated token count
    """
    total_chars = sum(len(m.get("content", "")) for m in history)
    return total_chars // 4


def build_llm_context(
    history: List[Dict[str, str]],
    system_prompt: str = "",
    max_context_tokens: int = 30000,
) -> List[Dict[str, str]]:
    """
    Build an LLM-ready context from history.

    Ensures the context fits within token limits, prioritizing recent messages.

    Args:
        history: Full conversation history
        system_prompt: System prompt to include
        max_context_tokens: Maximum tokens for the context

    Returns:
        List of messages ready for LLM
    """
    # Reserve space for system prompt
    system_tokens = len(system_prompt) // 4 if system_prompt else 0
    available_tokens = max_context_tokens - system_tokens

    # Get bounded history
    bounded = get_bounded_history(history, max_total_chars=available_tokens * 4)

    # Build context
    context = []

    if system_prompt:
        context.append({"role": "system", "content": system_prompt})

    context.extend(bounded)

    return context


def get_history_stats(history: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Get statistics about the conversation history.

    Useful for debugging and monitoring.

    Args:
        history: Conversation history

    Returns:
        Dict with stats
    """
    if not history:
        return {
            "message_count": 0,
            "user_messages": 0,
            "model_messages": 0,
            "total_chars": 0,
            "estimated_tokens": 0,
        }

    user_messages = sum(1 for m in history if m.get("role") == "user")
    model_messages = sum(1 for m in history if m.get("role") in ("model", "assistant"))
    total_chars = sum(len(m.get("content", "")) for m in history)

    return {
        "message_count": len(history),
        "user_messages": user_messages,
        "model_messages": model_messages,
        "total_chars": total_chars,
        "estimated_tokens": total_chars // 4,
        "avg_message_length": total_chars // len(history) if history else 0,
    }


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'add_to_history',
    'get_bounded_history',
    'compact_history_if_needed',
    'estimate_history_tokens',
    'build_llm_context',
    'get_history_stats',
    'MAX_HISTORY_LENGTH',
    'COMPACT_THRESHOLD',
]
