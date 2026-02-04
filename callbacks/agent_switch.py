"""
Agent Switching Callbacks
=========================

All callbacks for switching between Mindrian bots/agents.
Extracted from mindrian_chat.py lines 4114-4437.
"""

import chainlit as cl
from typing import Optional

# =============================================================================
# Agent Switch Mapping
# =============================================================================

AGENT_SWITCH_CALLBACKS = {
    "switch_to_tta": "tta",
    "switch_to_jtbd": "jtbd",
    "switch_to_scurve": "scurve",
    "switch_to_redteam": "redteam",
    "switch_to_ackoff": "ackoff",
    "switch_to_larry": "lawrence",
    "switch_to_bono": "bono",
    "switch_to_knowns": "knowns",
    "switch_to_nested_hierarchies": "nested_hierarchies",
    "switch_to_domain": "domain",
    "switch_to_investment": "investment",
    "switch_to_scenario": "scenario",
    "switch_to_validation": "validation",
    "switch_to_beautiful_question": "beautiful_question",
}


# =============================================================================
# Core Agent Switch Handler
# =============================================================================

async def handle_agent_switch(new_agent_id: str):
    """
    Handle switching to a new agent while preserving context.

    This function:
    1. Preserves conversation history
    2. Updates session state
    3. Shows welcome message for new agent
    4. Triggers appropriate UI updates

    Args:
        new_agent_id: The bot_id to switch to (e.g., "tta", "jtbd", "lawrence")
    """
    # Import here to avoid circular imports
    from mindrian_chat import (
        BOTS, context_store, get_context_key,
        create_workshop_roadmap, get_core_action_buttons,
        _get_phases_for_bot,
    )

    # Get current state
    current_bot_id = cl.user_session.get("bot_id", "lawrence")
    history = cl.user_session.get("history", [])

    # Don't switch if already on this agent
    if current_bot_id == new_agent_id:
        await cl.Message(content=f"You're already talking to {BOTS.get(new_agent_id, {}).get('name', new_agent_id)}!").send()
        return

    # Get new bot config
    new_bot = BOTS.get(new_agent_id)
    if not new_bot:
        await cl.Message(content=f"Unknown agent: {new_agent_id}").send()
        return

    # Save current context before switching
    context_key = get_context_key()
    context_store[context_key] = {
        "bot_id": new_agent_id,
        "history": history.copy(),
        "phases": cl.user_session.get("phases", []),
        "current_phase": cl.user_session.get("current_phase", 0),
    }

    # Update session state
    cl.user_session.set("bot", new_bot)
    cl.user_session.set("bot_id", new_agent_id)
    cl.user_session.set("chat_profile", new_agent_id)
    cl.user_session.set("previous_bot", current_bot_id)

    # Set context handoff flag for the new bot to acknowledge
    previous_bot_name = BOTS.get(current_bot_id, {}).get("name", current_bot_id)
    cl.user_session.set("context_handoff", f"Switched from {previous_bot_name}")

    # Initialize phases if new bot has phases
    phases = _get_phases_for_bot(new_agent_id)
    if phases:
        cl.user_session.set("phases", phases)
        cl.user_session.set("current_phase", 0)
        await create_workshop_roadmap(new_agent_id)

    # Build actions for new bot
    actions = get_core_action_buttons(include_example=new_bot.get("has_phases", False))

    # Get welcome message
    welcome = new_bot.get("welcome", f"Hello! I'm {new_bot.get('name', new_agent_id)}. How can I help?")

    # Add context handoff notice
    handoff_notice = f"\n\n*📋 I have access to your previous conversation with {previous_bot_name} ({len(history)} messages).*"

    await cl.Message(
        content=f"{welcome}{handoff_notice}",
        actions=actions,
    ).send()


# =============================================================================
# Individual Switch Callbacks
# =============================================================================

@cl.action_callback("switch_to_tta")
async def on_switch_to_tta(action: cl.Action):
    await handle_agent_switch("tta")


@cl.action_callback("switch_to_jtbd")
async def on_switch_to_jtbd(action: cl.Action):
    await handle_agent_switch("jtbd")


@cl.action_callback("switch_to_scurve")
async def on_switch_to_scurve(action: cl.Action):
    await handle_agent_switch("scurve")


