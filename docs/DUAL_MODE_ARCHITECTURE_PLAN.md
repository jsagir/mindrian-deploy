# Mindrian Dual-Mode Architecture: Implementation Plan

**Date:** 2026-02-02
**Status:** Planning
**Author:** Claude Opus 4.5 (Implementation Design)
**Based On:** Manus AI Research Report

---

## Executive Summary

This document presents a **refined implementation strategy** for Mindrian's dual-mode architecture. After deep analysis of the codebase, I recommend a **session-level mode approach** rather than duplicating bot entries. This approach:

1. **Preserves backward compatibility** - Existing bots work unchanged
2. **Reduces complexity** - 14 bots remain 14 bots (not 28)
3. **Leverages existing patterns** - Extends `simple_mode` naturally
4. **Enables gradual rollout** - Add mode support to bots incrementally
5. **Maintains context** - Session state preserved across mode switches

---

## Part 1: Critical Analysis of Manus Proposal

### What Manus Proposed

```python
# Manus: Duplicate entries per bot
BOTS = {
    "tta_workshop": { "mode": "structured", "base_agent": "tta", ... },
    "tta_sandbox": { "mode": "free_chat", "base_agent": "tta", ... },
    # Result: 28+ entries for 14 agents
}
```

### Why This Is Problematic

| Issue | Impact | Risk Level |
|-------|--------|------------|
| **2x bot entries** | 28 entries instead of 14; maintenance burden doubles | HIGH |
| **Duplicate prompts** | Two prompts per bot; sync issues | HIGH |
| **Context fragmentation** | Switching modes = switching bots; history reset | MEDIUM |
| **UI complexity** | BotModeSwitcher needs grouping logic | MEDIUM |
| **Phase data split** | Workshop progress separate from sandbox | HIGH |

### Better Approach: Session-Level Modes

```python
# Recommended: Single entry with mode support
BOTS = {
    "tta": {
        "name": "Trending to the Absurd",
        "system_prompt": TTA_PROMPT,  # One prompt
        "has_phases": True,
        "supports_modes": ["workshop", "sandbox"],  # NEW
        "default_mode": "workshop",  # NEW
        ...
    },
}

# Mode stored in session, not bot identity
cl.user_session.set("mode", "sandbox")  # Dynamic per session
```

---

## Part 2: Architectural Decisions

### Decision 1: Mode Is Session State, Not Bot Identity

**Rationale:** The user is still talking to "TTA" - they're just choosing HOW to interact with it.

```python
# Session state
cl.user_session.set("bot_id", "tta")      # WHO they're talking to
cl.user_session.set("mode", "workshop")    # HOW they're interacting
```

### Decision 2: System Prompt Does NOT Change Per Mode

**Rationale:** Mode affects *behavior* and *available tools*, not the agent's core expertise.

```python
# TTA knows TTA methodology regardless of mode
# What changes:
# - Workshop: Phase tracking active, guided progression
# - Sandbox: All tools available, no phase structure
```

### Decision 3: Mode Affects Action Buttons + Tool Access

**Rationale:** The primary UX differentiator is what actions are available.

| Feature | Workshop Mode | Sandbox Mode |
|---------|---------------|--------------|
| Phase progression | ✅ Active | ❌ Hidden |
| "Next Phase" button | ✅ Shown | ❌ Hidden |
| SmartPhaseTracker | ✅ Running | ❌ Disabled |
| Multi-agent analysis | ⚠️ Optional | ✅ Available |
| Deep research | ⚠️ Phase-relevant | ✅ Unrestricted |
| Web search | ⚠️ Contextual | ✅ Full access |
| TaskList sidebar | ✅ Phases shown | ❌ Hidden |

### Decision 4: Unified Action Generator

**Rationale:** Currently 5 places generate buttons. Consolidate to 1.

```python
def get_bot_actions(
    bot: dict,
    mode: str,           # "workshop" or "sandbox"
    phases: list = None,
    current_phase: int = 0,
    turn_count: int = 0,
) -> List[cl.Action]:
    """Single source of truth for all action buttons."""
```

