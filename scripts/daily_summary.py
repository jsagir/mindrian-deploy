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


def log_error(msg: str):
    """Print error message to stderr for proper subprocess error capture."""
    print(msg, file=sys.stderr)

# Load environment
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "mindrian-files")

# LightRAG configuration
LIGHTRAG_URL = os.getenv("LIGHTRAG_URL", "https://mondrian-ts.onrender.com")
LIGHTRAG_USERNAME = os.getenv("LIGHTRAG_USERNAME", "jsagir")
LIGHTRAG_PASSWORD = os.getenv("LIGHTRAG_PASSWORD")

# Neo4j configuration (PWS methodology consultant)
NEO4J_URI = os.getenv("NEO4J_URI", "")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")

# Default recipient
DEFAULT_RECIPIENT = "jsagir@gmail.com"

# LightRAG session cache
_lightrag_token = None


def get_lightrag_session():
    """Get authenticated LightRAG session."""
    global _lightrag_token
    import requests

    if not LIGHTRAG_PASSWORD:
        return None

    if _lightrag_token is None:
        try:
            resp = requests.post(
                f"{LIGHTRAG_URL}/login",
                data={"username": LIGHTRAG_USERNAME, "password": LIGHTRAG_PASSWORD},
                timeout=30
            )
            if resp.status_code == 200:
                _lightrag_token = resp.json().get("access_token")
            else:
                log_error(f"LightRAG login failed: {resp.status_code}")
                return None
        except Exception as e:
            log_error(f"LightRAG login error: {e}")
            return None

    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {_lightrag_token}"})
    return session


def get_lightrag_opportunities() -> Dict[str, Any]:
    """
    Query LightRAG knowledge graph for all Bank of Opportunities.

    Returns organized opportunity data from the graph.
    """
    import requests

    session = get_lightrag_session()
    if not session:
        return {"error": "LightRAG not configured", "opportunities": []}

    try:
        # Hybrid query for all opportunities in the knowledge graph
        resp = session.post(
            f"{LIGHTRAG_URL}/query",
            json={
                "query": "List ALL opportunities in the Bank of Opportunities. Include their domain, value potential, problem statement, and any cross-domain connections or reverse salients identified.",
                "mode": "hybrid",
            },
            timeout=30
        )

        if resp.status_code == 200:
            result = resp.json()
            # The response text contains the LLM-synthesized answer from the graph
            response_text = ""
            if isinstance(result, dict):
                response_text = result.get("response", result.get("text", str(result)))
            elif isinstance(result, str):
                response_text = result

            return {
                "success": True,
                "response": response_text,
                "raw": result,
            }
        else:
            log_error(f"LightRAG query failed: {resp.status_code} - {resp.text[:200]}")
            return {"error": f"Query failed: {resp.status_code}", "opportunities": []}

    except Exception as e:
        log_error(f"LightRAG query error: {e}")
        return {"error": str(e), "opportunities": []}


def get_pws_methodology_context() -> str:
    """
    Query Neo4j for PWS methodology knowledge to use as consultant context.

    Returns structured methodology guidance for the Gemini review prompt.
    """
    if not NEO4J_URI or not NEO4J_PASSWORD:
        # Return hardcoded PWS essentials as fallback (sourced from Neo4j knowledge graph)
        return _get_fallback_pws_context()

    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

        methodology_parts = []

        with driver.session() as session:
            # 1. Get Opportunity Discovery steps
            result = session.run("""
                MATCH (n)-[r:HAS_STEP]->(m)
                WHERE n.name = 'Opportunity Discovery'
                RETURN m.name AS step, m.description AS desc
            """)
            steps = [{"step": r["step"], "desc": r["desc"]} for r in result]
            if steps:
                methodology_parts.append("## Opportunity Discovery Process")
                for s in steps:
                    methodology_parts.append(f"- **{s['step']}**: {s['desc']}")

            # 2. Get PWS Methodology core
            result = session.run("""
                MATCH (n)-[r]->(m)
                WHERE n.name = 'PWS Methodology' AND m.description IS NOT NULL
                RETURN type(r) AS rel, m.name AS name, m.description AS desc
            """)
            pws_rels = [{"rel": r["rel"], "name": r["name"], "desc": r["desc"]} for r in result]
            if pws_rels:
                methodology_parts.append("\n## PWS Core Principles")
                for p in pws_rels:
                    methodology_parts.append(f"- **{p['name']}** ({p['rel']}): {p['desc']}")

            # 3. Get available frameworks
            result = session.run("""
                MATCH (n)
                WHERE n.name IN [
                    'Trending to the Absurd', 'Jobs to Be Done',
                    'Ackoff DIKW Pyramid', 'S-Curve Analysis',
                    'Beautiful Question', 'Scenario Analysis Framework',
                    'Reverse Salient Analysis'
                ] AND n.description IS NOT NULL
                RETURN DISTINCT n.name AS name, n.description AS desc
            """)
            frameworks = [{"name": r["name"], "desc": r["desc"]} for r in result]
            if frameworks:
                methodology_parts.append("\n## Available Analytical Frameworks")
                for f in frameworks:
                    methodology_parts.append(f"- **{f['name']}**: {f['desc']}")

            # 4. Get real Reverse Salient examples from the graph
            result = session.run("""
                MATCH (n:ReverseSalient)
                WHERE n.description IS NOT NULL AND size(n.description) > 20
                RETURN DISTINCT n.name AS name, n.description AS desc
                LIMIT 8
            """)
            rs_examples = [{"name": r["name"], "desc": r["desc"]} for r in result]
            if rs_examples:
                methodology_parts.append("\n## Known Reverse Salients in Graph")
                for rs in rs_examples:
                    methodology_parts.append(f"- **{rs['name']}**: {rs['desc']}")

        driver.close()

        if methodology_parts:
            return "\n".join(methodology_parts)
        else:
            return _get_fallback_pws_context()

    except Exception as e:
        log_error(f"Neo4j PWS context query failed: {e}")
        return _get_fallback_pws_context()