@cl.action_callback("switch_to_redteam")
async def on_switch_to_redteam(action: cl.Action):
    await handle_agent_switch("redteam")


@cl.action_callback("switch_to_ackoff")
async def on_switch_to_ackoff(action: cl.Action):
    await handle_agent_switch("ackoff")


@cl.action_callback("switch_to_larry")
async def on_switch_to_larry(action: cl.Action):
    await handle_agent_switch("lawrence")


@cl.action_callback("switch_to_bono")
async def on_switch_to_bono(action: cl.Action):
    await handle_agent_switch("bono")


@cl.action_callback("switch_to_knowns")
async def on_switch_to_knowns(action: cl.Action):
    await handle_agent_switch("knowns")


@cl.action_callback("switch_to_nested_hierarchies")
async def on_switch_to_nested_hierarchies(action: cl.Action):
    await handle_agent_switch("nested_hierarchies")


@cl.action_callback("switch_to_domain")
async def on_switch_to_domain(action: cl.Action):
    await handle_agent_switch("domain")


@cl.action_callback("switch_to_investment")
async def on_switch_to_investment(action: cl.Action):
    await handle_agent_switch("investment")


@cl.action_callback("switch_to_scenario")
async def on_switch_to_scenario(action: cl.Action):
    await handle_agent_switch("scenario")


@cl.action_callback("switch_to_validation")
async def on_switch_to_validation(action: cl.Action):
    await handle_agent_switch("validation")


@cl.action_callback("switch_to_beautiful_question")
async def on_switch_to_beautiful_question(action: cl.Action):
    await handle_agent_switch("beautiful_question")


# =============================================================================
# Extreme Opposition Mode (Red Team specific)
# =============================================================================

@cl.action_callback("toggle_extreme_opposition")
async def on_toggle_extreme_opposition(action: cl.Action):
    """Toggle Extreme Opposition mode for Red Team bot."""
    bot = cl.user_session.get("bot", {})

    # Only works for Red Team
    if bot.get("name") != "Red Team":
        await cl.Message(content="⚠️ Extreme Opposition mode is only available in Red Team.").send()
        return

    # Toggle the mode
    extreme_mode = not bot.get("extreme_opposition_mode", False)
    bot["extreme_opposition_mode"] = extreme_mode

    # Update system prompt
    from prompts.redteam import get_redteam_prompt
    bot["system_prompt"] = get_redteam_prompt(extreme_mode=extreme_mode)

    cl.user_session.set("bot", bot)

    # Notify user
    if extreme_mode:
        await cl.Message(
            content="🔴 **EXTREME OPPOSITION MODE ACTIVATED**\n\n"
                    "I'm now in pure opposition mode. I will:\n"
                    "- Contradict your main thesis\n"
                    "- Find counter-evidence for every claim\n"
                    "- Play strategic competitor\n"
                    "- Escalate edge cases\n"
                    "- Assume every assumption is wrong\n\n"
                    "*No mercy. No balanced views. Just the fatal flaw.*",
            actions=[
                cl.Action(
                    name="toggle_extreme_opposition",
                    payload={"action": "toggle"},
                    label="🟢 Return to Normal Mode",
                    description="Switch back to balanced Red Team analysis"
                )
            ]
        ).send()
    else:
        await cl.Message(
            content="🟢 **Normal Red Team Mode Restored**\n\n"
                    "I'm back to balanced devil's advocate mode:\n"
                    "- Challenge assumptions constructively\n"
                    "- Find weaknesses AND suggest fixes\n"
                    "- Stress-test ideas fairly\n\n"
                    "*Constructively brutal, but still helpful.*",
            actions=[
                cl.Action(
                    name="toggle_extreme_opposition",
                    payload={"action": "toggle"},
                    label="🔴 Activate Extreme Opposition",
                    description="Pure opposition mode - no mercy"
                )
            ]
        ).send()


# =============================================================================
# Registration Function
# =============================================================================

def register_agent_switch_callbacks():
    """
    Register all agent switch callbacks.

    Note: In Chainlit, callbacks are registered via decorators at import time.
    This function is a placeholder for any additional setup needed.
    """
    # Callbacks are auto-registered by decorators
    # This function can be used for any additional setup
    pass