---

## Part 3: Data Model Changes

### 3.1 BOTS Dictionary Extension

```python
# In mindrian_chat.py

BOTS = {
    # Core bots (no mode support - they ARE the modes)
    "lawrence": {
        "name": "Lawrence",
        "system_prompt": LARRY_RAG_SYSTEM_PROMPT,
        "has_phases": False,
        "simple_mode": True,  # Existing flag
        "supports_modes": None,  # No mode switching
    },
    "larry_playground": {
        "name": "Larry Playground",
        "system_prompt": LARRY_RAG_SYSTEM_PROMPT,
        "has_phases": False,
        "simple_mode": False,  # Full features
        "supports_modes": None,  # No mode switching
    },

    # Workshop bots (dual-mode capable)
    "tta": {
        "name": "Trending to the Absurd",
        "system_prompt": TTA_WORKSHOP_PROMPT,
        "has_phases": True,
        "supports_modes": ["workshop", "sandbox"],
        "default_mode": "workshop",
        "mode_config": {
            "workshop": {
                "label": "Workshop Mode",
                "icon": "🎯",
                "description": "Guided 8-phase TTA workshop with checkpoints",
                "features": {
                    "phase_tracking": True,
                    "smart_phase_tracker": True,
                    "next_phase_button": True,
                    "workshop_download": True,
                    "multi_agent": False,  # Optional, on request
                    "deep_research": "phase_relevant",
                }
            },
            "sandbox": {
                "label": "Sandbox Mode",
                "icon": "🔬",
                "description": "Free exploration with TTA expert and full toolset",
                "features": {
                    "phase_tracking": False,
                    "smart_phase_tracker": False,
                    "next_phase_button": False,
                    "workshop_download": False,
                    "multi_agent": True,
                    "deep_research": True,
                }
            }
        }
    },
    # ... other workshop bots
}
```

### 3.2 Session State

```python
# On chat start
cl.user_session.set("bot_id", "tta")
cl.user_session.set("mode", "workshop")  # New: per-session mode
cl.user_session.set("phases", WORKSHOP_PHASES["tta"])
cl.user_session.set("current_phase", 0)

# Mode feature access
def is_feature_enabled(feature: str) -> bool:
    bot = cl.user_session.get("bot")
    mode = cl.user_session.get("mode", "workshop")
    mode_config = bot.get("mode_config", {}).get(mode, {})
    return mode_config.get("features", {}).get(feature, False)
```

### 3.3 Context Store Extension

```python
# context_store already preserves history across bot switches
# Extend to also preserve mode

context_store[context_key] = {
    "bot_id": "tta",
    "mode": "workshop",  # NEW
    "history": [...],
    "phases": [...],
    "current_phase": 2,
    "sandbox_context": {...},  # NEW: Context from sandbox exploration
}
```

---

## Part 4: UI Components

### 4.1 ModeToggle Component (Recommended)

A simple, focused toggle - not a complex switcher.

**File:** `/public/elements/ModeToggle.jsx`

