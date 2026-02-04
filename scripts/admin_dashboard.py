#!/usr/bin/env python3
"""
Mindrian Admin Dashboard - Streamlit App
=========================================

Visual dashboard for conversation sampling, feedback analytics, and usage monitoring.

Usage:
    streamlit run scripts/admin_dashboard.py

Features:
    - Conversation browser with search
    - Feedback analytics with charts
    - Usage metrics over time
    - Audit trail viewer
    - Export functionality
"""

import os
import sys
import json
import csv
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

import streamlit as st
import pandas as pd

# Page config
st.set_page_config(
    page_title="Mindrian Admin Dashboard",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =============================================================================
# Data Loaders (Cached)
# =============================================================================

@st.cache_data(ttl=60)
def load_feedback_data() -> pd.DataFrame:
    """Load feedback from CSV."""
    csv_path = Path(__file__).parent.parent / "analytics" / "feedback_analytics.csv"
    if not csv_path.exists():
        return pd.DataFrame()

    try:
        df = pd.read_csv(csv_path)
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        return df
    except Exception as e:
        st.error(f"Error loading feedback: {e}")
        return pd.DataFrame()


def get_postgres_connection():
    """Get async PostgreSQL connection."""
    url = os.getenv("DATABASE_URL") or os.getenv("CHAINLIT_DATABASE_URL")
    if not url:
        return None

    import asyncpg

    async def connect():
        url_clean = url.replace("postgresql+asyncpg://", "postgresql://")
        return await asyncpg.connect(url_clean)

    return asyncio.get_event_loop().run_until_complete(connect())


@st.cache_data(ttl=30)
def load_recent_threads(_limit: int = 50) -> pd.DataFrame:
    """Load recent conversation threads."""
    url = os.getenv("DATABASE_URL") or os.getenv("CHAINLIT_DATABASE_URL")
    if not url:
        return pd.DataFrame()

    import asyncpg

    async def fetch():
        url_clean = url.replace("postgresql+asyncpg://", "postgresql://")
        conn = await asyncpg.connect(url_clean)
        try:
            query = """
                SELECT id, name, "createdAt", "userIdentifier",
                       (SELECT COUNT(*) FROM steps WHERE "threadId" = threads.id) as message_count
                FROM threads
                ORDER BY "createdAt" DESC
                LIMIT $1
            """
            rows = await conn.fetch(query, _limit)
            return [dict(r) for r in rows]
        finally:
            await conn.close()

    try:
        data = asyncio.get_event_loop().run_until_complete(fetch())
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Database error: {e}")
        return pd.DataFrame()


def load_thread_messages(thread_id: str) -> List[Dict]:
    """Load messages for a specific thread."""
    url = os.getenv("DATABASE_URL") or os.getenv("CHAINLIT_DATABASE_URL")
    if not url:
        return []

    import asyncpg

    async def fetch():
        url_clean = url.replace("postgresql+asyncpg://", "postgresql://")
        conn = await asyncpg.connect(url_clean)
        try:
            query = """
                SELECT id, name, type, content, "authorIsUser", "createdAt"
                FROM steps
                WHERE "threadId" = $1
                ORDER BY "createdAt" ASC
            """
            rows = await conn.fetch(query, thread_id)
            return [dict(r) for r in rows]
        finally:
            await conn.close()

    try:
        return asyncio.get_event_loop().run_until_complete(fetch())
    except Exception as e:
        st.error(f"Error loading messages: {e}")
        return []


def search_conversations(keyword: str, limit: int = 30) -> pd.DataFrame:
    """Search conversations by keyword."""
    url = os.getenv("DATABASE_URL") or os.getenv("CHAINLIT_DATABASE_URL")
    if not url:
        return pd.DataFrame()

    import asyncpg

    async def fetch():
        url_clean = url.replace("postgresql+asyncpg://", "postgresql://")
        conn = await asyncpg.connect(url_clean)
        try:
            query = """
                SELECT s.id, s."threadId", s.content, s."authorIsUser", s."createdAt",
                       t.name as thread_name, t."userIdentifier"
                FROM steps s
                JOIN threads t ON s."threadId" = t.id
                WHERE s.content ILIKE $1
                ORDER BY s."createdAt" DESC
                LIMIT $2
            """
            rows = await conn.fetch(query, f"%{keyword}%", limit)
            return [dict(r) for r in rows]
        finally:
            await conn.close()

    try:
        data = asyncio.get_event_loop().run_until_complete(fetch())
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Search error: {e}")
        return pd.DataFrame()


# =============================================================================
# Dashboard Pages
# =============================================================================

def page_overview():
    """Overview dashboard page."""
    st.header("📊 Overview")

    col1, col2, col3, col4 = st.columns(4)

    # Load data
    feedback_df = load_feedback_data()
    threads_df = load_recent_threads(100)

    # Metrics
    with col1:
        total_feedback = len(feedback_df)
        st.metric("Total Feedback", total_feedback)

    with col2:
        if not feedback_df.empty and "value" in feedback_df.columns:
            positive = (feedback_df["value"] == 1).sum()
            rate = positive / total_feedback * 100 if total_feedback > 0 else 0
            st.metric("Satisfaction Rate", f"{rate:.1f}%")
        else:
            st.metric("Satisfaction Rate", "N/A")

    with col3:
        total_threads = len(threads_df)
        st.metric("Total Conversations", total_threads)

    with col4:
        if not threads_df.empty and "message_count" in threads_df.columns:
            avg_msgs = threads_df["message_count"].mean()
            st.metric("Avg Messages/Session", f"{avg_msgs:.1f}")
        else:
            st.metric("Avg Messages/Session", "N/A")

    # Charts
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Feedback Over Time")
        if not feedback_df.empty and "date" in feedback_df.columns:
            daily = feedback_df.groupby(feedback_df["date"].dt.date).agg({
                "value": ["sum", "count"]
            }).reset_index()
            daily.columns = ["date", "positive", "total"]
            daily["negative"] = daily["total"] - daily["positive"]
            st.bar_chart(daily.set_index("date")[["positive", "negative"]])
        else:
            st.info("No feedback data available")

    with col2:
        st.subheader("Bot Usage")
        if not feedback_df.empty and "bot_id" in feedback_df.columns:
            bot_usage = feedback_df["bot_id"].value_counts()
            st.bar_chart(bot_usage)
        else:
            st.info("No bot usage data available")


def page_conversations():
    """Conversation browser page."""
    st.header("💬 Conversations")

    # Search
    search = st.text_input("🔍 Search conversations", placeholder="Enter keyword...")

    if search:
        results = search_conversations(search)
        if not results.empty:
            st.write(f"Found {len(results)} matches")
            for _, row in results.iterrows():
                author = "👤 User" if row.get("authorIsUser") else "🤖 Bot"
                with st.expander(f"{author}: {row.get('content', '')[:80]}..."):
                    st.write(f"**Thread:** {row.get('thread_name', 'Unknown')}")
                    st.write(f"**User:** {row.get('userIdentifier', 'Anonymous')}")
                    st.write(f"**Time:** {row.get('createdAt', '')}")
                    st.write(f"**Content:**\n{row.get('content', '')}")
        else:
            st.info("No results found")
        return

    # Recent threads
    st.subheader("Recent Conversations")
    threads_df = load_recent_threads(30)

    if threads_df.empty:
        st.warning("No conversations found. Check database connection.")
        return

    # Thread selector
    thread_options = {
        f"{row['name'][:40]} ({row['userIdentifier'][:15]}...) - {str(row['createdAt'])[:16]}": row['id']
        for _, row in threads_df.iterrows()
    }

    selected = st.selectbox("Select conversation", options=list(thread_options.keys()))

    if selected:
        thread_id = thread_options[selected]
        messages = load_thread_messages(thread_id)

        if messages:
            st.write(f"**{len(messages)} messages**")

            for msg in messages:
                author = "👤 User" if msg.get("authorIsUser") else "🤖 Lawrence"
                content = msg.get("content", "")

                if msg.get("authorIsUser"):
                    st.chat_message("user").write(content)
                else:
                    st.chat_message("assistant").write(content)

            # Export button
            if st.button("📥 Export as Markdown"):
                thread_info = threads_df[threads_df["id"] == thread_id].iloc[0]
                md = f"# Conversation Export\n\n"
                md += f"**Thread:** {thread_info.get('name', 'Unnamed')}\n"
                md += f"**User:** {thread_info.get('userIdentifier', 'Anonymous')}\n"
                md += f"**Date:** {thread_info.get('createdAt', '')}\n\n---\n\n"

                for msg in messages:
                    author = "**User:**" if msg.get("authorIsUser") else "**Lawrence:**"
                    md += f"{author}\n\n{msg.get('content', '')}\n\n---\n\n"

                st.download_button(
                    "Download Markdown",
                    data=md,
                    file_name=f"conversation_{thread_id[:8]}.md",
                    mime="text/markdown"
                )


def page_feedback():
    """Feedback analytics page."""
    st.header("👍 Feedback Analytics")

    feedback_df = load_feedback_data()

    if feedback_df.empty:
        st.warning("No feedback data available")
        return

    # Filters
    col1, col2 = st.columns(2)
    with col1:
        if "bot_id" in feedback_df.columns:
            bots = ["All"] + list(feedback_df["bot_id"].unique())
            selected_bot = st.selectbox("Filter by Bot", bots)
    with col2:
        days = st.slider("Days to show", 1, 30, 7)

    # Filter data
    df = feedback_df.copy()
    if selected_bot != "All":
        df = df[df["bot_id"] == selected_bot]

    cutoff = datetime.now() - timedelta(days=days)
    if "date" in df.columns:
        df = df[df["date"] >= cutoff]

    # Stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Ratings", len(df))
    with col2:
        positive = (df["value"] == 1).sum() if "value" in df.columns else 0
        st.metric("Positive", positive)
    with col3:
        negative = (df["value"] == 0).sum() if "value" in df.columns else 0
        st.metric("Negative", negative)

    # Detailed view
    st.subheader("Recent Feedback")
    if "comment" in df.columns:
        with_comments = df[df["comment"].notna() & (df["comment"] != "")]
        for _, row in with_comments.head(10).iterrows():
            rating = "👍" if row.get("value") == 1 else "👎"
            st.write(f"{rating} **{row.get('bot_id', 'unknown')}** - {row.get('comment', '')}")
            st.caption(f"{row.get('date', '')}")
    else:
        st.dataframe(df.head(20))


def page_qa_reports():
    """QA Reports page."""
    st.header("📋 QA Reports")

    qa_dir = Path(__file__).parent.parent / "qa"
    if not qa_dir.exists():
        st.warning("No QA reports directory found")
        return

    # List QA folders
    qa_folders = sorted([d for d in qa_dir.iterdir() if d.is_dir()], reverse=True)

    if not qa_folders:
        st.info("No QA reports available")
        return

    selected_date = st.selectbox("Select Date", [d.name for d in qa_folders])

    if selected_date:
        date_dir = qa_dir / selected_date
        reports = list(date_dir.glob("*.md"))

        for report in reports:
            with st.expander(f"📄 {report.name}"):
                st.markdown(report.read_text())


# =============================================================================
# Main App
# =============================================================================

def main():
    st.sidebar.title("🧠 Mindrian Admin")

    # Navigation
    page = st.sidebar.radio(
        "Navigate",
        ["Overview", "Conversations", "Feedback", "QA Reports"]
    )

    # Connection status
    st.sidebar.divider()
    st.sidebar.caption("**Data Sources**")

    db_url = os.getenv("DATABASE_URL") or os.getenv("CHAINLIT_DATABASE_URL")
    supabase = os.getenv("SUPABASE_URL")
    csv_exists = (Path(__file__).parent.parent / "analytics" / "feedback_analytics.csv").exists()

    st.sidebar.write(f"{'✅' if db_url else '❌'} PostgreSQL")
    st.sidebar.write(f"{'✅' if supabase else '❌'} Supabase")
    st.sidebar.write(f"{'✅' if csv_exists else '❌'} Feedback CSV")

    # Render page
    if page == "Overview":
        page_overview()
    elif page == "Conversations":
        page_conversations()
    elif page == "Feedback":
        page_feedback()
    elif page == "QA Reports":
        page_qa_reports()


if __name__ == "__main__":
    main()
