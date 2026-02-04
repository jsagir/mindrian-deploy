"""
API Health Monitoring System
============================

Continuously monitors API health with:
- Random sampling on system initialization
- Async health checks with timeouts
- Supabase logging for historical tracking
- Dashboard-ready statistics

Usage:
    from utils.api_health_monitor import (
        run_startup_health_check,
        check_api_health,
        get_health_dashboard,
    )

    # On startup
    await run_startup_health_check()

    # Manual check
    status = await check_api_health("gemini")

    # Dashboard data
    stats = await get_health_dashboard(days=7)
"""

import os
import asyncio
import random
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger("api_health_monitor")

# =============================================================================
# CONFIGURATION
# =============================================================================

class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

class APIPriority(str, Enum):
    CRITICAL = "critical"      # Must work for app to function
    IMPORTANT = "important"    # Degrades experience significantly
    OPTIONAL = "optional"      # Nice to have

@dataclass
class APIConfig:
    """Configuration for a monitored API."""
    name: str
    display_name: str
    priority: APIPriority
    check_function: str  # Function name to call
    env_vars: List[str]  # Required environment variables
    timeout_seconds: float = 10.0
    description: str = ""

# All monitored APIs
API_REGISTRY: Dict[str, APIConfig] = {
    "gemini": APIConfig(
        name="gemini",
        display_name="Google Gemini",
        priority=APIPriority.CRITICAL,
        check_function="_check_gemini",
        env_vars=["GOOGLE_API_KEY"],
        timeout_seconds=15.0,
        description="Core LLM for conversations"
    ),
    "filesearch": APIConfig(
        name="filesearch",
        display_name="Gemini FileSearch",
        priority=APIPriority.CRITICAL,
        check_function="_check_filesearch",
        env_vars=["GOOGLE_API_KEY"],
        timeout_seconds=20.0,
        description="RAG knowledge retrieval"
    ),
    "tavily": APIConfig(
        name="tavily",
        display_name="Tavily Search",
        priority=APIPriority.IMPORTANT,
        check_function="_check_tavily",
        env_vars=["TAVILY_API_KEY"],
        timeout_seconds=10.0,
        description="Web research and search"
    ),
    "neo4j": APIConfig(
        name="neo4j",
        display_name="Neo4j Graph",
        priority=APIPriority.IMPORTANT,
        check_function="_check_neo4j",
        env_vars=["NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD"],
        timeout_seconds=10.0,
        description="Knowledge graph database"
    ),
    "supabase": APIConfig(
        name="supabase",
        display_name="Supabase Storage",
        priority=APIPriority.CRITICAL,
        check_function="_check_supabase",
        env_vars=["SUPABASE_URL", "SUPABASE_SERVICE_KEY"],
        timeout_seconds=10.0,
        description="File storage and persistence"
    ),
    "elevenlabs": APIConfig(
        name="elevenlabs",
        display_name="ElevenLabs TTS",
        priority=APIPriority.OPTIONAL,
        check_function="_check_elevenlabs",
        env_vars=["ELEVENLABS_API_KEY"],
        timeout_seconds=10.0,
        description="Text-to-speech voice"
    ),
    "fred": APIConfig(
        name="fred",
        display_name="FRED Economic",
        priority=APIPriority.OPTIONAL,
        check_function="_check_fred",
        env_vars=["FRED_API_KEY"],
        timeout_seconds=10.0,
        description="Federal Reserve economic data"
    ),
    "serpapi": APIConfig(
        name="serpapi",
        display_name="SerpAPI Trends",
        priority=APIPriority.OPTIONAL,
        check_function="_check_serpapi",
        env_vars=["SERPAPI_KEY"],
        timeout_seconds=10.0,
        description="Google Trends and patents"
    ),
}

# =============================================================================
# HEALTH CHECK RESULT
# =============================================================================

@dataclass
class HealthCheckResult:
    """Result of a single health check."""
    api_name: str
    status: HealthStatus
    response_time_ms: int
    message: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return asdict(self)

# =============================================================================
# INDIVIDUAL API CHECKS
# =============================================================================

