"""
Oracle Pipeline — LangGraph StateGraph for Prediction Market Workflow
=====================================================================
A multi-stage pipeline that:
1. Formulates structured markets from fuzzy ideas
2. Gathers research briefs (Neo4j + FileSearch + Web + HSI)
3. Manages predictions with reasoning
4. Resolves and scores outcomes (Brier)
5. Performs retrospective analysis and knowledge graph updates

Architecture:
- TypedDict state management
- Parallel research execution (Neo4j, FileSearch, Tavily)
- Pydantic structured outputs for LLM responses
- Supabase persistence for markets/predictions/scores
"""

import os
import json
import asyncio
from typing import TypedDict, List, Dict, Any, Optional, Literal
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

# LangGraph
from langgraph.graph import StateGraph, END

# Google Gemini
from google import genai
from google.genai import types

# Initialize client
_client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))


# =============================================================================
# PYDANTIC SCHEMAS — Structured LLM Outputs
# =============================================================================

class ResolutionCriteria(BaseModel):
    """Structured resolution criteria for a market."""
    source: str = Field(description="Where the answer will come from")
    threshold: str = Field(description="What counts as YES/NO/PARTIAL")
    timeframe: str = Field(description="Specific date or duration")
    resolves_yes: str = Field(description="Condition for YES resolution")
    resolves_no: str = Field(description="Condition for NO resolution")
    resolves_partial: Optional[str] = Field(default=None, description="Condition for PARTIAL resolution")


class MarketFormulation(BaseModel):
    """Structured market formulation from LLM."""
    question: str = Field(description="The specific, measurable prediction question")
    resolution_criteria: ResolutionCriteria
    challenge: str = Field(description="Base rate challenge question")
    category: Literal["forecast_program", "validate_idea", "emerging_trend", "custom"]
    raw_input: str = Field(description="Original user input")
    confidence_notes: Optional[str] = Field(default=None, description="Notes about formulation confidence")


class ComparableCase(BaseModel):
    """A comparable case for research brief."""
    name: str
    outcome: str
    percentage: Optional[float] = None
    source: Optional[str] = None


class ResearchBrief(BaseModel):
    """Structured research brief."""
    market_question: str
    base_rates: List[ComparableCase] = Field(default_factory=list)
    success_factors: List[str] = Field(default_factory=list)
    failure_modes: List[str] = Field(default_factory=list)
    neo4j_context: List[str] = Field(default_factory=list)
    semantic_surprises: List[str] = Field(default_factory=list)
    key_uncertainties: List[str] = Field(default_factory=list)
    web_sources: List[Dict[str, str]] = Field(default_factory=list)


class PredictionInput(BaseModel):
    """A single prediction with reasoning."""
    user_id: str
    market_id: str
    probability: float = Field(ge=0, le=1, description="Prediction 0-1")
    reasoning: str = Field(min_length=10, description="Why this prediction")
    confidence_level: Literal["very_low", "low", "medium", "high", "very_high"] = "medium"
    key_assumption: Optional[str] = None


class ResolutionResult(BaseModel):
    """Market resolution outcome."""
    market_id: str
    outcome: Literal["yes", "no", "partial", "ambiguous"]
    actual_value: float = Field(ge=0, le=1)
    evidence: str
    evidence_sources: List[str] = Field(default_factory=list)
    resolved_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class BrierScore(BaseModel):
    """Brier score calculation result."""
    user_id: str
    prediction_value: float
    actual_value: float
    brier_score: float = Field(description="(prediction - actual)^2, lower is better")
    calibration_note: str


class ReasoningCluster(BaseModel):
    """A cluster of similar reasoning from predictions."""
    theme: str
    count: int
    representative_quotes: List[str]
    was_correct: Optional[bool] = None


class Retrospective(BaseModel):
    """Post-resolution analysis."""
    market_id: str
    market_question: str
    outcome: str
    crowd_accuracy: float  # Average Brier score
    optimist_themes: List[ReasoningCluster]
    skeptic_themes: List[ReasoningCluster]
    crux_disagreement: str
    crux_correct_side: Literal["optimists", "skeptics", "neither"]
    lesson_learned: str
    pattern_extracted: Optional[str] = None


