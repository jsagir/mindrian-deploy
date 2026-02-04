"""
Daily Opportunity Digest Generator
===================================

Generates a comprehensive 12-part daily email digest of the Bank of Opportunities.

Sections:
1. Executive Summary - Key metrics at a glance
2. New Opportunities - Discovered in last 24h
3. High-Value Spotlight - Transformative/high value opportunities
4. Domain Breakdown - Opportunities by industry/domain
5. Validation Status - What's been validated vs pending
6. Framework Applications - Which PWS frameworks are being used
7. User Activity - Who's discovering what
8. Trend Analysis - Emerging patterns
9. Action Required - Opportunities needing attention
10. API Health Summary - System status
11. Weekly Comparison - Week-over-week trends
12. Recommended Focus - AI-suggested priorities

Usage:
    from utils.opportunity_digest import (
        generate_daily_digest,
        send_opportunity_digest,
    )

    # Generate and send
    await send_opportunity_digest(to_email="user@example.com")
"""

import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# =============================================================================
# DIGEST CONFIGURATION
# =============================================================================

DIGEST_SECTIONS = [
    "executive_summary",
    "new_opportunities",
    "high_value_spotlight",
    "domain_breakdown",
    "validation_status",
    "framework_applications",
    "user_activity",
    "trend_analysis",
    "action_required",
    "api_health_summary",
    "weekly_comparison",
    "recommended_focus",
]

# =============================================================================
# DATA FETCHERS
# =============================================================================

async def _fetch_opportunities_data(days: int = 1) -> Dict[str, Any]:
    """Fetch opportunity data from Supabase."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")

    if not url or not key:
        return {"error": "Supabase not configured", "opportunities": []}

    try:
        from supabase import create_client

        client = create_client(url, key)
        since = (datetime.utcnow() - timedelta(days=days)).isoformat()

        # Get recent opportunities
        recent = client.table("opportunity_bank")\
            .select("*")\
            .gte("created_at", since)\
            .order("created_at", desc=True)\
            .execute()

        # Get all opportunities for stats
        all_opps = client.table("opportunity_bank")\
            .select("*")\
            .order("created_at", desc=True)\
            .limit(500)\
            .execute()

        return {
            "recent": recent.data or [],
            "all": all_opps.data or [],
            "since": since
        }

    except Exception as e:
        return {"error": str(e), "opportunities": []}

async def _fetch_health_data() -> Dict[str, Any]:
    """Fetch API health data for summary."""
    try:
        from utils.api_health_monitor import get_health_dashboard
        return await get_health_dashboard(days=1)
    except Exception as e:
        return {"error": str(e)}

# =============================================================================
# SECTION GENERATORS
# =============================================================================

def _generate_executive_summary(data: Dict) -> str:
    """Section 1: Executive Summary"""
    recent = data.get("recent", [])
    all_opps = data.get("all", [])

    total = len(all_opps)
    new_today = len(recent)

    # Value breakdown
    high_value = sum(1 for o in all_opps if o.get("value_potential") in ["high", "transformative"])
    validated = sum(1 for o in all_opps if o.get("validation_status") == "validated")

    # Top domains
    domains = {}
    for o in all_opps:
        d = o.get("domain", "Uncategorized")
        domains[d] = domains.get(d, 0) + 1
    top_domains = sorted(domains.items(), key=lambda x: x[1], reverse=True)[:3]

    return f"""
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 24px; border-radius: 12px; color: white;">
    <h2 style="margin: 0 0 16px 0;">📊 Executive Summary</h2>
    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px;">
        <div style="text-align: center;">
            <div style="font-size: 32px; font-weight: bold;">{total}</div>
            <div style="opacity: 0.9;">Total Opportunities</div>
        </div>
        <div style="text-align: center;">
            <div style="font-size: 32px; font-weight: bold; color: #90EE90;">+{new_today}</div>
            <div style="opacity: 0.9;">New Today</div>
        </div>
        <div style="text-align: center;">
            <div style="font-size: 32px; font-weight: bold; color: #FFD700;">{high_value}</div>
            <div style="opacity: 0.9;">High Value</div>
        </div>
        <div style="text-align: center;">
            <div style="font-size: 32px; font-weight: bold; color: #87CEEB;">{validated}</div>
            <div style="opacity: 0.9;">Validated</div>
        </div>
    </div>
    <div style="margin-top: 16px; padding-top: 16px; border-top: 1px solid rgba(255,255,255,0.3);">
        <strong>Top Domains:</strong> {', '.join([f"{d[0]} ({d[1]})" for d in top_domains]) or "N/A"}
    </div>
