"""
Oracle Tools — LangChain Tools for Prediction Market Operations
===============================================================
@tool decorated functions for Oracle agent composition.

Tools:
- create_prediction_market: Structure a market from fuzzy input
- get_research_brief: Gather intelligence for a market
- place_prediction: Submit a prediction with reasoning
- resolve_market: Resolve and score a market
- get_user_calibration: Get user's prediction accuracy
- find_similar_markets: Find comparable past markets

Integration:
- Works with LangGraph Oracle pipeline
- Supabase persistence
- Neo4j knowledge graph enrichment
"""

import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

# LangChain
from langchain_core.tools import tool

# Supabase
try:
    from supabase import create_client, Client
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
    supabase: Optional[Client] = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None
except ImportError:
    supabase = None

# Local imports
from .text2cypher import (
    query_knowledge_graph,
    find_frameworks_for_problem,
    find_reverse_salients,
    store_market_in_neo4j,
    store_market_outcome_in_neo4j,
)


# =============================================================================
# MARKET CREATION TOOLS
# =============================================================================

@tool
def create_prediction_market(
    raw_idea: str,
    timeframe_days: int = 90,
    category: str = "custom"
) -> str:
    """
    Create a structured prediction market from a fuzzy idea.

    This tool:
    1. Structures the idea into a measurable question
    2. Defines resolution criteria
    3. Generates a challenge question with base rates
    4. Stores the market in Supabase and Neo4j

    Args:
        raw_idea: The fuzzy idea or question to turn into a market
        timeframe_days: Default timeframe for resolution (default 90 days)
        category: Market category - forecast_program, validate_idea, emerging_trend, or custom

    Returns:
        Formatted market details with ID
    """
    # Import the pipeline function
    import asyncio
    from intelligence.pipelines.oracle_pipeline import run_oracle_formulation

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    result = loop.run_until_complete(run_oracle_formulation(raw_idea, "tool_session"))

    if not result.get("success"):
        return f"Failed to create market: {result.get('error', 'Unknown error')}"

    market = result.get("market", {})
    market_id = result.get("market_id")

    # Store in Supabase
    if supabase and market:
        try:
            closes_at = (datetime.now() + timedelta(days=timeframe_days)).isoformat()

            supabase.table("oracle_markets").insert({
                "id": market_id,
                "question": market.get("question"),
                "description": raw_idea,
                "resolution_criteria": market.get("resolution_criteria"),
                "category": market.get("category", category),
                "challenge_question": market.get("challenge"),
                "closes_at": closes_at,
                "status": "draft",
                "raw_input": raw_idea
            }).execute()
        except Exception as e:
            print(f"Supabase market storage error: {e}")

    # Store in Neo4j
    if market:
        store_market_in_neo4j(market)

    # Format response
    response = result.get("response", "")
    if not response:
        response = f"""## 🔮 Market Created

**MARKET:** {market.get('question', 'N/A')}

**Market ID:** `{market_id}`
**Category:** `{market.get('category', category)}`
**Closes:** {timeframe_days} days from now

**Challenge:** {market.get('challenge', 'N/A')}

*Use `get_research_brief("{market_id}")` to gather intelligence before predicting.*"""

    return response


@tool
def get_open_markets(category: str = None, limit: int = 10) -> str:
    """
    Get currently open prediction markets.

    Args:
        category: Filter by category (optional)
        limit: Maximum number of markets to return

    Returns:
        List of open markets with key details
    """
    if not supabase:
        return "Supabase not configured. Cannot retrieve markets."

    try:
        query = supabase.table("oracle_markets").select(
            "id, question, category, closes_at, prediction_count, avg_prediction"
        ).eq("status", "open")

        if category:
            query = query.eq("category", category)

        result = query.order("closes_at", desc=False).limit(limit).execute()

        if not result.data:
            return "No open markets found."

        response = "## 📊 Open Prediction Markets\n\n"
        for market in result.data:
            closes = market.get("closes_at", "Unknown")[:10] if market.get("closes_at") else "Unknown"
            count = market.get("prediction_count", 0)
            avg = market.get("avg_prediction")
            avg_str = f"{avg*100:.0f}%" if avg else "No predictions yet"

            response += f"""### {market.get('question', 'Unknown')}
- **ID:** `{market.get('id')}`
- **Category:** {market.get('category', 'custom')}
- **Closes:** {closes}
- **Predictions:** {count} ({avg_str} average)

---
"""

        return response

    except Exception as e:
        return f"Error retrieving markets: {str(e)}"