def _get_fallback_pws_context() -> str:
    """Hardcoded PWS methodology essentials (from Neo4j knowledge graph snapshot)."""
    return """## PWS Methodology (Problems Worth Solving)
Innovation begins with identifying problems worth solving, NOT solutions.
Problems must be well-defined before they can be addressed.
The most common failure mode is Premature Solutioning: jumping to solutions before properly defining problems.

## Opportunity Discovery Process
1. **Define Domain and Sub-Domain**: Identify primary domain, why it matters now, and expertise needed
2. **Identify Trends to Exploit**: Document relevant trends with time horizons and implications
3. **Identify Reverse Salients**: Find lagging elements that hold back system progress
4. **Craft Well-Defined Problem Statement**: Create clear, falsifiable problem statement
→ Leads to Problem Validation

## Analytical Lenses (Apply to Each Opportunity)
- **Reverse Salient Analysis**: What systemic bottleneck does this address? Components that have fallen behind and retard advancement
- **Trending to the Absurd**: What happens if the underlying trend continues? What breaks first?
- **Jobs to Be Done**: What progress is the customer/user trying to make? What job are they hiring a solution for?
- **S-Curve Position**: Is this early-stage (high risk, high reward), rapid growth, or plateau?
- **DIKW Level**: Is this grounded in Data, Information, Knowledge, or Wisdom?
- **Beautiful Question**: Can we frame this as WHY → WHAT IF → HOW?

## Problem Classification
- **Un-defined**: Vague, needs exploration (use Scenario Analysis)
- **Ill-defined**: Partially clear goals, hidden constraints (use TTA, Red Team)
- **Well-defined**: Clear problem, clear constraints (ready for solution design)

## Opportunity Recognition = Pattern Recognition
Entrepreneurs identify opportunities by perceiving connections between seemingly unrelated events or trends.
White Space Analysis reveals unoccupied territory. Opportunity Windows are timing-sensitive."""


