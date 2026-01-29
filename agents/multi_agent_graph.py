"""
Mindrian Multi-Agent Graph
LangGraph-based orchestration for complex multi-agent workflows

This module enables scenarios where multiple agents collaborate on a single query:
- Larry → Red Team → Ackoff → Larry (synthesis)
- Parallel agent execution
- Conditional routing based on query type

Usage:
    from agents.multi_agent_graph import run_multi_agent_workflow

    result = await run_multi_agent_workflow(
        query="I want to launch a healthcare AI startup",
        agents=["larry", "tta", "redteam", "ackoff"],
        mode="sequential"  # or "parallel"
    )
"""

import os
import asyncio
from typing import TypedDict, List, Optional, Literal, Annotated
from dataclasses import dataclass

# Check if LangGraph is available
try:
    from langgraph.graph import StateGraph, END
    from langgraph.graph.message import add_messages
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    print("⚠️ LangGraph not installed. Install with: pip install langgraph")

from google import genai
from google.genai import types

# Import prompts
from prompts import (
    LARRY_RAG_SYSTEM_PROMPT,
    TTA_WORKSHOP_PROMPT,
    JTBD_WORKSHOP_PROMPT,
    SCURVE_WORKSHOP_PROMPT,
    REDTEAM_PROMPT,
    ACKOFF_WORKSHOP_PROMPT
)

# === Configuration ===
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_AI_API_KEY")
client = genai.Client(api_key=GOOGLE_API_KEY)


# === Agent Definitions ===
AGENTS = {
    "larry": {
        "name": "Larry",
        "prompt": LARRY_RAG_SYSTEM_PROMPT,
        "role": "General PWS thinking partner - synthesizes and guides"
    },
    "tta": {
        "name": "Trending to the Absurd",
        "prompt": TTA_WORKSHOP_PROMPT,
        "role": "Future trends analyst - extrapolates and finds emerging problems"
    },
    "jtbd": {
        "name": "Jobs to Be Done",
        "prompt": JTBD_WORKSHOP_PROMPT,
        "role": "Customer jobs analyst - understands what customers really need"
    },
    "scurve": {
        "name": "S-Curve Analysis",
        "prompt": SCURVE_WORKSHOP_PROMPT,
        "role": "Technology timing analyst - determines if timing is right"
    },
    "redteam": {
        "name": "Red Team",
        "prompt": REDTEAM_PROMPT,
        "role": "Devil's advocate - finds holes and challenges assumptions"
    },
    "ackoff": {
        "name": "Ackoff's Pyramid",
        "prompt": ACKOFF_WORKSHOP_PROMPT,
        "role": "DIKW validator - ensures decisions are grounded in data"
    },
}


# === State Definition ===
class MultiAgentState(TypedDict):
    """State passed between agents in the graph."""
    query: str                          # Original user query
    messages: List[dict]                # Conversation history
    agent_responses: dict               # Responses from each agent
    current_agent: str                  # Currently active agent
    agents_to_run: List[str]            # Queue of agents to execute
    synthesis: str                      # Final synthesized response
    mode: Literal["sequential", "parallel", "router"]


# === Agent Functions ===
async def call_agent(agent_id: str, query: str, context: str = "") -> str:
    """Call a single agent and get its response."""

    agent = AGENTS.get(agent_id)
    if not agent:
        return f"Unknown agent: {agent_id}"

    # Build the prompt with context from other agents
    full_prompt = query
    if context:
        full_prompt = f"""CONTEXT FROM OTHER AGENTS:
{context}

USER QUERY:
{query}

Provide your unique perspective on this. Build on what others said, add new insights, or challenge their assumptions."""

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=full_prompt,
            config=types.GenerateContentConfig(
                system_instruction=agent["prompt"],
                temperature=0.7,
                max_output_tokens=800
            )
        )
        return response.text.strip()
    except Exception as e:
        return f"Error from {agent['name']}: {str(e)}"