</div>
"""

def _generate_new_opportunities(data: Dict) -> str:
    """Section 2: New Opportunities (last 24h)"""
    recent = data.get("recent", [])

    if not recent:
        return """
<div style="background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #28a745;">
    <h3 style="margin: 0 0 12px 0;">🆕 New Opportunities</h3>
    <p style="color: #666;">No new opportunities discovered in the last 24 hours.</p>
</div>
"""

    items_html = ""
    for opp in recent[:5]:
        value_color = {
            "transformative": "#9b59b6",
            "high": "#e74c3c",
            "medium": "#f39c12",
            "low": "#95a5a6"
        }.get(opp.get("value_potential", "medium"), "#95a5a6")

        items_html += f"""
<div style="background: white; padding: 12px; margin-bottom: 8px; border-radius: 6px; border-left: 4px solid {value_color};">
    <div style="font-weight: bold; color: #333;">{opp.get('name', 'Untitled')}</div>
    <div style="font-size: 13px; color: #666; margin: 4px 0;">{opp.get('description', '')[:150]}...</div>
    <div style="display: flex; gap: 12px; font-size: 12px; color: #888;">
        <span>📁 {opp.get('domain', 'General')}</span>
        <span>💎 {opp.get('value_potential', 'medium').title()}</span>
        <span>🤖 {opp.get('source_bot', 'system')}</span>
    </div>
</div>
"""

    return f"""
<div style="background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #28a745;">
    <h3 style="margin: 0 0 12px 0;">🆕 New Opportunities ({len(recent)} discovered)</h3>
    {items_html}
    {f'<div style="color: #666; font-size: 12px; margin-top: 8px;">+ {len(recent) - 5} more...</div>' if len(recent) > 5 else ''}
</div>
"""

def _generate_high_value_spotlight(data: Dict) -> str:
    """Section 3: High-Value Spotlight"""
    all_opps = data.get("all", [])

    high_value = [o for o in all_opps if o.get("value_potential") in ["high", "transformative"]]

    if not high_value:
        return """
<div style="background: #fff3cd; padding: 20px; border-radius: 8px;">
    <h3 style="margin: 0 0 12px 0;">💎 High-Value Spotlight</h3>
    <p>No high-value opportunities identified yet. Keep exploring!</p>
</div>
"""

    # Pick top 3 most recent high-value
    spotlight = high_value[:3]

    items_html = ""
    for opp in spotlight:
        is_transformative = opp.get("value_potential") == "transformative"
        badge = "🚀 TRANSFORMATIVE" if is_transformative else "⭐ HIGH VALUE"
        badge_color = "#9b59b6" if is_transformative else "#e74c3c"

        items_html += f"""
<div style="background: white; padding: 16px; margin-bottom: 12px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
        <span style="font-weight: bold; font-size: 16px;">{opp.get('name', 'Untitled')}</span>
        <span style="background: {badge_color}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 11px;">{badge}</span>
    </div>
    <p style="color: #555; margin: 8px 0;">{opp.get('description', '')[:200]}</p>
    <div style="background: #f8f9fa; padding: 8px; border-radius: 4px; font-size: 13px;">
        <strong>Problem:</strong> {opp.get('problem', 'Not specified')[:100]}
    </div>