async def _check_gemini() -> HealthCheckResult:
    """Check Google Gemini API health."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return HealthCheckResult(
            api_name="gemini",
            status=HealthStatus.UNHEALTHY,
            response_time_ms=0,
            message="API key not configured"
        )

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        start = time.time()
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Reply: OK",
            config=types.GenerateContentConfig(max_output_tokens=10),
        )
        elapsed_ms = int((time.time() - start) * 1000)

        if resp.text and "OK" in resp.text.upper():
            return HealthCheckResult(
                api_name="gemini",
                status=HealthStatus.HEALTHY,
                response_time_ms=elapsed_ms,
                message="LLM responding normally"
            )
        else:
            return HealthCheckResult(
                api_name="gemini",
                status=HealthStatus.DEGRADED,
                response_time_ms=elapsed_ms,
                message=f"Unexpected response: {resp.text[:50]}"
            )
    except Exception as e:
        return HealthCheckResult(
            api_name="gemini",
            status=HealthStatus.UNHEALTHY,
            response_time_ms=0,
            message=f"Error: {str(e)[:100]}"
        )

async def _check_filesearch() -> HealthCheckResult:
    """Check Gemini FileSearch RAG health."""
    api_key = os.getenv("GOOGLE_FILESEARCH_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return HealthCheckResult(
            api_name="filesearch",
            status=HealthStatus.UNHEALTHY,
            response_time_ms=0,
            message="API key not configured"
        )

    try:
        from google import genai
        from google.genai import types

        FILE_SEARCH_STORE = "fileSearchStores/pwsknowledgebase-a4rnz3u41lsn"
        tool = types.Tool(file_search=types.FileSearch(file_search_store_names=[FILE_SEARCH_STORE]))

        client = genai.Client(api_key=api_key)
        start = time.time()
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="What is PWS? One word answer.",
            config=types.GenerateContentConfig(tools=[tool], max_output_tokens=20),
        )
        elapsed_ms = int((time.time() - start) * 1000)

        if resp.text and len(resp.text.strip()) > 0:
            return HealthCheckResult(
                api_name="filesearch",
                status=HealthStatus.HEALTHY,
                response_time_ms=elapsed_ms,
                message="FileSearch retrieving documents"
            )
        else:
            return HealthCheckResult(
                api_name="filesearch",
                status=HealthStatus.DEGRADED,
                response_time_ms=elapsed_ms,
                message="Empty response from FileSearch"
            )
    except Exception as e:
        return HealthCheckResult(
            api_name="filesearch",
            status=HealthStatus.UNHEALTHY,
            response_time_ms=0,
            message=f"Error: {str(e)[:100]}"
        )

async def _check_tavily() -> HealthCheckResult:
    """Check Tavily Search API health."""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return HealthCheckResult(
            api_name="tavily",
            status=HealthStatus.UNKNOWN,
            response_time_ms=0,
            message="API key not configured"
        )

    try:
        from tavily import TavilyClient

        client = TavilyClient(api_key=api_key)
        start = time.time()
        result = client.search("test query health check", max_results=1)
        elapsed_ms = int((time.time() - start) * 1000)

        if result and "results" in result:
            return HealthCheckResult(
                api_name="tavily",
                status=HealthStatus.HEALTHY,
                response_time_ms=elapsed_ms,
                message=f"Search working ({len(result.get('results', []))} results)"
            )
        else:
            return HealthCheckResult(
                api_name="tavily",
                status=HealthStatus.DEGRADED,
                response_time_ms=elapsed_ms,
                message="No results returned"
            )
    except Exception as e:
        return HealthCheckResult(
            api_name="tavily",
            status=HealthStatus.UNHEALTHY,
            response_time_ms=0,
            message=f"Error: {str(e)[:100]}"
        )

async def _check_neo4j() -> HealthCheckResult:
    """Check Neo4j Graph Database health."""
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")

    if not all([uri, user, password]):
        return HealthCheckResult(
            api_name="neo4j",
            status=HealthStatus.UNKNOWN,
            response_time_ms=0,
            message="Not configured"
        )

    try:
        from neo4j import GraphDatabase

        driver = GraphDatabase.driver(uri, auth=(user, password))
        start = time.time()

        with driver.session() as session:
            result = session.run("MATCH (n) RETURN count(n) as count LIMIT 1")
            count = result.single()["count"]

        elapsed_ms = int((time.time() - start) * 1000)
        driver.close()

        return HealthCheckResult(
            api_name="neo4j",
            status=HealthStatus.HEALTHY,
            response_time_ms=elapsed_ms,
            message=f"Graph connected ({count} nodes)",
            details={"node_count": count}
        )
    except Exception as e:
        return HealthCheckResult(
            api_name="neo4j",
            status=HealthStatus.UNHEALTHY,
            response_time_ms=0,
            message=f"Error: {str(e)[:100]}"
        )

async def _check_supabase() -> HealthCheckResult:
    """Check Supabase Storage health."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")

    if not url or not key:
        return HealthCheckResult(
            api_name="supabase",
            status=HealthStatus.UNHEALTHY,
            response_time_ms=0,
            message="Not configured"
        )

    try:
        from supabase import create_client

        client = create_client(url, key)
        start = time.time()

        # List buckets as health check
        buckets = client.storage.list_buckets()
        elapsed_ms = int((time.time() - start) * 1000)

        return HealthCheckResult(
            api_name="supabase",
            status=HealthStatus.HEALTHY,
            response_time_ms=elapsed_ms,
            message=f"Storage accessible ({len(buckets)} buckets)",
            details={"bucket_count": len(buckets)}
        )
    except Exception as e:
        return HealthCheckResult(
            api_name="supabase",
            status=HealthStatus.UNHEALTHY,
            response_time_ms=0,
            message=f"Error: {str(e)[:100]}"
        )

