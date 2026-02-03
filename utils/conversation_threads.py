"""
Conversation Threads - Topic-Aware Context Management
=====================================================
Fixes the context-mixing bug by tracking conversations by topic, not just by user.

The Problem:
- User talks about WWI lesson plans with Nested Hierarchies
- User switches to Scenario Analysis for gamification
- User switches back, says "continue from above"
- System loads gamification context instead of WWI

The Solution:
- Track conversations by topic (thread_id)
- Each distinct topic gets its own thread
- "Continue from above" matches to the correct thread

Usage:
    from utils.conversation_threads import (
        get_or_create_thread,
        get_thread_for_topic,
        save_thread_context,
        get_active_threads,
    )

    # When starting a conversation
    thread_id = get_or_create_thread(user_key, bot_id, topic_keywords)

    # When saving context
    save_thread_context(thread_id, history, phases)

    # When user says "continue" - find the right thread
    thread = get_thread_for_topic(user_key, topic_keywords)
"""

import os
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import logging

logger = logging.getLogger("conversation_threads")

# =============================================================================
# IN-MEMORY THREAD STORE (Postgres-backed when available)
# =============================================================================

# Structure: {user_key: {thread_id: ThreadContext}}
_thread_store: Dict[str, Dict[str, Dict[str, Any]]] = {}


class ThreadContext:
    """Represents a conversation thread."""

    def __init__(
        self,
        thread_id: str,
        user_key: str,
        bot_id: str,
        topic_keywords: List[str],
        created_at: str = None,
    ):
        self.thread_id = thread_id
        self.user_key = user_key
        self.bot_id = bot_id
        self.topic_keywords = topic_keywords
        self.created_at = created_at or datetime.now().isoformat()
        self.last_updated = self.created_at
        self.history: List[Dict] = []
        self.phases: List[Dict] = []
        self.current_phase: int = 0
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "thread_id": self.thread_id,
            "user_key": self.user_key,
            "bot_id": self.bot_id,
            "topic_keywords": self.topic_keywords,
            "created_at": self.created_at,
            "last_updated": self.last_updated,
            "history": self.history,
            "phases": self.phases,
            "current_phase": self.current_phase,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ThreadContext":
        thread = cls(
            thread_id=data["thread_id"],
            user_key=data["user_key"],
            bot_id=data["bot_id"],
            topic_keywords=data.get("topic_keywords", []),
            created_at=data.get("created_at"),
        )
        thread.last_updated = data.get("last_updated", thread.created_at)
        thread.history = data.get("history", [])
        thread.phases = data.get("phases", [])
        thread.current_phase = data.get("current_phase", 0)
        thread.metadata = data.get("metadata", {})
        return thread


# =============================================================================
# TOPIC EXTRACTION
# =============================================================================

def extract_topic_keywords(history: List[Dict], limit: int = 10) -> List[str]:
    """
    Extract topic keywords from conversation history.

    Uses simple TF approach - most frequent meaningful words.
    """
    # Combine all user messages
    text = " ".join([
        msg.get("content", "")
        for msg in history
        if msg.get("role") == "user"
    ]).lower()

    # Remove common stopwords
    STOPWORDS = {
        "i", "me", "my", "we", "our", "you", "your", "the", "a", "an", "is", "are",
        "was", "were", "be", "been", "being", "have", "has", "had", "do", "does",
        "did", "will", "would", "could", "should", "can", "may", "might", "must",
        "to", "of", "in", "for", "on", "with", "at", "by", "from", "as", "into",
        "about", "that", "this", "these", "those", "it", "its", "what", "which",
        "who", "whom", "how", "when", "where", "why", "and", "or", "but", "if",
        "then", "so", "than", "too", "very", "just", "also", "now", "here", "there",
        "want", "like", "think", "know", "see", "look", "make", "get", "go", "come",
        "take", "use", "try", "let", "say", "tell", "ask", "give", "need", "help",
        "continue", "above", "below", "same", "more", "less", "good", "bad",
    }

    # Tokenize and filter
    words = text.replace(",", " ").replace(".", " ").replace("?", " ").split()
    words = [w for w in words if len(w) > 3 and w not in STOPWORDS]

    # Count frequencies
    freq = {}
    for word in words:
        freq[word] = freq.get(word, 0) + 1

    # Sort by frequency
    sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)

    return [word for word, count in sorted_words[:limit]]