async def synthesize_responses(query: str, agent_responses: dict) -> str:
    """Have Larry synthesize all agent responses into a cohesive answer."""

    # Build context from all agents
    context_parts = []
    for agent_id, response in agent_responses.items():
        agent_name = AGENTS.get(agent_id, {}).get("name", agent_id)
        context_parts.append(f"**{agent_name}:**\n{response}\n")

    all_context = "\n---\n".join(context_parts)

    synthesis_prompt = f"""Multiple PWS experts have analyzed this query. Synthesize their perspectives into a cohesive, actionable response.

ORIGINAL QUERY:
{query}

EXPERT ANALYSES:
{all_context}

YOUR TASK:
1. Identify the key insights from each expert
2. Note where they agree and disagree
3. Synthesize into a clear, actionable recommendation
4. Highlight the most critical next steps

Be concise but comprehensive. The user should walk away with a clear path forward."""

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=synthesis_prompt,
            config=types.GenerateContentConfig(
                system_instruction=LARRY_RAG_SYSTEM_PROMPT,
                temperature=0.5,
                max_output_tokens=1000
            )
        )
        return response.text.strip()
    except Exception as e:
        return f"Synthesis error: {str(e)}"


# === Workflow Functions (No LangGraph Required) ===

async def run_sequential_workflow(
    query: str,
    agents: List[str],
    include_synthesis: bool = True
) -> dict:
    """
    Run agents sequentially, each building on previous responses.

    Flow: Agent1 → Agent2 → Agent3 → Synthesis
    """
    agent_responses = {}
    context = ""

    for agent_id in agents:
        if agent_id not in AGENTS:
            continue

        response = await call_agent(agent_id, query, context)
        agent_responses[agent_id] = response

        # Build context for next agent
        agent_name = AGENTS[agent_id]["name"]
        context += f"\n\n**{agent_name}:** {response}"

    # Synthesize if requested
    synthesis = ""
    if include_synthesis and len(agent_responses) > 1:
        synthesis = await synthesize_responses(query, agent_responses)

    return {
        "agent_responses": agent_responses,
        "synthesis": synthesis,
        "mode": "sequential"
    }


async def run_parallel_workflow(
    query: str,
    agents: List[str],
    include_synthesis: bool = True
) -> dict:
    """
    Run agents in parallel, then synthesize.

    Flow: [Agent1, Agent2, Agent3] (parallel) → Synthesis
    """
    # Create tasks for all agents
    tasks = []
    valid_agents = [a for a in agents if a in AGENTS]

    for agent_id in valid_agents:
        tasks.append(call_agent(agent_id, query, ""))

    # Run all in parallel
    responses = await asyncio.gather(*tasks)

    # Map responses to agents
    agent_responses = {}
    for agent_id, response in zip(valid_agents, responses):
        agent_responses[agent_id] = response

    # Synthesize
    synthesis = ""
    if include_synthesis and len(agent_responses) > 1:
        synthesis = await synthesize_responses(query, agent_responses)

    return {
        "agent_responses": agent_responses,
        "synthesis": synthesis,
        "mode": "parallel"
    }


async def run_router_workflow(query: str) -> dict:
    """
    Let an LLM decide which agents should handle this query.

    Flow: Router → [Selected Agents] → Synthesis
    """
    # Ask Gemini which agents would be most helpful
    router_prompt = f"""Analyze this query and determine which PWS methodology experts should respond.

QUERY: {query}

AVAILABLE EXPERTS:
- larry: General thinking partner (always include for synthesis)
- tta: Future trends and emerging problems
- jtbd: Customer jobs and motivations
- scurve: Technology timing and adoption
- redteam: Assumption challenging and risk analysis
- ackoff: Data validation and DIKW pyramid

Return ONLY a comma-separated list of agent IDs that should respond.
Choose 2-4 agents most relevant to this query.
Example: larry,redteam,ackoff"""

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=router_prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=50
            )
        )

        # Parse agent list
        agent_list = [a.strip() for a in response.text.strip().split(",")]
        agent_list = [a for a in agent_list if a in AGENTS]

        if not agent_list:
            agent_list = ["larry"]  # Fallback

    except Exception:
        agent_list = ["larry", "redteam"]  # Fallback

    # Run the selected agents
    return await run_parallel_workflow(query, agent_list, include_synthesis=True)


# === Chainlit Visualization Integration ===
# Wraps LangGraph workflows with cl.Step for real-time visibility

