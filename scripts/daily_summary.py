#!/usr/bin/env python3
"""
Daily Summary Email Automation
==============================

Sends daily summary report to specified email with:
- Bank of Opportunities accumulation
- User engagement metrics (feedback, sessions)
- Key insights and trends

Run via cron or scheduler:
    0 8 * * * cd /path/to/mindrian-deploy && python scripts/daily_summary.py

Environment Variables Required:
- SUPABASE_URL
- SUPABASE_SERVICE_KEY
- SMTP_USER / SMTP_PASSWORD (or SENDGRID_API_KEY)
"""

import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "mindrian-files")

# Default recipient
DEFAULT_RECIPIENT = "jsagir@gmail.com"


def get_supabase_client():
    """Get Supabase client."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("Supabase not configured")
        return None

    try:
        from supabase import create_client
        return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    except Exception as e:
        print(f"Supabase client error: {e}")
        return None


def get_opportunities_summary(client, date_str: str = None) -> Dict[str, Any]:
    """
    Get opportunity bank summary from Supabase.

    Returns counts, types breakdown, and recent opportunities.
    """
    if not client:
        return {"error": "No Supabase client", "total": 0}

    if not date_str:
        date_str = datetime.utcnow().strftime("%Y-%m-%d")

    try:
        # List files in opportunities folder
        opportunities = []

        # Try to list today's opportunities
        try:
            today_files = client.storage.from_(SUPABASE_BUCKET).list(f"opportunities/{date_str}")
            for f in today_files:
                if f.get('name', '').endswith('.json'):
                    opportunities.append({
                        "date": date_str,
                        "file": f.get('name'),
                        "created": f.get('created_at', '')
                    })
        except Exception:
            pass

        # Get yesterday's opportunities for comparison
        yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        yesterday_count = 0
        try:
            yesterday_files = client.storage.from_(SUPABASE_BUCKET).list(f"opportunities/{yesterday}")
            yesterday_count = len([f for f in yesterday_files if f.get('name', '').endswith('.json')])
        except Exception:
            pass

        # Try to get total count (list all date folders)
        total_count = 0
        try:
            date_folders = client.storage.from_(SUPABASE_BUCKET).list("opportunities")
            for folder in date_folders:
                if folder.get('name') and not folder.get('name').endswith('.json'):
                    folder_files = client.storage.from_(SUPABASE_BUCKET).list(f"opportunities/{folder['name']}")
                    total_count += len([f for f in folder_files if f.get('name', '').endswith('.json')])
        except Exception:
            total_count = len(opportunities)

        return {
            "date": date_str,
            "today_count": len(opportunities),
            "yesterday_count": yesterday_count,
            "total_count": total_count,
            "change": len(opportunities) - yesterday_count,
            "recent": opportunities[:10]
        }

    except Exception as e:
        print(f"Opportunities fetch error: {e}")
        return {"error": str(e), "total": 0}


def get_feedback_summary(client, date_str: str = None) -> Dict[str, Any]:
    """
    Get user engagement/feedback summary from Supabase.
    """
    if not client:
        return {"error": "No Supabase client", "total": 0}

    if not date_str:
        date_str = datetime.utcnow().strftime("%Y-%m-%d")

    try:
        feedback_items = []
        positive = 0
        negative = 0

        # List today's feedback files
        try:
            today_files = client.storage.from_(SUPABASE_BUCKET).list(f"feedback/{date_str}")
            for f in today_files:
                if f.get('name', '').endswith('.json'):
                    # Download and parse feedback
                    try:
                        content = client.storage.from_(SUPABASE_BUCKET).download(
                            f"feedback/{date_str}/{f['name']}"
                        )
                        data = json.loads(content.decode('utf-8'))
                        feedback_items.append(data)
                        if str(data.get('value')) == '1':
                            positive += 1
                        else:
                            negative += 1
                    except Exception:
                        pass
        except Exception:
            pass

        # Get yesterday for comparison
        yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        yesterday_count = 0
        try:
            yesterday_files = client.storage.from_(SUPABASE_BUCKET).list(f"feedback/{yesterday}")
            yesterday_count = len([f for f in yesterday_files if f.get('name', '').endswith('.json')])
        except Exception:
            pass

        total = positive + negative
        satisfaction = (positive / total * 100) if total > 0 else 0

        # Group by bot
        by_bot = {}
        for fb in feedback_items:
            bot = fb.get('bot_id', 'unknown')
            if bot not in by_bot:
                by_bot[bot] = {'positive': 0, 'negative': 0}
            if str(fb.get('value')) == '1':
                by_bot[bot]['positive'] += 1
            else:
                by_bot[bot]['negative'] += 1

        return {
            "date": date_str,
            "today_count": total,
            "yesterday_count": yesterday_count,
            "positive": positive,
            "negative": negative,
            "satisfaction_rate": round(satisfaction, 1),
            "by_bot": by_bot,
            "negative_comments": [
                fb.get('comment', '')
                for fb in feedback_items
                if str(fb.get('value')) == '0' and fb.get('comment')
            ][:5]
        }

    except Exception as e:
        print(f"Feedback fetch error: {e}")
        return {"error": str(e), "total": 0}


def get_session_summary(client) -> Dict[str, Any]:
    """
    Get session/usage summary.

    Note: Sessions are typically stored in PostgreSQL via Chainlit.
    This provides an estimate based on feedback activity.
    """
    # Estimate based on feedback (rough proxy for sessions)
    feedback = get_feedback_summary(client)

    # Assume ~10 messages per feedback interaction
    estimated_messages = feedback.get('today_count', 0) * 10

    return {
        "estimated_interactions": feedback.get('today_count', 0),
        "estimated_messages": estimated_messages,
        "active_bots": list(feedback.get('by_bot', {}).keys())
    }


def generate_html_report(
    opportunities: Dict,
    feedback: Dict,
    sessions: Dict,
    date_str: str
) -> str:
    """Generate HTML email report."""

    # Color coding
    opp_change = opportunities.get('change', 0)
    opp_color = "#22c55e" if opp_change > 0 else "#ef4444" if opp_change < 0 else "#6b7280"

    sat_rate = feedback.get('satisfaction_rate', 0)
    sat_color = "#22c55e" if sat_rate >= 80 else "#eab308" if sat_rate >= 60 else "#ef4444"

    # Bot breakdown table
    bot_rows = ""
    for bot, data in feedback.get('by_bot', {}).items():
        total = data['positive'] + data['negative']
        rate = (data['positive'] / total * 100) if total > 0 else 0
        bot_rows += f"""
        <tr>
            <td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">{bot}</td>
            <td style="padding: 8px; border-bottom: 1px solid #e5e7eb; text-align: center;">{data['positive']}</td>
            <td style="padding: 8px; border-bottom: 1px solid #e5e7eb; text-align: center;">{data['negative']}</td>
            <td style="padding: 8px; border-bottom: 1px solid #e5e7eb; text-align: center;">{rate:.0f}%</td>
        </tr>
        """

    # Negative comments
    comments_html = ""
    for comment in feedback.get('negative_comments', []):
        if comment:
            comments_html += f'<li style="margin-bottom: 8px; color: #374151;">{comment}</li>'

    if not comments_html:
        comments_html = '<li style="color: #6b7280;">No negative comments today</li>'

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f9fafb;">

    <div style="background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); color: white; padding: 24px; border-radius: 12px 12px 0 0;">
        <h1 style="margin: 0; font-size: 24px;">Mindrian Daily Summary</h1>
        <p style="margin: 8px 0 0 0; opacity: 0.9;">{date_str}</p>
    </div>

    <div style="background: white; padding: 24px; border-radius: 0 0 12px 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">

        <!-- Key Metrics -->
        <div style="display: flex; gap: 16px; margin-bottom: 24px;">
            <div style="flex: 1; background: #f3f4f6; padding: 16px; border-radius: 8px; text-align: center;">
                <div style="font-size: 32px; font-weight: bold; color: #6366f1;">{opportunities.get('today_count', 0)}</div>
                <div style="font-size: 12px; color: #6b7280; margin-top: 4px;">Opportunities Today</div>
                <div style="font-size: 14px; color: {opp_color}; margin-top: 4px;">
                    {'+' if opp_change > 0 else ''}{opp_change} vs yesterday
                </div>
            </div>
            <div style="flex: 1; background: #f3f4f6; padding: 16px; border-radius: 8px; text-align: center;">
                <div style="font-size: 32px; font-weight: bold; color: {sat_color};">{sat_rate}%</div>
                <div style="font-size: 12px; color: #6b7280; margin-top: 4px;">Satisfaction Rate</div>
                <div style="font-size: 14px; color: #6b7280; margin-top: 4px;">
                    {feedback.get('today_count', 0)} total ratings
                </div>
            </div>
        </div>

        <!-- Bank of Opportunities -->
        <div style="margin-bottom: 24px;">
            <h2 style="font-size: 18px; color: #111827; margin: 0 0 12px 0; padding-bottom: 8px; border-bottom: 2px solid #e5e7eb;">
                Bank of Opportunities
            </h2>
            <table style="width: 100%; font-size: 14px;">
                <tr>
                    <td style="padding: 8px 0; color: #6b7280;">Total Accumulated</td>
                    <td style="padding: 8px 0; text-align: right; font-weight: bold; color: #111827;">
                        {opportunities.get('total_count', 0)}
                    </td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: #6b7280;">Added Today</td>
                    <td style="padding: 8px 0; text-align: right; font-weight: bold; color: #22c55e;">
                        +{opportunities.get('today_count', 0)}
                    </td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: #6b7280;">Added Yesterday</td>
                    <td style="padding: 8px 0; text-align: right; color: #6b7280;">
                        {opportunities.get('yesterday_count', 0)}
                    </td>
                </tr>
            </table>
        </div>

        <!-- User Engagement -->
        <div style="margin-bottom: 24px;">
            <h2 style="font-size: 18px; color: #111827; margin: 0 0 12px 0; padding-bottom: 8px; border-bottom: 2px solid #e5e7eb;">
                User Engagement
            </h2>
            <table style="width: 100%; font-size: 14px; border-collapse: collapse;">
                <tr style="background: #f3f4f6;">
                    <th style="padding: 8px; text-align: left; font-weight: 600;">Bot</th>
                    <th style="padding: 8px; text-align: center; font-weight: 600;">Positive</th>
                    <th style="padding: 8px; text-align: center; font-weight: 600;">Negative</th>
                    <th style="padding: 8px; text-align: center; font-weight: 600;">Rate</th>
                </tr>
                {bot_rows if bot_rows else '<tr><td colspan="4" style="padding: 8px; color: #6b7280; text-align: center;">No feedback yet today</td></tr>'}
            </table>
        </div>

        <!-- Activity Estimates -->
        <div style="margin-bottom: 24px;">
            <h2 style="font-size: 18px; color: #111827; margin: 0 0 12px 0; padding-bottom: 8px; border-bottom: 2px solid #e5e7eb;">
                Activity Summary
            </h2>
            <div style="display: flex; gap: 12px;">
                <div style="flex: 1; background: #fef3c7; padding: 12px; border-radius: 8px; text-align: center;">
                    <div style="font-size: 24px; font-weight: bold; color: #d97706;">{sessions.get('estimated_interactions', 0)}</div>
                    <div style="font-size: 11px; color: #92400e;">Interactions</div>
                </div>
                <div style="flex: 1; background: #dbeafe; padding: 12px; border-radius: 8px; text-align: center;">
                    <div style="font-size: 24px; font-weight: bold; color: #2563eb;">{sessions.get('estimated_messages', 0)}</div>
                    <div style="font-size: 11px; color: #1e40af;">Est. Messages</div>
                </div>
                <div style="flex: 1; background: #dcfce7; padding: 12px; border-radius: 8px; text-align: center;">
                    <div style="font-size: 24px; font-weight: bold; color: #16a34a;">{len(sessions.get('active_bots', []))}</div>
                    <div style="font-size: 11px; color: #166534;">Active Bots</div>
                </div>
            </div>
        </div>

        <!-- Negative Feedback -->
        {'<div style="margin-bottom: 24px;"><h2 style="font-size: 18px; color: #111827; margin: 0 0 12px 0; padding-bottom: 8px; border-bottom: 2px solid #e5e7eb;">Negative Feedback Comments</h2><ul style="margin: 0; padding-left: 20px;">' + comments_html + '</ul></div>' if feedback.get('negative_comments') else ''}

        <!-- Footer -->
        <div style="margin-top: 24px; padding-top: 16px; border-top: 1px solid #e5e7eb; text-align: center; color: #6b7280; font-size: 12px;">
            <p style="margin: 0;">Generated by Mindrian AI Platform</p>
            <p style="margin: 4px 0 0 0;">{datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}</p>
        </div>

    </div>
</body>
</html>
"""
    return html


