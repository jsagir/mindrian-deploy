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


def get_opportunities_summary(client, date_str: str = None, last_24h: bool = False) -> Dict[str, Any]:
    """
    Get opportunity bank summary from Supabase.

    Returns counts, types breakdown, and recent opportunities WITH CONTENT.

    Args:
        client: Supabase client
        date_str: Specific date to query (YYYY-MM-DD)
        last_24h: If True, get data from last 24 hours (today + yesterday)
    """
    if not client:
        return {"error": "No Supabase client", "total": 0}

    if not date_str:
        date_str = datetime.utcnow().strftime("%Y-%m-%d")

    yesterday_str = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")

    try:
        # Separate counts for today and yesterday
        today_opps = []
        yesterday_opps = []

        # Get today's opportunities with content
        try:
            today_files = client.storage.from_(SUPABASE_BUCKET).list(f"opportunities/{date_str}")
            for f in today_files:
                if f.get('name', '').endswith('.json'):
                    opp_data = {"date": date_str, "file": f.get('name'), "created": f.get('created_at', '')}
                    # Read full content
                    try:
                        content = client.storage.from_(SUPABASE_BUCKET).download(
                            f"opportunities/{date_str}/{f['name']}"
                        )
                        opp_data["content"] = json.loads(content.decode('utf-8'))
                    except Exception:
                        opp_data["content"] = None
                    today_opps.append(opp_data)
        except Exception:
            pass

        # Get yesterday's opportunities with content
        try:
            yesterday_files = client.storage.from_(SUPABASE_BUCKET).list(f"opportunities/{yesterday_str}")
            for f in yesterday_files:
                if f.get('name', '').endswith('.json'):
                    opp_data = {"date": yesterday_str, "file": f.get('name'), "created": f.get('created_at', '')}
                    # Read full content
                    try:
                        content = client.storage.from_(SUPABASE_BUCKET).download(
                            f"opportunities/{yesterday_str}/{f['name']}"
                        )
                        opp_data["content"] = json.loads(content.decode('utf-8'))
                    except Exception:
                        opp_data["content"] = None
                    yesterday_opps.append(opp_data)
        except Exception:
            pass

        # Combine for period if last_24h
        if last_24h:
            period_opps = today_opps + yesterday_opps
        else:
            period_opps = today_opps

        # Try to get total count (list all date folders)
        total_count = 0
        try:
            date_folders = client.storage.from_(SUPABASE_BUCKET).list("opportunities")
            for folder in date_folders:
                if folder.get('name') and not folder.get('name').endswith('.json'):
                    folder_files = client.storage.from_(SUPABASE_BUCKET).list(f"opportunities/{folder['name']}")
                    total_count += len([f for f in folder_files if f.get('name', '').endswith('.json')])
        except Exception:
            total_count = len(period_opps)

        period_label = "last 24h" if last_24h else "today"
        return {
            "date": date_str,
            "yesterday_date": yesterday_str,
            "period": period_label,
            "period_count": len(period_opps),
            "today_count": len(today_opps),
            "yesterday_count": len(yesterday_opps),
            "total_count": total_count,
            "change": len(today_opps) - len(yesterday_opps),
            "today_opportunities": today_opps,
            "yesterday_opportunities": yesterday_opps,
            "recent": period_opps[:10]
        }

    except Exception as e:
        print(f"Opportunities fetch error: {e}")
        return {"error": str(e), "total": 0}


