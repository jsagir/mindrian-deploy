# Failure Modes Reference

## The Three Failure Modes

When analyzing feedback, categorize issues into these three types:

---

## 1. Hidden Logic Failures

The system appears functional but **reasons incorrectly**.

### Symptoms
- Overconfidence in uncertain domains
- Skipped assumptions
- Premature conclusions
- "Sounds right but isn't"
- Framework misapplication
- Wrong Cynefin domain classification

### Where to Look

| File | What to Check |
|------|---------------|
| `prompts/*.py` | System prompt instructions |
| `mindrian_chat.py` line ~554 | BOTS dict model/temperature settings |
| `tools/graphrag_lite.py` | Context retrieval accuracy |
| `tools/smart_phase_tracker.py` | Phase detection logic |

### Common Causes
- Temperature too high for analytical tasks
- Missing constraints in system prompt
- GraphRAG returning irrelevant context
- Smart phase tracker misclassifying progress

### Fix Pattern
```python
# Before: Too permissive
"temperature": 0.9

# After: More controlled for analytical work
"temperature": 0.6
```

---

## 2. Cognitive UX Friction

The system is technically correct but **mentally exhausting**.

### Symptoms
- Too much explanation when none needed
- Wrong mode at the wrong time
- UI panels appearing when they shouldn't
- Context extracted incorrectly
- Buttons disappearing after actions
- Phase tracking mismatch (sidebar vs conversation)

### Where to Look

| File | Line | What to Check |
|------|------|---------------|
| `mindrian_chat.py` | 2800+ | `@cl.action_callback` handlers |
| `mindrian_chat.py` | 946 | `get_core_action_buttons()` |
| `mindrian_chat.py` | 990 | `get_contextual_actions()` |
| `utils/ui_elements.py` | all | UI component functions |
| `tools/smart_phase_tracker.py` | all | Phase detection |

### Common Causes
- Action callback not returning buttons
- `show_input=False` missing on `cl.Step`
- Phase state not synced on change
- Context not preserved on bot switch

### Fix Pattern: Buttons Disappear
```python
# Before: No buttons on result
msg = cl.Message(content=result)
await msg.send()

# After: Always include core buttons
msg = cl.Message(content=result)
msg.actions = get_core_action_buttons()
await msg.send()
```

### Fix Pattern: Tool Labels Leak
```python
# Before: Labels visible
async with cl.Step(name="Research") as step:
    result = await do_research()

# After: Hide input
async with cl.Step(name="Research", show_input=False) as step:
    result = await do_research()
```

---

## 3. Identity Drift

Bots **lose personality, tone, or epistemic role**.

### Symptoms
- Red Team becomes polite
- Lawrence becomes overly analytical
- TTA stops exploring extremes
- Grading becomes vague (no criteria shown)
- Investment bot missing disclaimers

### Where to Look

| Bot | Prompt File | Key Trait to Verify |
|-----|-------------|---------------------|
| Lawrence | `prompts/larry_core.py` | Conversational, asks first |
| Red Team | `prompts/redteam.py` | Attacks hard, finds weaknesses |
| TTA | `prompts/tta_workshop.py` | Explores extremes |
| Grading | `prompts/grading_agent.py` | Shows criteria WITH scores |
| PWS Investment | `prompts/pws_investment.py` | MUST show disclaimers |

### Common Causes
- System prompt diluted by context
- Temperature changed from original
- Context from previous bot bleeding through
- Model version change affecting behavior

### Fix Pattern: Context Bleeding
```python
# In handle_agent_switch() at line 3581
# Ensure clean context on switch
context_store[context_key] = {
    "topic": topic,
    "history": [],  # Clear history for fresh start
    "phase": 0
}
```

---

## Known Bug Patterns

### Pattern 1: Buttons Disappear After Action

**Location:** Action callbacks in `mindrian_chat.py` (lines 2800+)

**Root Cause:** Result message sent without `get_core_action_buttons()`

**Fix:**
```python
@cl.action_callback("some_action")
async def handle_action(action: cl.Action):
    result = await process_action()
    msg = cl.Message(content=result)
    msg.actions = get_core_action_buttons()  # CRITICAL
    await msg.send()
```

### Pattern 2: Context Lost on Bot Switch

**Location:** `handle_agent_switch()` at line 3581

**Root Cause:** Topic context not preserved in `context_store`

**Key Variable:** `context_store[context_key]`

### Pattern 3: Response Truncation

**Location:** Streaming loop in `@cl.on_message`

**Root Cause:** `await msg.update()` not called after streaming completes

**Fix:**
```python
msg = cl.Message(content="")
await msg.send()

async for chunk in response_stream:
    msg.content += chunk
    await msg.update()

# CRITICAL: Final update
await msg.update()
```

### Pattern 4: Tool Execution Labels Leak to UI

**Location:** `cl.Step` usage throughout codebase

**Fix:** Use `show_input=False` on cl.Step

### Pattern 5: Chainlit Version Compatibility

**Pattern:** `TypeError: got unexpected keyword argument`

**Fix:** Use `safe_task_list_send()` wrapper (line ~65)

### Pattern 6: Phase Tracking Mismatch

**Location:** `WORKSHOP_PHASES` dict (line 428), smart phase analysis

**Issue:** Sidebar shows different phase than conversation

**Fix:** Sync phase state explicitly on phase change

---

## Detection Checklist

When analyzing a bug report, check:

- [ ] Is it a **Logic**, **UX**, or **Identity** issue?
- [ ] Which bot(s) are affected?
- [ ] Is it reproducible? (Always / Sometimes / Once)
- [ ] Does it match a known pattern above?
- [ ] What's the exact file and line number?
- [ ] Is there a governance/safety implication?