# =============================================================================
# RESEARCH TOOLS
# =============================================================================

@tool
def get_research_brief(market_id: str) -> str:
    """
    Get the research brief for a prediction market.

    The brief includes:
    - Base rates and comparable cases
    - Success factors and failure modes
    - Knowledge graph context
    - Semantic surprises (cross-domain connections)

    Args:
        market_id: The market ID to get research for

    Returns:
        Formatted research brief
    """
    if not supabase:
        return "Supabase not configured."

    try:
        # Get market
        market_result = supabase.table("oracle_markets").select("*").eq("id", market_id).single().execute()

        if not market_result.data:
            return f"Market {market_id} not found."

        market = market_result.data
        brief = market.get("market_brief")

        if brief:
            # Return stored brief
            return format_research_brief(market.get("question"), brief)

        # Generate brief if not stored
        import asyncio
        from intelligence.pipelines.oracle_pipeline import run_oracle_formulation

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        result = loop.run_until_complete(
            run_oracle_formulation(market.get("question"), "brief_session")
        )

        if result.get("research_brief"):
            # Store for future use
            try:
                supabase.table("oracle_markets").update({
                    "market_brief": result.get("research_brief")
                }).eq("id", market_id).execute()
            except Exception:
                pass

            return format_research_brief(market.get("question"), result.get("research_brief"))

        return "Could not generate research brief."

    except Exception as e:
        return f"Error getting research brief: {str(e)}"


def format_research_brief(question: str, brief: Dict[str, Any]) -> str:
    """Format a research brief for display."""
    response = f"## 📋 Research Brief\n\n**Market:** {question}\n\n"

    response += "### Base Rates & Comparables\n"
    for case in brief.get("base_rates", [])[:3]:
        pct = f" ({case.get('percentage', 0)*100:.0f}%)" if case.get("percentage") else ""
        response += f"- **{case.get('name', 'Case')}**: {case.get('outcome', 'Unknown')}{pct}\n"

    response += "\n### ✅ Success Factors\n"
    for factor in brief.get("success_factors", [])[:4]:
        response += f"- {factor}\n"

    response += "\n### ⚠️ Failure Modes\n"
    for mode in brief.get("failure_modes", [])[:4]:
        response += f"- {mode}\n"

    if brief.get("neo4j_insights"):
        response += "\n### 🔗 Knowledge Graph Context\n"
        for insight in brief.get("neo4j_insights", [])[:3]:
            response += f"- {insight}\n"

    if brief.get("hsi_surprises"):
        response += "\n### 🧠 Semantic Surprises\n"
        for surprise in brief.get("hsi_surprises", [])[:3]:
            response += f"- {surprise}\n"

    response += "\n### ❓ Key Uncertainties\n"
    for unc in brief.get("key_uncertainties", [])[:3]:
        response += f"- {unc}\n"

    return response


@tool
def get_hsi_surprises(market_question: str) -> str:
    """
    Get HSI (Hierarchical Semantic Integration) surprise connections for a market.

    These are unexpected cross-domain connections that could inform predictions.

    Args:
        market_question: The market question to analyze

    Returns:
        List of semantic surprise connections
    """
    import asyncio
    from intelligence.pipelines.oracle_pipeline import generate_hsi_surprises

    # Build minimal state
    state = {
        "market": {"question": market_question},
        "neo4j_context": []
    }

    # Get Neo4j context first
    try:
        from tools.graphrag_lite import get_concepts_for_query
        concepts = get_concepts_for_query(market_question, limit=5)
        state["neo4j_context"] = [
            f"Concept: {c.get('name', '')} — {c.get('description', '')[:100]}"
            for c in (concepts or [])
        ]
    except Exception:
        pass

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    result = loop.run_until_complete(generate_hsi_surprises(state))

    surprises = result.get("hsi_surprises", [])

    if not surprises:
        return "No semantic surprises found for this market."

    response = "## 🧠 Semantic Surprises (HSI)\n\n"
    response += "*Unexpected cross-domain connections that could inform your prediction:*\n\n"
    for surprise in surprises:
        response += f"{surprise}\n\n"

    return response


