"""
Unified Agent Registry - UI Layer
==================================

Bridges the existing agent_registry.py (orchestration-focused) with UI concerns
(BOTS dict, AGENT_TRIGGERS, chat profiles, starters, switch callbacks).

One registration → appears everywhere:
- Chat profile dropdown
- Conversation starters
- BOTS dict (system prompt, welcome message, etc.)
- AGENT_TRIGGERS (keyword-based agent suggestions)
- Multi-agent graph (AGENTS dict)
- Switch callbacks (generic handler)

Usage:
    from protocols.unified_registry import (
        generate_bots_dict,
        generate_agent_triggers,
        generate_chat_profiles,
        generate_starters,
        generate_multi_agent_dict,
        handle_generic_switch,
    )

    BOTS = generate_bots_dict()
    AGENT_TRIGGERS = generate_agent_triggers()
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

from .agent_registry import (
    AgentRole,
    AgentCapability,
    AgentConfig,
    get_agent_config,
    get_all_agents,
    AGENT_REGISTRY,
)


# ============================================================================
# UI AGENT CONFIG
# ============================================================================

@dataclass
class UIAgentConfig:
    """
    UI-specific configuration for an agent.

    Extends the orchestration-focused AgentConfig with fields needed for
    the Chainlit UI layer: welcome messages, starters, icons, prompts, etc.
    """

    # Identity (must match agent_registry ID)
    id: str
    name: str
    description: str
    icon: str = "/public/icons/explore.svg"  # SVG path for chat profile
    emoji: str = "🤖"

    # Prompt reference (dotted import path or the prompt object itself)
    system_prompt: Any = None  # The actual prompt string or reference

    # UI behavior
    has_phases: bool = False
    simple_mode: bool = False
    welcome: str = ""

    # Chat profile visibility
    show_in_profiles: bool = True  # Show in chat profile dropdown
    profile_order: int = 100       # Lower = higher in dropdown

    # Conversation starters (list of dicts with label, message, icon)
    starters: List[Dict[str, str]] = field(default_factory=list)

    # Discovery (for agent suggestion system)
    trigger_keywords: List[str] = field(default_factory=list)
    trigger_description: str = ""

    # Orchestration tags (for workflow recipe matching)
    orchestration_tags: List[str] = field(default_factory=list)

    # Multi-agent role description
    agent_role_description: str = ""


# ============================================================================
# UI REGISTRY
# ============================================================================

_UI_REGISTRY: Dict[str, UIAgentConfig] = {}


def register_ui_agent(config: UIAgentConfig) -> None:
    """Register an agent's UI configuration."""
    _UI_REGISTRY[config.id] = config


def get_ui_config(agent_id: str) -> Optional[UIAgentConfig]:
    """Get UI configuration for an agent."""
    return _UI_REGISTRY.get(agent_id)


def get_all_ui_agents() -> Dict[str, UIAgentConfig]:
    """Get all registered UI agents."""
    return _UI_REGISTRY.copy()


# ============================================================================
# GENERATORS — Produce dicts compatible with existing code
# ============================================================================

def generate_bots_dict() -> Dict[str, Dict[str, Any]]:
    """
    Generate BOTS-compatible dict from UI registry.

    Output matches the existing BOTS dict structure expected by mindrian_chat.py:
    {
        "agent_id": {
            "name": str,
            "icon": str,
            "emoji": str,
            "description": str,
            "system_prompt": str,
            "has_phases": bool,
            "simple_mode": bool,
            "welcome": str,
        }
    }
    """
    bots = {}
    for agent_id, ui_config in _UI_REGISTRY.items():
        if not ui_config.system_prompt:
            continue  # Skip agents without prompts (service agents)

        bot_entry = {
            "name": ui_config.name,
            "icon": ui_config.icon,
            "emoji": ui_config.emoji,
            "description": ui_config.description,
            "system_prompt": ui_config.system_prompt,
            "has_phases": ui_config.has_phases,
            "welcome": ui_config.welcome,
        }

        if ui_config.simple_mode:
            bot_entry["simple_mode"] = True

        bots[agent_id] = bot_entry

    return bots