def generate_lightrag_review(lightrag_data: Dict, opportunities: Dict) -> Dict[str, Any]:
    """
    Have Gemini review and organize all opportunities from LightRAG + Supabase,
    using Neo4j PWS methodology as the analytical framework.

    Returns structured review with themes, clusters, and strategic recommendations.
    """
    try:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return {"error": "No AI API key", "review": ""}

        from google import genai as genai_client
        client = genai_client.Client(api_key=api_key)

        # Get PWS methodology context from Neo4j (consultant brain)
        pws_context = get_pws_methodology_context()

        # Build context from LightRAG graph response
        lightrag_text = lightrag_data.get("response", "No LightRAG data available.")
        if len(lightrag_text) > 6000:
            lightrag_text = lightrag_text[:6000] + "..."

        # Build context from Supabase opportunities
        supabase_opps = []
        for opp in opportunities.get('today_opportunities', []) + opportunities.get('yesterday_opportunities', []):
            content = opp.get('content') or {}
            supabase_opps.append({
                "name": content.get('name', content.get('title', 'Untitled')),
                "problem": content.get('problem', '')[:150],
                "domain": content.get('domain', ''),
                "value": content.get('value_potential', 'medium'),
                "type": content.get('opportunity_type', ''),
                "job_to_be_done": content.get('job_to_be_done', '')[:100],
            })

        total_in_bank = opportunities.get('total_count', 0)

        review_prompt = f"""You are Lawrence, a PWS (Problems Worth Solving) methodology expert and strategic analyst.
You think like an innovation professor — never jumping to solutions, always asking "is this problem well-defined?"

## YOUR METHODOLOGY (from the PWS Knowledge Graph)
{pws_context}

---

## OPPORTUNITY DATA

### Knowledge Graph (LightRAG - All Accumulated Opportunities)
{lightrag_text}

### Recent Opportunities (Supabase - Last 24-48h)
{json.dumps(supabase_opps, indent=2) if supabase_opps else "No recent opportunities."}

### Bank Stats
- Total accumulated: {total_in_bank}
- Recent (24-48h): {len(supabase_opps)}

---

## YOUR TASK
Apply the PWS methodology to review the Bank of Opportunities. Think like Lawrence — probe, question, classify.

### 1. Opportunity Themes
Group into 3-5 themes. For each:
- **Theme Name** (count)
  - Key opportunities
  - The underlying REVERSE SALIENT driving this theme (what bottleneck makes these problems worth solving?)

### 2. Top 5 Opportunities (Ranked by PWS Criteria)
Rank using these lenses:
- Is the PROBLEM well-defined? (Un-defined / Ill-defined / Well-defined)
- What REVERSE SALIENT does it address?
- What JOB TO BE DONE does it serve?
- Where on the S-CURVE is the relevant technology/market?
- Value potential (LOW / MEDIUM / HIGH / TRANSFORMATIVE)

For each:
1. **Name** | Domain | Problem Definition Level | Value
   - Reverse salient it addresses
   - The job being done
   - Why it matters NOW (timing/S-curve position)

### 3. Cross-Domain Connections & Reverse Salients
- What reverse salients cut across multiple domains?
- What connections exist between seemingly unrelated opportunities? (Pattern Recognition)
- Any White Space gaps — domains with no opportunities yet?

### 4. Strategic Recommendations (Lawrence's Perspective)
- Which opportunities suffer from PREMATURE SOLUTIONING? (solution stated before problem is validated)
- What domains need deeper PROBLEM DISCOVERY?
- What TRENDS should we push to the absurd to find new opportunities?
- What BEAUTIFUL QUESTIONS emerge from the bank? (frame as WHY → WHAT IF → HOW)

Be concise, specific, and grounded in the methodology. No generic advice."""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=review_prompt,
        )

        review_text = response.text if response.text else "Review generation failed."

        return {
            "success": True,
            "review": review_text,
            "lightrag_available": bool(lightrag_data.get("success")),
            "neo4j_consulted": bool(NEO4J_URI and NEO4J_PASSWORD),
        }

    except Exception as e:
        log_error(f"LightRAG review generation failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "review": "",
        }


