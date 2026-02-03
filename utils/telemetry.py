"""
Telemetry Decorator - Lightweight instrumentation for Mindrian

Adds timing, error tracking, and usage metrics without modifying function logic.
Uses simple in-memory counters + optional async flush to Supabase.

Usage:
    from utils.telemetry import timed, track_llm_call, get_metrics

    @timed("research_orchestrator")
    async def run_research(query: str):
        ...

    # Manual tracking
    track_llm_call("gemini-2.5-flash", tokens=1500, latency_ms=450)

    # Get aggregated metrics
    metrics = get_metrics()
"""

import time
import asyncio
import functools
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from collections import defaultdict


# === In-Memory Metrics Store ===

_metrics: Dict[str, Any] = {
    "function_calls": defaultdict(lambda: {"count": 0, "total_ms": 0, "errors": 0}),
    "llm_calls": defaultdict(lambda: {"count": 0, "total_tokens": 0, "total_ms": 0}),
    "session_start": datetime.utcnow().isoformat(),
    "last_flush": None,
}

# Flush configuration
FLUSH_INTERVAL_SECONDS = 300  # 5 minutes
_last_flush_time = time.time()


# === Timing Decorator ===

def timed(name: Optional[str] = None, track_errors: bool = True):
    """
    Decorator that tracks function execution time and error count.

    Works with both sync and async functions.

    Args:
        name: Optional metric name (defaults to function name)
        track_errors: Whether to count exceptions

    Example:
        @timed("research")
        async def run_research(query):
            ...

        @timed()
        def process_data(data):
            ...
    """
    def decorator(func: Callable):
        metric_name = name or func.__name__

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                elapsed_ms = (time.perf_counter() - start) * 1000
                _record_call(metric_name, elapsed_ms, error=False)
                return result
            except Exception as e:
                elapsed_ms = (time.perf_counter() - start) * 1000
                if track_errors:
                    _record_call(metric_name, elapsed_ms, error=True)
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                elapsed_ms = (time.perf_counter() - start) * 1000
                _record_call(metric_name, elapsed_ms, error=False)
                return result
            except Exception as e:
                elapsed_ms = (time.perf_counter() - start) * 1000
                if track_errors:
                    _record_call(metric_name, elapsed_ms, error=True)
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def _record_call(name: str, elapsed_ms: float, error: bool = False):
    """Record a function call in metrics."""
    stats = _metrics["function_calls"][name]
    stats["count"] += 1
    stats["total_ms"] += elapsed_ms
    if error:
        stats["errors"] += 1

    # Trigger background flush if interval exceeded
    _maybe_flush()


# === LLM Call Tracking ===

def track_llm_call(
    model: str,
    tokens: int = 0,
    latency_ms: float = 0,
    success: bool = True
):
    """
    Track an LLM API call for cost and performance monitoring.

    Args:
        model: Model identifier (e.g., "gemini-2.5-flash")
        tokens: Token count (input + output)
        latency_ms: Call latency in milliseconds
        success: Whether the call succeeded
    """
    stats = _metrics["llm_calls"][model]
    stats["count"] += 1
    stats["total_tokens"] += tokens
    stats["total_ms"] += latency_ms
    if not success:
        stats["errors"] = stats.get("errors", 0) + 1

    _maybe_flush()


# === Metrics Access ===

def get_metrics() -> Dict[str, Any]:
    """
    Get aggregated metrics.

    Returns:
        Dict with function_calls, llm_calls, and session info
    """
    result = {
        "session_start": _metrics["session_start"],
        "last_flush": _metrics["last_flush"],
        "function_calls": {},
        "llm_calls": {},
    }

    # Calculate averages for function calls
    for name, stats in _metrics["function_calls"].items():
        count = stats["count"]
        result["function_calls"][name] = {
            "count": count,
            "avg_ms": stats["total_ms"] / count if count > 0 else 0,
            "errors": stats["errors"],
            "error_rate": stats["errors"] / count if count > 0 else 0,
        }

    # Calculate averages for LLM calls
    for model, stats in _metrics["llm_calls"].items():
        count = stats["count"]
        result["llm_calls"][model] = {
            "count": count,
            "total_tokens": stats["total_tokens"],
            "avg_tokens": stats["total_tokens"] / count if count > 0 else 0,
            "avg_ms": stats["total_ms"] / count if count > 0 else 0,
            "errors": stats.get("errors", 0),
        }

    return result


