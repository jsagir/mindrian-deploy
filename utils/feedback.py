"""
Feedback Storage for Mindrian QA
Stores user feedback (thumbs up/down, comments) in Supabase for analytics
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
    score: int,  # 1 = thumbs up, 0 = thumbs down
    comment: Optional[str] = None,
    bot_id: Optional[str] = None,
    phase: Optional[str] = None,
    message_content: Optional[str] = None,
    user_message: Optional[str] = None,
) -> bool:
    """
    Store user feedback in Supabase storage.

    Args:
        message_id: Chainlit message ID
        thread_id: Conversation thread ID
        score: 1 for positive, 0 for negative
        comment: Optional user comment explaining the rating
        bot_id: Which bot generated the message (larry, tta, etc.)
        phase: Workshop phase if applicable
        message_content: The AI message that was rated (for context)
        user_message: The user's question that led to this response

    Returns:
        True if stored successfully
    """
    feedback_data = {
        "message_id": message_id,
        "thread_id": thread_id,
        "score": score,
        "rating": "positive" if score == 1 else "negative",
        "comment": comment,
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
