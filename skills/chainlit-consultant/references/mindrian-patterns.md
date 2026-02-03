# Mindrian Chainlit Patterns

This reference documents how Mindrian currently uses Chainlit and identifies extension points.

---

## Current Implementation

### File Structure

```
mindrian-deploy/
├── mindrian_chat.py          # Main Chainlit app (7000+ lines)
├── public/
│   └── elements/             # Custom JSX elements (if any)
├── prompts/                  # Bot system prompts
├── tools/                    # Research, grading, GraphRAG
├── utils/
│   └── ui_elements.py        # UI helper functions
└── governance/               # AI safety monitoring
```

### Key Chainlit Components Used

| Component | Location | Purpose |
|-----------|----------|---------|
| `cl.Message` | Throughout | Send bot responses |
| `cl.Action` | Line 946+ | Action buttons (Research, Synthesize, Think, Example) |
| `cl.TaskList` | Line 67+ | Phase sidebar |
| `cl.Step` | Various | Show thinking/tool usage |
| `cl.user_session` | Throughout | Session state storage |
| `@cl.action_callback` | Line 2800+ | Handle button clicks |
| `@cl.on_message` | Line 6500+ | Main message handler |

### Session State Variables

```python
# Core state
cl.user_session.get("bot_id")           # Current bot identifier
cl.user_session.get("history")          # Conversation history
cl.user_session.get("phases")           # Workshop phase list
cl.user_session.get("current_phase")    # Current phase index (0-indexed)
cl.user_session.get("phase_context")    # Extracted phase data
cl.user_session.get("topic")            # Current discussion topic

# Context persistence
context_store[context_key] = {
    "bot_id": bot_id,
    "history": history,
    "phases": phases,
    "current_phase": current_phase
}
```

### Action Buttons (get_core_action_buttons)

```python
# mindrian_chat.py:946
def get_core_action_buttons():
    return [
        cl.Action(name="research", label="🔍 Research", ...),
        cl.Action(name="synthesize", label="📥 Synthesize", ...),
        cl.Action(name="think", label="🧠 Think", ...),
        cl.Action(name="show_example", label="📖 Example", ...),
    ]
```

### TaskList Pattern (safe_task_list_send)

```python
# mindrian_chat.py:67-79
async def safe_task_list_send(task_list):
    """Wrapper to handle Chainlit version compatibility."""
    try:
        await task_list.send()
    except TypeError as e:
        if "for_id" in str(e):
            pass  # Known Chainlit version issue
        else:
            raise
```

### Phase Transition Card

```python
# mindrian_chat.py:1060-1150
async def send_phase_transition_card(phases, current_phase, bot_name, is_auto=False):
    """Send phase transition notification with actions."""
    content = f"""
## 📍 Phase {current_phase + 1}/{total}: {current_name}
{progress_bar}
"""
    actions = [
        cl.Action(name="help_start_phase", label="🚀 Help me start..."),
        cl.Action(name="acknowledge_phase", label="👍 Got it"),
        cl.Action(name="next_phase", label="⏭️ Skip to next"),
    ]
    await cl.Message(content=content, actions=actions).send()
```

---

## Extension Points

### 1. Custom Phase Roadmap Element

**Current**: Inline phase cards interrupt conversation flow

**Opportunity**: Create persistent JSX element for phase visualization

```jsx
// public/elements/PhaseRoadmap.jsx
import { Progress } from "@/components/ui/progress"
import { Card } from "@/components/ui/card"

export default function PhaseRoadmap() {
    const { phases, currentPhase, botName } = props;
    
    return (
        <Card className="w-64 p-4">
            <h3 className="font-semibold mb-4">{botName} Progress</h3>
            {phases.map((phase, i) => (
                <div key={i} className="flex items-center gap-2 mb-2">
                    {i < currentPhase ? "✅" : i === currentPhase ? "🔵" : "⚪"}
                    <span className={i === currentPhase ? "font-bold" : ""}>
                        {phase.name}
                    </span>
                </div>
            ))}
            <Progress value={(currentPhase / phases.length) * 100} className="mt-4" />
        </Card>
    );
}
```

### 2. Bot Switcher Component

**Current**: Bot switching via action buttons

**Opportunity**: Visual bot selector with descriptions