async def _check_elevenlabs() -> HealthCheckResult:
    """Check ElevenLabs TTS health."""
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        return HealthCheckResult(
            api_name="elevenlabs",
            status=HealthStatus.UNKNOWN,
            response_time_ms=0,
            message="Not configured"
        )

    try:
        import requests

        start = time.time()
        resp = requests.get(
            "https://api.elevenlabs.io/v1/voices",
            headers={"xi-api-key": api_key},
            timeout=10
        )
        elapsed_ms = int((time.time() - start) * 1000)

        if resp.status_code == 200:
            voices = resp.json().get("voices", [])
            return HealthCheckResult(
                api_name="elevenlabs",
                status=HealthStatus.HEALTHY,
                response_time_ms=elapsed_ms,
                message=f"TTS available ({len(voices)} voices)"
            )
        else:
            return HealthCheckResult(
                api_name="elevenlabs",
                status=HealthStatus.DEGRADED,
                response_time_ms=elapsed_ms,
                message=f"API returned {resp.status_code}"
            )
    except Exception as e:
        return HealthCheckResult(
            api_name="elevenlabs",
            status=HealthStatus.UNHEALTHY,
            response_time_ms=0,
            message=f"Error: {str(e)[:100]}"
        )

async def _check_fred() -> HealthCheckResult:
    """Check FRED Economic API health."""
    api_key = os.getenv("FRED_API_KEY")
    if not api_key:
        return HealthCheckResult(
            api_name="fred",
            status=HealthStatus.UNKNOWN,
            response_time_ms=0,
            message="Not configured"
        )

    try:
        import requests

        start = time.time()
        resp = requests.get(
            f"https://api.stlouisfed.org/fred/series?series_id=GDP&api_key={api_key}&file_type=json",
            timeout=10
        )
        elapsed_ms = int((time.time() - start) * 1000)

        if resp.status_code == 200:
            return HealthCheckResult(
                api_name="fred",
                status=HealthStatus.HEALTHY,
                response_time_ms=elapsed_ms,
                message="FRED API accessible"
            )
        else:
            return HealthCheckResult(
                api_name="fred",
                status=HealthStatus.DEGRADED,
                response_time_ms=elapsed_ms,
                message=f"API returned {resp.status_code}"
            )
    except Exception as e:
        return HealthCheckResult(
            api_name="fred",
            status=HealthStatus.UNHEALTHY,
            response_time_ms=0,
            message=f"Error: {str(e)[:100]}"
        )

async def _check_serpapi() -> HealthCheckResult:
    """Check SerpAPI health."""
    api_key = os.getenv("SERPAPI_KEY") or os.getenv("SERPAPI_API_KEY")
    if not api_key:
        return HealthCheckResult(
            api_name="serpapi",
            status=HealthStatus.UNKNOWN,
            response_time_ms=0,
            message="Not configured"
        )

    try:
        import requests

        start = time.time()
        resp = requests.get(
            f"https://serpapi.com/account?api_key={api_key}",
            timeout=10
        )
        elapsed_ms = int((time.time() - start) * 1000)

        if resp.status_code == 200:
            data = resp.json()
            remaining = data.get("total_searches_left", "?")
            return HealthCheckResult(
                api_name="serpapi",
                status=HealthStatus.HEALTHY,
                response_time_ms=elapsed_ms,
                message=f"SerpAPI OK ({remaining} searches remaining)"
            )
        else:
            return HealthCheckResult(
                api_name="serpapi",
                status=HealthStatus.DEGRADED,
                response_time_ms=elapsed_ms,
                message=f"API returned {resp.status_code}"
            )
    except Exception as e:
        return HealthCheckResult(
            api_name="serpapi",
            status=HealthStatus.UNHEALTHY,
            response_time_ms=0,
            message=f"Error: {str(e)[:100]}"
        )

