"""
Research Agent - LangChain Tool-Calling Implementation
======================================================
Autonomous research agent that decides when/how to search.

Instead of hardcoded function calls, the agent reasons about:
- Which tools to use (web search, arxiv, patents, neo4j, etc.)
- What queries to construct
- How to synthesize findings

Uses LangChain's create_tool_calling_agent for autonomous tool selection.

Usage:
    from intelligence.agents import run_research_agent

    result = await run_research_agent(
        query="How can AI transform education?",
        context="User interested in K-12 applications"
    )
"""

import os
from typing import List, Dict, Any, Optional

# Import LangChain components
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain.agents import AgentExecutor, create_tool_calling_agent
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain_core.messages import HumanMessage, AIMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

# Import our tools
from intelligence.research_tools import ALL_RESEARCH_TOOLS, ALL_KNOWLEDGE_TOOLS


# =============================================================================
# RESEARCH AGENT PROMPT
# =============================================================================

RESEARCH_AGENT_PROMPT = """You are a PWS (Problems Worth Solving) Research Agent.

Your job is to autonomously research topics using the available tools to gather
comprehensive, evidence-based information.

## Your Approach

1. **Understand the Query**: What exactly does the user want to know?
2. **Plan Your Research**: Which tools will give the best answers?
3. **Execute Strategically**: Run searches, validate findings, cross-reference
4. **Synthesize Clearly**: Combine findings into actionable insights

## Available Tool Categories

**Web Research:**
- search_web: General web search for current information
- search_arxiv: Academic papers (AI, ML, physics, CS)
- search_patents: Innovations and prior art
- search_trends: Market trends and forecasts
- search_govdata: Official statistics (BLS, Census, FRED)
- search_datasets: Data repositories (Kaggle, HuggingFace)
- search_news: Recent news and developments

**Validation:**
- validate_assumption: Find both supporting AND contradicting evidence
- research_trend: Comprehensive trend analysis for TTA

**Knowledge Graph:**
- query_concepts: Find concept relationships in PWS knowledge
- query_frameworks: Get relevant PWS frameworks
- query_problem_context: Classify problem type and get approaches

## Guidelines

1. **Start broad, then narrow**: Begin with general search, then go specific
2. **Validate claims**: Use validate_assumption for key claims
3. **Check the knowledge graph**: See what PWS frameworks apply
4. **Cross-reference**: Don't rely on single sources
5. **Be honest about uncertainty**: Note when evidence is weak

## Output Format

After research, provide:
1. **Executive Summary** (2-3 sentences)
2. **Key Findings** (bullet points with sources)
3. **Evidence Quality** (what's well-supported vs needs validation)
4. **Recommended Next Steps** (actionable items)
5. **Related PWS Frameworks** (from knowledge graph)

{context}
"""


# =============================================================================
# AGENT CREATION
# =============================================================================

def create_research_agent(model: str = "gemini-2.0-flash"):
    """
    Create a tool-calling research agent.

    Args:
        model: The Gemini model to use.

    Returns:
        AgentExecutor configured for research.
    """
    if not LANGCHAIN_AVAILABLE:
        raise ImportError("LangChain not available. Install langchain and langchain-google-genai.")

    # Create LLM
    llm = ChatGoogleGenerativeAI(
        model=model,
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.3,
    )

    # Combine all tools
    tools = ALL_RESEARCH_TOOLS + ALL_KNOWLEDGE_TOOLS

    # Create prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", RESEARCH_AGENT_PROMPT),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    # Create agent
    agent = create_tool_calling_agent(llm, tools, prompt)

    # Create executor
    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=10,
        return_intermediate_steps=True,
        handle_parsing_errors=True,
    )

    return executor


# =============================================================================
# PUBLIC API
# =============================================================================

