"""
Protocols Package - Agent Communication Standards

A2A Protocol: Agent-to-agent handoff via structured Markdown files
Context Journal: Living document that evolves with conversation
Agent Registry: Centralized agent registration with capabilities and routing
Triple Mode: Entry point detection, semantic grounding, and exploration tracking
Context Manager: Artifacts vs Frames separation for multi-agent context
Phase Manager: Directed graph phase transitions with explicit states
"""

from .context_manager import (
    Artifact,
    Frame,
    ContextManager,
    ArtifactType,
    FrameType,
    ValidationSource,
)

from .phase_manager import (
    Phase,
    PhaseTransition,
    PhaseManager,
    ALLOWED_TRANSITIONS,
    suggest_phase_from_classification,
)

from .classifier import (
    Classification,
    CynefinDomain,
    PWSType,
    classify,
    classify_with_logging,
    get_routing_recommendation,
    CLASSIFIER_PROMPT,
    TEST_CASES,
    run_test_cases,
)

from .agent_registry import (
    AgentRole,
    AgentCapability,
    AgentConfig,
    register_agent,
    get_agent_config,
    get_agents_for_entry_point,
    get_agents_for_venture_stage,
    get_agents_by_role,
    get_agents_with_capability,
    can_agent_call,
    get_default_capabilities,
    create_agent_with_defaults,
    AGENT_REGISTRY,
)

from .triple_mode import (
    init_triple_mode_session,
    auto_detect_entry_point,
    extract_and_update_progress,
    check_semantic_grounding,
    handle_entry_point_selection,
    handle_mode_or_stage,
    handle_grounding_response,
    show_entry_point_selector,
    show_exploration_progress_sidebar,
    show_grounding_prompt,
    get_entry_point_buttons,
    get_coaching_hint_for_message,
    get_triple_mode_state,
    restore_triple_mode_state,
    persist_triple_mode_state,
    TRIPLE_MODE_ENABLED,
    LANGEXTRACT_ENABLED,
)

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
    # Context Manager (Artifacts vs Frames)
    'Artifact',
    'Frame',
    'ContextManager',
    'ArtifactType',
    'FrameType',
    'ValidationSource',
    # Phase Manager (Directed Graph Transitions)
    'Phase',
    'PhaseTransition',
    'PhaseManager',
    'ALLOWED_TRANSITIONS',
    'suggest_phase_from_classification',
    # Classifier (Two-Stage: Cynefin + PWS)
    'Classification',
    'CynefinDomain',
    'PWSType',
    'classify',
    'classify_with_logging',
    'get_routing_recommendation',
    'CLASSIFIER_PROMPT',
    'TEST_CASES',
    'run_test_cases',
    # Agent Registry
    'AgentRole',
    'AgentCapability',
    'AgentConfig',
    'register_agent',
    'get_agent_config',
    'get_agents_for_entry_point',
    'get_agents_for_venture_stage',
    'get_agents_by_role',
    'get_agents_with_capability',
    'can_agent_call',
    'get_default_capabilities',
    'create_agent_with_defaults',
    'AGENT_REGISTRY',
    # Triple Mode
    'init_triple_mode_session',
    'auto_detect_entry_point',
    'extract_and_update_progress',
    'check_semantic_grounding',
    'handle_entry_point_selection',
    'handle_mode_or_stage',
    'handle_grounding_response',
    'show_entry_point_selector',
    'show_exploration_progress_sidebar',
    'show_grounding_prompt',
    'get_entry_point_buttons',
    'get_coaching_hint_for_message',
    'get_triple_mode_state',
    'restore_triple_mode_state',
    'persist_triple_mode_state',
    'TRIPLE_MODE_ENABLED',
    'LANGEXTRACT_ENABLED',
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