</div>
"""

    return f"""
<div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 20px; border-radius: 8px; color: white;">
    <h3 style="margin: 0 0 16px 0;">💎 High-Value Spotlight</h3>
    <div style="background: rgba(255,255,255,0.95); border-radius: 8px; padding: 16px; color: #333;">
        {items_html}
    </div>
</div>
"""

def _generate_domain_breakdown(data: Dict) -> str:
    """Section 4: Domain Breakdown"""
    all_opps = data.get("all", [])

    domains = {}
    for o in all_opps:
        d = o.get("domain", "Uncategorized")
        if d not in domains:
            domains[d] = {"count": 0, "high_value": 0}
        domains[d]["count"] += 1
        if o.get("value_potential") in ["high", "transformative"]:
            domains[d]["high_value"] += 1

    sorted_domains = sorted(domains.items(), key=lambda x: x[1]["count"], reverse=True)

    total = len(all_opps) or 1

    bars_html = ""
    colors = ["#3498db", "#2ecc71", "#e74c3c", "#f39c12", "#9b59b6", "#1abc9c", "#34495e"]

    for i, (domain, stats) in enumerate(sorted_domains[:7]):
        pct = (stats["count"] / total) * 100
        color = colors[i % len(colors)]
        bars_html += f"""
<div style="margin-bottom: 8px;">
    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
        <span style="font-weight: 500;">{domain}</span>
        <span style="color: #666;">{stats['count']} ({stats['high_value']} high-value)</span>
    </div>
    <div style="background: #e9ecef; border-radius: 4px; height: 20px; overflow: hidden;">
        <div style="background: {color}; height: 100%; width: {pct}%; border-radius: 4px;"></div>
    </div>
</div>
"""

    return f"""
<div style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
    <h3 style="margin: 0 0 16px 0;">📁 Domain Breakdown</h3>
    {bars_html}
</div>
"""

def _generate_validation_status(data: Dict) -> str:
    """Section 5: Validation Status"""
    all_opps = data.get("all", [])

    statuses = {"validated": 0, "unvalidated": 0, "rejected": 0}
    for o in all_opps:
        status = o.get("validation_status", "unvalidated")
        if status in statuses:
            statuses[status] += 1
        else:
            statuses["unvalidated"] += 1

    total = sum(statuses.values()) or 1

    return f"""
<div style="background: #e8f4f8; padding: 20px; border-radius: 8px;">
    <h3 style="margin: 0 0 16px 0;">✅ Validation Status</h3>
    <div style="display: flex; gap: 16px; text-align: center;">
        <div style="flex: 1; background: #d4edda; padding: 16px; border-radius: 8px;">
            <div style="font-size: 28px; font-weight: bold; color: #155724;">{statuses['validated']}</div>
            <div style="color: #155724;">Validated</div>
            <div style="font-size: 12px; color: #666;">{round(statuses['validated']/total*100)}%</div>
        </div>
        <div style="flex: 1; background: #fff3cd; padding: 16px; border-radius: 8px;">
            <div style="font-size: 28px; font-weight: bold; color: #856404;">{statuses['unvalidated']}</div>
            <div style="color: #856404;">Pending</div>
            <div style="font-size: 12px; color: #666;">{round(statuses['unvalidated']/total*100)}%</div>
        </div>
        <div style="flex: 1; background: #f8d7da; padding: 16px; border-radius: 8px;">
            <div style="font-size: 28px; font-weight: bold; color: #721c24;">{statuses['rejected']}</div>
            <div style="color: #721c24;">Rejected</div>
            <div style="font-size: 12px; color: #666;">{round(statuses['rejected']/total*100)}%</div>
        </div>
    </div>