# =============================================================================
# PREDICTION TOOLS
# =============================================================================

@tool
def place_prediction(
    market_id: str,
    probability: float,
    reasoning: str,
    key_assumption: str = None
) -> str:
    """
    Place a prediction on a market with mandatory reasoning.

    Args:
        market_id: The market to predict on
        probability: Your probability estimate (0.0 to 1.0)
        reasoning: WHY you predict this (required, minimum 10 characters)
        key_assumption: The key assumption behind your prediction (optional)

    Returns:
        Confirmation with prediction details
    """
    if not supabase:
        return "Supabase not configured. Cannot place prediction."

    # Validate probability
    if probability < 0 or probability > 1:
        return "Probability must be between 0.0 and 1.0"

    # Validate reasoning
    if not reasoning or len(reasoning) < 10:
        return "Reasoning must be at least 10 characters. Explain WHY you predict this."

    try:
        # Check market exists and is open
        market_result = supabase.table("oracle_markets").select("id, question, status").eq("id", market_id).single().execute()

        if not market_result.data:
            return f"Market {market_id} not found."

        if market_result.data.get("status") != "open":
            return f"Market is not open for predictions (status: {market_result.data.get('status')})"

        # Determine confidence level
        if probability < 0.2 or probability > 0.8:
            confidence = "high"
        elif probability < 0.35 or probability > 0.65:
            confidence = "medium"
        else:
            confidence = "low"

        # Store prediction (upsert)
        # Note: In production, user_id would come from auth
        user_id = "anonymous_user"  # Placeholder

        supabase.table("oracle_predictions").upsert({
            "market_id": market_id,
            "user_id": user_id,
            "prediction_value": probability,
            "confidence_reasoning": reasoning,
            "key_assumption": key_assumption,
            "confidence_level": confidence,
            "updated_at": datetime.now().isoformat()
        }, on_conflict="market_id,user_id").execute()

        return f"""## 🎯 Prediction Placed

**Market:** {market_result.data.get('question', 'Unknown')}
**Your Prediction:** {probability*100:.0f}%
**Confidence Level:** {confidence.capitalize()}

**Your Reasoning:**
{reasoning}

{f"**Key Assumption:** {key_assumption}" if key_assumption else ""}

---
*Your prediction has been recorded. You can update it until the market closes.*
*Remember: Good calibration (70% predictions happen 70% of the time) beats overconfidence.*"""

    except Exception as e:
        return f"Error placing prediction: {str(e)}"


@tool
def get_market_predictions(market_id: str) -> str:
    """
    Get all predictions for a market (anonymized reasoning).

    Args:
        market_id: The market to get predictions for

    Returns:
        Summary of predictions with reasoning themes
    """
    if not supabase:
        return "Supabase not configured."

    try:
        # Get market
        market_result = supabase.table("oracle_markets").select(
            "question, avg_prediction, prediction_count"
        ).eq("id", market_id).single().execute()

        if not market_result.data:
            return f"Market {market_id} not found."

        market = market_result.data

        # Get predictions
        pred_result = supabase.table("oracle_predictions").select(
            "prediction_value, confidence_reasoning, confidence_level"
        ).eq("market_id", market_id).execute()

        predictions = pred_result.data or []

        if not predictions:
            return f"No predictions yet for: {market.get('question')}"

        # Calculate statistics
        avg = market.get("avg_prediction", 0.5)
        count = len(predictions)

        # Separate optimists/skeptics
        optimists = [p for p in predictions if p.get("prediction_value", 0.5) > 0.5]
        skeptics = [p for p in predictions if p.get("prediction_value", 0.5) <= 0.5]

        response = f"""## 📊 Market Predictions

**Question:** {market.get('question')}
**Total Predictions:** {count}
**Average:** {avg*100:.0f}%

### Distribution
- **Optimists (>50%):** {len(optimists)} predictions
- **Skeptics (≤50%):** {len(skeptics)} predictions

### Sample Reasoning

**Optimist Themes:**
"""
        for p in optimists[:3]:
            response += f"- *{p.get('prediction_value', 0)*100:.0f}%*: {p.get('confidence_reasoning', '')[:150]}...\n"

        response += "\n**Skeptic Themes:**\n"
        for p in skeptics[:3]:
            response += f"- *{p.get('prediction_value', 0)*100:.0f}%*: {p.get('confidence_reasoning', '')[:150]}...\n"

        return response

    except Exception as e:
        return f"Error getting predictions: {str(e)}"