def generate_text_report(
    opportunities: Dict,
    feedback: Dict,
    sessions: Dict,
    date_str: str
) -> str:
    """Generate plain text version of report."""

    lines = [
        "=" * 50,
        f"MINDRIAN DAILY SUMMARY - {date_str}",
        "=" * 50,
        "",
        "BANK OF OPPORTUNITIES",
        "-" * 30,
        f"Total Accumulated: {opportunities.get('total_count', 0)}",
        f"Added Today: +{opportunities.get('today_count', 0)}",
        f"Yesterday: {opportunities.get('yesterday_count', 0)}",
        f"Change: {'+' if opportunities.get('change', 0) > 0 else ''}{opportunities.get('change', 0)}",
        "",
        "USER ENGAGEMENT",
        "-" * 30,
        f"Total Feedback: {feedback.get('today_count', 0)}",
        f"Positive: {feedback.get('positive', 0)}",
        f"Negative: {feedback.get('negative', 0)}",
        f"Satisfaction Rate: {feedback.get('satisfaction_rate', 0)}%",
        "",
        "By Bot:",
    ]

    for bot, data in feedback.get('by_bot', {}).items():
        total = data['positive'] + data['negative']
        rate = (data['positive'] / total * 100) if total > 0 else 0
        lines.append(f"  - {bot}: {data['positive']}+ / {data['negative']}- ({rate:.0f}%)")

    if feedback.get('negative_comments'):
        lines.extend([
            "",
            "NEGATIVE FEEDBACK COMMENTS",
            "-" * 30,
        ])
        for comment in feedback.get('negative_comments', []):
            lines.append(f"  - {comment}")

    lines.extend([
        "",
        "ACTIVITY SUMMARY",
        "-" * 30,
        f"Estimated Interactions: {sessions.get('estimated_interactions', 0)}",
        f"Estimated Messages: {sessions.get('estimated_messages', 0)}",
        f"Active Bots: {', '.join(sessions.get('active_bots', [])) or 'None'}",
        "",
        "=" * 50,
        f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
    ])

    return "\n".join(lines)