</div>
"""

def _generate_framework_applications(data: Dict) -> str:
    """Section 6: Framework Applications"""
    all_opps = data.get("all", [])

    frameworks = {}
    for o in all_opps:
        applied = o.get("frameworks_applied") or []
        if isinstance(applied, str):
            applied = [applied]
        for fw in applied:
            if fw:
                frameworks[fw] = frameworks.get(fw, 0) + 1

    # Also count by source_methodology
    for o in all_opps:
        method = o.get("source_methodology")
        if method:
            frameworks[method] = frameworks.get(method, 0) + 1

    sorted_fw = sorted(frameworks.items(), key=lambda x: x[1], reverse=True)[:6]

    if not sorted_fw:
        return """
<div style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
    <h3 style="margin: 0 0 12px 0;">🧩 Framework Applications</h3>
    <p style="color: #666;">No framework data available yet.</p>
</div>
"""

    items_html = ""
    for fw, count in sorted_fw:
        items_html += f"""
<div style="display: flex; justify-content: space-between; padding: 8px 12px; background: white; margin-bottom: 6px; border-radius: 4px;">
    <span style="font-weight: 500;">{fw}</span>
    <span style="background: #007bff; color: white; padding: 2px 8px; border-radius: 10px; font-size: 12px;">{count}</span>
</div>
"""

    return f"""
<div style="background: #e7f3ff; padding: 20px; border-radius: 8px;">
    <h3 style="margin: 0 0 16px 0;">🧩 Framework Applications</h3>
    {items_html}
</div>
"""

def _generate_user_activity(data: Dict) -> str:
    """Section 7: User Activity"""
    all_opps = data.get("all", [])

    users = {}
    for o in all_opps:
        user = o.get("created_by") or o.get("user_id") or "anonymous"
        if user not in users:
            users[user] = {"count": 0, "high_value": 0}
        users[user]["count"] += 1
        if o.get("value_potential") in ["high", "transformative"]:
            users[user]["high_value"] += 1

    sorted_users = sorted(users.items(), key=lambda x: x[1]["count"], reverse=True)[:5]

    if not sorted_users:
        return """
<div style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
    <h3 style="margin: 0 0 12px 0;">👥 User Activity</h3>
    <p style="color: #666;">No user activity data available.</p>
</div>
"""

    items_html = ""
    for user, stats in sorted_users:
        display_user = user[:30] + "..." if len(user) > 30 else user
        items_html += f"""
<div style="display: flex; justify-content: space-between; align-items: center; padding: 10px; background: white; margin-bottom: 6px; border-radius: 4px;">
    <span>👤 {display_user}</span>
    <div>
        <span style="margin-right: 12px;">{stats['count']} opportunities</span>
        <span style="color: #e74c3c;">💎 {stats['high_value']} high-value</span>
    </div>
</div>
"""

    return f"""
<div style="background: #f0f7ff; padding: 20px; border-radius: 8px;">
    <h3 style="margin: 0 0 16px 0;">👥 Top Contributors</h3>
    {items_html}
</div>
"""

def _generate_trend_analysis(data: Dict) -> str:
    """Section 8: Trend Analysis"""
    all_opps = data.get("all", [])

    # Analyze tags and keywords
    keywords = {}
    for o in all_opps:
        tags = o.get("tags") or []
        if isinstance(tags, str):
            tags = [tags]
        for tag in tags:
            if tag:
                keywords[tag.lower()] = keywords.get(tag.lower(), 0) + 1

        # Also extract from extracted_keywords
        ext_kw = o.get("extracted_keywords") or []
        if isinstance(ext_kw, str):
            ext_kw = [ext_kw]
        for kw in ext_kw:
            if kw:
                keywords[kw.lower()] = keywords.get(kw.lower(), 0) + 1

    top_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:10]

    if not top_keywords:
        return """
<div style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
    <h3 style="margin: 0 0 12px 0;">📈 Trend Analysis</h3>
    <p style="color: #666;">Not enough data for trend analysis yet.</p>