# =============================================================================
# LANGGRAPH STATE
# =============================================================================

class OracleState(TypedDict):
    """State for the Oracle pipeline."""
    # Input
    user_input: str
    session_id: str
    phase: Literal["formulation", "research", "prediction", "resolution", "retrospective"]

    # Market data
    market: Optional[Dict[str, Any]]
    market_id: Optional[str]

    # Research
    web_results: List[Dict[str, Any]]
    neo4j_context: List[str]
    filesearch_context: List[str]
    hsi_surprises: List[str]
    research_brief: Optional[Dict[str, Any]]

    # Predictions
    predictions: List[Dict[str, Any]]

    # Resolution
    resolution: Optional[Dict[str, Any]]
    brier_scores: List[Dict[str, Any]]

    # Retrospective
    retrospective: Optional[Dict[str, Any]]

    # Output
    response: str
    error: Optional[str]


# =============================================================================
# NODE FUNCTIONS
# =============================================================================

async def formulate_market(state: OracleState) -> Dict[str, Any]:
    """
    Phase 1: Transform fuzzy user input into structured market.
    Uses Gemini with structured output for reliable parsing.
    """
    user_input = state["user_input"]

    prompt = f"""You are Oracle, Mindrian's prediction market formulation expert.

Transform this fuzzy idea into a well-structured prediction market:

USER INPUT: {user_input}

Output a structured market with:
1. A specific, measurable question with timeframe
2. Clear resolution criteria (source, threshold, timeframe, conditions)
3. A challenge question citing base rates or comparable cases
4. A category (forecast_program, validate_idea, emerging_trend, or custom)

The question should be:
- Specific enough to resolve unambiguously
- Measurable with clear thresholds
- Timebound with explicit deadlines
- Challenging but not impossible to verify

For the challenge, research or estimate a relevant base rate. If you don't know the exact rate, make an educated estimate and note it.

Respond in JSON format matching this schema:
{{
    "question": "Will [specific thing] achieve [threshold] by [date]?",
    "resolution_criteria": {{
        "source": "Where to verify",
        "threshold": "What counts as yes/no",
        "timeframe": "Specific deadline",
        "resolves_yes": "Condition for YES",
        "resolves_no": "Condition for NO",
        "resolves_partial": "Optional partial condition"
    }},
    "challenge": "Similar X showed Y% - what's different here?",
    "category": "validate_idea",
    "raw_input": "{user_input}",
    "confidence_notes": "Any notes about formulation quality"
}}"""

    try:
        response = _client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=1500,
                response_mime_type="application/json"
            )
        )

        result_text = response.text.strip()
        market_data = json.loads(result_text)

        # Generate a market ID
        import uuid
        market_id = str(uuid.uuid4())
        market_data["id"] = market_id
        market_data["created_at"] = datetime.now().isoformat()
        market_data["status"] = "draft"

        return {
            "market": market_data,
            "market_id": market_id,
            "phase": "research"
        }

    except Exception as e:
        return {
            "error": f"Market formulation failed: {str(e)}",
            "market": None
        }


async def gather_web_research(state: OracleState) -> Dict[str, Any]:
    """
    Gather web research for the market question using Tavily.
    """
    market = state.get("market")
    if not market:
        return {"web_results": []}

    question = market.get("question", "")
    category = market.get("category", "custom")

    try:
        from tools.tavily_search import search_tavily, search_trend

        # Build research queries based on category
        queries = []
        if category == "validate_idea":
            queries = [
                f"{question} success rate statistics",
                f"{question} failure case study",
                f"{question} comparable deployment results"
            ]
        elif category == "emerging_trend":
            queries = [
                f"{question} trend data forecast",
                f"{question} expert predictions",
                f"{question} growth rate analysis"
            ]
        else:
            queries = [
                f"{question} research evidence",
                f"{question} case studies"
            ]

        # Execute searches in parallel
        results = []
        for query in queries[:3]:  # Limit to 3 queries
            try:
                search_result = search_tavily(query, max_results=3)
                if search_result and search_result.get("results"):
                    results.extend(search_result["results"])
            except Exception:
                continue

        # Deduplicate by URL
        seen_urls = set()
        unique_results = []
        for r in results:
            url = r.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append({
                    "title": r.get("title", ""),
                    "content": r.get("content", "")[:500],
                    "url": url
                })

        return {"web_results": unique_results[:8]}

    except Exception as e:
        print(f"Web research error: {e}")
        return {"web_results": []}