def get_supabase_client():
    """Get Supabase client."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        log_error("Supabase not configured")
        return None

    try:
        from supabase import create_client
        return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    except Exception as e:
        log_error(f"Supabase client error: {e}")
        return None


def get_opportunities_summary(client, date_str: str = None, last_24h: bool = False) -> Dict[str, Any]:
    """
    Get opportunity bank summary from Supabase.

    Returns counts, types breakdown, and recent opportunities WITH CONTENT.
    Tries Supabase table first (opportunity_bank), falls back to JSON storage.

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

    # Calculate date boundaries
    today_start = datetime.strptime(date_str, "%Y-%m-%d")
    today_end = today_start + timedelta(days=1)
    yesterday_start = today_start - timedelta(days=1)

    try:
        # Try Supabase table first (opportunity_bank)
        table_available = False
        today_opps = []
        yesterday_opps = []
        total_count = 0

        try:
            # Query today's opportunities from table
            result = client.table("opportunity_bank").select("*").gte(
                "created_at", today_start.isoformat()
            ).lt("created_at", today_end.isoformat()).order(
                "created_at", desc=True
            ).execute()

            if result.data:
                table_available = True
                for row in result.data:
                    # Convert table row to expected format with PWS fields
                    opp_data = {
                        "date": date_str,
                        "file": row.get("id"),
                        "created": row.get("created_at", ""),
                        "content": {
                            "title": row.get("name"),
                            "name": row.get("name"),
                            "description": row.get("description"),
                            "problem": row.get("problem"),
                            "value_potential": row.get("value_potential"),
                            "solution_direction": row.get("solution_direction"),
                            "job_to_be_done": row.get("job_to_be_done"),
                            "opportunity_type": row.get("opportunity_type"),
                            "domain": row.get("domain"),
                            "confidence_score": row.get("extraction_confidence", 0.5),
                            "extraction_confidence": row.get("extraction_confidence", 0.5),
                            "created_by": row.get("created_by"),
                            "created_by_type": row.get("created_by_type"),
                            "source_snippet": row.get("source_snippet"),
                            "source_bot": row.get("source_bot"),
                            "tags": row.get("tags", []),
                        }
                    }
                    today_opps.append(opp_data)

            # Query yesterday's opportunities from table
            result = client.table("opportunity_bank").select("*").gte(
                "created_at", yesterday_start.isoformat()
            ).lt("created_at", today_start.isoformat()).order(
                "created_at", desc=True
            ).execute()

            if result.data:
                for row in result.data:
                    opp_data = {
                        "date": yesterday_str,
                        "file": row.get("id"),
                        "created": row.get("created_at", ""),
                        "content": {
                            "title": row.get("name"),
                            "name": row.get("name"),
                            "description": row.get("description"),
                            "problem": row.get("problem"),
                            "value_potential": row.get("value_potential"),
                            "solution_direction": row.get("solution_direction"),
                            "job_to_be_done": row.get("job_to_be_done"),
                            "opportunity_type": row.get("opportunity_type"),
                            "domain": row.get("domain"),
                            "confidence_score": row.get("extraction_confidence", 0.5),
                            "extraction_confidence": row.get("extraction_confidence", 0.5),
                            "created_by": row.get("created_by"),
                            "created_by_type": row.get("created_by_type"),
                            "source_snippet": row.get("source_snippet"),
                            "source_bot": row.get("source_bot"),
                            "tags": row.get("tags", []),
                        }
                    }
                    yesterday_opps.append(opp_data)

            # Get total count from table
            count_result = client.table("opportunity_bank").select("id", count="exact").execute()
            if count_result.count is not None:
                total_count = count_result.count

        except Exception as table_error:
            if "does not exist" in str(table_error):
                table_available = False
            else:
                log_error(f"Table query error: {table_error}")

        # Fallback to JSON storage if table not available or empty
        if not table_available or (len(today_opps) == 0 and len(yesterday_opps) == 0):
            # Get today's opportunities from JSON files
            try:
                today_files = client.storage.from_(SUPABASE_BUCKET).list(f"opportunities/{date_str}")
                for f in today_files:
                    if f.get('name', '').endswith('.json'):
                        opp_data = {"date": date_str, "file": f.get('name'), "created": f.get('created_at', '')}
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

            # Get yesterday's opportunities from JSON files
            try:
                yesterday_files = client.storage.from_(SUPABASE_BUCKET).list(f"opportunities/{yesterday_str}")
                for f in yesterday_files:
                    if f.get('name', '').endswith('.json'):
                        opp_data = {"date": yesterday_str, "file": f.get('name'), "created": f.get('created_at', '')}
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

            # Count total from JSON folders
            if total_count == 0:
                try:
                    date_folders = client.storage.from_(SUPABASE_BUCKET).list("opportunities")
                    for folder in date_folders:
                        if folder.get('name') and not folder.get('name').endswith('.json'):
                            folder_files = client.storage.from_(SUPABASE_BUCKET).list(f"opportunities/{folder['name']}")
                            total_count += len([f for f in folder_files if f.get('name', '').endswith('.json')])
                except Exception:
                    total_count = len(today_opps) + len(yesterday_opps)

        # Combine for period if last_24h
        if last_24h:
            period_opps = today_opps + yesterday_opps
        else:
            period_opps = today_opps

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
            "recent": period_opps[:10],
            "source": "table" if table_available else "json"
        }

    except Exception as e:
        log_error(f"Opportunities fetch error: {e}")
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
        log_error(f"Feedback fetch error: {e}")
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