</div>
"""

    tags_html = " ".join([
        f'<span style="background: #17a2b8; color: white; padding: 4px 10px; border-radius: 12px; margin: 2px; display: inline-block; font-size: 13px;">{kw} ({count})</span>'
        for kw, count in top_keywords
    ])

    return f"""
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 8px; color: white;">
    <h3 style="margin: 0 0 16px 0;">📈 Emerging Themes</h3>
    <div style="background: rgba(255,255,255,0.95); padding: 16px; border-radius: 8px; color: #333;">
        {tags_html}
    </div>
</div>
"""

def _generate_action_required(data: Dict) -> str:
    """Section 9: Action Required"""
    all_opps = data.get("all", [])

    # Find opportunities needing attention
    needs_validation = [o for o in all_opps if o.get("validation_status") == "unvalidated" and o.get("value_potential") in ["high", "transformative"]]
    stale = [o for o in all_opps if o.get("status") == "draft"]

    action_items = []

    for o in needs_validation[:3]:
        action_items.append({
            "type": "validate",
            "name": o.get("name"),
            "reason": f"High-value opportunity needs validation",
            "icon": "🔍"
        })

    for o in stale[:2]:
        action_items.append({
            "type": "review",
            "name": o.get("name"),
            "reason": "Draft status - needs review",
            "icon": "📝"
        })

    if not action_items:
        return """
<div style="background: #d4edda; padding: 20px; border-radius: 8px;">
    <h3 style="margin: 0 0 12px 0;">✅ Action Required</h3>
    <p style="color: #155724;">All opportunities are up to date! No immediate action needed.</p>
</div>
"""

    items_html = ""
    for item in action_items:
        items_html += f"""
<div style="background: white; padding: 12px; margin-bottom: 8px; border-radius: 6px; border-left: 4px solid #ffc107;">
    <div style="font-weight: bold;">{item['icon']} {item['name']}</div>
    <div style="font-size: 13px; color: #666;">{item['reason']}</div>
</div>
"""

    return f"""
<div style="background: #fff3cd; padding: 20px; border-radius: 8px;">
    <h3 style="margin: 0 0 16px 0;">⚠️ Action Required ({len(action_items)} items)</h3>
    {items_html}
</div>
"""

def _generate_api_health_summary(health_data: Dict) -> str:
    """Section 10: API Health Summary"""
    if "error" in health_data:
        return f"""
<div style="background: #f8d7da; padding: 20px; border-radius: 8px;">
    <h3 style="margin: 0 0 12px 0;">🏥 API Health</h3>
    <p style="color: #721c24;">Could not fetch health data: {health_data['error']}</p>
</div>
"""

    by_api = health_data.get("by_api", {})

    if not by_api:
        return """
<div style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
    <h3 style="margin: 0 0 12px 0;">🏥 API Health</h3>
    <p style="color: #666;">No health check data available. Run startup health check to populate.</p>
</div>
"""

    items_html = ""
    for api, stats in by_api.items():
        uptime = stats.get("uptime_percent", 0)
        color = "#28a745" if uptime >= 99 else "#ffc107" if uptime >= 95 else "#dc3545"
        icon = "✅" if uptime >= 99 else "⚠️" if uptime >= 95 else "❌"

        items_html += f"""
<div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; background: white; margin-bottom: 6px; border-radius: 4px;">
    <span>{icon} {api}</span>
    <div>
        <span style="color: {color}; font-weight: bold;">{uptime}%</span>
        <span style="color: #666; margin-left: 8px;">({stats.get('avg_response_ms', 0)}ms avg)</span>
    </div>
</div>
"""

    return f"""
<div style="background: #e8f5e9; padding: 20px; border-radius: 8px;">
    <h3 style="margin: 0 0 16px 0;">🏥 API Health (24h)</h3>
    {items_html}
</div>
"""

def _generate_weekly_comparison(data: Dict) -> str:
    """Section 11: Weekly Comparison"""
    # This would need historical data - simplified version
    recent = data.get("recent", [])
    all_opps = data.get("all", [])

    today_count = len(recent)
    total = len(all_opps)

    # Estimate weekly average (simplified)
    avg_daily = total / 30 if total > 0 else 0

    trend = "📈 Up" if today_count > avg_daily else "📉 Down" if today_count < avg_daily else "➡️ Stable"

    return f"""