def get_function_stats(name: str) -> Dict[str, Any]:
    """Get stats for a specific function."""
    stats = _metrics["function_calls"].get(name)
    if not stats:
        return {"count": 0, "avg_ms": 0, "errors": 0}

    count = stats["count"]
    return {
        "count": count,
        "avg_ms": stats["total_ms"] / count if count > 0 else 0,
        "errors": stats["errors"],
    }


def reset_metrics():
    """Reset all metrics (useful for testing)."""
    _metrics["function_calls"].clear()
    _metrics["llm_calls"].clear()
    _metrics["session_start"] = datetime.utcnow().isoformat()
    _metrics["last_flush"] = None


# === Background Flush ===

def _maybe_flush():
    """Check if we should flush metrics to persistent storage."""
    global _last_flush_time

    now = time.time()
    if now - _last_flush_time >= FLUSH_INTERVAL_SECONDS:
        _last_flush_time = now
        asyncio.create_task(_flush_to_storage())


async def _flush_to_storage():
    """
    Flush metrics to Supabase storage (async, fire-and-forget).

    Stores a snapshot in the 'telemetry/' folder with timestamp.
    """
    import os
    import json

    try:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY")
        bucket = os.getenv("SUPABASE_BUCKET", "mindrian-files")

        if not url or not key:
            return  # Supabase not configured

        from supabase import create_client
        client = create_client(url, key)

        # Generate filename with timestamp
        timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"telemetry/metrics_{timestamp}.json"

        # Prepare metrics snapshot
        snapshot = get_metrics()
        snapshot["flushed_at"] = datetime.utcnow().isoformat()

        # Upload to storage
        content = json.dumps(snapshot, indent=2).encode('utf-8')

        try:
            client.storage.from_(bucket).upload(
                path=filename,
                file=content,
                file_options={"content-type": "application/json"}
            )
        except Exception as e:
            if "duplicate" in str(e).lower() or "already exists" in str(e).lower():
                # File exists, use update
                client.storage.from_(bucket).update(
                    path=filename,
                    file=content,
                    file_options={"content-type": "application/json"}
                )
            else:
                raise

        _metrics["last_flush"] = datetime.utcnow().isoformat()
        print(f"[TELEMETRY] Flushed metrics to {filename}")

    except Exception as e:
        print(f"[TELEMETRY] Flush failed (non-critical): {e}")


# === Convenience Decorators ===

def timed_llm(model: str):
    """
    Decorator for LLM-calling functions that auto-tracks model usage.

    Example:
        @timed_llm("gemini-2.5-flash")
        async def generate_response(prompt):
            response = await client.generate(prompt)
            return response
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                elapsed_ms = (time.perf_counter() - start) * 1000

                # Estimate tokens if response has text
                tokens = 0
                if hasattr(result, 'text'):
                    tokens = len(result.text.split()) * 1.3  # Rough estimate
                elif isinstance(result, str):
                    tokens = len(result.split()) * 1.3

                track_llm_call(model, tokens=int(tokens), latency_ms=elapsed_ms, success=True)
                return result

            except Exception as e:
                elapsed_ms = (time.perf_counter() - start) * 1000
                track_llm_call(model, latency_ms=elapsed_ms, success=False)
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                elapsed_ms = (time.perf_counter() - start) * 1000

                tokens = 0
                if hasattr(result, 'text'):
                    tokens = len(result.text.split()) * 1.3
                elif isinstance(result, str):
                    tokens = len(result.split()) * 1.3

                track_llm_call(model, tokens=int(tokens), latency_ms=elapsed_ms, success=True)
                return result

            except Exception as e:
                elapsed_ms = (time.perf_counter() - start) * 1000
                track_llm_call(model, latency_ms=elapsed_ms, success=False)
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# === Health Check Integration ===

def get_health_summary() -> Dict[str, Any]:
    """
    Get a health summary suitable for the health check script.

    Returns:
        Dict with key health indicators
    """
    metrics = get_metrics()

    # Calculate overall error rate
    total_calls = sum(s["count"] for s in metrics["function_calls"].values())
    total_errors = sum(s["errors"] for s in metrics["function_calls"].values())

    # Find slowest function
    slowest = ("none", 0)
    for name, stats in metrics["function_calls"].items():
        if stats["avg_ms"] > slowest[1]:
            slowest = (name, stats["avg_ms"])

    return {
        "status": "healthy" if total_errors / max(total_calls, 1) < 0.1 else "degraded",
        "total_calls": total_calls,
        "total_errors": total_errors,
        "error_rate": total_errors / max(total_calls, 1),
        "slowest_function": slowest[0],
        "slowest_avg_ms": round(slowest[1], 2),
        "llm_models_used": list(metrics["llm_calls"].keys()),
        "session_start": metrics["session_start"],
    }