# =============================================================================
# RESOLUTION TOOLS
# =============================================================================

@tool
def resolve_market(
    market_id: str,
    outcome: str,
    evidence: str,
    actual_value: float = None
) -> str:
    """
    Resolve a market and calculate Brier scores.

    Args:
        market_id: The market to resolve
        outcome: Resolution outcome - "yes", "no", "partial", or "ambiguous"
        evidence: Description of what happened and how it was verified
        actual_value: Exact value if partial (0.0-1.0), otherwise auto-set from outcome

    Returns:
        Resolution summary with scoring
    """
    if not supabase:
        return "Supabase not configured."

    # Map outcome to actual value if not provided
    outcome_map = {"yes": 1.0, "no": 0.0, "partial": 0.5, "ambiguous": 0.5}
    if actual_value is None:
        actual_value = outcome_map.get(outcome.lower(), 0.5)

    try:
        # Get market and predictions
        market_result = supabase.table("oracle_markets").select("*").eq("id", market_id).single().execute()

        if not market_result.data:
            return f"Market {market_id} not found."

        market = market_result.data

        pred_result = supabase.table("oracle_predictions").select("*").eq("market_id", market_id).execute()
        predictions = pred_result.data or []

        if not predictions:
            return f"No predictions to score for this market."

        # Calculate Brier scores
        import asyncio
        from intelligence.pipelines.oracle_pipeline import run_oracle_resolution

        resolution_data = {
            "outcome": outcome.lower(),
            "actual_value": actual_value,
            "evidence": evidence,
            "resolved_at": datetime.now().isoformat()
        }

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        result = loop.run_until_complete(run_oracle_resolution(
            market_id=market_id,
            market=market,
            predictions=[{
                "user_id": p.get("user_id"),
                "probability": p.get("prediction_value"),
                "reasoning": p.get("confidence_reasoning")
            } for p in predictions],
            resolution=resolution_data,
            session_id="resolution_session"
        ))

        brier_scores = result.get("brier_scores", [])
        retrospective = result.get("retrospective", {})

        # Update database
        # Update market
        supabase.table("oracle_markets").update({
            "status": "resolved",
            "resolution_outcome": resolution_data,
            "resolves_at": datetime.now().isoformat()
        }).eq("id", market_id).execute()

        # Update prediction scores
        for score in brier_scores:
            supabase.table("oracle_predictions").update({
                "accuracy_brier": score.get("brier_score")
            }).eq("market_id", market_id).eq("user_id", score.get("user_id")).execute()

        # Store in Neo4j
        store_market_outcome_in_neo4j(market_id, resolution_data, retrospective)

        # Store retrospective
        if retrospective:
            supabase.table("oracle_retrospectives").insert({
                "market_id": market_id,
                "outcome": outcome,
                "crowd_accuracy": retrospective.get("crowd_accuracy"),
                "optimist_themes": retrospective.get("optimist_themes"),
                "skeptic_themes": retrospective.get("skeptic_themes"),
                "crux_disagreement": retrospective.get("crux_disagreement"),
                "crux_correct_side": retrospective.get("crux_correct_side"),
                "lesson_learned": retrospective.get("lesson_learned"),
                "pattern_extracted": retrospective.get("pattern_extracted"),
                "synced_to_neo4j": True
            }).execute()

        # Format response
        avg_brier = sum(s.get("brier_score", 0.5) for s in brier_scores) / len(brier_scores) if brier_scores else 0.5

        response = f"""## ✅ Market Resolved

**Question:** {market.get('question')}
**Outcome:** {outcome.upper()} (actual: {actual_value*100:.0f}%)

**Evidence:**
{evidence}

### 📊 Scoring Summary
- **Predictions Scored:** {len(brier_scores)}
- **Average Brier Score:** {avg_brier:.4f} (lower is better)

### 🏆 Top Predictions
"""
        sorted_scores = sorted(brier_scores, key=lambda x: x.get("brier_score", 1))[:5]
        for i, score in enumerate(sorted_scores, 1):
            response += f"{i}. **{score.get('prediction_value', 0)*100:.0f}%** → Brier: {score.get('brier_score', 0):.4f} ({score.get('calibration_note', '')})\n"

        if retrospective:
            response += f"""
### 🔬 Retrospective Analysis
**Crux Disagreement:** {retrospective.get('crux_disagreement', 'N/A')}
**Correct Side:** {retrospective.get('crux_correct_side', 'N/A').capitalize()}
**Lesson:** {retrospective.get('lesson_learned', 'N/A')}
"""

        return response

    except Exception as e:
        return f"Error resolving market: {str(e)}"