<div style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
    <h3 style="margin: 0 0 16px 0;">📊 Weekly Comparison</h3>
    <div style="display: flex; gap: 20px;">
        <div style="flex: 1; text-align: center; padding: 16px; background: white; border-radius: 8px;">
            <div style="font-size: 24px; font-weight: bold; color: #333;">{today_count}</div>
            <div style="color: #666;">Today</div>
        </div>
        <div style="flex: 1; text-align: center; padding: 16px; background: white; border-radius: 8px;">
            <div style="font-size: 24px; font-weight: bold; color: #333;">{round(avg_daily, 1)}</div>
            <div style="color: #666;">Daily Avg</div>
        </div>
        <div style="flex: 1; text-align: center; padding: 16px; background: white; border-radius: 8px;">
            <div style="font-size: 24px;">{trend}</div>
            <div style="color: #666;">Trend</div>
        </div>
    </div>
</div>
"""

def _generate_recommended_focus(data: Dict) -> str:
    """Section 12: AI Recommended Focus"""
    all_opps = data.get("all", [])

    # Find high-value unvalidated opportunities
    priorities = []

    high_value_unvalidated = [
        o for o in all_opps
        if o.get("value_potential") in ["high", "transformative"]
        and o.get("validation_status") != "validated"
    ]

    if high_value_unvalidated:
        top = high_value_unvalidated[0]
        priorities.append({
            "recommendation": f"Validate '{top.get('name')}'",
            "reason": "High-value opportunity awaiting validation",
            "priority": "HIGH"
        })

    # Domains with momentum
    domains = {}
    for o in data.get("recent", []):
        d = o.get("domain", "General")
        domains[d] = domains.get(d, 0) + 1

    if domains:
        top_domain = max(domains.items(), key=lambda x: x[1])
        priorities.append({
            "recommendation": f"Deep dive into {top_domain[0]}",
            "reason": f"{top_domain[1]} new opportunities discovered today",
            "priority": "MEDIUM"
        })

    if not priorities:
        priorities.append({
            "recommendation": "Start a new PWS exploration session",
            "reason": "Build momentum with more problem discovery",
            "priority": "MEDIUM"
        })

    items_html = ""
    for p in priorities[:3]:
        color = "#dc3545" if p["priority"] == "HIGH" else "#ffc107" if p["priority"] == "MEDIUM" else "#6c757d"
        items_html += f"""
<div style="background: white; padding: 16px; margin-bottom: 12px; border-radius: 8px; border-left: 4px solid {color};">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <span style="font-weight: bold; font-size: 15px;">🎯 {p['recommendation']}</span>
        <span style="background: {color}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px;">{p['priority']}</span>
    </div>
    <div style="color: #666; margin-top: 8px; font-size: 13px;">{p['reason']}</div>
</div>
"""

    return f"""
<div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); padding: 20px; border-radius: 8px; color: white;">
    <h3 style="margin: 0 0 16px 0;">🎯 Recommended Focus</h3>
    <div style="background: rgba(255,255,255,0.95); border-radius: 8px; padding: 16px; color: #333;">
        {items_html}
    </div>