# =============================================================================
# CHECK DISPATCHER
# =============================================================================

# Map function names to actual functions
CHECK_FUNCTIONS = {
    "_check_gemini": _check_gemini,
    "_check_filesearch": _check_filesearch,
    "_check_tavily": _check_tavily,
    "_check_neo4j": _check_neo4j,
    "_check_supabase": _check_supabase,
    "_check_elevenlabs": _check_elevenlabs,
    "_check_fred": _check_fred,
    "_check_serpapi": _check_serpapi,
}

async def check_api_health(api_name: str) -> HealthCheckResult:
    """
    Check health of a specific API.

    Args:
        api_name: Name from API_REGISTRY (e.g., "gemini", "tavily")

    Returns:
        HealthCheckResult with status and timing
    """
    if api_name not in API_REGISTRY:
        return HealthCheckResult(
            api_name=api_name,
            status=HealthStatus.UNKNOWN,
            response_time_ms=0,
            message=f"Unknown API: {api_name}"
        )

    config = API_REGISTRY[api_name]
    check_func = CHECK_FUNCTIONS.get(config.check_function)

    if not check_func:
        return HealthCheckResult(
            api_name=api_name,
            status=HealthStatus.UNKNOWN,
            response_time_ms=0,
            message="Check function not implemented"
        )

    try:
        # Run with timeout
        result = await asyncio.wait_for(
            check_func(),
            timeout=config.timeout_seconds
        )
        return result
    except asyncio.TimeoutError:
        return HealthCheckResult(
            api_name=api_name,
            status=HealthStatus.UNHEALTHY,
            response_time_ms=int(config.timeout_seconds * 1000),
            message=f"Timeout after {config.timeout_seconds}s"
        )
    except Exception as e:
        return HealthCheckResult(
            api_name=api_name,
            status=HealthStatus.UNHEALTHY,
            response_time_ms=0,
            message=f"Check failed: {str(e)[:100]}"
        )

# =============================================================================
# SUPABASE LOGGING
# =============================================================================

