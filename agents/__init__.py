# Mindrian Multi-Agent System
# LangGraph-based orchestration for complex workflows

from .multi_agent_graph import (
    # Core workflow functions
    run_multi_agent_workflow,
    run_multi_agent_with_steps,  # Chainlit-visualized version
    visualize_langgraph_execution,  # Generic LangGraph visualizer

    # Convenience workflows
    quick_analysis,
    comprehensive_analysis,
    stress_test,

    # Agent registries
    AGENTS,
    BACKGROUND_AGENTS,

    # Check for LangGraph availability
    LANGGRAPH_AVAILABLE,
)

__all__ = [
    "run_multi_agent_workflow",
    "run_multi_agent_with_steps",
    "visualize_langgraph_execution",
    "quick_analysis",
    "comprehensive_analysis",
    "stress_test",
    "AGENTS",
    "BACKGROUND_AGENTS",
    "LANGGRAPH_AVAILABLE",
]
