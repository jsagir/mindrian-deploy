"""
Feedback Storage for Mindrian QA
Stores user feedback (thumbs up/down, detailed ratings, comments) in Supabase for analytics
"""

import os
import json
from datetime import datetime
from typing import Optional, Dict, Any, List

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "mindrian-files")

# In-memory cache for recent feedback (for session analytics)
_feedback_cache: Dict[str, Dict] = {}

# Initialize Supabase client
_supabase_client = None

# Rating scale options (1-5 with emojis)
RATING_SCALE = {
    1: {"emoji": "😞", "label": "Not helpful", "description": "Response missed the point"},
    2: {"emoji": "😕", "label": "Somewhat helpful", "description": "Partially addressed my question"},
    3: {"emoji": "😐", "label": "Okay", "description": "Adequate but could be better"},
    4: {"emoji": "🙂", "label": "Helpful", "description": "Good response, addressed my needs"},
    5: {"emoji": "🤩", "label": "Excellent", "description": "Exactly what I needed!"},
}

# Quick feedback categories for detailed insights
FEEDBACK_CATEGORIES = {
    "accuracy": "Was the information accurate?",
    "relevance": "Was it relevant to your question?",
    "clarity": "Was it easy to understand?",
    "depth": "Was it detailed enough?",
    "actionable": "Did it give actionable insights?",
}


def get_supabase_client():
    """Get or create Supabase client."""
    global _supabase_client

    if _supabase_client is None and SUPABASE_URL and SUPABASE_SERVICE_KEY:
        try:
            from supabase import create_client
            _supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        except Exception as e:
            print(f"Supabase feedback client error: {e}")
            return None

    return _supabase_client


def store_feedback(
    message_id: str,
    thread_id: str,
    score: int,  # 0-1 for thumbs, 1-5 for detailed rating
    comment: Optional[str] = None,
    bot_id: Optional[str] = None,
    phase: Optional[str] = None,
    message_content: Optional[str] = None,
    user_message: Optional[str] = None,
    feedback_type: str = "thumbs",  # "thumbs" or "detailed"
    categories: Optional[Dict[str, bool]] = None,  # Category ratings
) -> bool:
    """
    Store user feedback in Supabase storage.

    Args:
        message_id: Chainlit message ID
        thread_id: Conversation thread ID
        score: 0-1 for thumbs (0=down, 1=up), 1-5 for detailed rating
        comment: Optional user comment explaining the rating
        bot_id: Which bot generated the message (larry, tta, etc.)
        phase: Workshop phase if applicable
        message_content: The AI message that was rated (for context)
        user_message: The user's question that led to this response
        feedback_type: "thumbs" for simple up/down, "detailed" for 1-5 scale
        categories: Dict of category ratings (e.g., {"accuracy": True, "clarity": False})

    Returns:
        True if stored successfully
    """
    # Determine rating label based on feedback type
    if feedback_type == "detailed" and score in RATING_SCALE:
        rating_info = RATING_SCALE[score]
        rating_label = rating_info["label"]
        rating_emoji = rating_info["emoji"]
    else:
        rating_label = "positive" if score >= 1 else "negative"
        rating_emoji = "👍" if score >= 1 else "👎"

    feedback_data = {
        "message_id": message_id,
        "thread_id": thread_id,
        "score": score,
        "feedback_type": feedback_type,
        "rating": rating_label,
        "rating_emoji": rating_emoji,
        "comment": comment,
        "categories": categories or {},
        "bot_id": bot_id,
        "phase": phase,
        "message_preview": (message_content[:500] + "...") if message_content and len(message_content) > 500 else message_content,
        "user_message_preview": (user_message[:200] + "...") if user_message and len(user_message) > 200 else user_message,
        "timestamp": datetime.utcnow().isoformat(),
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
    }

    # Cache in memory
    _feedback_cache[message_id] = feedback_data

    # Store in Supabase
    return _save_to_supabase(feedback_data)


def get_feedback_confirmation_message(
    score: int,
    feedback_type: str = "thumbs",
    comment: Optional[str] = None
) -> str:
    """
    Generate a confirmation message to show in the conversation.

    Args:
        score: The rating score
        feedback_type: "thumbs" or "detailed"
        comment: Optional user comment

    Returns:
        Formatted confirmation message
    """
    if feedback_type == "detailed" and score in RATING_SCALE:
        info = RATING_SCALE[score]
        msg = f"**{info['emoji']} Feedback Received: {info['label']}**"
    else:
        emoji = "👍" if score >= 1 else "👎"
        label = "Positive" if score >= 1 else "Negative"
        msg = f"**{emoji} Feedback Received: {label}**"

    if comment:
        msg += f"\n\n*Your comment:* \"{comment}\""

    msg += "\n\n*Thank you for helping improve Mindrian!*"
    return msg