def generate_agent_triggers() -> Dict[str, Dict[str, Any]]:
    """
    Generate AGENT_TRIGGERS-compatible dict from UI registry.

    Output matches the existing AGENT_TRIGGERS structure:
    {
        "agent_id": {
            "keywords": List[str],
            "description": str,
        }
    }
    """
    triggers = {}
    for agent_id, ui_config in _UI_REGISTRY.items():
        if not ui_config.trigger_keywords:
            continue

        triggers[agent_id] = {
            "keywords": ui_config.trigger_keywords,
            "description": ui_config.trigger_description or ui_config.description,
        }

    return triggers


def generate_multi_agent_dict() -> Dict[str, Dict[str, Any]]:
    """
    Generate AGENTS-compatible dict for multi_agent_graph.py.

    Output matches the existing AGENTS structure:
    {
        "agent_id": {
            "name": str,
            "prompt": str,
            "role": str,
        }
    }
    """
    agents = {}
    for agent_id, ui_config in _UI_REGISTRY.items():
        if not ui_config.system_prompt:
            continue
        if not ui_config.agent_role_description:
            continue

        agents[agent_id] = {
            "name": ui_config.name,
            "prompt": ui_config.system_prompt,
            "role": ui_config.agent_role_description,
        }

    return agents


def generate_chat_profiles() -> List[Dict[str, Any]]:
    """
    Generate chat profile data sorted by profile_order.

    Returns list of dicts with: id, name, description, icon
    (Caller converts to cl.ChatProfile objects)
    """
    profiles = []
    for agent_id, ui_config in sorted(
        _UI_REGISTRY.items(),
        key=lambda x: x[1].profile_order
    ):
        if not ui_config.show_in_profiles:
            continue
        if not ui_config.system_prompt:
            continue

        profiles.append({
            "id": agent_id,
            "name": ui_config.name,
            "description": ui_config.description,
            "icon": ui_config.icon,
        })

    return profiles


def generate_starters() -> Dict[str, List[Dict[str, str]]]:
    """
    Generate STARTERS-compatible dict from UI registry.

    Output: { "agent_id": [{"label": str, "message": str, "icon": str}, ...] }
    """
    starters = {}
    for agent_id, ui_config in _UI_REGISTRY.items():
        if ui_config.starters:
            starters[agent_id] = ui_config.starters

    return starters


# ============================================================================
# GENERIC SWITCH HANDLER
# ============================================================================

async def handle_generic_switch(agent_id: str):
    """
    Generic agent switch handler — replaces 15+ individual switch_to_* callbacks.

    Usage in Chainlit:
        @cl.action_callback("switch_agent")
        async def on_switch_agent(action: cl.Action):
            agent_id = action.payload.get("agent_id")
            if agent_id:
                await handle_generic_switch(agent_id)
    """
    # Import handle_agent_switch from the main module at runtime to avoid circular import
    import importlib
    main_module = importlib.import_module("mindrian_chat")
    await main_module.handle_agent_switch(agent_id)


# ============================================================================
# QUERY HELPERS
# ============================================================================

def get_agent_display_name(agent_id: str) -> str:
    """Get the display name for an agent from UI registry, falling back to orchestration registry."""
    ui = get_ui_config(agent_id)
    if ui:
        return ui.name

    orch = get_agent_config(agent_id)
    if orch:
        return orch.name

    return agent_id.replace("_", " ").title()


def get_agents_for_orchestration_tag(tag: str) -> List[str]:
    """Find agents that match an orchestration tag."""
    matches = []
    for agent_id, ui_config in _UI_REGISTRY.items():
        if tag in ui_config.orchestration_tags:
            matches.append(agent_id)
    return matches


def get_agent_role_description(agent_id: str) -> str:
    """Get role description for multi-agent context."""
    ui = get_ui_config(agent_id)
    if ui and ui.agent_role_description:
        return ui.agent_role_description

    # Fall back to orchestration registry
    orch = get_agent_config(agent_id)
    if orch:
        return orch.description

    return f"Expert agent: {agent_id}"