def generate_ai_insights(opportunities: Dict, feedback: Dict, sessions: Dict) -> Dict[str, Any]:
    """
    Generate AI-powered quality insights and operational recommendations.

    Uses Gemini to analyze the data and provide actionable insights.
    """
    try:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return {"error": "No AI API key", "insights": [], "recommendations": []}

        # Use new google-genai SDK (matches requirements.txt)
        from google import genai as genai_client
        client = genai_client.Client(api_key=api_key)

        # Build context for analysis
        today_opps = opportunities.get('today_opportunities', [])
        opp_summaries = []
        for opp in today_opps[:10]:
            content = opp.get('content') or {}
            opp_summaries.append({
                "title": content.get('name', content.get('title', 'Untitled')),
                "problem": content.get('problem', ''),
                "type": content.get('opportunity_type', 'unknown'),
                "value": content.get('value_potential', 'medium'),
                "confidence": content.get('extraction_confidence', 0.5),
            })

        negative_comments = feedback.get('negative_comments', [])
        satisfaction = feedback.get('satisfaction_rate', 0)
        by_bot = feedback.get('by_bot', {})

        analysis_prompt = f"""You are an AI operations analyst for Mindrian, a PWS (Problems Worth Solving) innovation platform.

Analyze this daily data and provide operational insights:

## TODAY'S OPPORTUNITIES ({len(today_opps)} discovered)
{json.dumps(opp_summaries, indent=2)}

## USER SATISFACTION
- Overall: {satisfaction}%
- By Bot: {json.dumps(by_bot, indent=2)}
- Negative Comments: {json.dumps(negative_comments, indent=2)}

## TASK
Provide EXACTLY this JSON structure (no markdown, just JSON):
{{
    "quality_score": <0-100 overall quality of opportunities discovered>,
    "key_insights": [
        "Insight 1 about patterns in opportunities",
        "Insight 2 about user engagement",
        "Insight 3 about platform health"
    ],
    "operational_recommendations": [
        "Specific action to improve X",
        "Specific action to address Y"
    ],
    "highlight_opportunity": "<title of most promising opportunity and why>",
    "concern_flag": "<any urgent concern to address or null>"
}}"""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=analysis_prompt,
        )

        # Parse JSON from response
        response_text = response.text.strip()
        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()

        insights_data = json.loads(response_text)
        return {
            "success": True,
            "quality_score": insights_data.get("quality_score", 50),
            "insights": insights_data.get("key_insights", []),
            "recommendations": insights_data.get("operational_recommendations", []),
            "highlight": insights_data.get("highlight_opportunity", ""),
            "concern": insights_data.get("concern_flag"),
        }

    except Exception as e:
        log_error(f"AI insights generation failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "quality_score": 0,
            "insights": [],
            "recommendations": [],
            "highlight": "",
            "concern": None,
        }