async def gather_neo4j_context(state: OracleState) -> Dict[str, Any]:
    """
    Query Neo4j for related concepts, frameworks, and reverse salients.
    """
    market = state.get("market")
    if not market:
        return {"neo4j_context": []}

    question = market.get("question", "")

    try:
        from tools.graphrag_lite import get_concepts_for_query, get_frameworks_for_query

        context = []

        # Get related concepts
        concepts = get_concepts_for_query(question, limit=5)
        if concepts:
            for c in concepts:
                context.append(f"Concept: {c.get('name', '')} — {c.get('description', '')[:150]}")

        # Get related frameworks
        frameworks = get_frameworks_for_query(question, limit=3)
        if frameworks:
            for f in frameworks:
                context.append(f"Framework: {f.get('name', '')} — relevant for this type of prediction")

        # Look for reverse salients (cross-domain connections)
        try:
            from neo4j import GraphDatabase

            neo4j_uri = os.getenv("NEO4J_URI")
            neo4j_user = os.getenv("NEO4J_USER", "neo4j")
            neo4j_password = os.getenv("NEO4J_PASSWORD")

            if neo4j_uri and neo4j_password:
                driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

                with driver.session() as session:
                    # Find reverse salients that might connect
                    result = session.run("""
                        MATCH (rs:ReverseSalient)
                        WHERE rs.description CONTAINS $keyword OR rs.name CONTAINS $keyword
                        RETURN rs.name AS name, rs.description AS description
                        LIMIT 3
                    """, keyword=question.split()[0] if question else "innovation")

                    for record in result:
                        context.append(
                            f"ReverseSalient: {record['name']} — {record['description'][:150] if record['description'] else 'Cross-domain connection found'}"
                        )

                driver.close()
        except Exception as e:
            print(f"Neo4j ReverseSalient query error: {e}")

        return {"neo4j_context": context}

    except Exception as e:
        print(f"Neo4j context error: {e}")
        return {"neo4j_context": []}


async def gather_filesearch_context(state: OracleState) -> Dict[str, Any]:
    """
    Query FileSearch for PWS knowledge relevant to the market.
    """
    market = state.get("market")
    if not market:
        return {"filesearch_context": []}

    question = market.get("question", "")
    category = market.get("category", "custom")

    try:
        from tools.pws_brain import query_pws_knowledge

        # Build query based on category
        if category == "validate_idea":
            query = f"idea validation methodology {question}"
        elif category == "emerging_trend":
            query = f"trend analysis forecasting {question}"
        else:
            query = f"PWS methodology {question}"

        results = query_pws_knowledge(query, max_results=5)

        context = []
        if results:
            for r in results[:5]:
                context.append(f"PWS: {r.get('content', '')[:200]}")

        return {"filesearch_context": context}

    except Exception as e:
        print(f"FileSearch error: {e}")
        return {"filesearch_context": []}


async def generate_hsi_surprises(state: OracleState) -> Dict[str, Any]:
    """
    Generate HSI (Hierarchical Semantic Integration) surprise connections.
    Find unexpected cross-domain insights that could inform predictions.
    """
    market = state.get("market")
    neo4j_context = state.get("neo4j_context", [])

    if not market:
        return {"hsi_surprises": []}

    question = market.get("question", "")

    prompt = f"""You are an expert at finding surprising, non-obvious connections between domains.

MARKET QUESTION: {question}

NEO4J CONTEXT (existing knowledge graph connections):
{chr(10).join(neo4j_context[:5]) if neo4j_context else "No existing connections found"}

Your task: Identify 2-3 SURPRISING cross-domain connections that could inform predictions about this market.

A good surprise connection:
- Comes from an unexpected field (not the obvious domain)
- Has actual predictive relevance (not just superficial similarity)
- Challenges assumptions the community might hold

For each surprise, explain:
1. The unexpected domain/concept
2. Why it's relevant to this prediction
3. What it suggests about likely outcomes

Format as JSON array:
[
    {{
        "domain": "unexpected field name",
        "connection": "why this connects to the market",
        "implication": "what this suggests for predictions"
    }}
]"""

    try:
        response = _client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,  # Higher temp for creative connections
                max_output_tokens=1000,
                response_mime_type="application/json"
            )
        )

        surprises_data = json.loads(response.text.strip())

        surprises = []
        for s in surprises_data[:3]:
            surprises.append(
                f"🧠 **{s.get('domain', 'Unknown')}**: {s.get('connection', '')} → {s.get('implication', '')}"
            )

        return {"hsi_surprises": surprises}

    except Exception as e:
        print(f"HSI surprise generation error: {e}")
        return {"hsi_surprises": []}