def get_rating_scale_display() -> str:
    """Get a formatted display of the rating scale for UI."""
    lines = ["**Rate this response:**\n"]
    for score, info in RATING_SCALE.items():
        lines.append(f"{info['emoji']} **{score}** - {info['label']}")
    return "\n".join(lines)


def _save_to_supabase(feedback_data: Dict) -> bool:
    """Save feedback to Supabase Storage as JSON."""
    client = get_supabase_client()
    if not client:
        print("Feedback stored in memory only (Supabase not configured)")
        return False

    try:
        # Create a unique filename based on date and message ID
        date_str = feedback_data.get("date", datetime.utcnow().strftime("%Y-%m-%d"))
        message_id = feedback_data.get("message_id", "unknown")
        filename = f"feedback/{date_str}/{message_id}.json"

        # Upload to Supabase Storage
        json_content = json.dumps(feedback_data, indent=2).encode('utf-8')
        client.storage.from_(SUPABASE_BUCKET).upload(
            path=filename,
            file=json_content,
            file_options={"content-type": "application/json"}
        )
        print(f"Feedback saved: {filename}")
        return True

    except Exception as e:
        # If file exists, try to update (upsert)
        if "Duplicate" in str(e) or "already exists" in str(e).lower():
            try:
                client.storage.from_(SUPABASE_BUCKET).update(
                    path=filename,
                    file=json_content,
                    file_options={"content-type": "application/json"}
                )
                print(f"Feedback updated: {filename}")
                return True
            except Exception as update_err:
                print(f"Feedback update error: {update_err}")
                return False
        print(f"Feedback storage error: {e}")
        return False