def send_daily_summary(
    recipient: str = DEFAULT_RECIPIENT,
    date_str: str = None
) -> bool:
    """
    Compile and send daily summary email.

    Args:
        recipient: Email address to send to
        date_str: Date to report on (defaults to today)

    Returns:
        True if sent successfully
    """
    import sys
    sys.path.insert(0, str(project_root / "utils"))
    from email_sender import send_email, is_email_configured

    if not is_email_configured():
        print("Email not configured. Set SMTP_USER/SMTP_PASSWORD or SENDGRID_API_KEY")
        return False

    if not date_str:
        date_str = datetime.utcnow().strftime("%Y-%m-%d")

    print(f"Generating daily summary for {date_str}...")

    # Get Supabase client
    client = get_supabase_client()

    # Collect data
    opportunities = get_opportunities_summary(client, date_str)
    feedback = get_feedback_summary(client, date_str)
    sessions = get_session_summary(client)

    print(f"  - Opportunities: {opportunities.get('today_count', 0)} today, {opportunities.get('total_count', 0)} total")
    print(f"  - Feedback: {feedback.get('today_count', 0)} ratings, {feedback.get('satisfaction_rate', 0)}% satisfaction")

    # Generate reports
    html_report = generate_html_report(opportunities, feedback, sessions, date_str)
    text_report = generate_text_report(opportunities, feedback, sessions, date_str)

    # Send email
    subject = f"Mindrian Daily Summary - {date_str}"

    success = send_email(
        to_email=recipient,
        subject=subject,
        body_html=html_report,
        body_text=text_report
    )

    if success:
        print(f"Daily summary sent to {recipient}")
    else:
        print(f"Failed to send daily summary to {recipient}")

    return success


def main():
    """Main entry point for command-line usage."""
    import argparse

    parser = argparse.ArgumentParser(description='Send Mindrian daily summary email')
    parser.add_argument(
        '--recipient', '-r',
        default=DEFAULT_RECIPIENT,
        help=f'Email recipient (default: {DEFAULT_RECIPIENT})'
    )
    parser.add_argument(
        '--date', '-d',
        default=None,
        help='Date to report on (YYYY-MM-DD, default: today)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Generate report but do not send email'
    )

    args = parser.parse_args()

    if args.dry_run:
        print("DRY RUN - generating report without sending...")
        client = get_supabase_client()
        date_str = args.date or datetime.utcnow().strftime("%Y-%m-%d")

        opportunities = get_opportunities_summary(client, date_str)
        feedback = get_feedback_summary(client, date_str)
        sessions = get_session_summary(client)

        print("\n" + generate_text_report(opportunities, feedback, sessions, date_str))
        return

    success = send_daily_summary(
        recipient=args.recipient,
        date_str=args.date
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