async def synthesize_research_brief(state: OracleState) -> Dict[str, Any]:
    """
    Synthesize all research into a structured brief.
    """
    market = state.get("market")
    web_results = state.get("web_results", [])
    neo4j_context = state.get("neo4j_context", [])
    filesearch_context = state.get("filesearch_context", [])
    hsi_surprises = state.get("hsi_surprises", [])

    if not market:
        return {"research_brief": None, "error": "No market to synthesize"}

    prompt = f"""Synthesize this research into a prediction market brief.

MARKET QUESTION: {market.get('question', '')}

WEB RESEARCH:
{chr(10).join([f"- {r.get('title', '')}: {r.get('content', '')[:200]}" for r in web_results[:5]]) if web_results else "No web results"}

NEO4J KNOWLEDGE GRAPH:
{chr(10).join(neo4j_context[:5]) if neo4j_context else "No graph connections"}

PWS METHODOLOGY (FileSearch):
{chr(10).join(filesearch_context[:3]) if filesearch_context else "No PWS context"}

SEMANTIC SURPRISES (HSI):
{chr(10).join(hsi_surprises[:3]) if hsi_surprises else "No surprise connections"}

Create a structured research brief with:
1. Base rates and comparable cases (with percentages if available)
2. Success factors (what correlates with positive outcomes)
3. Failure modes (what causes similar efforts to fail)
4. Key uncertainties (what we don't know that matters most)

Output as JSON:
{{
    "market_question": "...",
    "base_rates": [
        {{"name": "Comparable case", "outcome": "what happened", "percentage": 0.XX}}
    ],
    "success_factors": ["factor 1", "factor 2"],
    "failure_modes": ["mode 1", "mode 2"],
    "key_uncertainties": ["uncertainty 1", "uncertainty 2"],
    "neo4j_insights": ["insight 1"],
    "hsi_surprises": ["surprise 1"],
    "web_sources": [{{"title": "...", "url": "..."}}]
}}"""

    try:
        response = _client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=2000,
                response_mime_type="application/json"
            )
        )

        brief = json.loads(response.text.strip())

        # Add web sources
        brief["web_sources"] = [{"title": r.get("title", ""), "url": r.get("url", "")} for r in web_results[:5]]

        return {
            "research_brief": brief,
            "phase": "prediction"
        }

    except Exception as e:
        return {
            "research_brief": None,
            "error": f"Brief synthesis failed: {str(e)}"
        }


async def calculate_brier_scores(state: OracleState) -> Dict[str, Any]:
    """
    Calculate Brier scores for all predictions after resolution.
    Brier = (prediction - actual)^2, lower is better (0 = perfect)
    """
    predictions = state.get("predictions", [])
    resolution = state.get("resolution")

    if not resolution or not predictions:
        return {"brier_scores": []}

    actual_value = resolution.get("actual_value", 0.5)

    scores = []
    for pred in predictions:
        pred_value = pred.get("probability", 0.5)
        brier = (pred_value - actual_value) ** 2

        # Calibration note
        if brier < 0.1:
            note = "Excellent calibration"
        elif brier < 0.25:
            note = "Good calibration"
        elif brier < 0.5:
            note = "Fair calibration"
        else:
            note = "Poor calibration — consider adjusting confidence"

        scores.append({
            "user_id": pred.get("user_id", "unknown"),
            "prediction_value": pred_value,
            "actual_value": actual_value,
            "brier_score": round(brier, 4),
            "calibration_note": note
        })

    return {"brier_scores": scores}