```jsx
/**
 * ModeToggle - Switch between Workshop and Sandbox modes
 *
 * Props:
 * - currentMode: 'workshop' | 'sandbox'
 * - modes: array of {id, icon, label, description}
 * - botName: string (for display)
 */
export default function ModeToggle() {
  const { callAction, updateElement } = window.Chainlit || {}

  const {
    currentMode = "workshop",
    modes = [
      { id: "workshop", icon: "🎯", label: "Workshop", description: "Guided process" },
      { id: "sandbox", icon: "🔬", label: "Sandbox", description: "Free exploration" }
    ],
    botName = "Agent"
  } = props || {}

  const handleToggle = (modeId) => {
    if (modeId === currentMode) return

    if (callAction) {
      callAction({ name: "toggle_mode", payload: { mode: modeId } })
    }
    if (updateElement) {
      updateElement({ ...props, currentMode: modeId })
    }
  }

  return (
    <div className="flex flex-col gap-3 p-4 bg-card rounded-lg border">
      <div className="text-sm font-medium text-muted-foreground">
        {botName} Mode
      </div>

      <div className="flex gap-2">
        {modes.map(mode => (
          <button
            key={mode.id}
            onClick={() => handleToggle(mode.id)}
            className={`flex-1 px-4 py-3 rounded-lg border-2 transition-all ${
              currentMode === mode.id
                ? "border-primary bg-primary/10 text-primary"
                : "border-border hover:border-primary/50"
            }`}
          >
            <div className="text-lg mb-1">{mode.icon}</div>
            <div className="font-medium">{mode.label}</div>
            <div className="text-xs text-muted-foreground">{mode.description}</div>
          </button>
        ))}
      </div>

      {currentMode === "workshop" && (
        <div className="text-xs text-muted-foreground flex items-center gap-1">
          <span>💡</span>
          Phase progress is tracked. Switch to Sandbox for free exploration.
        </div>
      )}
    </div>
  )
}
```

### 4.2 Python Integration

```python
# utils/ui_elements.py

def create_mode_toggle(
    bot_name: str,
    current_mode: str,
    mode_config: dict
) -> cl.CustomElement:
    """Create a mode toggle element."""
    modes = []
    for mode_id, config in mode_config.items():
        modes.append({
            "id": mode_id,
            "icon": config.get("icon", "⚡"),
            "label": config.get("label", mode_id.title()),
            "description": config.get("description", "")
        })

    return cl.CustomElement(
        name="ModeToggle",
        props={
            "currentMode": current_mode,
            "modes": modes,
            "botName": bot_name
        },
        display="inline"
    )
```

### 4.3 Settings Panel Integration (Alternative)

For persistent access, use Chainlit's built-in settings:

```python
@cl.on_chat_start
async def start():
    bot = cl.user_session.get("bot")

    if bot.get("supports_modes"):
        settings = await cl.ChatSettings([
            cl.input_widget.Select(
                id="mode",
                label="Interaction Mode",
                values=[
                    cl.input_widget.SelectValue(value="workshop", label="🎯 Workshop"),
                    cl.input_widget.SelectValue(value="sandbox", label="🔬 Sandbox"),
                ],
                initial_value="workshop"
            )
        ]).send()

@cl.on_settings_update
async def on_settings_update(settings):
    new_mode = settings.get("mode")
    current_mode = cl.user_session.get("mode")

    if new_mode != current_mode:
        await handle_mode_switch(new_mode)
```

---

## Part 5: Core Logic Changes

### 5.1 Mode Switch Handler

```python
# mindrian_chat.py

async def handle_mode_switch(new_mode: str):
    """Switch between workshop and sandbox modes."""
    bot_id = cl.user_session.get("bot_id")
    bot = BOTS.get(bot_id)
    current_mode = cl.user_session.get("mode", "workshop")

    if not bot or not bot.get("supports_modes"):
        return

    if new_mode not in bot.get("supports_modes", []):
        return

    # Update session
    cl.user_session.set("mode", new_mode)

    # Preserve or clear phase state based on mode
    if new_mode == "workshop":
        # Entering workshop: Check for saved progress
        context_key = get_context_key()
        saved = context_store.get(context_key, {})
        if saved.get("phases"):
            cl.user_session.set("phases", saved["phases"])
            cl.user_session.set("current_phase", saved.get("current_phase", 0))
        else:
            # Fresh workshop
            cl.user_session.set("phases", [p.copy() for p in WORKSHOP_PHASES[bot_id]])
            cl.user_session.set("current_phase", 0)

        # Show TaskList
        await render_workshop_phases()

    else:  # sandbox
        # Leaving workshop: Save progress
        phases = cl.user_session.get("phases", [])
        current_phase = cl.user_session.get("current_phase", 0)
        context_store[get_context_key()] = {
            "phases": phases,
            "current_phase": current_phase,
            "mode": "workshop",  # Remember they were in workshop
        }

        # Hide TaskList (no phases in sandbox)
        await hide_workshop_phases()

    # Generate transition message
    mode_config = bot.get("mode_config", {}).get(new_mode, {})
    await cl.Message(
        content=f"""## Switched to {mode_config.get('label', new_mode.title())} {mode_config.get('icon', '')}

{mode_config.get('description', '')}

{'Your workshop progress is saved. You can switch back anytime.' if new_mode == 'sandbox' else 'Welcome back to the guided workshop!'}
"""
    ).send()

@cl.action_callback("toggle_mode")
async def on_toggle_mode(action: cl.Action):
    new_mode = action.payload.get("mode")
    await handle_mode_switch(new_mode)
```