def get_feedback_stats(
    date: Optional[str] = None,
    bot_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get feedback statistics.

    Args:
        date: Filter by date (YYYY-MM-DD format)
        bot_id: Filter by bot ID

    Returns:
        Dictionary with feedback statistics
    """
    client = get_supabase_client()

    # Start with in-memory cache
    all_feedback = list(_feedback_cache.values())

    # Add from Supabase if available
    if client:
        try:
            folder = f"feedback/{date}" if date else "feedback"
            files = client.storage.from_(SUPABASE_BUCKET).list(folder)

            for file_info in files:
                if file_info.get("name", "").endswith(".json"):
                    path = f"{folder}/{file_info['name']}"
                    content = client.storage.from_(SUPABASE_BUCKET).download(path)
                    if content:
                        feedback = json.loads(content.decode('utf-8'))
                        all_feedback.append(feedback)
        except Exception as e:
            print(f"Error fetching feedback from Supabase: {e}")

    # Filter by bot if specified
    if bot_id:
        all_feedback = [f for f in all_feedback if f.get("bot_id") == bot_id]

    # Calculate statistics
    total = len(all_feedback)
    positive = sum(1 for f in all_feedback if f.get("score") == 1)
    negative = total - positive
    with_comments = sum(1 for f in all_feedback if f.get("comment"))

    # Bot breakdown
    bot_stats = {}
    for f in all_feedback:
        bot = f.get("bot_id", "unknown")
        if bot not in bot_stats:
            bot_stats[bot] = {"positive": 0, "negative": 0, "total": 0}
        bot_stats[bot]["total"] += 1
        if f.get("score") == 1:
            bot_stats[bot]["positive"] += 1
        else:
            bot_stats[bot]["negative"] += 1

    return {
        "total_feedback": total,
        "positive": positive,
        "negative": negative,
        "positive_rate": (positive / total * 100) if total > 0 else 0,
        "with_comments": with_comments,
        "by_bot": bot_stats,
        "recent_negative": [
            f for f in all_feedback
            if f.get("score") == 0
        ][-5:],  # Last 5 negative feedback for review
    }


def get_session_feedback(thread_id: str) -> List[Dict]:
    """Get all feedback for a specific session/thread."""
    return [
        f for f in _feedback_cache.values()
        if f.get("thread_id") == thread_id
    ]


def export_feedback_report(date: Optional[str] = None) -> str:
    """
    Generate a markdown report of feedback.

    Args:
        date: Filter by date (YYYY-MM-DD) or None for all

    Returns:
        Markdown formatted report
    """
    stats = get_feedback_stats(date=date)

    report = f"""# Mindrian Feedback Report
**Date:** {date or "All Time"}
**Generated:** {datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}

---

## Summary

| Metric | Value |
|--------|-------|
| Total Feedback | {stats['total_feedback']} |
| Positive (👍) | {stats['positive']} |
| Negative (👎) | {stats['negative']} |
| Satisfaction Rate | {stats['positive_rate']:.1f}% |
| With Comments | {stats['with_comments']} |

---

## By Bot

| Bot | 👍 | 👎 | Total | Rate |
|-----|----|----|-------|------|
"""

    for bot, data in stats.get("by_bot", {}).items():
        rate = (data['positive'] / data['total'] * 100) if data['total'] > 0 else 0
        report += f"| {bot} | {data['positive']} | {data['negative']} | {data['total']} | {rate:.1f}% |\n"

    # Add recent negative feedback for review
    if stats.get("recent_negative"):
        report += "\n---\n\n## Recent Negative Feedback (for review)\n\n"
        for f in stats["recent_negative"]:
            report += f"""
### Message ID: {f.get('message_id', 'N/A')[:8]}...
- **Bot:** {f.get('bot_id', 'unknown')}
- **Phase:** {f.get('phase', 'N/A')}
- **User Question:** {f.get('user_message_preview', 'N/A')}
- **Comment:** {f.get('comment', 'No comment')}
- **Time:** {f.get('timestamp', 'N/A')}
"""

    return report


def is_feedback_configured() -> bool:
    """Check if Supabase is configured for feedback storage."""
    return bool(SUPABASE_URL and SUPABASE_SERVICE_KEY)


# === Enhanced Analytics Dashboard ===

async def get_feedback_dashboard(
    days: int = 7,
    bot_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get comprehensive feedback analytics for dashboard display.

    Args:
        days: Number of days to analyze (default 7)
        bot_id: Filter by specific bot (optional)

    Returns:
        Comprehensive analytics dictionary
    """
    from datetime import timedelta

    client = get_supabase_client()
    all_feedback = []

    # Collect feedback from Supabase for the date range
    if client:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Iterate through date folders
        current = start_date
        while current <= end_date:
            date_str = current.strftime("%Y-%m-%d")
            try:
                folder = f"feedback/{date_str}"
                files = client.storage.from_(SUPABASE_BUCKET).list(folder)

                for file_info in files:
                    if file_info.get("name", "").endswith(".json"):
                        path = f"{folder}/{file_info['name']}"
                        try:
                            content = client.storage.from_(SUPABASE_BUCKET).download(path)
                            if content:
                                feedback = json.loads(content.decode('utf-8'))
                                all_feedback.append(feedback)
                        except Exception:
                            continue
            except Exception:
                pass
            current += timedelta(days=1)

    # Add in-memory cache
    all_feedback.extend(_feedback_cache.values())

    # Filter by bot if specified
    if bot_id:
        all_feedback = [f for f in all_feedback if f.get("bot_id") == bot_id]

    # Remove duplicates by message_id
    seen = set()
    unique_feedback = []
    for f in all_feedback:
        msg_id = f.get("message_id")
        if msg_id and msg_id not in seen:
            seen.add(msg_id)
            unique_feedback.append(f)
    all_feedback = unique_feedback

    # Calculate comprehensive stats
    total = len(all_feedback)
    if total == 0:
        return {
            "period_days": days,
            "total_feedback": 0,
            "message": "No feedback data found for this period"
        }

    positive = sum(1 for f in all_feedback if f.get("score", 0) >= 1)
    negative = total - positive
    with_comments = sum(1 for f in all_feedback if f.get("comment"))

    # Daily breakdown
    daily_stats = {}
    for f in all_feedback:
        date = f.get("date", "unknown")
        if date not in daily_stats:
            daily_stats[date] = {"positive": 0, "negative": 0, "total": 0}
        daily_stats[date]["total"] += 1
        if f.get("score", 0) >= 1:
            daily_stats[date]["positive"] += 1
        else:
            daily_stats[date]["negative"] += 1

    # Bot breakdown with detailed stats
    bot_stats = {}
    for f in all_feedback:
        bot = f.get("bot_id", "unknown")
        if bot not in bot_stats:
            bot_stats[bot] = {
                "positive": 0, "negative": 0, "total": 0,
                "comments": [], "phases": {}
            }
        bot_stats[bot]["total"] += 1
        if f.get("score", 0) >= 1:
            bot_stats[bot]["positive"] += 1
        else:
            bot_stats[bot]["negative"] += 1
            # Collect negative feedback comments for review
            if f.get("comment"):
                bot_stats[bot]["comments"].append({
                    "comment": f["comment"],
                    "user_question": f.get("user_message_preview", "N/A"),
                    "timestamp": f.get("timestamp", "N/A")
                })

        # Track by phase
        phase = f.get("phase", "general")
        if phase not in bot_stats[bot]["phases"]:
            bot_stats[bot]["phases"][phase] = {"positive": 0, "negative": 0}
        if f.get("score", 0) >= 1:
            bot_stats[bot]["phases"][phase]["positive"] += 1
        else:
            bot_stats[bot]["phases"][phase]["negative"] += 1

    # Calculate satisfaction rates
    for bot in bot_stats:
        total_bot = bot_stats[bot]["total"]
        bot_stats[bot]["satisfaction_rate"] = (
            (bot_stats[bot]["positive"] / total_bot * 100) if total_bot > 0 else 0
        )

    # Recent feedback (last 10)
    sorted_feedback = sorted(
        all_feedback,
        key=lambda x: x.get("timestamp", ""),
        reverse=True
    )[:10]

    # Trend analysis (compare first half vs second half of period)
    mid_point = len(all_feedback) // 2
    if mid_point > 0:
        first_half = all_feedback[:mid_point]
        second_half = all_feedback[mid_point:]
        first_rate = sum(1 for f in first_half if f.get("score", 0) >= 1) / len(first_half) * 100
        second_rate = sum(1 for f in second_half if f.get("score", 0) >= 1) / len(second_half) * 100
        trend = "improving" if second_rate > first_rate else "declining" if second_rate < first_rate else "stable"
        trend_delta = second_rate - first_rate
    else:
        trend = "insufficient_data"
        trend_delta = 0

    return {
        "period_days": days,
        "total_feedback": total,
        "positive": positive,
        "negative": negative,
        "satisfaction_rate": (positive / total * 100) if total > 0 else 0,
        "with_comments": with_comments,
        "daily_breakdown": daily_stats,
        "by_bot": bot_stats,
        "recent_feedback": sorted_feedback,
        "trend": trend,
        "trend_delta": round(trend_delta, 1),
        "generated_at": datetime.utcnow().isoformat()
    }


def format_dashboard_message(dashboard: Dict[str, Any]) -> str:
    """
    Format dashboard data as a readable message for display.

    Args:
        dashboard: Dashboard data from get_feedback_dashboard()

    Returns:
        Formatted markdown string
    """
    if dashboard.get("total_feedback", 0) == 0:
        return f"**Feedback Dashboard** ({dashboard.get('period_days', 7)} days)\n\nNo feedback data found for this period."

    # Header
    msg = f"""**Feedback Analytics Dashboard**
*Period: Last {dashboard['period_days']} days | Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC*

---

## Overall Summary

| Metric | Value |
|--------|-------|
| Total Feedback | {dashboard['total_feedback']} |
| Positive | {dashboard['positive']} |
| Negative | {dashboard['negative']} |
| **Satisfaction Rate** | **{dashboard['satisfaction_rate']:.1f}%** |
| With Comments | {dashboard['with_comments']} |
| Trend | {dashboard['trend'].replace('_', ' ').title()} ({'+' if dashboard['trend_delta'] > 0 else ''}{dashboard['trend_delta']}%) |

---

## By Bot

| Bot | Total | Rate | Trend |
|-----|-------|---------|-------|
"""

    # Bot stats
    for bot, stats in dashboard.get("by_bot", {}).items():
        emoji = "🟢" if stats["satisfaction_rate"] >= 80 else "🟡" if stats["satisfaction_rate"] >= 60 else "🔴"
        msg += f"| {bot} | {stats['total']} | {stats['satisfaction_rate']:.1f}% | {emoji} |\n"

    # Daily breakdown (last 5 days)
    msg += "\n---\n\n## Daily Trend (Recent)\n\n| Date | Total | Rate |\n|------|-------|------|\n"
    daily = dashboard.get("daily_breakdown", {})
    for date in sorted(daily.keys(), reverse=True)[:5]:
        stats = daily[date]
        rate = (stats["positive"] / stats["total"] * 100) if stats["total"] > 0 else 0
        msg += f"| {date} | {stats['total']} | {rate:.0f}% |\n"

    # Recent negative feedback for review
    negative_feedback = [f for f in dashboard.get("recent_feedback", []) if f.get("score", 0) == 0]
    if negative_feedback:
        msg += "\n---\n\n## Recent Negative Feedback (Action Items)\n\n"
        for i, f in enumerate(negative_feedback[:3], 1):
            msg += f"**{i}. {f.get('bot_id', 'unknown')}** - {f.get('timestamp', 'N/A')[:10]}\n"
            msg += f"   - Question: *{f.get('user_message_preview', 'N/A')[:100]}*\n"
            if f.get("comment"):
                msg += f"   - Comment: \"{f['comment'][:150]}\"\n"
            msg += "\n"

    return msg
