"""
TTL Cache for Research Tool Results
=====================================

Simple in-memory cache with time-to-live expiry.
Prevents redundant API calls when the same topic is discussed
across multiple turns in a conversation.

Usage:
    from tools.research_cache import cached_call

    result = cached_call("arxiv", "machine learning fairness", lambda: search_papers("machine learning fairness"))
"""

import time
import hashlib
import logging
from typing import Any, Callable, Optional

logger = logging.getLogger("research_cache")

_cache: dict = {}
DEFAULT_TTL = 600  # 10 minutes


def _make_key(source: str, query: str) -> str:
    normalized = query.strip().lower()
    h = hashlib.md5(f"{source}:{normalized}".encode()).hexdigest()[:12]
    return f"{source}:{h}"


def cached_call(
    source: str,
    query: str,
    fetch_fn: Callable[[], Any],
    ttl: int = DEFAULT_TTL,
) -> Any:
    """
    Return cached result if fresh, otherwise call fetch_fn and cache it.

    Args:
        source: Cache namespace (e.g. 'arxiv', 'fred', 'kaggle')
        query: The search query (used for cache key)
        fetch_fn: Zero-arg callable that fetches the data
        ttl: Time-to-live in seconds (default 600 = 10 min)
    """
    key = _make_key(source, query)
    now = time.time()

    entry = _cache.get(key)
    if entry and (now - entry["ts"]) < ttl:
        logger.debug("Cache HIT: %s", key)
        return entry["data"]

    logger.debug("Cache MISS: %s", key)
    data = fetch_fn()
    _cache[key] = {"data": data, "ts": now}

    # Evict stale entries if cache grows large
    if len(_cache) > 200:
        cutoff = now - ttl * 3
        stale = [k for k, v in _cache.items() if v["ts"] < cutoff]
        for k in stale:
            del _cache[k]

    return data


def invalidate(source: Optional[str] = None):
    """Clear cache. If source given, clear only that namespace."""
    if source is None:
        _cache.clear()
    else:
        prefix = f"{source}:"
        keys = [k for k in _cache if k.startswith(prefix)]
        for k in keys:
            del _cache[k]


def stats() -> dict:
    """Return cache statistics."""
    now = time.time()
    total = len(_cache)
    fresh = sum(1 for v in _cache.values() if (now - v["ts"]) < DEFAULT_TTL)
    return {"total": total, "fresh": fresh, "stale": total - fresh}