### 5.2 Unified Action Generator

```python
# mindrian_chat.py

def get_bot_actions(
    bot: dict,
    mode: str,
    phases: list = None,
    current_phase: int = 0,
    turn_count: int = 0,
) -> List[cl.Action]:
    """
    Generate action buttons based on bot config and current mode.

    This is the SINGLE SOURCE OF TRUTH for all action buttons.
    """
    actions = []
    bot_id = bot.get("id", "")
    mode_config = bot.get("mode_config", {}).get(mode, {})
    features = mode_config.get("features", {})

    # Core actions (always available)
    actions.append(cl.Action(
        name="think_through",
        label="🤔 Think",
        description="Reason through this step-by-step"
    ))

    actions.append(cl.Action(
        name="synthesize_thread",
        label="📝 Synthesize",
        description="Summarize the conversation"
    ))

    # Research actions
    if features.get("deep_research"):
        actions.append(cl.Action(
            name="gemini_deep_research",
            label="🔬 Deep Research",
            description="Thorough multi-source research"
        ))
    else:
        actions.append(cl.Action(
            name="tavily_research",
            label="🔍 Research",
            description="Quick web search"
        ))

    # Workshop-specific actions
    if features.get("phase_tracking") and phases:
        if current_phase < len(phases) - 1:
            next_phase = phases[current_phase + 1]
            actions.append(cl.Action(
                name="next_phase",
                label=f"✅ Continue → {next_phase['name']}",
                description="Advance to next phase"
            ))

        if features.get("workshop_download"):
            actions.append(cl.Action(
                name="workshop_download",
                label="⬇️ Download Progress",
                description="Export workshop as document"
            ))

    # Sandbox-specific actions
    if features.get("multi_agent"):
        actions.append(cl.Action(
            name="multi_agent_analysis",
            label="🤖 Multi-Agent Analysis",
            description="Get perspectives from multiple agents"
        ))

    # Context-aware actions (examples, help)
    actions.append(cl.Action(
        name="show_example",
        label="💡 Show Example",
        description="See a real-world example"
    ))

    return actions
```

### 5.3 Message Handler Mode Check

```python
# In @cl.on_message handler

async def on_message(message: cl.Message):
    bot = cl.user_session.get("bot")
    mode = cl.user_session.get("mode", "workshop")
    phases = cl.user_session.get("phases", [])
    current_phase = cl.user_session.get("current_phase", 0)

    # Get mode-specific features
    mode_config = bot.get("mode_config", {}).get(mode, {})
    features = mode_config.get("features", {})

    # SmartPhaseTracker: Only in workshop mode
    if features.get("smart_phase_tracker") and phases:
        # Run phase analysis
        workshop_state = await analyze_workshop_state(...)

    # Generate response with Gemini
    response = await generate_response(...)

    # Add actions based on mode
    actions = get_bot_actions(
        bot=bot,
        mode=mode,
        phases=phases if features.get("phase_tracking") else None,
        current_phase=current_phase,
        turn_count=turn_count
    )

    await response_msg.update(actions=actions)
```

---

## Part 6: Implementation Phases

### Phase 1: Foundation (Week 1)

**Objective:** Add mode infrastructure without breaking existing behavior.