async def log_health_check_to_supabase(results: List[HealthCheckResult]) -> bool:
    """
    Log health check results to Supabase table.

    Table: api_health_log
    Columns: id, api_name, status, response_time_ms, message, details, created_at
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")

    if not url or not key:
        logger.warning("Supabase not configured - skipping health log")
        return False

    try:
        from supabase import create_client

        client = create_client(url, key)

        rows = [
            {
                "api_name": r.api_name,
                "status": r.status.value if isinstance(r.status, HealthStatus) else r.status,
                "response_time_ms": r.response_time_ms,
                "message": r.message,
                "details": r.details,
                "created_at": r.timestamp
            }
            for r in results
        ]

        client.table("api_health_log").insert(rows).execute()
        logger.info(f"Logged {len(rows)} health checks to Supabase")
        return True

    except Exception as e:
        logger.error(f"Failed to log health checks: {e}")
        return False

# =============================================================================
# STARTUP HEALTH CHECK
# =============================================================================

async def run_startup_health_check(
    sample_count: int = 5,
    include_critical: bool = True,
    log_to_supabase: bool = True
) -> Dict[str, HealthCheckResult]:
    """
    Run health checks on system startup.

    Args:
        sample_count: Number of random optional APIs to check
        include_critical: Always check critical APIs
        log_to_supabase: Log results to Supabase

    Returns:
        Dict of API name -> HealthCheckResult
    """
    logger.info("Running startup health check...")

    apis_to_check = []

    # Always include critical APIs
    if include_critical:
        for name, config in API_REGISTRY.items():
            if config.priority == APIPriority.CRITICAL:
                apis_to_check.append(name)

    # Random sample of non-critical APIs
    optional_apis = [
        name for name, config in API_REGISTRY.items()
        if config.priority != APIPriority.CRITICAL and name not in apis_to_check
    ]

    sampled = random.sample(optional_apis, min(sample_count, len(optional_apis)))
    apis_to_check.extend(sampled)

    logger.info(f"Checking {len(apis_to_check)} APIs: {apis_to_check}")

    # Run all checks concurrently
    tasks = [check_api_health(api) for api in apis_to_check]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Process results
    result_dict = {}
    valid_results = []

    for api, result in zip(apis_to_check, results):
        if isinstance(result, Exception):
            result = HealthCheckResult(
                api_name=api,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=0,
                message=f"Check exception: {str(result)[:100]}"
            )
        result_dict[api] = result
        valid_results.append(result)

    # Log to Supabase
    if log_to_supabase and valid_results:
        await log_health_check_to_supabase(valid_results)

    # Summary
    healthy = sum(1 for r in valid_results if r.status == HealthStatus.HEALTHY)
    degraded = sum(1 for r in valid_results if r.status == HealthStatus.DEGRADED)
    unhealthy = sum(1 for r in valid_results if r.status == HealthStatus.UNHEALTHY)

    logger.info(f"Health check complete: {healthy} healthy, {degraded} degraded, {unhealthy} unhealthy")

    return result_dict

# =============================================================================
# DASHBOARD DATA
# =============================================================================

async def get_health_dashboard(days: int = 7) -> Dict[str, Any]:
    """
    Get health dashboard data from Supabase.

    Returns aggregated statistics over the specified period.
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")

    if not url or not key:
        return {"error": "Supabase not configured"}

    try:
        from supabase import create_client

        client = create_client(url, key)

        since = (datetime.utcnow() - timedelta(days=days)).isoformat()

        # Get all health logs for period
        result = client.table("api_health_log")\
            .select("*")\
            .gte("created_at", since)\
            .order("created_at", desc=True)\
            .execute()

        logs = result.data or []

        if not logs:
            return {
                "period_days": days,
                "total_checks": 0,
                "by_api": {},
                "recent_issues": []
            }

        # Aggregate by API
        by_api = {}
        for log in logs:
            api = log["api_name"]
            if api not in by_api:
                by_api[api] = {
                    "total_checks": 0,
                    "healthy": 0,
                    "degraded": 0,
                    "unhealthy": 0,
                    "avg_response_ms": 0,
                    "response_times": []
                }

            by_api[api]["total_checks"] += 1
            status = log["status"]
            if status == "healthy":
                by_api[api]["healthy"] += 1
            elif status == "degraded":
                by_api[api]["degraded"] += 1
            else:
                by_api[api]["unhealthy"] += 1

            if log["response_time_ms"]:
                by_api[api]["response_times"].append(log["response_time_ms"])

        # Calculate averages and uptime
        for api in by_api:
            times = by_api[api].pop("response_times")
            by_api[api]["avg_response_ms"] = int(sum(times) / len(times)) if times else 0
            total = by_api[api]["total_checks"]
            by_api[api]["uptime_percent"] = round(
                (by_api[api]["healthy"] + by_api[api]["degraded"]) / total * 100, 1
            ) if total > 0 else 0

        # Recent issues
        recent_issues = [
            {
                "api": log["api_name"],
                "status": log["status"],
                "message": log["message"],
                "time": log["created_at"]
            }
            for log in logs[:20]
            if log["status"] in ["degraded", "unhealthy"]
        ]

        return {
            "period_days": days,
            "total_checks": len(logs),
            "by_api": by_api,
            "recent_issues": recent_issues[:10]
        }

    except Exception as e:
        logger.error(f"Failed to get health dashboard: {e}")
        return {"error": str(e)}

# =============================================================================
# SQL SCHEMA (for reference)
# =============================================================================

API_HEALTH_LOG_SCHEMA = """
-- Run this in Supabase SQL editor to create the health log table

CREATE TABLE IF NOT EXISTS api_health_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    api_name TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('healthy', 'degraded', 'unhealthy', 'unknown')),
    response_time_ms INTEGER,
    message TEXT,
    details JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes for dashboard queries
CREATE INDEX idx_api_health_api_name ON api_health_log(api_name);
CREATE INDEX idx_api_health_created_at ON api_health_log(created_at DESC);
CREATE INDEX idx_api_health_status ON api_health_log(status);

-- Partition by time (optional, for high-volume logging)
-- Consider adding time-based retention policy

-- Grant access
ALTER TABLE api_health_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow service role full access" ON api_health_log
    FOR ALL USING (true);
"""

# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "HealthStatus",
    "APIPriority",
    "APIConfig",
    "HealthCheckResult",
    "API_REGISTRY",
    "check_api_health",
    "run_startup_health_check",
    "log_health_check_to_supabase",
    "get_health_dashboard",
    "API_HEALTH_LOG_SCHEMA",
]