def compute_topic_similarity(keywords1: List[str], keywords2: List[str]) -> float:
    """
    Compute Jaccard similarity between two keyword lists.
    """
    if not keywords1 or not keywords2:
        return 0.0

    set1 = set(keywords1)
    set2 = set(keywords2)

    intersection = len(set1 & set2)
    union = len(set1 | set2)

    return intersection / union if union > 0 else 0.0


# =============================================================================
# THREAD MANAGEMENT
# =============================================================================

def generate_thread_id(user_key: str, bot_id: str, topic_keywords: List[str]) -> str:
    """Generate a unique thread ID."""
    # Use hash of keywords for topic-based uniqueness
    topic_hash = hashlib.md5("_".join(sorted(topic_keywords[:5])).encode()).hexdigest()[:8]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{user_key}_{bot_id}_{topic_hash}_{timestamp}"


def get_or_create_thread(
    user_key: str,
    bot_id: str,
    history: List[Dict] = None,
    similarity_threshold: float = 0.4
) -> Tuple[str, ThreadContext]:
    """
    Get an existing thread for this topic or create a new one.

    Args:
        user_key: User identifier
        bot_id: Current bot ID
        history: Current conversation history
        similarity_threshold: Minimum similarity to reuse an existing thread

    Returns:
        Tuple of (thread_id, ThreadContext)
    """
    # Extract topic keywords from history
    topic_keywords = extract_topic_keywords(history or [])

    # Get user's threads
    user_threads = _thread_store.get(user_key, {})

    # Find best matching thread
    best_match = None
    best_similarity = 0.0

    for thread_id, thread_data in user_threads.items():
        thread = ThreadContext.from_dict(thread_data)

        # Check if same bot
        if thread.bot_id != bot_id:
            continue

        # Compute topic similarity
        similarity = compute_topic_similarity(topic_keywords, thread.topic_keywords)

        if similarity > best_similarity and similarity >= similarity_threshold:
            best_similarity = similarity
            best_match = thread

    if best_match:
        # Update existing thread
        best_match.last_updated = datetime.now().isoformat()
        return best_match.thread_id, best_match

    # Create new thread
    thread_id = generate_thread_id(user_key, bot_id, topic_keywords)
    thread = ThreadContext(
        thread_id=thread_id,
        user_key=user_key,
        bot_id=bot_id,
        topic_keywords=topic_keywords,
    )

    # Store thread
    if user_key not in _thread_store:
        _thread_store[user_key] = {}
    _thread_store[user_key][thread_id] = thread.to_dict()

    return thread_id, thread


def get_thread_for_topic(
    user_key: str,
    topic_keywords: List[str],
    bot_id: str = None
) -> Optional[ThreadContext]:
    """
    Find the best matching thread for given topic keywords.

    Args:
        user_key: User identifier
        topic_keywords: Keywords to match
        bot_id: Optional filter by bot

    Returns:
        Best matching ThreadContext or None
    """
    user_threads = _thread_store.get(user_key, {})

    best_match = None
    best_similarity = 0.0

    for thread_id, thread_data in user_threads.items():
        thread = ThreadContext.from_dict(thread_data)

        # Filter by bot if specified
        if bot_id and thread.bot_id != bot_id:
            continue

        similarity = compute_topic_similarity(topic_keywords, thread.topic_keywords)

        if similarity > best_similarity:
            best_similarity = similarity
            best_match = thread

    return best_match if best_similarity > 0.3 else None


