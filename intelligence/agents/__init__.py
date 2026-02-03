"""
Mindrian Intelligence Agents
============================
LangChain tool-calling agents and LangGraph orchestrators.

Agents:
- research_agent: Autonomous research with tool selection
- multi_agent: Multi-perspective analysis orchestrator
- workshop_manager: LangGraph workshop mode controller

Usage:
    from intelligence.agents import (
        run_research_agent,
        run_multi_agent_analysis,
        WorkshopManager,
    )

    # Research
    result = await run_research_agent("AI in education trends")

    # Multi-agent
    result = await run_multi_agent_analysis("Should I pivot?", "full")

    # Workshop
    manager = WorkshopManager("tta", session_id="user_123")
    result = await manager.process_message("Let's explore urban farming")
"""

from .research_agent import (
    run_research_agent,
    run_research_agent_sync,
    research_for_tta,
    research_for_validation,
    research_for_domain,
    create_research_agent,
)

from .multi_agent import (
    run_multi_agent_analysis,
    quick_analysis,
    research_and_explore,
    validated_decision,
    full_analysis,
    format_multi_agent_result,
    create_multi_agent_pipeline,
)

__all__ = [
    # Research Agent
    "run_research_agent",
    "run_research_agent_sync",
    "research_for_tta",
    "research_for_validation",
    "research_for_domain",
    "create_research_agent",
    # Multi-Agent
    "run_multi_agent_analysis",
    "quick_analysis",
    "research_and_explore",
    "validated_decision",
    "full_analysis",
    "format_multi_agent_result",
    "create_multi_agent_pipeline",
]