</div>
"""

# =============================================================================
# MAIN DIGEST GENERATOR
# =============================================================================

async def generate_daily_digest() -> str:
    """
    Generate the full 12-part daily digest HTML.

    Returns:
        Complete HTML email body
    """
    # Fetch data
    opp_data = await _fetch_opportunities_data(days=1)
    health_data = await _fetch_health_data()

    # Generate sections
    sections = {
        "executive_summary": _generate_executive_summary(opp_data),
        "new_opportunities": _generate_new_opportunities(opp_data),
        "high_value_spotlight": _generate_high_value_spotlight(opp_data),
        "domain_breakdown": _generate_domain_breakdown(opp_data),
        "validation_status": _generate_validation_status(opp_data),
        "framework_applications": _generate_framework_applications(opp_data),
        "user_activity": _generate_user_activity(opp_data),
        "trend_analysis": _generate_trend_analysis(opp_data),
        "action_required": _generate_action_required(opp_data),
        "api_health_summary": _generate_api_health_summary(health_data),
        "weekly_comparison": _generate_weekly_comparison(opp_data),
        "recommended_focus": _generate_recommended_focus(opp_data),
    }

    # Compose email
    date_str = datetime.utcnow().strftime("%B %d, %Y")

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mindrian Daily Digest</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f4f4f4; margin: 0; padding: 20px;">
    <div style="max-width: 700px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">

        <!-- Header -->
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 32px; text-align: center; color: white;">
            <h1 style="margin: 0; font-size: 28px;">🏦 Bank of Opportunities</h1>
            <p style="margin: 8px 0 0 0; opacity: 0.9;">Daily Digest — {date_str}</p>
        </div>

        <!-- Content -->
        <div style="padding: 24px;">
            <!-- Section 1: Executive Summary -->
            {sections['executive_summary']}

            <div style="height: 24px;"></div>

            <!-- Section 2: New Opportunities -->
            {sections['new_opportunities']}

            <div style="height: 24px;"></div>

            <!-- Section 3: High-Value Spotlight -->
            {sections['high_value_spotlight']}

            <div style="height: 24px;"></div>

            <!-- Section 4: Domain Breakdown -->
            {sections['domain_breakdown']}

            <div style="height: 24px;"></div>

            <!-- Section 5: Validation Status -->
            {sections['validation_status']}

            <div style="height: 24px;"></div>

            <!-- Section 6: Framework Applications -->
            {sections['framework_applications']}

            <div style="height: 24px;"></div>

            <!-- Section 7: User Activity -->
            {sections['user_activity']}

            <div style="height: 24px;"></div>

            <!-- Section 8: Trend Analysis -->
            {sections['trend_analysis']}

            <div style="height: 24px;"></div>

            <!-- Section 9: Action Required -->
            {sections['action_required']}

            <div style="height: 24px;"></div>

            <!-- Section 10: API Health -->
            {sections['api_health_summary']}

            <div style="height: 24px;"></div>

            <!-- Section 11: Weekly Comparison -->
            {sections['weekly_comparison']}

            <div style="height: 24px;"></div>

            <!-- Section 12: Recommended Focus -->
            {sections['recommended_focus']}
        </div>

        <!-- Footer -->
        <div style="background: #f8f9fa; padding: 20px; text-align: center; color: #666; font-size: 12px;">
            <p style="margin: 0;">Generated by Mindrian AI — Problems Worth Solving</p>
            <p style="margin: 8px 0 0 0;">
                <a href="https://mindrian.onrender.com" style="color: #667eea;">Open Mindrian</a>
            </p>
        </div>
    </div>
</body>
</html>
"""

    return html

async def send_opportunity_digest(
    to_email: str,
    subject: str = None
) -> bool:
    """
    Generate and send the daily opportunity digest.

    Args:
        to_email: Recipient email address
        subject: Custom subject (optional)

    Returns:
        True if sent successfully
    """
    from utils.email_sender import send_email

    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    subject = subject or f"🏦 Mindrian Opportunity Digest — {date_str}"

    html_content = await generate_daily_digest()

    # Plain text version (simplified)
    text_content = f"""
Mindrian Daily Opportunity Digest — {date_str}

View the full HTML version in your email client for best experience.

Generated by Mindrian AI — Problems Worth Solving
https://mindrian.onrender.com
"""

    return send_email(
        to_email=to_email,
        subject=subject,
        body_html=html_content,
        body_text=text_content
    )

# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "generate_daily_digest",
    "send_opportunity_digest",
    "DIGEST_SECTIONS",
]