def save_thread_context(
    thread_id: str,
    user_key: str,
    history: List[Dict],
    phases: List[Dict] = None,
    current_phase: int = 0,
    bot_id: str = None,
    metadata: Dict = None
) -> bool:
    """
    Save context to a specific thread.

    Args:
        thread_id: Thread to save to
        user_key: User identifier
        history: Conversation history
        phases: Workshop phases
        current_phase: Current phase index
        bot_id: Bot ID (updates if provided)
        metadata: Additional metadata

    Returns:
        True if successful
    """
    if user_key not in _thread_store:
        _thread_store[user_key] = {}

    if thread_id not in _thread_store[user_key]:
        # Create new thread
        topic_keywords = extract_topic_keywords(history)
        thread = ThreadContext(
            thread_id=thread_id,
            user_key=user_key,
            bot_id=bot_id or "lawrence",
            topic_keywords=topic_keywords,
        )
    else:
        thread = ThreadContext.from_dict(_thread_store[user_key][thread_id])

    # Update thread
    thread.history = history.copy() if history else []
    thread.phases = [p.copy() for p in phases] if phases else []
    thread.current_phase = current_phase
    thread.last_updated = datetime.now().isoformat()
    thread.topic_keywords = extract_topic_keywords(history)

    if bot_id:
        thread.bot_id = bot_id
    if metadata:
        thread.metadata.update(metadata)

    # Save
    _thread_store[user_key][thread_id] = thread.to_dict()

    return True


def get_active_threads(user_key: str, limit: int = 5) -> List[ThreadContext]:
    """
    Get active threads for a user, sorted by last_updated.

    Args:
        user_key: User identifier
        limit: Maximum threads to return

    Returns:
        List of ThreadContext objects
    """
    user_threads = _thread_store.get(user_key, {})

    threads = [ThreadContext.from_dict(data) for data in user_threads.values()]

    # Sort by last_updated descending
    threads.sort(key=lambda t: t.last_updated, reverse=True)

    return threads[:limit]


def get_thread_by_id(user_key: str, thread_id: str) -> Optional[ThreadContext]:
    """Get a specific thread by ID."""
    user_threads = _thread_store.get(user_key, {})
    thread_data = user_threads.get(thread_id)
    return ThreadContext.from_dict(thread_data) if thread_data else None


def get_most_recent_thread(user_key: str, bot_id: str = None) -> Optional[ThreadContext]:
    """
    Get the most recently updated thread for a user.

    Args:
        user_key: User identifier
        bot_id: Optional filter by bot

    Returns:
        Most recent ThreadContext or None
    """
    threads = get_active_threads(user_key, limit=10)

    if bot_id:
        threads = [t for t in threads if t.bot_id == bot_id]

    return threads[0] if threads else None


# =============================================================================
# PERSISTENCE TO POSTGRES (async)
# =============================================================================

async def persist_thread_to_db(thread: ThreadContext) -> bool:
    """
    Persist thread to Postgres for durability.

    Uses the conversation_threads table if available.
    """
    try:
        # Check if Supabase is available
        import os
        database_url = os.getenv("DATABASE_URL") or os.getenv("CHAINLIT_DATABASE_URL")
        if not database_url:
            return False

        # Use SQLAlchemy async
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text

        # Convert to async URL
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

        engine = create_async_engine(database_url)

        async with engine.connect() as conn:
            # Upsert thread
            await conn.execute(
                text("""
                    INSERT INTO conversation_threads (thread_id, user_key, bot_id, topic_keywords, history, phases, current_phase, metadata, created_at, last_updated)
                    VALUES (:thread_id, :user_key, :bot_id, :topic_keywords, :history, :phases, :current_phase, :metadata, :created_at, :last_updated)
                    ON CONFLICT (thread_id) DO UPDATE SET
                        history = :history,
                        phases = :phases,
                        current_phase = :current_phase,
                        metadata = :metadata,
                        last_updated = :last_updated
                """),
                {
                    "thread_id": thread.thread_id,
                    "user_key": thread.user_key,
                    "bot_id": thread.bot_id,
                    "topic_keywords": json.dumps(thread.topic_keywords),
                    "history": json.dumps(thread.history),
                    "phases": json.dumps(thread.phases),
                    "current_phase": thread.current_phase,
                    "metadata": json.dumps(thread.metadata),
                    "created_at": thread.created_at,
                    "last_updated": thread.last_updated,
                }
            )
            await conn.commit()

        return True

    except Exception as e:
        logger.error(f"Failed to persist thread to DB: {e}")
        return False


