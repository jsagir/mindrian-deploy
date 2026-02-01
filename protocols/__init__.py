"""
Protocols Package - Agent Communication Standards

A2A Protocol: Agent-to-agent handoff via structured Markdown files
Context Journal: Living document that evolves with conversation
"""

from .a2a_protocol import (
    A2AHandoff,
    HandoffType,
    HandoffPriority,
    ExtractedEntity,
    AgentTask,
    create_switch_handoff,
    create_delegate_handoff,
    create_return_handoff,
    save_handoff,
    load_handoff,
    inject_handoff_context,
    get_handoff_for_display,
    validate_handoff_frontmatter,
    get_handoff_schema,
)

from .context_journal import (
    ContextJournal,
    ThinkingStep,
    get_journal,
    log_thinking,
    log_switch,
    inject_journal_context,
    get_journal_entries_for_ui,
    create_journal_viewer_element,
)

__all__ = [
    # A2A Protocol
    'A2AHandoff',
    'HandoffType',
    'HandoffPriority',
    'ExtractedEntity',
    'AgentTask',
    'create_switch_handoff',
    'create_delegate_handoff',
    'create_return_handoff',
    'save_handoff',
    'load_handoff',
    'inject_handoff_context',
    'get_handoff_for_display',
    'validate_handoff_frontmatter',
    'get_handoff_schema',
    # Context Journal
    'ContextJournal',
    'ThinkingStep',
    'get_journal',
    'log_thinking',
    'log_switch',
    'inject_journal_context',
    'get_journal_entries_for_ui',
    'create_journal_viewer_element',
]