async def run_multi_agent_with_steps(
    query: str,
    agents: List[str],
    mode: Literal["sequential", "parallel"] = "sequential"
) -> dict:
    """
    Run multi-agent workflow with Chainlit cl.Step visualization.

    Each agent's execution is displayed as a nested step in the UI,
    providing real-time visibility into the multi-agent collaboration.

    Args:
        query: User's question or problem
        agents: List of agent IDs to run
        mode: "sequential" (agents build on each other) or "parallel"

    Returns:
        dict with agent_responses, synthesis, mode, and step_logs
    """
    try:
        import chainlit as cl
        HAS_CHAINLIT = True
    except ImportError:
        HAS_CHAINLIT = False

    agent_responses = {}
    step_logs = []

    # Main workflow step
    if HAS_CHAINLIT:
        async with cl.Step(name="Multi-Agent Analysis", type="tool") as main_step:
            main_step.input = f"Query: {query}\nAgents: {', '.join(agents)}\nMode: {mode}"

            if mode == "sequential":
                # Run sequentially with visible steps
                context = ""
                for agent_id in agents:
                    if agent_id not in AGENTS:
                        continue

                    agent_name = AGENTS[agent_id]["name"]
                    async with cl.Step(name=f"🤖 {agent_name}", type="llm") as agent_step:
                        agent_step.input = query if not context else f"Building on previous insights:\n{context[:500]}..."

                        response = await call_agent(agent_id, query, context)
                        agent_responses[agent_id] = response

                        # Update context for next agent
                        context += f"\n\n**{agent_name}:** {response}"

                        agent_step.output = response[:500] + "..." if len(response) > 500 else response
                        step_logs.append({
                            "agent": agent_id,
                            "name": agent_name,
                            "response_length": len(response)
                        })

            else:  # parallel
                async with cl.Step(name="⚡ Parallel Execution", type="tool") as parallel_step:
                    parallel_step.input = f"Running {len(agents)} agents simultaneously"

                    # Create tasks
                    tasks = []
                    valid_agents = [a for a in agents if a in AGENTS]
                    for agent_id in valid_agents:
                        tasks.append(call_agent(agent_id, query, ""))

                    # Run in parallel
                    responses = await asyncio.gather(*tasks)

                    # Map responses
                    for agent_id, response in zip(valid_agents, responses):
                        agent_responses[agent_id] = response
                        step_logs.append({
                            "agent": agent_id,
                            "name": AGENTS[agent_id]["name"],
                            "response_length": len(response)
                        })

                    parallel_step.output = f"Completed: {', '.join([AGENTS[a]['name'] for a in valid_agents])}"

            # Synthesize
            synthesis = ""
            if len(agent_responses) > 1:
                async with cl.Step(name="🔮 Synthesis", type="llm") as synth_step:
                    synth_step.input = f"Synthesizing {len(agent_responses)} agent perspectives"
                    synthesis = await synthesize_responses(query, agent_responses)
                    synth_step.output = synthesis[:500] + "..." if len(synthesis) > 500 else synthesis

            main_step.output = f"Analysis complete. {len(agent_responses)} agents consulted."

    else:
        # Fallback without Chainlit visualization
        if mode == "sequential":
            result = await run_sequential_workflow(query, agents)
        else:
            result = await run_parallel_workflow(query, agents)
        return result

    return {
        "agent_responses": agent_responses,
        "synthesis": synthesis,
        "mode": mode,
        "step_logs": step_logs
    }


async def visualize_langgraph_execution(
    graph,
    initial_state: dict,
    step_name: str = "LangGraph Workflow"
) -> dict:
    """
    Execute a compiled LangGraph with Chainlit step visualization.

    This generic wrapper can visualize any LangGraph execution,
    showing each node as it executes.

    Args:
        graph: Compiled LangGraph (from StateGraph.compile())
        initial_state: Initial state dictionary
        step_name: Name to display in the UI

    Returns:
        Final state after graph execution
    """
    try:
        import chainlit as cl
        HAS_CHAINLIT = True
    except ImportError:
        HAS_CHAINLIT = False

    if not HAS_CHAINLIT:
        # Execute without visualization
        result = await graph.ainvoke(initial_state)
        return result

    async with cl.Step(name=step_name, type="tool") as main_step:
        main_step.input = f"Starting {step_name}..."

        # Execute with streaming to capture node transitions
        final_state = None
        current_node = None

        async for event in graph.astream(initial_state):
            # Each event is {node_name: state_update}
            for node_name, state_update in event.items():
                if node_name != current_node:
                    # New node started
                    current_node = node_name
                    async with cl.Step(name=f"📍 {node_name}", type="llm") as node_step:
                        # Show what this node produced
                        if isinstance(state_update, dict):
                            output_preview = str(state_update)[:300]
                        else:
                            output_preview = str(state_update)[:300]
                        node_step.output = output_preview

                final_state = state_update

        main_step.output = f"Workflow completed through {current_node or 'unknown'}"

    return final_state


