"""
Multi-Agent Orchestrator - LangGraph Implementation
===================================================
Automatic multi-bot consultation on complex queries without user orchestration.

Instead of user-initiated bot switching, this orchestrator:
1. Routes queries to appropriate agents based on content
2. Runs multiple agents in parallel when beneficial
3. Synthesizes perspectives into unified output

Agents available:
- Lawrence (general PWS coaching)
- TTA (Trending to the Absurd)
- JTBD (Jobs to Be Done)
- RedTeam (Devil's Advocate)
- Ackoff (DIKW Pyramid)
- Research (autonomous tool-calling)
- Validation (Camera Test)

Usage:
    from intelligence.agents import run_multi_agent_analysis

    result = await run_multi_agent_analysis(
        query="Should I pivot to AI-powered education?",
        analysis_type="full"  # quick, research, validate, full
    )
"""

import os
import json
import asyncio
from typing import TypedDict, Annotated, List, Dict, Any, Optional
from operator import add
from datetime import datetime

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver


# =============================================================================
# STATE DEFINITION
# =============================================================================

def merge_dicts(left: dict, right: dict) -> dict:
    """Reducer: merge dictionaries."""
    return {**left, **right}


class MultiAgentState(TypedDict):
    """State for multi-agent orchestration."""
    # Input
    query: str
    context: str
    analysis_type: str  # quick, research, validate, full

    # Agent outputs
    perspectives: Annotated[dict, merge_dicts]  # {agent_id: analysis}
    research_results: dict
    validation_results: dict

    # Final output
    synthesis: str
    recommended_agents: list
    confidence: float

    # Metadata
    started_at: str
    completed_agents: Annotated[list, add]
    errors: Annotated[list, add]


# =============================================================================
# AGENT ROUTING
# =============================================================================

def score_agent_relevance(query: str, agent_id: str) -> float:
    """
    Score how relevant an agent is to a query.

    Uses keyword matching and pattern recognition.
    """
    query_lower = query.lower()

    AGENT_KEYWORDS = {
        "lawrence": ["problem", "pws", "discovery", "coach", "think", "help", "advice"],
        "tta": ["trend", "absurd", "future", "extrapolate", "growth", "trajectory", "forecast"],
        "jtbd": ["job", "customer", "hire", "progress", "struggling", "switch", "outcome"],
        "redteam": ["challenge", "risk", "weakness", "devil", "critique", "validate", "test"],
        "ackoff": ["data", "information", "knowledge", "wisdom", "dikw", "pyramid", "understanding"],
        "research": ["research", "search", "find", "evidence", "data", "statistics", "source"],
        "validation": ["validate", "test", "camera", "assumption", "prove", "verify", "check"],
    }

    keywords = AGENT_KEYWORDS.get(agent_id, [])
    if not keywords:
        return 0.1

    # Count keyword matches
    matches = sum(1 for kw in keywords if kw in query_lower)

    # Normalize score (0-1)
    return min(1.0, matches / max(len(keywords) / 2, 1))


def route_to_agents(state: MultiAgentState) -> List[str]:
    """
    Determine which agents to consult based on query and analysis type.

    Returns list of agent IDs to run.
    """
    query = state["query"]
    analysis_type = state.get("analysis_type", "quick")

    # Score all agents
    scores = {}
    for agent_id in ["lawrence", "tta", "jtbd", "redteam", "ackoff"]:
        scores[agent_id] = score_agent_relevance(query, agent_id)

    # Sort by score
    sorted_agents = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    if analysis_type == "quick":
        # Top 2 agents
        return [a[0] for a in sorted_agents[:2]]
    elif analysis_type == "research":
        # Top 2 + research agent
        return [a[0] for a in sorted_agents[:2]] + ["research"]
    elif analysis_type == "validate":
        # Top 2 + validation + redteam
        agents = [a[0] for a in sorted_agents[:2]]
        if "redteam" not in agents:
            agents.append("redteam")
        agents.append("validation")
        return agents
    else:  # full
        # Top 3 + research + validation
        return [a[0] for a in sorted_agents[:3]] + ["research", "validation"]


# =============================================================================
# AGENT IMPLEMENTATIONS
# =============================================================================