| Task | File | Lines Est. |
|------|------|------------|
| Add `supports_modes`, `mode_config` to BOTS dict | mindrian_chat.py | 50 |
| Add `mode` to session state | mindrian_chat.py | 10 |
| Create `is_feature_enabled()` helper | mindrian_chat.py | 20 |
| Create `get_bot_actions()` unified generator | mindrian_chat.py | 80 |
| Add `handle_mode_switch()` function | mindrian_chat.py | 60 |
| Add `@cl.action_callback("toggle_mode")` | mindrian_chat.py | 10 |

**Validation:**
- [ ] Existing bots work unchanged
- [ ] New `mode` session variable is set on start
- [ ] `get_bot_actions()` produces same buttons as current logic

### Phase 2: UI Components (Week 2)

**Objective:** Create mode toggle UI.

| Task | File | Lines Est. |
|------|------|------------|
| Create ModeToggle.jsx | public/elements/ModeToggle.jsx | 60 |
| Add `create_mode_toggle()` helper | utils/ui_elements.py | 20 |
| Integrate toggle into `on_chat_start` | mindrian_chat.py | 15 |
| Add settings panel alternative | mindrian_chat.py | 25 |

**Validation:**
- [ ] ModeToggle renders correctly
- [ ] Toggle triggers mode switch
- [ ] Settings panel updates mode

### Phase 3: TTA Pilot (Week 3)

**Objective:** Full dual-mode support for TTA bot.

| Task | File | Lines Est. |
|------|------|------------|
| Add full `mode_config` to TTA bot | mindrian_chat.py | 30 |
| Wire SmartPhaseTracker to mode | mindrian_chat.py | 20 |
| Test workshop → sandbox → workshop flow | - | Testing |
| Verify phase progress preservation | - | Testing |

**Validation:**
- [ ] TTA workshop mode has phases, tracking
- [ ] TTA sandbox mode has full tools, no phases
- [ ] Switching modes preserves history
- [ ] Returning to workshop restores phase progress

### Phase 4: Rollout (Week 4+)

**Objective:** Enable dual-mode for remaining workshop bots.

| Bot | Priority | Notes |
|-----|----------|-------|
| ackoff | HIGH | Complex workshop, big benefit |
| jtbd | HIGH | Popular workshop |
| scenario | MEDIUM | New smart transitions |
| bono | MEDIUM | Many phases |
| Others | LOW | Add incrementally |

---

## Part 7: Testing Strategy

### Unit Tests

```python
# tests/test_dual_mode.py

def test_mode_switch_preserves_history():
    """Switching modes should not lose conversation history."""

def test_workshop_to_sandbox_saves_phases():
    """Workshop progress saved when switching to sandbox."""

def test_sandbox_to_workshop_restores_phases():
    """Workshop progress restored when returning."""

def test_get_bot_actions_workshop():
    """Workshop mode returns phase buttons."""

def test_get_bot_actions_sandbox():
    """Sandbox mode returns full tool buttons."""
```

### Integration Tests

```python
def test_full_mode_toggle_flow():
    """
    1. Start in workshop mode
    2. Complete 2 phases
    3. Switch to sandbox
    4. Do some exploration
    5. Switch back to workshop
    6. Verify phase 3 is ready
    """
```

### UI Tests

- [ ] ModeToggle renders in dark/light mode
- [ ] Toggle animation is smooth
- [ ] Buttons are accessible (keyboard nav)
- [ ] Mobile responsive

---

## Part 8: Migration Path

### For Existing Users

1. **Default to workshop mode** for workshop bots (no surprise behavior change)
2. **Show mode toggle** after first response (not on empty chat)
3. **Tooltip/hint** explaining the two modes on first view
4. **Remember preference** for returning users (per-bot)

### For Existing Code

1. **Gradual replacement** of scattered action logic with `get_bot_actions()`
2. **Backward compatibility** - `simple_mode` still works for Lawrence
3. **Feature flags** - Can disable dual-mode per environment

---

## Part 9: Comparison with Manus Proposal