# === Main Entry Point ===

async def run_multi_agent_workflow(
    query: str,
    agents: Optional[List[str]] = None,
    mode: Literal["sequential", "parallel", "router"] = "parallel"
) -> dict:
    """
    Main entry point for multi-agent workflows.

    Args:
        query: User's question or problem
        agents: List of agent IDs to use (None = let router decide)
        mode:
            - "sequential": Agents run one after another, building on each other
            - "parallel": Agents run simultaneously, then synthesize
            - "router": LLM decides which agents to use

    Returns:
        dict with agent_responses, synthesis, and mode

    Example:
        result = await run_multi_agent_workflow(
            query="Should I pivot my startup to AI?",
            agents=["larry", "scurve", "redteam"],
            mode="sequential"
        )
    """
    if mode == "router" or agents is None:
        return await run_router_workflow(query)
    elif mode == "sequential":
        return await run_sequential_workflow(query, agents)
    else:  # parallel
        return await run_parallel_workflow(query, agents)


# === LangGraph Implementation (Optional) ===

if LANGGRAPH_AVAILABLE:

    def create_langgraph_workflow(agents: List[str]):
        """
        Create a LangGraph StateGraph for more complex workflows.

        This enables:
        - Conditional routing
        - Loops and cycles
        - More sophisticated state management
        """

        # Define the graph
        workflow = StateGraph(MultiAgentState)

        # Add agent nodes
        for agent_id in agents:
            async def agent_node(state: MultiAgentState, aid=agent_id):
                context = "\n".join([
                    f"{AGENTS[k]['name']}: {v}"
                    for k, v in state["agent_responses"].items()
                ])
                response = await call_agent(aid, state["query"], context)
                state["agent_responses"][aid] = response

                # Move to next agent
                remaining = state["agents_to_run"]
                if remaining:
                    state["current_agent"] = remaining[0]
                    state["agents_to_run"] = remaining[1:]
                else:
                    state["current_agent"] = "synthesize"

                return state

            workflow.add_node(agent_id, agent_node)

        # Add synthesis node
        async def synthesize_node(state: MultiAgentState):
            state["synthesis"] = await synthesize_responses(
                state["query"],
                state["agent_responses"]
            )
            return state

        workflow.add_node("synthesize", synthesize_node)

        # Add routing logic
        def route(state: MultiAgentState):
            if state["current_agent"] == "synthesize":
                return "synthesize"
            return state["current_agent"]

        # Connect nodes
        workflow.set_entry_point(agents[0])
        for i, agent_id in enumerate(agents):
            if i < len(agents) - 1:
                workflow.add_edge(agent_id, agents[i + 1])
            else:
                workflow.add_edge(agent_id, "synthesize")
        workflow.add_edge("synthesize", END)

        return workflow.compile()


# === Convenience Functions ===

async def quick_analysis(query: str) -> str:
    """
    Quick multi-agent analysis with automatic agent selection.
    Returns just the synthesis.
    """
    result = await run_multi_agent_workflow(query, mode="router")
    return result.get("synthesis", "No synthesis available")


async def comprehensive_analysis(query: str) -> dict:
    """
    Full analysis with all major agents.
    """
    return await run_multi_agent_workflow(
        query,
        agents=["larry", "tta", "redteam", "ackoff"],
        mode="sequential"
    )


async def stress_test(query: str) -> dict:
    """
    Focused stress-testing with Red Team and Ackoff.
    """
    return await run_multi_agent_workflow(
        query,
        agents=["redteam", "ackoff"],
        mode="sequential"
    )


# ============================================================
# BACKGROUND AGENTS - Specialized Tool Agents
# ============================================================
# These agents have unique abilities beyond conversation:
# - Research Agent: Web search, data gathering
# - Validation Agent: Fact-checking, data verification
# - Analysis Agent: Data processing, pattern recognition
# ============================================================

class BackgroundAgent:
    """Base class for background agents with tool access."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    async def run(self, query: str, context: dict = None) -> dict:
        raise NotImplementedError


class ResearchAgent(BackgroundAgent):
    """
    Research Agent - Performs web research using Tavily.

    Capabilities:
    - Web search for current information
    - Multi-query research planning
    - Source citation and verification
    """

    def __init__(self):
        super().__init__(
            name="Research Agent",
            description="Performs deep web research to gather evidence and current data"
        )

    async def run(self, query: str, context: dict = None) -> dict:
        """Execute research workflow."""
        from tools.tavily_search import search_web

        # Step 1: Plan research queries
        planning_prompt = f"""Create 3 specific search queries to research this topic:
{query}

