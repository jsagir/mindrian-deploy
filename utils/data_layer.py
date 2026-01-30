"""
Custom Data Layer for Mindrian
Extends Chainlit's SQLAlchemy data layer with feedback analytics, CSV export, and Supabase integration.

Built-in Human Feedback System using Chainlit's native feedback collection.
"""

import os
import json
import csv
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path

import chainlit as cl
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "mindrian-files")

# Analytics export directory
ANALYTICS_DIR = Path("analytics")
ANALYTICS_DIR.mkdir(exist_ok=True)


class MindrianDataLayer(SQLAlchemyDataLayer):
    """
    Custom data layer that extends SQLAlchemyDataLayer with:
    - Automatic CSV export of feedback
    - Supabase storage integration
    - Enhanced analytics tracking
    """

    def __init__(self, conninfo: str, ssl_require: bool = True):
        """Initialize the data layer with PostgreSQL connection."""
        super().__init__(conninfo=conninfo, ssl_require=ssl_require)

        # In-memory feedback cache for fast analytics
        self.feedback_cache: List[Dict] = []

        # Load existing feedback from CSV if available
        self._load_existing_feedback()

        # Supabase client (lazy initialization)
        self._supabase_client = None

        print("✅ MindrianDataLayer initialized with feedback analytics")

    def _load_existing_feedback(self):
        """Load existing feedback from CSV file."""
        csv_path = ANALYTICS_DIR / "feedback_analytics.csv"
        if csv_path.exists():
            try:
                with open(csv_path, 'r', newline='') as f:
                    reader = csv.DictReader(f)
                    self.feedback_cache = list(reader)
                print(f"📊 Loaded {len(self.feedback_cache)} existing feedback records")
            except Exception as e:
                print(f"⚠️ Could not load existing feedback: {e}")

    def _get_supabase_client(self):
        """Get or create Supabase client."""
        if self._supabase_client is None and SUPABASE_URL and SUPABASE_SERVICE_KEY:
            try:
                from supabase import create_client
                self._supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
            except Exception as e:
                print(f"⚠️ Supabase client error: {e}")
        return self._supabase_client

    async def upsert_feedback(self, feedback) -> str:
        """
        Called automatically when user clicks thumbs up/down or adds comment.

        This is the core of Chainlit's native feedback system - the UI automatically
        shows thumbs up/down buttons on AI messages, and this method is called
        when the user interacts with them.

        Args:
            feedback: Chainlit Feedback object with:
                - id: Feedback ID
                - for_id: Message ID being rated
                - value: 1 for thumbs up, 0 for thumbs down
                - comment: Optional user comment

        Returns:
            feedback.id
        """
        # First, call parent to store in PostgreSQL
        try:
            await super().upsert_feedback(feedback)
        except Exception as e:
            print(f"⚠️ Parent feedback storage error: {e}")

        # Extract feedback details
        try:
            user = cl.user_session.get("user")
            user_id = user.identifier if user else "anonymous"
        except Exception:
            user_id = "anonymous"

        # Get current bot context
        try:
            bot_id = cl.user_session.get("bot_id", "unknown")
            # current_phase is an index, phases is the array
            phase_idx = cl.user_session.get("current_phase", 0)
            phases = cl.user_session.get("phases", [])
            if phases and isinstance(phase_idx, int) and phase_idx < len(phases):
                phase = phases[phase_idx].get("name", "general")
            else:
                phase = "general"
        except Exception:
            bot_id = "unknown"
            phase = "general"

        # Create feedback record
        feedback_record = {
            "feedback_id": feedback.id,
            "message_id": feedback.for_id,
            "value": feedback.value,  # 1 = thumbs up, 0 = thumbs down
            "comment": feedback.comment or "",
            "timestamp": datetime.utcnow().isoformat(),
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "user_id": user_id,
            "bot_id": bot_id,
            "phase": phase,
            "rating": "positive" if feedback.value >= 1 else "negative",
        }

        # Add to in-memory cache
        self.feedback_cache.append(feedback_record)

        # Export to CSV
        self._export_to_csv()

        # Store in Supabase (async, fire-and-forget)
        self._save_to_supabase(feedback_record)

        print(f"📊 Feedback received: {'👍' if feedback.value >= 1 else '👎'} for message {feedback.for_id[:8]}...")

        return feedback.id

    def _export_to_csv(self):
        """Export all feedback to CSV for analysis."""
        csv_path = ANALYTICS_DIR / "feedback_analytics.csv"

        try:
            fieldnames = [
                'feedback_id', 'message_id', 'value', 'comment',
                'timestamp', 'date', 'user_id', 'bot_id', 'phase', 'rating'
            ]

            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.feedback_cache)

            print(f"📁 Feedback exported to {csv_path}")
        except Exception as e:
            print(f"⚠️ CSV export error: {e}")

    def _save_to_supabase(self, feedback_record: Dict):
        """Save feedback to Supabase Storage as JSON."""
        client = self._get_supabase_client()
        if not client:
            return

        try:
            date_str = feedback_record.get("date", datetime.utcnow().strftime("%Y-%m-%d"))
            feedback_id = feedback_record.get("feedback_id", "unknown")
            filename = f"feedback/{date_str}/{feedback_id}.json"

            json_content = json.dumps(feedback_record, indent=2).encode('utf-8')

            # Try upload, update if exists
            try:
                client.storage.from_(SUPABASE_BUCKET).upload(
                    path=filename,
                    file=json_content,
                    file_options={"content-type": "application/json"}
                )
            except Exception as upload_error:
                if "Duplicate" in str(upload_error) or "already exists" in str(upload_error).lower():
                    client.storage.from_(SUPABASE_BUCKET).update(
                        path=filename,
                        file=json_content,
                        file_options={"content-type": "application/json"}
                    )

            print(f"☁️ Feedback saved to Supabase: {filename}")
        except Exception as e:
            print(f"⚠️ Supabase storage error: {e}")

    # === Analytics Methods ===

    def get_feedback_stats(self, date: Optional[str] = None, bot_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get feedback statistics.

        Args:
            date: Filter by date (YYYY-MM-DD format)
            bot_id: Filter by bot ID

        Returns:
            Dictionary with feedback statistics
        """
        feedback = self.feedback_cache.copy()

        # Apply filters
        if date:
            feedback = [f for f in feedback if f.get("date") == date]
        if bot_id:
            feedback = [f for f in feedback if f.get("bot_id") == bot_id]

        total = len(feedback)
        if total == 0:
            return {"total": 0, "message": "No feedback found"}

        positive = sum(1 for f in feedback if str(f.get("value")) == "1")
        negative = total - positive
        with_comments = sum(1 for f in feedback if f.get("comment"))

        # Bot breakdown
        bot_stats = {}
        for f in feedback:
            bot = f.get("bot_id", "unknown")
            if bot not in bot_stats:
                bot_stats[bot] = {"positive": 0, "negative": 0, "total": 0}
            bot_stats[bot]["total"] += 1
            if str(f.get("value")) == "1":
                bot_stats[bot]["positive"] += 1
            else:
                bot_stats[bot]["negative"] += 1

        return {
            "total": total,
            "positive": positive,
            "negative": negative,
            "satisfaction_rate": (positive / total * 100) if total > 0 else 0,
            "with_comments": with_comments,
            "by_bot": bot_stats,
            "recent_negative": [
                f for f in feedback if str(f.get("value")) == "0"
            ][-5:],
        }

    def get_recent_feedback(self, limit: int = 10) -> List[Dict]:
        """Get most recent feedback entries."""
        sorted_feedback = sorted(
            self.feedback_cache,
            key=lambda x: x.get("timestamp", ""),
            reverse=True
        )
        return sorted_feedback[:limit]

    def export_feedback_report(self, date: Optional[str] = None) -> str:
        """
        Generate a markdown report of feedback.

        Args:
            date: Filter by date (YYYY-MM-DD) or None for all

        Returns:
            Markdown formatted report
        """
        stats = self.get_feedback_stats(date=date)

        report = f"""# Mindrian Feedback Report
**Date:** {date or "All Time"}
**Generated:** {datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}

---

## Summary

| Metric | Value |
|--------|-------|
| Total Feedback | {stats.get('total', 0)} |
| Positive (👍) | {stats.get('positive', 0)} |
| Negative (👎) | {stats.get('negative', 0)} |
| Satisfaction Rate | {stats.get('satisfaction_rate', 0):.1f}% |
| With Comments | {stats.get('with_comments', 0)} |

---

## By Bot

| Bot | 👍 | 👎 | Total | Rate |
|-----|----|----|-------|------|
"""

        for bot, data in stats.get("by_bot", {}).items():
            rate = (data['positive'] / data['total'] * 100) if data['total'] > 0 else 0
            report += f"| {bot} | {data['positive']} | {data['negative']} | {data['total']} | {rate:.1f}% |\n"

        # Recent negative feedback
        if stats.get("recent_negative"):
            report += "\n---\n\n## Recent Negative Feedback\n\n"
            for f in stats["recent_negative"]:
                report += f"""
### {f.get('feedback_id', 'N/A')[:8]}...
- **Bot:** {f.get('bot_id', 'unknown')}
- **Phase:** {f.get('phase', 'N/A')}
- **Comment:** {f.get('comment', 'No comment')}
- **Time:** {f.get('timestamp', 'N/A')}
"""

        return report


def create_mindrian_data_layer(database_url: str) -> Optional[MindrianDataLayer]:
    """
    Create and return a MindrianDataLayer instance.

    Args:
        database_url: PostgreSQL connection URL

    Returns:
        MindrianDataLayer instance or None if connection fails
    """
    if not database_url:
        print("ℹ️ No DATABASE_URL provided, data layer disabled")
        return None

    try:
        # Convert postgresql:// to postgresql+asyncpg:// for async support
        db_url = database_url
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)

        return MindrianDataLayer(conninfo=db_url, ssl_require=True)
    except Exception as e:
        print(f"⚠️ Failed to create data layer: {e}")
        return None


# === Standalone Analytics Functions (for use without data layer) ===

def get_csv_feedback_stats() -> Dict[str, Any]:
    """Get feedback stats directly from CSV file (no data layer needed)."""
    csv_path = ANALYTICS_DIR / "feedback_analytics.csv"

    if not csv_path.exists():
        return {"total": 0, "message": "No feedback CSV found"}

    feedback = []
    try:
        with open(csv_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            feedback = list(reader)
    except Exception as e:
        return {"total": 0, "error": str(e)}

    total = len(feedback)
    if total == 0:
        return {"total": 0, "message": "CSV is empty"}

    positive = sum(1 for f in feedback if str(f.get("value")) == "1")

    return {
        "total": total,
        "positive": positive,
        "negative": total - positive,
        "satisfaction_rate": (positive / total * 100) if total > 0 else 0,
    }