async def run_conversation_agent(
    agent_id: str,
    query: str,
    context: str = ""
) -> Dict[str, Any]:
    """
    Run a conversation agent (Lawrence, TTA, JTBD, etc.).

    Uses the agent's system prompt to generate a perspective.
    """
    try:
        from google import genai
        from google.genai import types

        # Import system prompts
        AGENT_PROMPTS = {
            "lawrence": "You are Lawrence, a PWS methodology coach. Provide focused, practical guidance.",
            "tta": "You are the Trending to the Absurd agent. Extrapolate trends to absurd endpoints.",
            "jtbd": "You are the Jobs to Be Done agent. Focus on progress customers seek.",
            "redteam": "You are the Red Team agent. Challenge assumptions and find weaknesses.",
            "ackoff": "You are the Ackoff agent. Analyze through the DIKW pyramid lens.",
        }

        system_prompt = AGENT_PROMPTS.get(agent_id, AGENT_PROMPTS["lawrence"])

        client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

        prompt = f"""{system_prompt}

QUERY: {query}
{f"CONTEXT: {context}" if context else ""}

Provide your perspective in 2-3 focused paragraphs. Be specific and actionable."""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[types.Content(role="user", parts=[types.Part(text=prompt)])],
        )

        return {
            "agent_id": agent_id,
            "perspective": response.text,
            "success": True
        }

    except Exception as e:
        return {
            "agent_id": agent_id,
            "perspective": f"Error: {str(e)}",
            "success": False,
            "error": str(e)
        }


async def run_research_agent_node(query: str, context: str = "") -> Dict[str, Any]:
    """Run the research agent."""
    try:
        from intelligence.agents.research_agent import run_research_agent
        return await run_research_agent(query, context)
    except Exception as e:
        return {"output": f"Research error: {str(e)}", "error": str(e)}


async def run_validation_agent_node(query: str, context: str = "") -> Dict[str, Any]:
    """Run validation on key assumptions in the query."""
    try:
        from intelligence.agents.research_agent import research_for_validation

        # Extract key assumption from query
        assumption = query  # In practice, would extract specific assumption

        return await research_for_validation(assumption)
    except Exception as e:
        return {"output": f"Validation error: {str(e)}", "error": str(e)}


# =============================================================================
# PIPELINE NODES
# =============================================================================

async def router_node(state: MultiAgentState) -> dict:
    """Route query to appropriate agents."""
    agents = route_to_agents(state)
    return {
        "recommended_agents": agents,
        "completed_agents": ["router"]
    }


async def run_agents_parallel(state: MultiAgentState) -> dict:
    """Run all recommended agents in parallel."""
    agents = state.get("recommended_agents", ["lawrence"])
    query = state["query"]
    context = state.get("context", "")

    # Create tasks for each agent
    tasks = []
    for agent_id in agents:
        if agent_id in ["lawrence", "tta", "jtbd", "redteam", "ackoff"]:
            tasks.append(run_conversation_agent(agent_id, query, context))
        elif agent_id == "research":
            tasks.append(run_research_agent_node(query, context))
        elif agent_id == "validation":
            tasks.append(run_validation_agent_node(query, context))

    # Run in parallel
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Collect perspectives
    perspectives = {}
    research_results = {}
    validation_results = {}

    for i, result in enumerate(results):
        agent_id = agents[i] if i < len(agents) else f"agent_{i}"

        if isinstance(result, Exception):
            perspectives[agent_id] = f"Error: {str(result)}"
        elif agent_id in ["lawrence", "tta", "jtbd", "redteam", "ackoff"]:
            perspectives[agent_id] = result.get("perspective", "No perspective")
        elif agent_id == "research":
            research_results = result
        elif agent_id == "validation":
            validation_results = result

    return {
        "perspectives": perspectives,
        "research_results": research_results,
        "validation_results": validation_results,
        "completed_agents": agents
    }


async def synthesize_perspectives(state: MultiAgentState) -> dict:
    """Synthesize all perspectives into unified output."""
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

        perspectives = state.get("perspectives", {})
        research = state.get("research_results", {})
        validation = state.get("validation_results", {})

        # Build synthesis prompt
        perspectives_text = "\n\n".join([
            f"## {agent.upper()} Perspective:\n{text}"
            for agent, text in perspectives.items()
        ])

        research_text = ""
        if research and research.get("output"):
            research_text = f"\n\n## Research Findings:\n{research.get('output', '')[:2000]}"

        validation_text = ""
        if validation and validation.get("output"):
            validation_text = f"\n\n## Validation Results:\n{validation.get('output', '')[:1500]}"

        prompt = f"""Synthesize these multi-agent perspectives into a unified analysis:

ORIGINAL QUERY: {state["query"]}

{perspectives_text}
{research_text}
{validation_text}

---

Provide a synthesis that:
1. **Executive Summary** (2-3 sentences capturing the key insight)
2. **Key Agreements** (where agents aligned)
3. **Key Tensions** (where agents disagreed - these are valuable!)
4. **Integrated Recommendation** (combining the best insights)
5. **Confidence Level** (how confident is this synthesis?)
6. **Next Steps** (what should the user do?)

Be specific and actionable. Don't just summarize - integrate and elevate."""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[types.Content(role="user", parts=[types.Part(text=prompt)])],
        )

        # Estimate confidence based on agent agreement
        num_agents = len(perspectives)
        confidence = min(0.9, 0.5 + (num_agents * 0.1))

        return {
            "synthesis": response.text,
            "confidence": confidence,
            "completed_agents": ["synthesizer"]
        }

    except Exception as e:
        return {
            "synthesis": f"Synthesis error: {str(e)}",
            "confidence": 0.3,
            "errors": [f"Synthesis error: {str(e)}"],
            "completed_agents": ["synthesizer_failed"]
        }


