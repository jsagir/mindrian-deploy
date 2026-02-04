#!/usr/bin/env python3
"""
Conversation Sampler - Admin CLI for Mindrian
==============================================

Interactive tool to sample and analyze user interactions across all data sources:
- PostgreSQL (conversation history via Chainlit)
- Supabase (audit trail, session events, metrics)
- CSV (feedback analytics)
- Neo4j (user journeys)

Usage:
    python scripts/conversation_sampler.py
    python scripts/conversation_sampler.py --sessions
    python scripts/conversation_sampler.py --feedback
    python scripts/conversation_sampler.py --search "critical thinking"
    python scripts/conversation_sampler.py --export session_id
"""

import os
import sys
import json
import csv
import argparse
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path
from collections import defaultdict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment
from dotenv import load_dotenv
load_dotenv()


# =============================================================================
# Data Source Connectors
# =============================================================================

class PostgresConnector:
    """Connect to Chainlit's PostgreSQL database for conversation history."""

    def __init__(self):
        self.conn = None
        self.url = os.getenv("DATABASE_URL") or os.getenv("CHAINLIT_DATABASE_URL")

    async def connect(self):
        if not self.url:
            print("⚠️  No DATABASE_URL configured")
            return False
        try:
            import asyncpg
            # Convert SQLAlchemy URL to asyncpg format
            url = self.url.replace("postgresql+asyncpg://", "postgresql://")
            url = url.replace("postgresql://", "")
            self.conn = await asyncpg.connect(f"postgresql://{url}")
            return True
        except Exception as e:
            print(f"⚠️  PostgreSQL connection failed: {e}")
            return False

    async def close(self):
        if self.conn:
            await self.conn.close()

    async def get_recent_threads(self, limit: int = 20) -> List[Dict]:
        """Get recent conversation threads."""
        if not self.conn:
            return []

        query = """
            SELECT id, name, "createdAt", metadata, "userIdentifier"
            FROM threads
            ORDER BY "createdAt" DESC
            LIMIT $1
        """
        rows = await self.conn.fetch(query, limit)
        return [dict(r) for r in rows]

    async def get_thread_messages(self, thread_id: str) -> List[Dict]:
        """Get all messages in a thread."""
        if not self.conn:
            return []

        query = """
            SELECT id, name, type, "isError", indent, "authorIsUser",
                   "waitForAnswer", content, "createdAt"
            FROM steps
            WHERE "threadId" = $1
            ORDER BY "createdAt" ASC
        """
        rows = await self.conn.fetch(query, thread_id)
        return [dict(r) for r in rows]

    async def search_messages(self, keyword: str, limit: int = 50) -> List[Dict]:
        """Search messages by content."""
        if not self.conn:
            return []

        query = """
            SELECT s.id, s."threadId", s.content, s."createdAt", s."authorIsUser",
                   t.name as thread_name, t."userIdentifier"
            FROM steps s
            JOIN threads t ON s."threadId" = t.id
            WHERE s.content ILIKE $1
            ORDER BY s."createdAt" DESC
            LIMIT $2
        """
        rows = await self.conn.fetch(query, f"%{keyword}%", limit)
        return [dict(r) for r in rows]

    async def get_thread_by_user(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get threads for a specific user."""
        if not self.conn:
            return []

        query = """
            SELECT id, name, "createdAt", metadata
            FROM threads
            WHERE "userIdentifier" = $1
            ORDER BY "createdAt" DESC
            LIMIT $2
        """
        rows = await self.conn.fetch(query, user_id, limit)
        return [dict(r) for r in rows]


class SupabaseConnector:
    """Connect to Supabase for audit trail, events, and metrics."""

    def __init__(self):
        self.client = None
        self.bucket = os.getenv("SUPABASE_BUCKET", "mindrian-files")

    def connect(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY")
        if not url or not key:
            print("⚠️  No Supabase credentials configured")
            return False
        try:
            from supabase import create_client
            self.client = create_client(url, key)
            return True
        except Exception as e:
            print(f"⚠️  Supabase connection failed: {e}")
            return False

    def list_audit_entries(self, date: str = None, limit: int = 20) -> List[Dict]:
        """List audit trail entries."""
        if not self.client:
            return []

        date = date or datetime.now().strftime("%Y-%m-%d")
        prefix = f"audit/{date}/"

        try:
            result = self.client.storage.from_(self.bucket).list(prefix)
            entries = []
            for item in result[:limit]:
                if item.get("name", "").endswith(".json"):
                    path = f"{prefix}{item['name']}"
                    data = self.client.storage.from_(self.bucket).download(path)
                    entries.append(json.loads(data))
            return entries
        except Exception as e:
            print(f"⚠️  Audit listing failed: {e}")
            return []

    def list_session_events(self, date: str = None, limit: int = 50) -> List[Dict]:
        """List session events from Supabase table."""
        if not self.client:
            return []

        try:
            # Try table first
            result = self.client.table("session_events").select("*").order(
                "created_at", desc=True
            ).limit(limit).execute()
            return result.data if result.data else []
        except Exception as e:
            # Fallback to storage
            return []

    def get_metrics(self, date: str = None) -> Dict:
        """Get usage metrics for a date."""
        if not self.client:
            return {}

        date = date or datetime.now().strftime("%Y-%m-%d")
        prefix = f"metrics/{date}/"

        try:
            result = self.client.storage.from_(self.bucket).list(prefix)
            # Get most recent metrics file
            if result:
                latest = sorted(result, key=lambda x: x.get("name", ""))[-1]
                path = f"{prefix}{latest['name']}"
                data = self.client.storage.from_(self.bucket).download(path)
                return json.loads(data)
            return {}
        except Exception as e:
            return {}


class FeedbackConnector:
    """Read feedback from CSV file."""

    def __init__(self):
        self.csv_path = Path(__file__).parent.parent / "analytics" / "feedback_analytics.csv"

    def get_feedback(self, limit: int = 50, bot_id: str = None) -> List[Dict]:
        """Get feedback entries from CSV."""
        if not self.csv_path.exists():
            print(f"⚠️  Feedback CSV not found: {self.csv_path}")
            return []

        entries = []
        try:
            with open(self.csv_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if bot_id and row.get("bot_id") != bot_id:
                        continue
                    entries.append(row)
        except Exception as e:
            print(f"⚠️  Error reading feedback CSV: {e}")
            return []

        # Return most recent
        return entries[-limit:][::-1]

    def get_stats(self, days: int = 7) -> Dict:
        """Get feedback statistics."""
        entries = self.get_feedback(limit=1000)

        stats = {
            "total": len(entries),
            "positive": sum(1 for e in entries if e.get("value") == "1"),
            "negative": sum(1 for e in entries if e.get("value") == "0"),
            "by_bot": defaultdict(lambda: {"positive": 0, "negative": 0}),
            "by_date": defaultdict(lambda: {"positive": 0, "negative": 0}),
        }

        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        for entry in entries:
            bot = entry.get("bot_id", "unknown")
            date = entry.get("date", "")
            value = entry.get("value", "0")

            if value == "1":
                stats["by_bot"][bot]["positive"] += 1
                if date >= cutoff:
                    stats["by_date"][date]["positive"] += 1
            else:
                stats["by_bot"][bot]["negative"] += 1
                if date >= cutoff:
                    stats["by_date"][date]["negative"] += 1

        stats["satisfaction_rate"] = (
            stats["positive"] / stats["total"] * 100 if stats["total"] > 0 else 0
        )

        return stats


# =============================================================================
# Display Functions
# =============================================================================

def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")


def print_thread(thread: Dict, messages: List[Dict] = None):
    """Print a conversation thread."""
    print(f"\n📝 Thread: {thread.get('id', 'unknown')[:8]}...")
    print(f"   Name: {thread.get('name', 'Unnamed')}")
    print(f"   User: {thread.get('userIdentifier', 'anonymous')}")
    print(f"   Created: {thread.get('createdAt', 'unknown')}")

    if messages:
        print(f"\n   Messages ({len(messages)}):")
        print("   " + "-" * 50)
        for msg in messages:
            author = "👤 User" if msg.get("authorIsUser") else "🤖 Bot"
            content = msg.get("content", "")[:200]
            if len(msg.get("content", "")) > 200:
                content += "..."
            print(f"   {author}: {content}")
        print("   " + "-" * 50)


def print_feedback_stats(stats: Dict):
    """Print feedback statistics."""
    print(f"\n📊 Overall: {stats['total']} ratings")
    print(f"   👍 Positive: {stats['positive']} ({stats['satisfaction_rate']:.1f}%)")
    print(f"   👎 Negative: {stats['negative']}")

    print("\n   By Bot:")
    for bot, counts in sorted(stats["by_bot"].items()):
        total = counts["positive"] + counts["negative"]
        rate = counts["positive"] / total * 100 if total > 0 else 0
        print(f"   • {bot}: {counts['positive']}👍 {counts['negative']}👎 ({rate:.0f}%)")


def print_audit_entry(entry: Dict):
    """Print an audit trail entry."""
    print(f"\n🔍 Audit: {entry.get('id', 'unknown')[:8]}...")
    print(f"   Time: {entry.get('timestamp', 'unknown')}")
    print(f"   Bot: {entry.get('bot_id', 'unknown')}")
    print(f"   User: {entry.get('user_id', 'anonymous')[:20]}...")
    print(f"   Risk Tier: {entry.get('risk_tier', 0)}")

    user_msg = entry.get("user_message", "")[:100]
    bot_resp = entry.get("bot_response", "")[:100]
    print(f"   User: {user_msg}{'...' if len(entry.get('user_message', '')) > 100 else ''}")
    print(f"   Bot: {bot_resp}{'...' if len(entry.get('bot_response', '')) > 100 else ''}")

    if entry.get("monitoring_alerts"):
        print(f"   ⚠️  Alerts: {', '.join(entry['monitoring_alerts'])}")


def export_thread_to_markdown(thread: Dict, messages: List[Dict]) -> str:
    """Export a conversation thread to markdown format."""
    md = f"# Conversation: {thread.get('name', 'Unnamed')}\n\n"
    md += f"**Thread ID:** {thread.get('id', 'unknown')}\n"
    md += f"**User:** {thread.get('userIdentifier', 'anonymous')}\n"
    md += f"**Created:** {thread.get('createdAt', 'unknown')}\n\n"
    md += "---\n\n"

    for msg in messages:
        author = "**User:**" if msg.get("authorIsUser") else "**Lawrence:**"
        content = msg.get("content", "")
        time = msg.get("createdAt", "")
        md += f"{author} _{time}_\n\n{content}\n\n---\n\n"

    return md


# =============================================================================
# Interactive Menu
# =============================================================================

async def interactive_menu():
    """Run interactive CLI menu."""
    pg = PostgresConnector()
    sb = SupabaseConnector()
    fb = FeedbackConnector()

    # Connect to data sources
    print("\n🔌 Connecting to data sources...")
    pg_ok = await pg.connect()
    sb_ok = sb.connect()

    if pg_ok:
        print("   ✅ PostgreSQL connected")
    if sb_ok:
        print("   ✅ Supabase connected")
    print("   ✅ CSV feedback available")

    while True:
        print_header("Mindrian Conversation Sampler")
        print("  1. Recent conversations")
        print("  2. Search conversations")
        print("  3. Feedback analytics")
        print("  4. Audit trail")
        print("  5. Usage metrics")
        print("  6. Export conversation")
        print("  7. View by user")
        print("  0. Exit")

        choice = input("\nSelect option: ").strip()

        if choice == "0":
            break

        elif choice == "1":
            # Recent conversations
            print_header("Recent Conversations")
            threads = await pg.get_recent_threads(limit=10)
            if not threads:
                print("No conversations found.")
                continue

            for i, t in enumerate(threads, 1):
                print(f"  {i}. {t.get('name', 'Unnamed')[:40]} - {t.get('userIdentifier', 'anon')[:20]} - {str(t.get('createdAt', ''))[:16]}")

            # Option to view details
            detail = input("\nEnter number to view details (or Enter to skip): ").strip()
            if detail.isdigit() and 1 <= int(detail) <= len(threads):
                thread = threads[int(detail) - 1]
                messages = await pg.get_thread_messages(thread["id"])
                print_thread(thread, messages)

        elif choice == "2":
            # Search
            keyword = input("Search keyword: ").strip()
            if keyword:
                print_header(f"Search Results: '{keyword}'")
                results = await pg.search_messages(keyword, limit=20)
                for r in results:
                    author = "User" if r.get("authorIsUser") else "Bot"
                    content = r.get("content", "")[:80]
                    print(f"  [{author}] {content}...")
                    print(f"       Thread: {r.get('thread_name', 'unknown')[:30]} - {str(r.get('createdAt', ''))[:16]}")

        elif choice == "3":
            # Feedback
            print_header("Feedback Analytics")
            stats = fb.get_stats(days=7)
            print_feedback_stats(stats)

            # Recent negative
            print("\n📉 Recent Negative Feedback:")
            negative = [f for f in fb.get_feedback(limit=100) if f.get("value") == "0"]
            for f in negative[:5]:
                print(f"   • {f.get('bot_id', 'unknown')}: {f.get('comment', 'No comment')[:50]} ({f.get('date', '')})")

        elif choice == "4":
            # Audit trail
            print_header("Audit Trail")
            date = input(f"Date (YYYY-MM-DD) [default: today]: ").strip()
            date = date or datetime.now().strftime("%Y-%m-%d")

            entries = sb.list_audit_entries(date=date, limit=10)
            if not entries:
                print("No audit entries found.")
            for entry in entries:
                print_audit_entry(entry)

        elif choice == "5":
            # Usage metrics
            print_header("Usage Metrics")
            metrics = sb.get_metrics()
            if not metrics:
                print("No metrics available.")
            else:
                print(f"  📊 Context Saves: {sum(metrics.get('context_saves', {}).values())}")
                print(f"  🤖 Bot Usage:")
                for bot, count in sorted(metrics.get("bot_usage", {}).items(), key=lambda x: -x[1]):
                    print(f"     • {bot}: {count}")
                print(f"  👥 Daily Active Users: {len(metrics.get('daily_active', []))}")

        elif choice == "6":
            # Export
            thread_id = input("Thread ID to export: ").strip()
            if thread_id:
                threads = await pg.get_recent_threads(limit=100)
                thread = next((t for t in threads if t["id"].startswith(thread_id)), None)
                if thread:
                    messages = await pg.get_thread_messages(thread["id"])
                    md = export_thread_to_markdown(thread, messages)

                    filename = f"export_{thread_id[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                    export_path = Path(__file__).parent.parent / "exports" / filename
                    export_path.parent.mkdir(exist_ok=True)
                    export_path.write_text(md)
                    print(f"\n✅ Exported to: {export_path}")
                else:
                    print("Thread not found.")

        elif choice == "7":
            # By user
            user = input("User ID or email: ").strip()
            if user:
                print_header(f"Conversations for: {user}")
                threads = await pg.get_thread_by_user(user, limit=10)
                for t in threads:
                    print(f"  • {t.get('name', 'Unnamed')[:40]} - {str(t.get('createdAt', ''))[:16]}")

        input("\nPress Enter to continue...")

    await pg.close()
    print("\n👋 Goodbye!\n")


# =============================================================================
# CLI Entry Points
# =============================================================================

async def main():
    parser = argparse.ArgumentParser(description="Mindrian Conversation Sampler")
    parser.add_argument("--sessions", "-s", action="store_true", help="List recent sessions")
    parser.add_argument("--feedback", "-f", action="store_true", help="Show feedback stats")
    parser.add_argument("--search", "-q", type=str, help="Search conversations by keyword")
    parser.add_argument("--export", "-e", type=str, help="Export thread by ID")
    parser.add_argument("--audit", "-a", type=str, nargs="?", const="today", help="Show audit trail for date")
    parser.add_argument("--user", "-u", type=str, help="Show conversations for user")
    parser.add_argument("--limit", "-l", type=int, default=20, help="Limit results")

    args = parser.parse_args()

    # If no specific command, run interactive menu
    if not any([args.sessions, args.feedback, args.search, args.export, args.audit, args.user]):
        await interactive_menu()
        return

    # Connect to data sources
    pg = PostgresConnector()
    sb = SupabaseConnector()
    fb = FeedbackConnector()

    await pg.connect()
    sb.connect()

    try:
        if args.sessions:
            print_header("Recent Sessions")
            threads = await pg.get_recent_threads(limit=args.limit)
            for t in threads:
                print(f"  {t.get('id', '')[:8]}  {t.get('name', 'Unnamed')[:35]:35}  {t.get('userIdentifier', 'anon')[:20]:20}  {str(t.get('createdAt', ''))[:16]}")

        if args.feedback:
            print_header("Feedback Analytics")
            stats = fb.get_stats(days=7)
            print_feedback_stats(stats)

        if args.search:
            print_header(f"Search: '{args.search}'")
            results = await pg.search_messages(args.search, limit=args.limit)
            for r in results:
                author = "👤" if r.get("authorIsUser") else "🤖"
                print(f"  {author} {r.get('content', '')[:70]}...")
                print(f"     Thread: {r.get('thread_name', '')[:30]} | {str(r.get('createdAt', ''))[:16]}")

        if args.export:
            threads = await pg.get_recent_threads(limit=100)
            thread = next((t for t in threads if t["id"].startswith(args.export)), None)
            if thread:
                messages = await pg.get_thread_messages(thread["id"])
                md = export_thread_to_markdown(thread, messages)
                filename = f"export_{args.export[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                print(md)
                print(f"\n--- Would save to: exports/{filename} ---")
            else:
                print(f"Thread '{args.export}' not found")

        if args.audit:
            print_header("Audit Trail")
            date = args.audit if args.audit != "today" else datetime.now().strftime("%Y-%m-%d")
            entries = sb.list_audit_entries(date=date, limit=args.limit)
            for entry in entries:
                print_audit_entry(entry)

        if args.user:
            print_header(f"User: {args.user}")
            threads = await pg.get_thread_by_user(args.user, limit=args.limit)
            for t in threads:
                print(f"  {t.get('id', '')[:8]}  {t.get('name', 'Unnamed')[:40]:40}  {str(t.get('createdAt', ''))[:16]}")

    finally:
        await pg.close()


if __name__ == "__main__":
    asyncio.run(main())