async def generate_retrospective(state: OracleState) -> Dict[str, Any]:
    """
    Generate retrospective analysis: reasoning clusters, crux identification, lessons.
    """
    market = state.get("market")
    predictions = state.get("predictions", [])
    resolution = state.get("resolution")
    brier_scores = state.get("brier_scores", [])

    if not market or not resolution:
        return {"retrospective": None}

    # Calculate crowd accuracy
    avg_brier = sum(s.get("brier_score", 0.5) for s in brier_scores) / len(brier_scores) if brier_scores else 0.5

    # Cluster reasoning
    prompt = f"""Analyze the prediction reasoning for this resolved market.

MARKET: {market.get('question', '')}
OUTCOME: {resolution.get('outcome', '')} (actual: {resolution.get('actual_value', 0.5)})

PREDICTIONS AND REASONING:
{chr(10).join([f"- {p.get('probability', 0.5):.0%}: {p.get('reasoning', '')}" for p in predictions[:10]]) if predictions else "No predictions"}

Analyze:
1. What themes did optimists (high probability) cite?
2. What themes did skeptics (low probability) cite?
3. What was the CRUX disagreement (the key factor people disagreed about)?
4. Which side was correct about the crux?
5. What lesson should be extracted for future predictions?
6. Is there a pattern we should store? (e.g., "Markets about X tend to be overconfident")

Output as JSON:
{{
    "optimist_themes": [{{"theme": "...", "count": N, "representative_quotes": ["..."]}}],
    "skeptic_themes": [{{"theme": "...", "count": N, "representative_quotes": ["..."]}}],
    "crux_disagreement": "The key factor...",
    "crux_correct_side": "optimists|skeptics|neither",
    "lesson_learned": "For future predictions...",
    "pattern_extracted": "Markets about X tend to... (or null if no clear pattern)"
}}"""

    try:
        response = _client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=1500,
                response_mime_type="application/json"
            )
        )

        analysis = json.loads(response.text.strip())

        retrospective = {
            "market_id": state.get("market_id"),
            "market_question": market.get("question"),
            "outcome": resolution.get("outcome"),
            "crowd_accuracy": round(avg_brier, 4),
            **analysis
        }

        return {
            "retrospective": retrospective,
            "phase": "complete"
        }

    except Exception as e:
        return {
            "retrospective": None,
            "error": f"Retrospective generation failed: {str(e)}"
        }


def format_market_output(state: OracleState) -> Dict[str, Any]:
    """Format the market for display."""
    market = state.get("market")
    if not market:
        return {"response": "Failed to create market."}

    response = f"""## 🔮 Market Created

**MARKET:** {market.get('question', '')}

### Resolution Criteria
"""

    criteria = market.get("resolution_criteria", {})
    if isinstance(criteria, dict):
        response += f"""- **Source:** {criteria.get('source', 'TBD')}
- **Threshold:** {criteria.get('threshold', 'TBD')}
- **Timeframe:** {criteria.get('timeframe', 'TBD')}
- **YES if:** {criteria.get('resolves_yes', 'TBD')}
- **NO if:** {criteria.get('resolves_no', 'TBD')}
"""
        if criteria.get('resolves_partial'):
            response += f"- **PARTIAL if:** {criteria.get('resolves_partial')}\n"

    response += f"""
### ⚠️ Challenge Question
*{market.get('challenge', 'What makes your context different from comparable cases?')}*

**Category:** `{market.get('category', 'custom')}`
**Market ID:** `{market.get('id', 'N/A')}`
"""

    return {"response": response}


def format_research_brief_output(state: OracleState) -> Dict[str, Any]:
    """Format the research brief for display."""
    brief = state.get("research_brief")
    market = state.get("market")
    hsi_surprises = state.get("hsi_surprises", [])

    if not brief:
        return {"response": "Research brief not available."}

    response = f"""## 📋 Research Brief: {market.get('question', '') if market else 'Market'}

### Base Rates & Comparables
"""

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

    if hsi_surprises:
        response += "\n### 🧠 Semantic Surprises (Cross-Domain)\n"
        for surprise in hsi_surprises[:3]:
            response += f"{surprise}\n\n"

    response += "\n### ❓ Key Uncertainties\n"
    for unc in brief.get("key_uncertainties", [])[:3]:
        response += f"- {unc}\n"

    if brief.get("web_sources"):
        response += "\n### 📚 Sources\n"
        for src in brief.get("web_sources", [])[:5]:
            if src.get("url"):
                response += f"- [{src.get('title', 'Source')}]({src.get('url')})\n"

    return {"response": response}