def get_feedback_summary(client, date_str: str = None, last_24h: bool = False) -> Dict[str, Any]:
    """
    Get user engagement/feedback summary from Supabase.

    Args:
        client: Supabase client
        date_str: Specific date to query (YYYY-MM-DD)
        last_24h: If True, get data from last 24 hours (today + yesterday)
    """
    if not client:
        return {"error": "No Supabase client", "total": 0}

    if not date_str:
        date_str = datetime.utcnow().strftime("%Y-%m-%d")

    try:
        feedback_items = []
        positive = 0
        negative = 0

        # Dates to query
        dates_to_query = [date_str]
        if last_24h:
            yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
            dates_to_query = [date_str, yesterday]

        # Get feedback for target date(s)
        for query_date in dates_to_query:
            try:
                date_files = client.storage.from_(SUPABASE_BUCKET).list(f"feedback/{query_date}")
                for f in date_files:
                    if f.get('name', '').endswith('.json'):
                        try:
                            content = client.storage.from_(SUPABASE_BUCKET).download(
                                f"feedback/{query_date}/{f['name']}"
                            )
                            data = json.loads(content.decode('utf-8'))
                            data['_query_date'] = query_date
                            feedback_items.append(data)
                            if str(data.get('value')) == '1':
                                positive += 1
                            else:
                                negative += 1
                        except Exception:
                            pass
            except Exception:
                pass

        # Get comparison period
        compare_date = (datetime.utcnow() - timedelta(days=2 if last_24h else 1)).strftime("%Y-%m-%d")
        compare_count = 0
        try:
            compare_files = client.storage.from_(SUPABASE_BUCKET).list(f"feedback/{compare_date}")
            compare_count = len([f for f in compare_files if f.get('name', '').endswith('.json')])
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

        period_label = "last 24h" if last_24h else "today"
        return {
            "date": date_str,
            "period": period_label,
            "today_count": total,
            "period_count": total,
            "yesterday_count": compare_count,
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


def get_session_summary(client, last_24h: bool = False) -> Dict[str, Any]:
    """
    Get session/usage summary.

    Note: Sessions are typically stored in PostgreSQL via Chainlit.
    This provides an estimate based on feedback activity.
    """
    # Estimate based on feedback (rough proxy for sessions)
    feedback = get_feedback_summary(client, last_24h=last_24h)

    # Assume ~10 messages per feedback interaction
    estimated_messages = feedback.get('today_count', 0) * 10

    return {
        "estimated_interactions": feedback.get('today_count', 0),
        "estimated_messages": estimated_messages,
        "active_bots": list(feedback.get('by_bot', {}).keys())
    }


def build_opportunities_html(opportunities_list: List[Dict], label: str = "Today") -> str:
    """Build HTML for a list of opportunities with their content."""
    if not opportunities_list:
        return f'<p style="color: #6b7280; font-style: italic;">No opportunities discovered {label.lower()}</p>'

    html_parts = []
    for i, opp in enumerate(opportunities_list, 1):
        content = opp.get('content') or {}
        title = content.get('title', 'Untitled Opportunity')
        description = content.get('description', 'No description available')
        opp_type = content.get('opportunity_type', 'unknown').replace('_', ' ').title()
        domain = content.get('domain', '')
        confidence = content.get('confidence_score', 0)
        confidence_pct = f"{confidence * 100:.0f}%" if confidence else "N/A"

        # Truncate description if too long
        if len(description) > 200:
            description = description[:197] + "..."

        # Type badge color
        type_colors = {
            'problem_worth_solving': '#6366f1',
            'unmet_need': '#ec4899',
            'market_gap': '#f59e0b',
            'technology_opportunity': '#10b981',
            'process_improvement': '#3b82f6',
            'emerging_trend': '#8b5cf6',
            'validated_insight': '#22c55e'
        }
        type_color = type_colors.get(content.get('opportunity_type', ''), '#6b7280')

        html_parts.append(f'''
        <div style="background: #f9fafb; border-left: 4px solid {type_color}; padding: 12px; margin-bottom: 12px; border-radius: 0 8px 8px 0;">
            <div style="font-weight: 600; color: #111827; margin-bottom: 4px;">{i}. {title}</div>
            <div style="font-size: 13px; color: #4b5563; margin-bottom: 8px;">{description}</div>
            <div style="display: flex; gap: 12px; flex-wrap: wrap; font-size: 11px;">
                <span style="background: {type_color}; color: white; padding: 2px 8px; border-radius: 4px;">{opp_type}</span>
                {f'<span style="color: #6b7280;">📍 {domain}</span>' if domain else ''}
                <span style="color: #6b7280;">🎯 {confidence_pct} confidence</span>
            </div>
        </div>
        ''')

    return ''.join(html_parts)


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

    # Build opportunities content sections
    today_opps_html = build_opportunities_html(opportunities.get('today_opportunities', []), "Today")
    yesterday_opps_html = build_opportunities_html(opportunities.get('yesterday_opportunities', []), "Yesterday")

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

        <!-- Today's Opportunities Details -->
        <div style="margin-bottom: 24px;">
            <h2 style="font-size: 18px; color: #111827; margin: 0 0 12px 0; padding-bottom: 8px; border-bottom: 2px solid #e5e7eb;">
                🆕 Today's Opportunities
            </h2>
            {today_opps_html}
        </div>

        <!-- Yesterday's Opportunities Details (if any) -->
        {'<div style="margin-bottom: 24px;"><h2 style="font-size: 18px; color: #111827; margin: 0 0 12px 0; padding-bottom: 8px; border-bottom: 2px solid #e5e7eb;">📋 Yesterday Opportunities</h2>' + yesterday_opps_html + '</div>' if opportunities.get('yesterday_opportunities') else ''}

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
    ]

    # Add today's opportunities details
    today_opps = opportunities.get('today_opportunities', [])
    if today_opps:
        lines.extend([
            "TODAY'S OPPORTUNITIES",
            "-" * 30,
        ])
        for i, opp in enumerate(today_opps, 1):
            content = opp.get('content') or {}
            title = content.get('title', 'Untitled')
            description = content.get('description', '')[:150]
            opp_type = content.get('opportunity_type', 'unknown').replace('_', ' ').title()
            domain = content.get('domain', '')
            confidence = content.get('confidence_score', 0)
            lines.append(f"  {i}. {title}")
            lines.append(f"     Type: {opp_type} | Domain: {domain or 'N/A'} | Confidence: {confidence*100:.0f}%")
            if description:
                lines.append(f"     {description}...")
            lines.append("")
    else:
        lines.extend([
            "TODAY'S OPPORTUNITIES",
            "-" * 30,
            "  No opportunities discovered today",
            "",
        ])

    # Add yesterday's opportunities details
    yesterday_opps = opportunities.get('yesterday_opportunities', [])
    if yesterday_opps:
        lines.extend([
            "YESTERDAY'S OPPORTUNITIES",
            "-" * 30,
        ])
        for i, opp in enumerate(yesterday_opps, 1):
            content = opp.get('content') or {}
            title = content.get('title', 'Untitled')
            opp_type = content.get('opportunity_type', 'unknown').replace('_', ' ').title()
            lines.append(f"  {i}. {title} ({opp_type})")
        lines.append("")

    lines.extend([
        "USER ENGAGEMENT",
        "-" * 30,
        f"Total Feedback: {feedback.get('today_count', 0)}",
        f"Positive: {feedback.get('positive', 0)}",
        f"Negative: {feedback.get('negative', 0)}",
        f"Satisfaction Rate: {feedback.get('satisfaction_rate', 0)}%",
        "",
        "By Bot:",
    ])

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
    date_str: str = None,
    last_24h: bool = False
) -> bool:
    """
    Compile and send daily summary email.

    Args:
        recipient: Email address to send to
        date_str: Date to report on (defaults to today)
        last_24h: Include last 24 hours of data (today + yesterday)

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

    period_label = "Last 24 Hours" if last_24h else date_str
    print(f"Generating summary for {period_label}...")

    # Get Supabase client
    client = get_supabase_client()

    # Collect data
    opportunities = get_opportunities_summary(client, date_str, last_24h=last_24h)
    feedback = get_feedback_summary(client, date_str, last_24h=last_24h)
    sessions = get_session_summary(client, last_24h=last_24h)

    print(f"  - Opportunities: {opportunities.get('period_count', 0)} in period, {opportunities.get('total_count', 0)} total")
    print(f"  - Feedback: {feedback.get('period_count', 0)} ratings, {feedback.get('satisfaction_rate', 0)}% satisfaction")

    # Generate reports
    report_title = f"Last 24 Hours ({date_str})" if last_24h else date_str
    html_report = generate_html_report(opportunities, feedback, sessions, report_title)
    text_report = generate_text_report(opportunities, feedback, sessions, report_title)

    # Send email
    subject = f"Mindrian Summary - {period_label}"

    success = send_email(
        to_email=recipient,
        subject=subject,
        body_html=html_report,
        body_text=text_report
    )

    if success:
        print(f"Summary sent to {recipient}")
    else:
        print(f"Failed to send summary to {recipient}")

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
        '--last-24h', '-24',
        action='store_true',
        help='Include data from last 24 hours (today + yesterday)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Generate report but do not send email'
    )

    args = parser.parse_args()

    last_24h = getattr(args, 'last_24h', False)
    date_str = args.date or datetime.utcnow().strftime("%Y-%m-%d")
    period_label = "Last 24 Hours" if last_24h else date_str

    if args.dry_run:
        print(f"DRY RUN - generating report for {period_label}...")
        client = get_supabase_client()

        opportunities = get_opportunities_summary(client, date_str, last_24h=last_24h)
        feedback = get_feedback_summary(client, date_str, last_24h=last_24h)
        sessions = get_session_summary(client, last_24h=last_24h)

        report_title = f"Last 24 Hours ({date_str})" if last_24h else date_str
        print("\n" + generate_text_report(opportunities, feedback, sessions, report_title))
        return

    success = send_daily_summary(
        recipient=args.recipient,
        date_str=args.date,
        last_24h=last_24h
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