def build_opportunities_html(opportunities_list: List[Dict], label: str = "Today") -> str:
    """Build HTML for a list of opportunities with their content (PWS-compliant)."""
    if not opportunities_list:
        return f'<p style="color: #6b7280; font-style: italic;">No opportunities discovered {label.lower()}</p>'

    html_parts = []
    for i, opp in enumerate(opportunities_list, 1):
        content = opp.get('content') or {}

        # PWS fields (with backwards compat for title/name)
        title = content.get('name', content.get('title', 'Untitled Opportunity'))
        description = content.get('description', 'No description available')
        problem = content.get('problem', '')
        value_potential = content.get('value_potential', 'medium')
        solution_direction = content.get('solution_direction', '')
        job_to_be_done = content.get('job_to_be_done', '')
        opp_type = content.get('opportunity_type', 'unknown').replace('_', ' ').title()
        domain = content.get('domain', '')
        confidence = content.get('extraction_confidence', content.get('confidence_score', 0))
        confidence_pct = f"{confidence * 100:.0f}%" if confidence else "N/A"

        # Provenance
        created_by = content.get('created_by', '')
        created_by_type = content.get('created_by_type', '')
        source_snippet = content.get('source_snippet', '')
        source_bot = content.get('source_bot', '')

        # Truncate long fields
        if len(description) > 200:
            description = description[:197] + "..."
        if problem and len(problem) > 150:
            problem = problem[:147] + "..."
        if source_snippet and len(source_snippet) > 100:
            source_snippet = source_snippet[:97] + "..."

        # Type badge color
        type_colors = {
            'problem_worth_solving': '#6366f1',
            'unmet_need': '#ec4899',
            'market_gap': '#f59e0b',
            'technology_opportunity': '#10b981',
            'process_improvement': '#3b82f6',
            'emerging_trend': '#8b5cf6',
            'validated_insight': '#22c55e',
            'innovation': '#6366f1',
            'reverse_salient': '#dc2626',
            'strategic': '#0891b2'
        }
        type_color = type_colors.get(content.get('opportunity_type', ''), '#6b7280')

        # Value potential badge color
        value_colors = {
            'low': '#6b7280',
            'medium': '#eab308',
            'high': '#22c55e',
            'transformative': '#6366f1'
        }
        value_color = value_colors.get(value_potential, '#6b7280')

        # Build problem section if available
        problem_html = f'''
            <div style="font-size: 12px; color: #dc2626; margin-bottom: 6px; padding: 6px; background: #fef2f2; border-radius: 4px;">
                <strong>🔍 Problem:</strong> {problem}
            </div>
        ''' if problem else ''

        # Build source snippet if available
        snippet_html = f'''
            <div style="font-size: 11px; color: #6b7280; margin-top: 8px; padding: 6px; background: #f3f4f6; border-radius: 4px; font-style: italic;">
                "{source_snippet}"
            </div>
        ''' if source_snippet else ''

        # Build provenance line
        provenance_parts = []
        if created_by and created_by != 'system':
            provenance_parts.append(f'👤 {created_by}')
        if source_bot:
            provenance_parts.append(f'🤖 {source_bot}')
        provenance_html = f'<span style="color: #6b7280;">{" · ".join(provenance_parts)}</span>' if provenance_parts else ''

        html_parts.append(f'''
        <div style="background: #f9fafb; border-left: 4px solid {type_color}; padding: 12px; margin-bottom: 12px; border-radius: 0 8px 8px 0;">
            <div style="font-weight: 600; color: #111827; margin-bottom: 4px;">{i}. {title}</div>
            <div style="font-size: 13px; color: #4b5563; margin-bottom: 8px;">{description}</div>
            {problem_html}
            <div style="display: flex; gap: 8px; flex-wrap: wrap; font-size: 11px; margin-bottom: 6px;">
                <span style="background: {type_color}; color: white; padding: 2px 8px; border-radius: 4px;">{opp_type}</span>
                <span style="background: {value_color}; color: white; padding: 2px 8px; border-radius: 4px;">💎 {value_potential.title()}</span>
                {f'<span style="color: #6b7280;">📍 {domain}</span>' if domain else ''}
                <span style="color: #6b7280;">🎯 {confidence_pct}</span>
            </div>
            <div style="font-size: 11px;">
                {provenance_html}
            </div>
            {snippet_html}
        </div>
        ''')

    return ''.join(html_parts)