```jsx
// public/elements/BotSwitcher.jsx
import { Select, SelectContent, SelectItem, SelectTrigger } from "@/components/ui/select"

export default function BotSwitcher() {
    const handleSwitch = (botId) => {
        callAction({ name: "switch_bot", payload: { bot_id: botId }});
    };
    
    return (
        <Select onValueChange={handleSwitch} value={props.currentBot}>
            <SelectTrigger>Current: {props.bots[props.currentBot]?.name}</SelectTrigger>
            <SelectContent>
                {Object.entries(props.bots).map(([id, bot]) => (
                    <SelectItem key={id} value={id}>
                        {bot.name} - {bot.description}
                    </SelectItem>
                ))}
            </SelectContent>
        </Select>
    );
}
```

### 3. Research Results Panel

**Current**: Research results shown inline

**Opportunity**: Side panel with filterable results

```jsx
// public/elements/ResearchPanel.jsx
import { ScrollArea } from "@/components/ui/scroll-area"
import { Card } from "@/components/ui/card"

export default function ResearchPanel() {
    return (
        <ScrollArea className="h-96">
            {props.results.map((result, i) => (
                <Card key={i} className="p-3 mb-2">
                    <h4 className="font-medium">{result.title}</h4>
                    <p className="text-sm text-muted-foreground">{result.snippet}</p>
                    <a href={result.url} target="_blank" className="text-primary text-sm">
                        View source →
                    </a>
                </Card>
            ))}
        </ScrollArea>
    );
}
```

### 4. Grading Scorecard

**Current**: Grading shown as text

**Opportunity**: Visual scorecard component

```jsx
// public/elements/GradingScorecard.jsx
import { Progress } from "@/components/ui/progress"
import { Card, CardHeader, CardContent } from "@/components/ui/card"

export default function GradingScorecard() {
    const { criteria, scores, overall } = props;
    
    return (
        <Card>
            <CardHeader>
                <h3>PWS Grading: {overall}/100</h3>
            </CardHeader>
            <CardContent>
                {criteria.map((c, i) => (
                    <div key={i} className="mb-3">
                        <div className="flex justify-between text-sm">
                            <span>{c.name}</span>
                            <span>{scores[i]}/10</span>
                        </div>
                        <Progress value={scores[i] * 10} />
                    </div>
                ))}
            </CardContent>
        </Card>
    );
}
```

---

## Integration Patterns

### Adding Custom Element to Message

```python
# In mindrian_chat.py

# 1. Create element with props
phase_roadmap = cl.CustomElement(
    name="PhaseRoadmap",
    props={
        "phases": [{"name": p["name"]} for p in phases],
        "currentPhase": current_phase,
        "botName": bot.get("name", "Workshop")
    },
    display="side"  # Show in sidebar
)

# 2. Attach to message
await cl.Message(
    content="Let's continue with the workshop.",
    elements=[phase_roadmap]
).send()

# 3. Update element later
phase_roadmap.props["currentPhase"] = current_phase + 1
await phase_roadmap.update()
```

### Replacing TaskList with Custom Element

```python
# Instead of:
task_list = cl.TaskList()
await task_list.send()

# Use:
roadmap = cl.CustomElement(
    name="PhaseRoadmap",
    props={"phases": phases, "currentPhase": current_phase},
    display="side"
)
cl.user_session.set("roadmap_element", roadmap)
await cl.Message(content="", elements=[roadmap]).send()
```

### Handling Custom Element Actions

```python
@cl.action_callback("phase_click")
async def on_phase_click(action: cl.Action):
    """Handle click on phase in custom roadmap."""
    target_phase = action.payload.get("phase_index")
    # Navigate to that phase
    await advance_to_phase(target_phase)
```

---

## Known Limitations

### TaskList Issues

The TaskList has known compatibility issues across Chainlit versions. The `safe_task_list_send()` wrapper handles the `for_id` TypeError but doesn't solve:

1. TaskList not updating visually after `send()`
2. TaskList disappearing on bot switch
3. No click handlers on tasks

**Workaround**: Use CustomElement for more control.

### Custom Element Limitations

1. Cannot import local packages (only allowed list)
2. No TypeScript support (JSX only)
3. Props must be JSON-serializable
4. Limited to shadcn component library

### Session State Persistence

`cl.user_session` is lost on:
- Server restart
- Session timeout
- Browser refresh (unless using data persistence)

**Workaround**: Use `context_store` dict + Supabase for persistence.