Format as:
1. [query]
2. [query]
3. [query]"""

        try:
            plan_response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=planning_prompt,
                config=types.GenerateContentConfig(temperature=0.3, max_output_tokens=200)
            )

            # Extract queries
            queries = []
            for line in plan_response.text.split('\n'):
                line = line.strip()
                if line and line[0].isdigit():
                    query_text = line.split('.', 1)[-1].strip().strip('[]')
                    if len(query_text) > 10:
                        queries.append(query_text)

            if not queries:
                queries = [query]  # Fallback to original query

            # Step 2: Execute searches
            all_results = []
            for q in queries[:3]:
                result = search_web(q, search_depth="advanced", max_results=3)
                if result.get("results"):
                    all_results.append({
                        "query": q,
                        "results": result["results"],
                        "answer": result.get("answer", "")
                    })

            # Step 3: Synthesize findings
            if all_results:
                findings = []
                sources = []
                for item in all_results:
                    if item.get("answer"):
                        findings.append(f"**{item['query']}:** {item['answer']}")
                    for r in item.get("results", []):
                        sources.append({
                            "title": r.get("title", ""),
                            "url": r.get("url", ""),
                            "content": r.get("content", "")[:200]
                        })

                return {
                    "success": True,
                    "findings": "\n\n".join(findings),
                    "sources": sources[:10],
                    "queries_executed": len(all_results)
                }
            else:
                return {
                    "success": False,
                    "error": "No results found",
                    "findings": "",
                    "sources": []
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "findings": "",
                "sources": []
            }


class ValidationAgent(BackgroundAgent):
    """
    Validation Agent - Verifies claims and checks data quality.

    Capabilities:
    - Fact-checking claims against sources
    - Data quality assessment (Camera Test)
    - Assumption verification
    - Source credibility evaluation
    """

    def __init__(self):
        super().__init__(
            name="Validation Agent",
            description="Verifies claims, checks data quality, and validates assumptions"
        )

    async def run(self, query: str, context: dict = None) -> dict:
        """Execute validation workflow."""

        claims = context.get("claims", []) if context else []
        data_points = context.get("data_points", []) if context else []

        # If no specific claims/data provided, extract them from query
        if not claims and not data_points:
            extraction_prompt = f"""From this text, extract:
1. Specific claims that could be verified (list each)
2. Data points or statistics mentioned (list each)
3. Assumptions being made (list each)

TEXT:
{query}

Format:
CLAIMS:
- [claim 1]
- [claim 2]

DATA POINTS:
- [data 1]
- [data 2]

ASSUMPTIONS:
- [assumption 1]
- [assumption 2]"""

            try:
                extract_response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=extraction_prompt,
                    config=types.GenerateContentConfig(temperature=0.2, max_output_tokens=500)
                )
                extracted_text = extract_response.text
            except Exception as e:
                extracted_text = f"Extraction failed: {e}"

        else:
            extracted_text = f"Claims: {claims}\nData: {data_points}"

        # Validation assessment
        validation_prompt = f"""You are a validation expert applying the "Camera Test" and fact-checking methodology.

CONTENT TO VALIDATE:
{extracted_text}

For each item, assess:
1. **Camera Test**: Could a camera record this? Is it observable fact or interpretation?
2. **Verifiability**: Can this be independently verified?
3. **Source Quality**: What source would confirm/refute this?
4. **Risk Level**: HIGH/MEDIUM/LOW - how risky is it to assume this is true?

Provide a structured validation report with:
- Items that PASS validation (grounded in observable data)
- Items that NEED VERIFICATION (claims requiring evidence)
- Items that FAIL validation (interpretations stated as facts)
- Recommended verification steps"""

        try:
            validation_response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=validation_prompt,
                config=types.GenerateContentConfig(
                    system_instruction="You are a rigorous data validation expert. Apply strict evidentiary standards.",
                    temperature=0.3,
                    max_output_tokens=800
                )
            )

            return {
                "success": True,
                "validation_report": validation_response.text,
                "extracted_items": extracted_text,
                "methodology": "Camera Test + DIKW Validation"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "validation_report": "",
                "extracted_items": extracted_text
            }


class AnalysisAgent(BackgroundAgent):
    """
    Analysis Agent - Processes data and identifies patterns.

    Capabilities:
    - Pattern recognition in text/data
    - Trend identification
    - Comparative analysis
    - Structured data extraction
    """

    def __init__(self):
        super().__init__(
            name="Analysis Agent",
            description="Processes data, identifies patterns, and performs structured analysis"
        )

    async def run(self, query: str, context: dict = None) -> dict:
        """Execute analysis workflow."""

        analysis_type = context.get("type", "general") if context else "general"

        analysis_prompt = f"""Perform a structured analysis on this content:

{query}

Provide:
1. **Key Patterns**: What patterns or trends do you observe?
2. **Data Points**: Quantifiable elements mentioned
3. **Relationships**: How do elements connect to each other?
4. **Gaps**: What information is missing?
5. **Insights**: Non-obvious conclusions from the data

Format your response as a structured analysis report."""

        try:
            analysis_response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=analysis_prompt,
                config=types.GenerateContentConfig(
                    temperature=0.4,
                    max_output_tokens=800
                )
            )

            return {
                "success": True,
                "analysis": analysis_response.text,
                "type": analysis_type
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "analysis": ""
            }


# === Background Agent Registry ===
BACKGROUND_AGENTS = {
    "research": ResearchAgent(),
    "validation": ValidationAgent(),
    "analysis": AnalysisAgent(),
}


# === Enhanced Multi-Agent Workflow with Background Agents ===

async def run_enhanced_workflow(
    query: str,
    conversation_agents: List[str] = None,
    background_agents: List[str] = None,
    mode: str = "parallel"
) -> dict:
    """
    Run a workflow combining conversation agents and background agents.

    Args:
        query: User's question
        conversation_agents: PWS methodology agents (larry, redteam, etc.)
        background_agents: Tool agents (research, validation, analysis)
        mode: "parallel" or "sequential"

    Returns:
        Combined results from all agents
    """

    results = {
        "query": query,
        "conversation_responses": {},
        "background_results": {},
        "synthesis": ""
    }

    # Run background agents first to gather data
    if background_agents:
        bg_tasks = []
        for bg_id in background_agents:
            if bg_id in BACKGROUND_AGENTS:
                bg_tasks.append((bg_id, BACKGROUND_AGENTS[bg_id].run(query)))

        if bg_tasks:
            bg_results = await asyncio.gather(*[t[1] for t in bg_tasks])
            for (bg_id, _), result in zip(bg_tasks, bg_results):
                results["background_results"][bg_id] = result

    # Build context from background agent results
    bg_context = ""
    for bg_id, bg_result in results["background_results"].items():
        if bg_result.get("success"):
            agent_name = BACKGROUND_AGENTS[bg_id].name
            if bg_id == "research":
                bg_context += f"\n\n**{agent_name} Findings:**\n{bg_result.get('findings', '')}"
            elif bg_id == "validation":
                bg_context += f"\n\n**{agent_name} Report:**\n{bg_result.get('validation_report', '')}"
            elif bg_id == "analysis":
                bg_context += f"\n\n**{agent_name}:**\n{bg_result.get('analysis', '')}"

    # Run conversation agents with background context
    if conversation_agents:
        enhanced_query = query
        if bg_context:
            enhanced_query = f"{query}\n\n---\nBACKGROUND RESEARCH:\n{bg_context}"

        conv_result = await run_multi_agent_workflow(
            enhanced_query,
            agents=conversation_agents,
            mode=mode
        )
        results["conversation_responses"] = conv_result.get("agent_responses", {})
        results["synthesis"] = conv_result.get("synthesis", "")

    return results


# === Preset Workflows ===

async def full_analysis_with_research(query: str) -> dict:
    """
    Complete analysis: Research → Validate → Multiple Agents → Synthesize
    """
    return await run_enhanced_workflow(
        query,
        conversation_agents=["larry", "redteam", "ackoff"],
        background_agents=["research", "validation"],
        mode="sequential"
    )


async def validated_decision(query: str) -> dict:
    """
    For decision validation: Validate → Ackoff → Red Team → Synthesis
    """
    return await run_enhanced_workflow(
        query,
        conversation_agents=["ackoff", "redteam"],
        background_agents=["validation"],
        mode="sequential"
    )


async def research_and_explore(query: str) -> dict:
    """
    For exploration: Research → TTA → Larry → Synthesis
    """
    return await run_enhanced_workflow(
        query,
        conversation_agents=["tta", "larry"],
        background_agents=["research"],
        mode="sequential"
    )