async def load_threads_from_db(user_key: str) -> List[ThreadContext]:
    """Load threads from Postgres for a user."""
    try:
        import os
        database_url = os.getenv("DATABASE_URL") or os.getenv("CHAINLIT_DATABASE_URL")
        if not database_url:
            return []

        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text

        if database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

        engine = create_async_engine(database_url)

        async with engine.connect() as conn:
            result = await conn.execute(
                text("SELECT * FROM conversation_threads WHERE user_key = :user_key ORDER BY last_updated DESC LIMIT 20"),
                {"user_key": user_key}
            )
            rows = result.fetchall()

        threads = []
        for row in rows:
            thread = ThreadContext(
                thread_id=row.thread_id,
                user_key=row.user_key,
                bot_id=row.bot_id,
                topic_keywords=json.loads(row.topic_keywords) if row.topic_keywords else [],
                created_at=row.created_at,
            )
            thread.last_updated = row.last_updated
            thread.history = json.loads(row.history) if row.history else []
            thread.phases = json.loads(row.phases) if row.phases else []
            thread.current_phase = row.current_phase or 0
            thread.metadata = json.loads(row.metadata) if row.metadata else {}
            threads.append(thread)

            # Also populate in-memory cache
            if user_key not in _thread_store:
                _thread_store[user_key] = {}
            _thread_store[user_key][thread.thread_id] = thread.to_dict()

        return threads

    except Exception as e:
        logger.error(f"Failed to load threads from DB: {e}")
        return []


# =============================================================================
# INTEGRATION HELPERS
# =============================================================================

def get_context_for_continue(
    user_key: str,
    current_message: str,
    current_bot_id: str
) -> Optional[ThreadContext]:
    """
    Smart context matching for "continue from above" type requests.

    Analyzes the current message and finds the best matching thread.
    """
    # Extract keywords from current message
    current_keywords = current_message.lower().split()

    # Check for explicit topic references
    topic_signals = []
    for word in current_keywords:
        if len(word) > 4 and word not in {"continue", "above", "where", "left"}:
            topic_signals.append(word)

    if topic_signals:
        # Try to find thread matching topic
        thread = get_thread_for_topic(user_key, topic_signals, bot_id=current_bot_id)
        if thread:
            return thread

    # Fallback to most recent thread for this bot
    return get_most_recent_thread(user_key, bot_id=current_bot_id)


def migrate_from_context_store(context_store: Dict, user_key: str) -> None:
    """
    Migrate existing context_store data to thread-based system.

    Call this during the transition period.
    """
    if user_key not in context_store:
        return

    old_context = context_store[user_key]

    if not old_context.get("history"):
        return

    # Create thread from old context
    history = old_context.get("history", [])
    bot_id = old_context.get("bot_id", "lawrence")
    topic_keywords = extract_topic_keywords(history)

    thread_id = generate_thread_id(user_key, bot_id, topic_keywords)
    thread = ThreadContext(
        thread_id=thread_id,
        user_key=user_key,
        bot_id=bot_id,
        topic_keywords=topic_keywords,
    )
    thread.history = history
    thread.phases = old_context.get("phases", [])
    thread.current_phase = old_context.get("current_phase", 0)

    # Store
    if user_key not in _thread_store:
        _thread_store[user_key] = {}
    _thread_store[user_key][thread_id] = thread.to_dict()

    logger.info(f"Migrated context_store to thread: {thread_id}")