def generate_html_report(
    opportunities: Dict,
    feedback: Dict,
    sessions: Dict,
    date_str: str,
    ai_insights: Dict = None,
    lightrag_review: Dict = None
) -> str:
    """Generate HTML email report with AI-powered insights and LightRAG review."""
    ai_insights = ai_insights or {}
    lightrag_review = lightrag_review or {}

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

    # Build AI insights section
    ai_quality_score = ai_insights.get('quality_score', 0)
    ai_quality_color = "#22c55e" if ai_quality_score >= 70 else "#eab308" if ai_quality_score >= 40 else "#ef4444"

    ai_insights_html = ""
    if ai_insights.get('success') and (ai_insights.get('insights') or ai_insights.get('recommendations')):
        insights_list = "".join([f'<li style="margin-bottom: 8px; color: #374151;">{insight}</li>' for insight in ai_insights.get('insights', [])])
        recs_list = "".join([f'<li style="margin-bottom: 8px; color: #374151;">{rec}</li>' for rec in ai_insights.get('recommendations', [])])

        highlight = ai_insights.get('highlight', '')
        highlight_html = f'<div style="background: #ecfdf5; padding: 12px; border-radius: 8px; margin-bottom: 12px; border-left: 4px solid #22c55e;"><strong>Highlight:</strong> {highlight}</div>' if highlight else ''

        concern = ai_insights.get('concern')
        concern_html = f'<div style="background: #fef2f2; padding: 12px; border-radius: 8px; margin-bottom: 12px; border-left: 4px solid #ef4444;"><strong>Concern:</strong> {concern}</div>' if concern else ''

        ai_insights_html = f'''
        <div style="margin-bottom: 24px; background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); padding: 16px; border-radius: 8px;">
            <h2 style="font-size: 18px; color: #0369a1; margin: 0 0 12px 0; display: flex; align-items: center; gap: 8px;">
                AI Quality Insights
                <span style="background: {ai_quality_color}; color: white; padding: 4px 10px; border-radius: 12px; font-size: 14px;">{ai_quality_score}/100</span>
            </h2>
            {highlight_html}
            {concern_html}
            <div style="margin-bottom: 12px;">
                <strong style="color: #0369a1;">Key Insights:</strong>
                <ul style="margin: 8px 0 0 0; padding-left: 20px;">{insights_list or '<li style="color: #6b7280;">No insights available</li>'}</ul>
            </div>
            <div>
                <strong style="color: #0369a1;">Operational Recommendations:</strong>
                <ul style="margin: 8px 0 0 0; padding-left: 20px;">{recs_list or '<li style="color: #6b7280;">No recommendations</li>'}</ul>
            </div>
        </div>
        '''

    # Build LightRAG review section
    lightrag_review_html = ""
    if lightrag_review.get('success') and lightrag_review.get('review'):
        # Convert markdown to simple HTML (bold, headers, lists)
        import re
        review_text = lightrag_review['review']
        # Convert ### headers
        review_text = re.sub(r'^### (.+)$', r'<h3 style="font-size: 15px; color: #4338ca; margin: 16px 0 8px 0;">\1</h3>', review_text, flags=re.MULTILINE)
        # Convert **bold**
        review_text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', review_text)
        # Convert bullet points
        review_text = re.sub(r'^- (.+)$', r'<li style="margin-bottom: 4px; color: #374151;">\1</li>', review_text, flags=re.MULTILINE)
        # Convert numbered lists
        review_text = re.sub(r'^\d+\. (.+)$', r'<li style="margin-bottom: 6px; color: #374151;">\1</li>', review_text, flags=re.MULTILINE)
        # Wrap consecutive <li> in <ul>
        review_text = re.sub(r'((?:<li[^>]*>.*?</li>\n?)+)', r'<ul style="margin: 4px 0 12px 0; padding-left: 20px;">\1</ul>', review_text)
        # Convert remaining newlines to <br>
        review_text = review_text.replace('\n', '<br>')
        # Clean up double <br>
        review_text = re.sub(r'(<br>){3,}', '<br><br>', review_text)

        source_parts = []
        if lightrag_review.get('lightrag_available'):
            source_parts.append("LightRAG")
        if lightrag_review.get('neo4j_consulted'):
            source_parts.append("Neo4j PWS Methodology")
        source_parts.append("Supabase")
        source_label = " + ".join(source_parts)

        lightrag_review_html = f'''
        <div style="margin-bottom: 24px; background: linear-gradient(135deg, #faf5ff 0%, #f3e8ff 100%); padding: 16px; border-radius: 8px; border: 1px solid #e9d5ff;">
            <h2 style="font-size: 18px; color: #6b21a8; margin: 0 0 12px 0;">
                🤖 Lawrence's PWS Review — Bank of Opportunities
            </h2>
            <div style="font-size: 11px; color: #7c3aed; margin-bottom: 12px;">Methodology: PWS | Sources: {source_label}</div>
            <div style="font-size: 13px; line-height: 1.6; color: #374151;">
                {review_text}
            </div>
        </div>
        '''

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

        <!-- AI Quality Insights -->
        {ai_insights_html}

        <!-- LightRAG Opportunity Bank Review -->
        {lightrag_review_html}

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
    date_str: str,
    ai_insights: Dict = None,
    lightrag_review: Dict = None
) -> str:
    """Generate plain text version of report with AI insights and LightRAG review."""
    ai_insights = ai_insights or {}
    lightrag_review = lightrag_review or {}

    lines = [
        "=" * 50,
        f"MINDRIAN DAILY SUMMARY - {date_str}",
        "=" * 50,
        "",
    ]

    # Add AI insights section if available
    if ai_insights.get('success') and (ai_insights.get('insights') or ai_insights.get('recommendations')):
        lines.extend([
            "AI QUALITY INSIGHTS",
            "-" * 30,
            f"Quality Score: {ai_insights.get('quality_score', 0)}/100",
            "",
        ])

        if ai_insights.get('highlight'):
            lines.append(f"HIGHLIGHT: {ai_insights.get('highlight')}")
            lines.append("")

        if ai_insights.get('concern'):
            lines.append(f"CONCERN: {ai_insights.get('concern')}")
            lines.append("")

        if ai_insights.get('insights'):
            lines.append("Key Insights:")
            for insight in ai_insights.get('insights', []):
                lines.append(f"  - {insight}")
            lines.append("")

        if ai_insights.get('recommendations'):
            lines.append("Operational Recommendations:")
            for rec in ai_insights.get('recommendations', []):
                lines.append(f"  - {rec}")
            lines.append("")

    # Add LightRAG review section
    if lightrag_review.get('success') and lightrag_review.get('review'):
        source_label = "LightRAG + Supabase" if lightrag_review.get('lightrag_available') else "Supabase only"
        lines.extend([
            "LLM-ORGANIZED OPPORTUNITY BANK REVIEW",
            "-" * 30,
            f"Source: {source_label}",
            "",
            lightrag_review['review'],
            "",
        ])

    lines.extend([
        "BANK OF OPPORTUNITIES",
        "-" * 30,
        f"Total Accumulated: {opportunities.get('total_count', 0)}",
        f"Added Today: +{opportunities.get('today_count', 0)}",
        f"Yesterday: {opportunities.get('yesterday_count', 0)}",
        f"Change: {'+' if opportunities.get('change', 0) > 0 else ''}{opportunities.get('change', 0)}",
        "",
    ])

    # Add today's opportunities details (PWS-compliant)
    today_opps = opportunities.get('today_opportunities', [])
    if today_opps:
        lines.extend([
            "TODAY'S OPPORTUNITIES",
            "-" * 30,
        ])
        for i, opp in enumerate(today_opps, 1):
            content = opp.get('content') or {}
            title = content.get('name', content.get('title', 'Untitled'))
            description = content.get('description', '')[:150]
            problem = content.get('problem', '')[:100] if content.get('problem') else ''
            value_potential = content.get('value_potential', 'medium')
            opp_type = content.get('opportunity_type', 'unknown').replace('_', ' ').title()
            domain = content.get('domain', '')
            confidence = content.get('extraction_confidence', content.get('confidence_score', 0))
            created_by = content.get('created_by', '')
            source_snippet = content.get('source_snippet', '')[:80] if content.get('source_snippet') else ''

            lines.append(f"  {i}. {title}")
            lines.append(f"     Type: {opp_type} | Value: {value_potential.upper()} | Domain: {domain or 'N/A'} | Confidence: {confidence*100:.0f}%")
            if problem:
                lines.append(f"     Problem: {problem}...")
            if description:
                lines.append(f"     {description}...")
            if created_by and created_by != 'system':
                lines.append(f"     Created by: {created_by}")
            if source_snippet:
                lines.append(f"     Excerpt: \"{source_snippet}...\"")
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
        log_error("Email not configured. Set SMTP_USER/SMTP_PASSWORD or SENDGRID_API_KEY")
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

    # Fetch from LightRAG knowledge graph
    print("  - Querying LightRAG knowledge graph...")
    lightrag_data = get_lightrag_opportunities()
    if lightrag_data.get('success'):
        print("  - LightRAG data retrieved successfully")
    else:
        print(f"  - LightRAG skipped: {lightrag_data.get('error', 'Not available')}")

    # Generate LLM-organized review of full opportunity bank
    print("  - Generating LLM-organized opportunity review...")
    lightrag_review = generate_lightrag_review(lightrag_data, opportunities)
    if lightrag_review.get('success'):
        print("  - Opportunity bank review generated")
    else:
        print(f"  - Review skipped: {lightrag_review.get('error', 'Unknown error')}")

    # Generate AI insights
    print("  - Generating AI quality insights...")
    ai_insights = generate_ai_insights(opportunities, feedback, sessions)
    if ai_insights.get('success'):
        print(f"  - AI Quality Score: {ai_insights.get('quality_score', 'N/A')}/100")
    else:
        print(f"  - AI insights skipped: {ai_insights.get('error', 'Unknown error')}")

    # Generate reports
    report_title = f"Last 24 Hours ({date_str})" if last_24h else date_str
    html_report = generate_html_report(opportunities, feedback, sessions, report_title, ai_insights, lightrag_review)
    text_report = generate_text_report(opportunities, feedback, sessions, report_title, ai_insights, lightrag_review)

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
        log_error(f"Failed to send summary to {recipient}")

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

        print("Querying LightRAG knowledge graph...")
        lightrag_data = get_lightrag_opportunities()
        print("Generating LLM-organized opportunity review...")
        lightrag_review = generate_lightrag_review(lightrag_data, opportunities)

        print("Generating AI quality insights...")
        ai_insights = generate_ai_insights(opportunities, feedback, sessions)
        if ai_insights.get('success'):
            print(f"AI Quality Score: {ai_insights.get('quality_score', 'N/A')}/100")

        report_title = f"Last 24 Hours ({date_str})" if last_24h else date_str
        print("\n" + generate_text_report(opportunities, feedback, sessions, report_title, ai_insights, lightrag_review))
        return

    success = send_daily_summary(
        recipient=args.recipient,
        date_str=args.date,
        last_24h=last_24h
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
