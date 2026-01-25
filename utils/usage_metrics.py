"""
Usage Metrics for Mindrian
Tracks context saves, bot usage, session activity, and user engagement.
Stores metrics in Supabase for analytics dashboard.
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from collections import defaultdict

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "mindrian-files")

# In-memory metrics cache (aggregated periodically)
_metrics_cache: Dict[str, Dict] = {
    "context_saves": defaultdict(int),      # user_key -> count
    "bot_usage": defaultdict(int),          # bot_id -> count
    "session_messages": defaultdict(int),   # session_id -> message count
    "daily_active": set(),                  # Set of active user_keys today
    "hourly_requests": defaultdict(int),    # hour -> count
    "image_uploads": defaultdict(int),      # user_key -> count
    "image_generations": defaultdict(int),  # user_key -> count
}

# Supabase client singleton
_supabase_client = None

# Last flush timestamp
_last_flush = datetime.utcnow()


def get_supabase_client():
    """Get or create Supabase client."""
    global _supabase_client

    if _supabase_client is None and SUPABASE_URL and SUPABASE_SERVICE_KEY:
        try:
            from supabase import create_client
            _supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        except Exception as e:
            print(f"Usage metrics Supabase client error: {e}")
            return None

    return _supabase_client


def track_context_save(user_key: str, bot_id: str, message_count: int):
    """
    Track a context save event.

    Args:
        user_key: User identifier
        bot_id: Bot that was used
        message_count: Number of messages in the context
    """
    _metrics_cache["context_saves"][user_key] += 1
    _metrics_cache["bot_usage"][bot_id] += 1
    _metrics_cache["daily_active"].add(user_key)

    hour = datetime.utcnow().hour
    _metrics_cache["hourly_requests"][hour] += 1


def track_message(session_id: str, user_key: str, bot_id: str):
    """
    Track a message sent in a session.

    Args:
        session_id: Session identifier
        user_key: User identifier
        bot_id: Bot that responded
    """
    _metrics_cache["session_messages"][session_id] += 1
    _metrics_cache["bot_usage"][bot_id] += 1
    _metrics_cache["daily_active"].add(user_key)

    hour = datetime.utcnow().hour
    _metrics_cache["hourly_requests"][hour] += 1


def track_image_upload(user_key: str, count: int = 1):
    """Track image upload events."""
    _metrics_cache["image_uploads"][user_key] += count
    _metrics_cache["daily_active"].add(user_key)


def track_image_generation(user_key: str, count: int = 1):
    """Track image generation events."""
    _metrics_cache["image_generations"][user_key] += count
    _metrics_cache["daily_active"].add(user_key)


def get_current_metrics() -> Dict[str, Any]:
    """
    Get current in-memory metrics snapshot.

    Returns:
        Dictionary with current metrics
    """
    return {
        "context_saves_total": sum(_metrics_cache["context_saves"].values()),
        "context_saves_by_user": len(_metrics_cache["context_saves"]),
        "bot_usage": dict(_metrics_cache["bot_usage"]),
        "active_sessions": len(_metrics_cache["session_messages"]),
        "total_messages": sum(_metrics_cache["session_messages"].values()),
        "daily_active_users": len(_metrics_cache["daily_active"]),
        "hourly_distribution": dict(_metrics_cache["hourly_requests"]),
        "image_uploads_total": sum(_metrics_cache["image_uploads"].values()),
        "image_generations_total": sum(_metrics_cache["image_generations"].values()),
        "timestamp": datetime.utcnow().isoformat()
    }


async def flush_metrics_to_supabase() -> bool:
    """
    Flush current metrics to Supabase Storage.
    Call this periodically (e.g., every 5 minutes) or on shutdown.

    Returns:
        True if flushed successfully
    """
    global _last_flush

    client = get_supabase_client()
    if not client:
        return False

    try:
        metrics = get_current_metrics()
        metrics["period_start"] = _last_flush.isoformat()
        metrics["period_end"] = datetime.utcnow().isoformat()

        # Create filename based on date and hour
        now = datetime.utcnow()
        filename = f"metrics/{now.strftime('%Y-%m-%d')}/{now.strftime('%H-%M-%S')}.json"

        json_content = json.dumps(metrics, indent=2, default=str).encode('utf-8')

        try:
            client.storage.from_(SUPABASE_BUCKET).upload(
                path=filename,
                file=json_content,
                file_options={"content-type": "application/json"}
            )
        except Exception as e:
            if "Duplicate" in str(e) or "already exists" in str(e).lower():
                client.storage.from_(SUPABASE_BUCKET).update(
                    path=filename,
                    file=json_content,
                    file_options={"content-type": "application/json"}
                )

        print(f"Metrics flushed to Supabase: {filename}")
        _last_flush = datetime.utcnow()
        return True

    except Exception as e:
        print(f"Metrics flush error: {e}")
        return False


async def get_usage_dashboard(days: int = 7) -> Dict[str, Any]:
    """
    Get comprehensive usage metrics for dashboard display.

    Args:
        days: Number of days to analyze

    Returns:
        Comprehensive usage analytics dictionary
    """
    client = get_supabase_client()
    all_metrics = []

    # Collect metrics from Supabase for the date range
    if client:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        current = start_date
        while current <= end_date:
            date_str = current.strftime("%Y-%m-%d")
            try:
                folder = f"metrics/{date_str}"
                files = client.storage.from_(SUPABASE_BUCKET).list(folder)

                for file_info in files:
                    if file_info.get("name", "").endswith(".json"):
                        path = f"{folder}/{file_info['name']}"
                        try:
                            content = client.storage.from_(SUPABASE_BUCKET).download(path)
                            if content:
                                metrics = json.loads(content.decode('utf-8'))
                                metrics["_date"] = date_str
                                all_metrics.append(metrics)
                        except Exception:
                            continue
            except Exception:
                pass
            current += timedelta(days=1)

    # Aggregate metrics
    total_saves = 0
    total_messages = 0
    total_image_uploads = 0
    total_image_generations = 0
    all_users = set()
    bot_usage_total = defaultdict(int)
    daily_stats = defaultdict(lambda: {
        "saves": 0, "messages": 0, "users": 0,
        "image_uploads": 0, "image_generations": 0
    })
    hourly_total = defaultdict(int)

    for m in all_metrics:
        total_saves += m.get("context_saves_total", 0)
        total_messages += m.get("total_messages", 0)
        total_image_uploads += m.get("image_uploads_total", 0)
        total_image_generations += m.get("image_generations_total", 0)

        # Bot usage
        for bot, count in m.get("bot_usage", {}).items():
            bot_usage_total[bot] += count

        # Hourly distribution
        for hour, count in m.get("hourly_distribution", {}).items():
            hourly_total[int(hour)] += count

        # Daily stats
        date = m.get("_date", "unknown")
        daily_stats[date]["saves"] += m.get("context_saves_total", 0)
        daily_stats[date]["messages"] += m.get("total_messages", 0)
        daily_stats[date]["users"] += m.get("daily_active_users", 0)
        daily_stats[date]["image_uploads"] += m.get("image_uploads_total", 0)
        daily_stats[date]["image_generations"] += m.get("image_generations_total", 0)

    # Add current in-memory metrics
    current = get_current_metrics()
    total_saves += current["context_saves_total"]
    total_messages += current["total_messages"]
    total_image_uploads += current["image_uploads_total"]
    total_image_generations += current["image_generations_total"]

    for bot, count in current["bot_usage"].items():
        bot_usage_total[bot] += count

    # Calculate peak hours
    if hourly_total:
        peak_hour = max(hourly_total, key=hourly_total.get)
        peak_hour_formatted = f"{peak_hour:02d}:00-{(peak_hour+1)%24:02d}:00 UTC"
    else:
        peak_hour_formatted = "N/A"

    # Calculate averages
    num_days = max(len(daily_stats), 1)
    avg_daily_messages = total_messages / num_days
    avg_daily_saves = total_saves / num_days

    return {
        "period_days": days,
        "total_context_saves": total_saves,
        "total_messages": total_messages,
        "total_image_uploads": total_image_uploads,
        "total_image_generations": total_image_generations,
        "avg_daily_messages": round(avg_daily_messages, 1),
        "avg_daily_saves": round(avg_daily_saves, 1),
        "bot_usage": dict(bot_usage_total),
        "daily_breakdown": dict(daily_stats),
        "hourly_distribution": dict(hourly_total),
        "peak_hour": peak_hour_formatted,
        "current_session_metrics": current,
        "generated_at": datetime.utcnow().isoformat()
    }


def format_usage_dashboard_message(dashboard: Dict[str, Any]) -> str:
    """
    Format usage dashboard data as a readable message.

    Args:
        dashboard: Dashboard data from get_usage_dashboard()

    Returns:
        Formatted markdown string
    """
    msg = f"""**Usage Metrics Dashboard**
