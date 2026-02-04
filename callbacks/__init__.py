"""
Mindrian Callbacks Module
=========================

Refactored action callbacks from mindrian_chat.py monolith.

Modules:
- agent_switch: Bot switching callbacks
- research: Research tool callbacks (arxiv, patents, trends, etc.)
- grading: Student grading system
- phase_navigation: Workshop phase callbacks
- media: Video, audiobook, export callbacks
- pipelines: LangGraph pipeline callbacks

Usage:
    from callbacks import register_all_callbacks
    register_all_callbacks()  # Call after Chainlit app is ready
"""

# Import all callback registration functions
from .agent_switch import (
    handle_agent_switch,
    register_agent_switch_callbacks,
    AGENT_SWITCH_CALLBACKS,
)

from .research import (
    register_research_callbacks,
    on_arxiv_search,
    on_patent_search,
    on_trends_search,
    on_govdata_search,
    on_dataset_search,
    on_news_search,
)

__all__ = [
    # Agent Switch
    "handle_agent_switch",
    "register_agent_switch_callbacks",
    "AGENT_SWITCH_CALLBACKS",
    # Research
    "register_research_callbacks",
    "on_arxiv_search",
    "on_patent_search",
    "on_trends_search",
    "on_govdata_search",
    "on_dataset_search",
    "on_news_search",
]


def register_all_callbacks():
    """
    Register all refactored callbacks.
    Call this once at app startup.
    """
    register_agent_switch_callbacks()
    register_research_callbacks()
    print("✅ Refactored callbacks registered")
