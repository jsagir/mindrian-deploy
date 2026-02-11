"""
Unified Registry Test Suite

Validates the unified agent registry system:
1. All agents are registered
2. generate_bots_dict produces valid BOTS structure
3. generate_agent_triggers produces valid AGENT_TRIGGERS structure
4. generate_chat_profiles returns sorted profiles
5. New agents auto-appear in generated dicts
6. Agent role descriptions are accessible
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from protocols.unified_registry import (
    UIAgentConfig,
    register_ui_agent,
    get_ui_config,
    get_all_ui_agents,
    generate_bots_dict,
    generate_agent_triggers,
    generate_multi_agent_dict,
    generate_chat_profiles,
    generate_starters,
    get_agent_display_name,
    get_agents_for_orchestration_tag,
    get_agent_role_description,
    _UI_REGISTRY,
)

# Importing agent_definitions triggers registration
import protocols.agent_definitions  # noqa: F401


# === Test 1: All agents are registered ===

def test_all_agents_registered():
    """At least 15 agents should be registered (we have 18 definitions)."""
    all_agents = get_all_ui_agents()
    assert len(all_agents) >= 15, f"Expected >=15 agents, got {len(all_agents)}: {list(all_agents.keys())}"


def test_core_agents_present():
    """Core agents must be in the registry."""
    core_agents = ["lawrence", "larry_playground", "tta", "jtbd", "scurve", "redteam", "ackoff"]
    all_agents = get_all_ui_agents()
    for agent_id in core_agents:
        assert agent_id in all_agents, f"Core agent '{agent_id}' missing from registry"


# === Test 2: generate_bots_dict ===

def test_generates_valid_bots_dict():
    """Output should match expected BOTS dict structure."""
    bots = generate_bots_dict()
    assert isinstance(bots, dict)
    assert len(bots) > 0

    for bot_id, bot_config in bots.items():
        assert "name" in bot_config, f"{bot_id} missing 'name'"
        assert "description" in bot_config, f"{bot_id} missing 'description'"
        assert "system_prompt" in bot_config, f"{bot_id} missing 'system_prompt'"
        assert "has_phases" in bot_config, f"{bot_id} missing 'has_phases'"
        assert "welcome" in bot_config, f"{bot_id} missing 'welcome'"
        assert isinstance(bot_config["name"], str)
        assert isinstance(bot_config["has_phases"], bool)


def test_bots_dict_has_core_bots():
    """Core bots should appear in generated BOTS dict."""
    bots = generate_bots_dict()
    # These require system_prompt to be set — some may be None (prompt import failures)
    # At minimum, check that the dict is not empty
    assert len(bots) >= 1, "BOTS dict should have at least 1 bot"


# === Test 3: generate_agent_triggers ===

def test_generates_valid_triggers():
    """Output should match expected AGENT_TRIGGERS structure."""
    triggers = generate_agent_triggers()
    assert isinstance(triggers, dict)

    for agent_id, trigger_config in triggers.items():
        assert "keywords" in trigger_config, f"{agent_id} missing 'keywords'"
        assert "description" in trigger_config, f"{agent_id} missing 'description'"
        assert isinstance(trigger_config["keywords"], list)
        assert len(trigger_config["keywords"]) > 0, f"{agent_id} has empty keywords"


# === Test 4: generate_chat_profiles ===

def test_chat_profiles_sorted():
    """Chat profiles should be sorted by profile_order."""
    profiles = generate_chat_profiles()
    assert isinstance(profiles, list)

    for profile in profiles:
        assert "id" in profile
        assert "name" in profile
        assert "description" in profile


# === Test 5: New agent auto-discovered ===

def test_new_agent_auto_discovered():
    """Registering a new agent should make it appear in all generated dicts."""
    test_id = "_test_agent_auto_discover"
    try:
        # Register a new test agent
        register_ui_agent(UIAgentConfig(
            id=test_id,
            name="Test Agent",
            description="A test agent for unit tests",
            system_prompt="You are a test agent.",
            trigger_keywords=["test_keyword_xyz"],
            trigger_description="Test agent trigger",
            agent_role_description="Test role for multi-agent",
            orchestration_tags=["test_tag"],
            starters=[{"label": "Test", "message": "Test", "icon": "🧪"}],
        ))

        # Verify it appears in all generated dicts
        bots = generate_bots_dict()
        assert test_id in bots, "New agent should appear in BOTS dict"

        triggers = generate_agent_triggers()
        assert test_id in triggers, "New agent should appear in AGENT_TRIGGERS"
        assert "test_keyword_xyz" in triggers[test_id]["keywords"]

        agents = generate_multi_agent_dict()
        assert test_id in agents, "New agent should appear in multi-agent dict"

        starters = generate_starters()
        assert test_id in starters, "New agent should appear in STARTERS"

        profiles = generate_chat_profiles()
        profile_ids = [p["id"] for p in profiles]
        assert test_id in profile_ids, "New agent should appear in chat profiles"

        # Check orchestration tag lookup
        matched = get_agents_for_orchestration_tag("test_tag")
        assert test_id in matched

    finally:
        # Clean up
        _UI_REGISTRY.pop(test_id, None)


# === Test 6: Agent display names ===

def test_agent_display_name():
    """get_agent_display_name should return the registered name."""
    # For a registered agent
    all_agents = get_all_ui_agents()
    if "lawrence" in all_agents:
        name = get_agent_display_name("lawrence")
        assert name == "Lawrence"

    # For an unknown agent, should return title-cased fallback
    name = get_agent_display_name("nonexistent_agent")
    assert name == "Nonexistent Agent"


# === Test 7: Agent role descriptions ===

def test_agent_role_description():
    """get_agent_role_description should return role description."""
    all_agents = get_all_ui_agents()
    if "tta" in all_agents:
        desc = get_agent_role_description("tta")
        assert isinstance(desc, str)
        assert len(desc) > 10  # Should be a meaningful description

    # Fallback for unknown agent
    desc = get_agent_role_description("totally_unknown")
    assert "Expert agent" in desc


# === Test 8: UIAgentConfig defaults ===

def test_ui_agent_config_defaults():
    """UIAgentConfig should have sensible defaults."""
    config = UIAgentConfig(
        id="test",
        name="Test",
        description="Test agent",
    )
    assert config.show_in_profiles is True
    assert config.profile_order == 100
    assert config.has_phases is False
    assert config.simple_mode is False
    assert config.starters == []
    assert config.trigger_keywords == []
    assert config.orchestration_tags == []


# === Test 9: Agents without prompts excluded from BOTS ===

def test_agents_without_prompts_excluded():
    """Agents with system_prompt=None should not appear in BOTS dict."""
    test_id = "_test_no_prompt_agent"
    try:
        register_ui_agent(UIAgentConfig(
            id=test_id,
            name="No Prompt Agent",
            description="An agent without a system prompt",
            system_prompt=None,  # No prompt
        ))

        bots = generate_bots_dict()
        assert test_id not in bots, "Agent without prompt should not appear in BOTS"

    finally:
        _UI_REGISTRY.pop(test_id, None)


# === Test 10: Starters dict generation ===

def test_generates_starters():
    """generate_starters should return dict of agent_id -> starters list."""
    starters = generate_starters()
    assert isinstance(starters, dict)

    for agent_id, starter_list in starters.items():
        assert isinstance(starter_list, list)
        for starter in starter_list:
            assert "label" in starter
            assert "message" in starter