# =============================================================================
# PIPELINE CONSTRUCTION
# =============================================================================

def create_multi_agent_pipeline(checkpointer=None):
    """
    Create the multi-agent orchestration pipeline.

    Returns:
        Compiled LangGraph application.
    """
    graph = StateGraph(MultiAgentState)

    # Add nodes
    graph.add_node("router", router_node)
    graph.add_node("run_agents", run_agents_parallel)
    graph.add_node("synthesize", synthesize_perspectives)

    # Flow
    graph.add_edge(START, "router")
    graph.add_edge("router", "run_agents")
    graph.add_edge("run_agents", "synthesize")
    graph.add_edge("synthesize", END)

    # Use provided checkpointer or default to memory
    if checkpointer is None:
        checkpointer = MemorySaver()

    return graph.compile(checkpointer=checkpointer)


# =============================================================================
# PUBLIC API
# =============================================================================

async def run_multi_agent_analysis(
    query: str,
    analysis_type: str = "quick",
    context: str = "",
    session_id: str = None
) -> Dict[str, Any]:
    """
    Run multi-agent analysis on a query.

    Args:
        query: The question or topic to analyze.
        analysis_type: 'quick' (2 agents), 'research' (+ research),
                       'validate' (+ validation), 'full' (all).
        context: Additional context.
        session_id: Session ID for checkpointing.

    Returns:
        Dict with synthesis, perspectives, and metadata.

    Example:
        result = await run_multi_agent_analysis(
            query="Should I pivot to AI-powered education?",
            analysis_type="full"
        )
        print(result["synthesis"])
    """
    if session_id is None:
        session_id = f"multi_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Create pipeline
    pipeline = create_multi_agent_pipeline()

    # Initial state
    initial_state = {
        "query": query,
        "context": context,
        "analysis_type": analysis_type,
        "perspectives": {},
        "research_results": {},
        "validation_results": {},
        "synthesis": "",
        "recommended_agents": [],
        "confidence": 0.0,
        "started_at": datetime.now().isoformat(),
        "completed_agents": [],
        "errors": [],
    }

    # Config for checkpointing
    config = {"configurable": {"thread_id": session_id}}

    # Run pipeline
    try:
        result = await pipeline.ainvoke(initial_state, config)
        return result
    except Exception as e:
        return {
            **initial_state,
            "errors": [f"Pipeline error: {str(e)}"],
            "synthesis": f"Multi-agent analysis failed: {str(e)}"
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

async def quick_analysis(query: str, context: str = "") -> str:
    """Quick 2-agent analysis. Returns just the synthesis."""
    result = await run_multi_agent_analysis(query, "quick", context)
    return result.get("synthesis", "Analysis failed")


async def research_and_explore(query: str, context: str = "") -> str:
    """Research-focused analysis. Returns synthesis with research."""
    result = await run_multi_agent_analysis(query, "research", context)
    return result.get("synthesis", "Analysis failed")


async def validated_decision(query: str, context: str = "") -> str:
    """Validation-focused analysis. Returns synthesis with validation."""
    result = await run_multi_agent_analysis(query, "validate", context)
    return result.get("synthesis", "Analysis failed")


async def full_analysis(query: str, context: str = "") -> str:
    """Full multi-agent analysis. Returns comprehensive synthesis."""
    result = await run_multi_agent_analysis(query, "full", context)
    return result.get("synthesis", "Analysis failed")


def format_multi_agent_result(result: Dict[str, Any]) -> str:
    """Format multi-agent result as markdown."""
    output = ["# Multi-Agent Analysis\n"]

    # Synthesis
    output.append(result.get("synthesis", "No synthesis available"))
    output.append("\n---\n")

    # Agents consulted
    agents = result.get("completed_agents", [])
    output.append(f"**Agents Consulted:** {', '.join(agents)}\n")
    output.append(f"**Confidence:** {result.get('confidence', 0):.0%}\n")

    # Individual perspectives (collapsed)
    if result.get("perspectives"):
        output.append("\n## Individual Perspectives\n")
        for agent, perspective in result["perspectives"].items():
            output.append(f"### {agent.upper()}\n{perspective[:500]}...\n")

    return "\n".join(output)