# =============================================================================
# USER SCORING TOOLS
# =============================================================================

@tool
def get_user_calibration(user_id: str = "anonymous_user") -> str:
    """
    Get a user's prediction calibration and accuracy statistics.

    Args:
        user_id: The user to get stats for (default: anonymous_user)

    Returns:
        Calibration statistics and level
    """
    if not supabase:
        return "Supabase not configured."

    try:
        result = supabase.table("oracle_scores").select("*").eq("user_id", user_id).single().execute()

        if not result.data:
            return f"No prediction history found for user {user_id}."

        scores = result.data

        response = f"""## 🎯 Prediction Calibration

**User Level:** {scores.get('analyst_level', 'observer').capitalize()}
**Total Predictions:** {scores.get('total_predictions', 0)}
**Resolved:** {scores.get('resolved_predictions', 0)}

### Accuracy Metrics
- **Average Brier Score:** {scores.get('avg_brier_score', 0):.4f}
  *(Lower is better. 0 = perfect, 0.25 = random guessing)*
- **Best Score:** {scores.get('best_brier_score', 0):.4f}
- **Worst Score:** {scores.get('worst_brier_score', 0):.4f}

### Achievements
- **Crux Calls:** {scores.get('crux_calls', 0)} *(correct when minority)*
- **Current Streak:** {scores.get('current_streak', 0)}
- **Best Streak:** {scores.get('best_streak', 0)}
- **Insight Points:** {scores.get('insight_points', 0)}

### Badges
{', '.join(scores.get('badges', [])) or 'None yet'}

---
*Improve your calibration by predicting probabilities that match how often things actually happen.*
"""
        return response

    except Exception as e:
        return f"Error getting calibration: {str(e)}"


@tool
def get_leaderboard(limit: int = 10) -> str:
    """
    Get the Oracle prediction accuracy leaderboard.

    Args:
        limit: Number of top users to show

    Returns:
        Leaderboard ranked by Brier score (lower is better)
    """
    if not supabase:
        return "Supabase not configured."

    try:
        result = supabase.table("oracle_scores").select(
            "user_id, analyst_level, avg_brier_score, resolved_predictions, crux_calls"
        ).gte("resolved_predictions", 5).order("avg_brier_score", desc=False).limit(limit).execute()

        if not result.data:
            return "Not enough users with 5+ resolved predictions for leaderboard."

        response = "## 🏆 Oracle Leaderboard\n\n"
        response += "| Rank | User | Level | Brier Score | Predictions | Crux Calls |\n"
        response += "|------|------|-------|-------------|-------------|------------|\n"

        for i, user in enumerate(result.data, 1):
            brier = user.get("avg_brier_score", 0)
            response += f"| {i} | {user.get('user_id', 'Anonymous')[:15]} | {user.get('analyst_level', '-')} | {brier:.4f} | {user.get('resolved_predictions', 0)} | {user.get('crux_calls', 0)} |\n"

        response += "\n*Ranked by Brier score (lower = better calibration)*"

        return response

    except Exception as e:
        return f"Error getting leaderboard: {str(e)}"


# =============================================================================
# EXPORTS
# =============================================================================

ALL_ORACLE_TOOLS = [
    create_prediction_market,
    get_open_markets,
    get_research_brief,
    get_hsi_surprises,
    place_prediction,
    get_market_predictions,
    resolve_market,
    get_user_calibration,
    get_leaderboard,
]

__all__ = [
    # Market tools
    "create_prediction_market",
    "get_open_markets",
    # Research tools
    "get_research_brief",
    "get_hsi_surprises",
    # Prediction tools
    "place_prediction",
    "get_market_predictions",
    # Resolution tools
    "resolve_market",
    # Scoring tools
    "get_user_calibration",
    "get_leaderboard",
    # Collections
    "ALL_ORACLE_TOOLS",
]