async def run_research_agent(
    query: str,
    context: str = "",
    chat_history: List[Dict] = None,
    model: str = "gemini-2.0-flash"
) -> Dict[str, Any]:
    """
    Run the research agent on a query.

    Args:
        query: The research question.
        context: Additional context (e.g., user background).
        chat_history: Optional conversation history.
        model: Gemini model to use.

    Returns:
        Dict with output, intermediate_steps, and tools_used.

    Example:
        result = await run_research_agent(
            query="What are the latest trends in vertical farming?",
            context="User is interested in urban agriculture startups"
        )
        print(result["output"])
    """
    if not LANGCHAIN_AVAILABLE:
        # Fallback to quick pipeline research (Claude-planned queries)
        try:
            from intelligence.pipelines.research_pipeline import quick_pipeline_research
            import asyncio
            result = await quick_pipeline_research(query, max_results=5)
            sources = result.get("sources", [])
            return {
                "output": f"Research results for: {query}\n\n" +
                          (result.get("answer", "") + "\n\n" if result.get("answer") else "") +
                          "\n".join([f"- {r.get('title')}: {r.get('content', '')[:200]}"
                                    for r in sources]),
                "intermediate_steps": [],
                "tools_used": ["quick_pipeline_research (fallback)"],
                "queries_planned": result.get("planned_queries", []),
            }
        except Exception:
            # Ultimate fallback to raw search
            from tools.tavily_search import search_web
            results = search_web(query, search_depth="advanced", max_results=5)
            return {
                "output": f"Basic search results for: {query}\n\n" +
                          "\n".join([f"- {r.get('title')}: {r.get('content', '')[:200]}"
                                    for r in results.get("results", [])]),
                "intermediate_steps": [],
                "tools_used": ["search_web (fallback)"]
            }

    try:
        # Create agent
        executor = create_research_agent(model)

        # Build context string
        context_str = f"\n\nAdditional Context: {context}" if context else ""

        # Convert chat history to messages
        history_messages = []
        if chat_history:
            for msg in chat_history[-5:]:  # Last 5 messages
                if msg.get("role") == "user":
                    history_messages.append(HumanMessage(content=msg.get("content", "")))
                else:
                    history_messages.append(AIMessage(content=msg.get("content", "")))

        # Run agent
        result = await executor.ainvoke({
            "input": query,
            "context": context_str,
            "chat_history": history_messages,
        })

        # Extract tools used
        tools_used = []
        for step in result.get("intermediate_steps", []):
            if hasattr(step[0], "tool"):
                tools_used.append(step[0].tool)

        return {
            "output": result.get("output", "No output generated"),
            "intermediate_steps": result.get("intermediate_steps", []),
            "tools_used": list(set(tools_used)),
        }

    except Exception as e:
        return {
            "output": f"Research agent error: {str(e)}",
            "intermediate_steps": [],
            "tools_used": [],
            "error": str(e)
        }


def run_research_agent_sync(
    query: str,
    context: str = "",
    model: str = "gemini-2.0-flash"
) -> Dict[str, Any]:
    """
    Synchronous version of run_research_agent.

    For use in non-async contexts.
    """
    import asyncio
    return asyncio.run(run_research_agent(query, context, model=model))


# =============================================================================
# SPECIALIZED RESEARCH FUNCTIONS
# =============================================================================

async def research_for_tta(trend_topic: str) -> Dict[str, Any]:
    """
    Specialized research for Trending to the Absurd analysis.

    Focuses on trend data, growth trajectories, and extrapolation points.
    """
    context = """
Focus on:
1. Current statistics and growth rates
2. Historical trajectory (where did this come from?)
3. Expert forecasts and predictions
4. Potential disruption factors
5. Absurd endpoint scenarios (what if this trend continues exponentially?)

Use research_trend and search_trends tools heavily.
"""
    return await run_research_agent(
        query=f"Analyze the trend: {trend_topic}. Find growth data, forecasts, and potential absurd endpoints.",
        context=context
    )


async def research_for_validation(assumption: str) -> Dict[str, Any]:
    """
    Specialized research for assumption validation (Camera Test).

    Finds both supporting AND contradicting evidence.
    """
    context = """
This is a Camera Test validation. You MUST:
1. Find evidence SUPPORTING the assumption
2. Find evidence CONTRADICTING the assumption
3. Note the quality of each piece of evidence
4. Be honest about which side has stronger support

Use validate_assumption tool and be rigorous.
"""
    return await run_research_agent(
        query=f"Validate this assumption: {assumption}",
        context=context
    )


async def research_for_domain(domain_description: str) -> Dict[str, Any]:
    """
    Specialized research for domain exploration.

    Investigates a problem domain for PWS analysis.
    """
    context = """
Explore this domain for Problems Worth Solving:
1. Who are the stakeholders?
2. What problems exist?
3. What solutions have been tried?
4. What gaps remain?
5. What frameworks apply?

Use knowledge graph tools to find relevant PWS frameworks.
"""
    return await run_research_agent(
        query=f"Explore this domain for PWS analysis: {domain_description}",
        context=context
    )