| Aspect | Manus Proposal | This Plan |
|--------|----------------|-----------|
| **Bot entries** | 28+ (doubled) | 14 (unchanged) |
| **System prompts** | 28+ (duplicated) | 14 (unchanged) |
| **Context handling** | Complex (cross-bot) | Simple (same bot, different mode) |
| **Phase preservation** | Requires sync | Automatic (same session) |
| **Rollout** | All-or-nothing | Incremental per bot |
| **UI complexity** | BotModeSwitcher with grouping | Simple ModeToggle |
| **Maintenance** | High (duplicate configs) | Low (mode_config per bot) |

---

## Part 10: Success Metrics

### User Experience

- [ ] Mode switch < 500ms (perceived instant)
- [ ] No history loss on mode switch
- [ ] Workshop progress survives sandbox exploration
- [ ] Users discover sandbox mode (tracking via analytics)

### Code Quality

- [ ] Action button logic in single function
- [ ] No duplicate system prompts
- [ ] Mode config is declarative, not imperative
- [ ] Tests cover mode transitions

### Adoption

- [ ] 50% of TTA users try sandbox mode (month 1)
- [ ] Workshop completion rate unchanged
- [ ] Sandbox mode exploration depth (avg turns)

---

## Appendix A: File Changes Summary

| File | Changes |
|------|---------|
| `mindrian_chat.py` | +200 lines (mode logic, unified actions) |
| `public/elements/ModeToggle.jsx` | +60 lines (new component) |
| `utils/ui_elements.py` | +20 lines (toggle helper) |
| `tests/test_dual_mode.py` | +100 lines (new tests) |

**Total:** ~380 lines of new code, replacing ~150 lines of scattered logic.

---

## Appendix B: Example Mode Configs

### TTA (Trending to the Absurd)

```python
"mode_config": {
    "workshop": {
        "label": "TTA Workshop",
        "icon": "🎯",
        "description": "Guided 8-phase journey from trend to opportunity",
        "features": {
            "phase_tracking": True,
            "smart_phase_tracker": True,
            "next_phase_button": True,
            "workshop_download": True,
            "multi_agent": False,
            "deep_research": "phase_relevant",
            "graphrag": True,
        }
    },
    "sandbox": {
        "label": "TTA Sandbox",
        "icon": "🔮",
        "description": "Free-form trend analysis with full toolkit",
        "features": {
            "phase_tracking": False,
            "smart_phase_tracker": False,
            "next_phase_button": False,
            "workshop_download": False,
            "multi_agent": True,
            "deep_research": True,
            "graphrag": True,
        }
    }
}
```

### Ackoff (Ackoff's Pyramid DIKW)

```python
"mode_config": {
    "workshop": {
        "label": "DIKW Workshop",
        "icon": "🏛️",
        "description": "Structured climb from Data to Wisdom",
        "features": {
            "phase_tracking": True,
            "smart_phase_tracker": True,
            "dikw_chart": True,
            "next_phase_button": True,
            "workshop_download": True,
            "multi_agent": False,
            "deep_research": "phase_relevant",
        }
    },
    "sandbox": {
        "label": "Ackoff Sandbox",
        "icon": "🧪",
        "description": "Explore DIKW concepts freely",
        "features": {
            "phase_tracking": False,
            "dikw_chart": True,  # Still useful in sandbox
            "multi_agent": True,
            "deep_research": True,
        }
    }
}
```

---

## Conclusion

This implementation plan provides a **cleaner, more maintainable** approach to dual-mode architecture than the Manus proposal. By treating mode as session state rather than bot identity, we:

1. **Avoid duplication** of bot configs and prompts
2. **Preserve context** naturally across mode switches
3. **Enable gradual rollout** to individual bots
4. **Maintain backward compatibility** with existing code
5. **Create a foundation** for future mode additions (e.g., "teaching mode", "review mode")

The key insight is that **users don't want two different bots** - they want one expert they can interact with in different ways. This plan delivers exactly that.