# =============================================================================
# LANGGRAPH WORKFLOW CONSTRUCTION
# =============================================================================

def create_oracle_pipeline():
    """
    Create the Oracle LangGraph pipeline.

    Workflow:
    1. formulate_market — Structure the prediction question
    2. [parallel] gather_web_research, gather_neo4j_context, gather_filesearch_context
    3. generate_hsi_surprises — Find cross-domain connections
    4. synthesize_research_brief — Create structured brief
    5. format output
    """

    workflow = StateGraph(OracleState)

    # Add nodes
    workflow.add_node("formulate_market", formulate_market)
    workflow.add_node("gather_web_research", gather_web_research)
    workflow.add_node("gather_neo4j_context", gather_neo4j_context)
    workflow.add_node("gather_filesearch_context", gather_filesearch_context)
    workflow.add_node("generate_hsi_surprises", generate_hsi_surprises)
    workflow.add_node("synthesize_research_brief", synthesize_research_brief)
    workflow.add_node("format_market_output", format_market_output)
    workflow.add_node("format_research_brief_output", format_research_brief_output)

    # Resolution nodes
    workflow.add_node("calculate_brier_scores", calculate_brier_scores)
    workflow.add_node("generate_retrospective", generate_retrospective)

    # Define edges
    workflow.set_entry_point("formulate_market")

    # After formulation, run research in parallel
    workflow.add_edge("formulate_market", "gather_web_research")
    workflow.add_edge("formulate_market", "gather_neo4j_context")
    workflow.add_edge("formulate_market", "gather_filesearch_context")

    # After all research, generate surprises
    workflow.add_edge("gather_web_research", "generate_hsi_surprises")
    workflow.add_edge("gather_neo4j_context", "generate_hsi_surprises")
    workflow.add_edge("gather_filesearch_context", "generate_hsi_surprises")

    # Synthesize and format
    workflow.add_edge("generate_hsi_surprises", "synthesize_research_brief")
    workflow.add_edge("synthesize_research_brief", "format_research_brief_output")
    workflow.add_edge("format_research_brief_output", END)

    return workflow.compile()


def create_resolution_pipeline():
    """
    Create pipeline for market resolution and retrospective.
    """
    workflow = StateGraph(OracleState)

    workflow.add_node("calculate_brier_scores", calculate_brier_scores)
    workflow.add_node("generate_retrospective", generate_retrospective)

    workflow.set_entry_point("calculate_brier_scores")
    workflow.add_edge("calculate_brier_scores", "generate_retrospective")
    workflow.add_edge("generate_retrospective", END)

    return workflow.compile()


# =============================================================================
# PUBLIC API
# =============================================================================

async def run_oracle_formulation(user_input: str, session_id: str) -> Dict[str, Any]:
    """
    Run the full Oracle formulation + research pipeline.

    Args:
        user_input: The fuzzy idea/question from user
        session_id: Session identifier

    Returns:
        Dict with market, research_brief, and formatted response
    """
    pipeline = create_oracle_pipeline()

    initial_state: OracleState = {
        "user_input": user_input,
        "session_id": session_id,
        "phase": "formulation",
        "market": None,
        "market_id": None,
        "web_results": [],
        "neo4j_context": [],
        "filesearch_context": [],
        "hsi_surprises": [],
        "research_brief": None,
        "predictions": [],
        "resolution": None,
        "brier_scores": [],
        "retrospective": None,
        "response": "",
        "error": None
    }

    try:
        # Run the pipeline
        final_state = await pipeline.ainvoke(initial_state)

        return {
            "success": True,
            "market": final_state.get("market"),
            "market_id": final_state.get("market_id"),
            "research_brief": final_state.get("research_brief"),
            "hsi_surprises": final_state.get("hsi_surprises"),
            "response": final_state.get("response"),
            "error": final_state.get("error")
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "market": None,
            "research_brief": None
        }