*Period: Last {dashboard['period_days']} days | Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC*

---

## Overall Activity

| Metric | Value |
|--------|-------|
| Total Messages | {dashboard['total_messages']:,} |
| Context Saves | {dashboard['total_context_saves']:,} |
| Avg Daily Messages | {dashboard['avg_daily_messages']:,} |
| Avg Daily Saves | {dashboard['avg_daily_saves']:,} |
| Image Uploads | {dashboard['total_image_uploads']:,} |
| Image Generations | {dashboard['total_image_generations']:,} |
| Peak Activity Hour | {dashboard['peak_hour']} |

---

## Bot Usage

| Bot | Interactions | Share |
|-----|--------------|-------|
"""

    total_bot = sum(dashboard.get("bot_usage", {}).values()) or 1
    for bot, count in sorted(dashboard.get("bot_usage", {}).items(), key=lambda x: -x[1]):
        share = (count / total_bot) * 100
        bar = "█" * int(share / 10) + "░" * (10 - int(share / 10))
        msg += f"| {bot} | {count:,} | {bar} {share:.1f}% |\n"

    # Daily trend
    msg += "\n---\n\n## Daily Activity (Recent)\n\n| Date | Messages | Saves | Images |\n|------|----------|-------|--------|\n"
    daily = dashboard.get("daily_breakdown", {})
    for date in sorted(daily.keys(), reverse=True)[:7]:
        stats = daily[date]
        msg += f"| {date} | {stats['messages']:,} | {stats['saves']:,} | {stats.get('image_uploads', 0) + stats.get('image_generations', 0)} |\n"

    # Current session
    current = dashboard.get("current_session_metrics", {})
    if current:
        msg += f"""
---

## Current Session

| Metric | Value |
|--------|-------|
| Active Sessions | {current.get('active_sessions', 0)} |
| Messages (session) | {current.get('total_messages', 0)} |
| Active Users | {current.get('daily_active_users', 0)} |
"""

    return msg


def reset_daily_metrics():
    """Reset daily metrics (call at midnight UTC)."""
    _metrics_cache["daily_active"] = set()
    _metrics_cache["hourly_requests"] = defaultdict(int)


def is_metrics_configured() -> bool:
    """Check if Supabase is configured for metrics storage."""
    return bool(SUPABASE_URL and SUPABASE_SERVICE_KEY)