async def run_oracle_resolution(
    market_id: str,
    market: Dict[str, Any],
    predictions: List[Dict[str, Any]],
    resolution: Dict[str, Any],
    session_id: str
) -> Dict[str, Any]:
    """
    Run resolution and retrospective analysis.

    Args:
        market_id: The market being resolved
        market: Market data
        predictions: List of predictions with reasoning
        resolution: Resolution data (outcome, actual_value, evidence)
        session_id: Session identifier

    Returns:
        Dict with brier_scores and retrospective
    """
    pipeline = create_resolution_pipeline()

    state: OracleState = {
        "user_input": "",
        "session_id": session_id,
        "phase": "resolution",
        "market": market,
        "market_id": market_id,
        "web_results": [],
        "neo4j_context": [],
        "filesearch_context": [],
        "hsi_surprises": [],
        "research_brief": None,
        "predictions": predictions,
        "resolution": resolution,
        "brier_scores": [],
        "retrospective": None,
        "response": "",
        "error": None
    }

    try:
        final_state = await pipeline.ainvoke(state)

        return {
            "success": True,
            "brier_scores": final_state.get("brier_scores"),
            "retrospective": final_state.get("retrospective"),
            "error": final_state.get("error")
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "brier_scores": [],
            "retrospective": None
        }


def format_brier_leaderboard(scores: List[Dict[str, Any]]) -> str:
    """Format Brier scores as a leaderboard."""
    if not scores:
        return "No scores to display."

    # Sort by Brier (lower is better)
    sorted_scores = sorted(scores, key=lambda x: x.get("brier_score", 1.0))

    response = "## 🏆 Prediction Accuracy Leaderboard\n\n"
    response += "| Rank | User | Prediction | Actual | Brier Score | Calibration |\n"
    response += "|------|------|------------|--------|-------------|-------------|\n"

    for i, score in enumerate(sorted_scores[:10], 1):
        pred = f"{score.get('prediction_value', 0)*100:.0f}%"
        actual = f"{score.get('actual_value', 0)*100:.0f}%"
        brier = f"{score.get('brier_score', 0):.4f}"
        note = score.get("calibration_note", "")

        response += f"| {i} | {score.get('user_id', 'Anonymous')[:12]} | {pred} | {actual} | {brier} | {note} |\n"

    return response


def format_retrospective_output(retrospective: Dict[str, Any]) -> str:
    """Format retrospective for display."""
    if not retrospective:
        return "Retrospective not available."

    response = f"""## 🔬 Prediction Autopsy

**Market:** {retrospective.get('market_question', '')}
**Outcome:** {retrospective.get('outcome', '')}
**Crowd Accuracy (Avg Brier):** {retrospective.get('crowd_accuracy', 0):.4f}

### Optimist Themes (High Probability Predictors)
"""

    for theme in retrospective.get("optimist_themes", [])[:3]:
        response += f"- **{theme.get('theme', '')}** ({theme.get('count', 0)} predictors)\n"

    response += "\n### Skeptic Themes (Low Probability Predictors)\n"
    for theme in retrospective.get("skeptic_themes", [])[:3]:
        response += f"- **{theme.get('theme', '')}** ({theme.get('count', 0)} predictors)\n"

    response += f"""
### 🎯 The Crux
*{retrospective.get('crux_disagreement', 'Unknown')}*

**Correct side:** {retrospective.get('crux_correct_side', 'Neither').capitalize()}

### 📚 Lesson Learned
{retrospective.get('lesson_learned', 'No specific lesson extracted.')}
"""

    if retrospective.get("pattern_extracted"):
        response += f"\n### 📊 Pattern Extracted\n*{retrospective.get('pattern_extracted')}*"

    return response


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Schemas
    "MarketFormulation",
    "ResearchBrief",
    "PredictionInput",
    "ResolutionResult",
    "BrierScore",
    "Retrospective",
    # State
    "OracleState",
    # Pipelines
    "create_oracle_pipeline",
    "create_resolution_pipeline",
    # API
    "run_oracle_formulation",
    "run_oracle_resolution",
    # Formatting
    "format_brier_leaderboard",
    "format_retrospective_output",
]
