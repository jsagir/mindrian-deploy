# Claude Code Project Guide - Mindrian

This file is for AI assistants (Claude Code, etc.) to quickly understand this project and continue development effectively.

> **REPO GUARD:** This is the **production deploy repo** (`mindrian-deploy`). All code changes go here.
> Do NOT edit files in `mindrian-langgraph` or any other sibling folder — those are archived experiments.
> The canonical working directory is `/home/jsagi/Mindrian/mindrian-deploy/`.

---

## Session Start: Health Check Protocol

**Every new Claude Code session on this project MUST begin by running:**

```bash
python3 scripts/health_check.py
```

This verifies: AI API, FileSearch RAG, Neo4j LazyGraph, Tavily, Supabase, ElevenLabs, LangExtract, optional research APIs, and code integrity. Fix any failures before proceeding with development work.

You can also run it via: `/health-check`

---

## Quick Context

**What is Mindrian?**
A Chainlit-based multi-bot platform for PWS (Problems Worth Solving) methodology workshops. Users chat with specialized AI bots (Lawrence, Ackoff, TTA, etc.) to work through structured innovation frameworks.

**Bot Naming:**
- **Lawrence** (`"lawrence"`) — Default bot. Focused, concise PWS thinking partner (`simple_mode: True`).
- **Larry Playground** (`"larry_playground"`) — Full-featured PWS lab with all tools, research, multi-agent analysis (`simple_mode: False`).
- Both share the same system prompt (`LARRY_RAG_SYSTEM_PROMPT` from `prompts/larry_core.py`).

**Tech Stack:**
- **Frontend/UI:** Chainlit 2.9+
- **AI Model:** gemini-3-flash-preview, gemini-2.0-flash
- **RAG:** File Search with semantic retrieval
- **Database:** PostgreSQL
- **Storage:** Cloud Storage
- **Voice:** TTS integration
- **Research:** Web search APIs

---

## Project Structure

```
mindrian-deploy/
├── mindrian_chat.py          # Main app (1600+ lines) - ALL Chainlit handlers
├── prompts/                  # System prompts for each bot
│   ├── __init__.py          # Exports all prompts
│   ├── larry_core.py        # Larry's general PWS prompt
│   ├── tta_workshop.py      # Trending to the Absurd
│   ├── jtbd_workshop.py     # Jobs to Be Done
│   ├── scurve_workshop.py   # S-Curve Analysis
│   ├── redteam.py           # Red Teaming
│   └── ackoff_workshop.py   # Ackoff's Pyramid DIKW (650+ lines)
├── tools/                   # External tool integrations
│   ├── tavily_search.py     # Tavily web search wrapper
│   └── langextract.py       # Zero-latency structured data extraction
├── utils/                   # Utility modules
│   ├── charts.py            # Plotly visualizations (DIKW pyramid, S-curve, DataFrames)
│   ├── gemini_rag.py        # RAG cache utilities
│   ├── file_processor.py    # PDF/DOCX/TXT extraction
│   ├── media.py             # ElevenLabs TTS, videos, audiobook chapters, file exports
│   ├── storage.py           # Supabase Storage integration
│   └── feedback.py          # User feedback storage for QA analytics
├── public/icons/            # SVG icons for conversation starters
├── .chainlit/config.toml    # Chainlit UI configuration
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variable template
└── .env                     # Actual environment variables (gitignored)
```

---

## Key Files Deep Dive

### mindrian_chat.py - The Main App

This is the heart of the application. Key sections:

```python
# === Important Data Structures ===

BOTS = {
    "lawrence": { "name": "Lawrence", "simple_mode": True, "system_prompt": LARRY_RAG_SYSTEM_PROMPT, ... },
    "larry_playground": { "name": "Larry Playground", "simple_mode": False, "system_prompt": LARRY_RAG_SYSTEM_PROMPT, ... },
    "tta": { "name": "Trending to the Absurd", ... },
    "jtbd": { ... },
    "scurve": { ... },
    "redteam": { ... },
    "ackoff": { ... },
}

WORKSHOP_PHASES = {
    "tta": [{"name": "Introduction", "status": "ready"}, ...],
    "ackoff": [{"name": "Team Onboarding", ...}, ...],
    # etc.
}

STARTERS = {
    "lawrence": [cl.Starter(label="...", message="...", icon="..."), ...],
    # 4 starters per bot
}

context_store = {}  # Preserves conversation across bot switches
stop_events = {}    # For cancellation support

# === Key Chainlit Decorators ===

@cl.set_chat_profiles      # Define available bots
@cl.set_starters           # Conversation starter buttons
@cl.on_settings_update     # Handle settings panel changes
@cl.on_chat_start          # Session initialization
@cl.on_chat_resume         # Restore from database
@cl.on_stop                # Handle stop button
@cl.on_message             # Main message handler
@cl.on_audio_start/chunk/end  # Voice input handling
@cl.action_callback("...")    # Button click handlers
```

### Adding a New Bot/Agent - COMPLETE CHECKLIST

**⚠️ USE THE GENERATOR SCRIPT: `python scripts/generate_agent.py newbot "New Bot Name"`**

This creates all boilerplate automatically. If doing manually, follow ALL steps below.

---

#### TIER 1: Core Setup (Required)

| # | Task | File | Status |
|---|------|------|--------|
| 1 | Create system prompt | `prompts/newbot.py` | ☐ |
| 2 | Export prompt | `prompts/__init__.py` | ☐ |
| 3 | Add to BOTS dict | `mindrian_chat.py` | ☐ |
| 4 | Add chat profile | `mindrian_chat.py` → `chat_profiles()` | ☐ |
| 5 | Add starters (4 required) | `mindrian_chat.py` → `STARTERS` | ☐ |

#### TIER 2: Workshop Features (If has_phases=True)

| # | Task | File | Status |
|---|------|------|--------|
| 6 | Define workshop phases | `mindrian_chat.py` → `WORKSHOP_PHASES` | ☐ |
| 7 | Add phase completion criteria | Phase definitions (see Phase Insights below) | ☐ |
| 8 | Add video URLs per phase | `utils/media.py` → `WORKSHOP_VIDEOS` | ☐ |
| 9 | Add audiobook chapters | `utils/media.py` → `AUDIOBOOK_CHAPTERS` | ☐ |

#### TIER 3: Dynamic Features (Required for Full Integration)

| # | Task | File | Status |
|---|------|------|--------|
| 9 | Add agent trigger keywords | `mindrian_chat.py` → `AGENT_TRIGGERS` | ☐ |
| 10 | Add switch callback | `mindrian_chat.py` → `@cl.action_callback` | ☐ |
| 11 | Add dynamic examples | `utils/dynamic_examples.py` | ☐ |
| 12 | Add quality scoring criteria | `utils/quality_scorer.py` (optional) | ☐ |

#### TIER 4: Knowledge Base (For RAG-enabled bots)

| # | Task | File/Location | Status |
|---|------|---------------|--------|
| 13 | Upload workshop materials | File Search → `T2_Tools/` | ☐ |
| 14 | Add case studies | Neo4j → `CaseStudy` nodes | ☐ |
| 15 | Create RAG cache | `utils/gemini_rag.py` → `setup_X_cache()` | ☐ |

---

### Detailed Implementation Guide

#### Step 1: Create System Prompt
```python
# prompts/newbot.py
NEWBOT_PROMPT = """
You are [Name], a PWS methodology expert specializing in [methodology].

## Your Role
[Describe the bot's expertise and approach]

## Workshop Phases (if applicable)
1. Phase 1: [Name] - [Description]
2. Phase 2: [Name] - [Description]
...

## Key Concepts
- [Concept 1]: [Brief explanation]
- [Concept 2]: [Brief explanation]

## Interaction Style
- Ask probing questions (Socratic method)
- Never jump to solutions before understanding the problem
- Always ground responses in PWS methodology
"""
```

#### Step 2: Export Prompt
```python
# prompts/__init__.py
from .newbot import NEWBOT_PROMPT
```

#### Step 3: Add to BOTS Dict
```python
# mindrian_chat.py
BOTS["newbot"] = {
    "name": "New Bot Name",
    "icon": "🆕",
    "description": "One-line description for chat profile",
    "system_prompt": NEWBOT_PROMPT,
    "has_phases": True,  # True for workshops, False for general
    "welcome": """**🆕 Welcome to New Bot Workshop!**

I'll guide you through [methodology]. We'll work through [X] phases:

1. **Phase 1** - [Brief description]
2. **Phase 2** - [Brief description]

Let's begin! [Opening question]"""
}
```

#### Step 4: Add Chat Profile
```python
# mindrian_chat.py → chat_profiles()
cl.ChatProfile(
    name="newbot",
    markdown_description=BOTS["newbot"]["description"],
    icon=BOTS["newbot"]["icon"],
),
```

#### Step 5: Add Starters (4 Required)
```python
# mindrian_chat.py → STARTERS
STARTERS["newbot"] = [
    cl.Starter(
        label="Start Workshop",
        message="I'm ready to begin the [methodology] workshop",
        icon="/public/icons/start.svg"
    ),
    cl.Starter(
        label="Explain Methodology",
        message="Explain how [methodology] works",
        icon="/public/icons/info.svg"
    ),
    cl.Starter(
        label="Show Example",
        message="Show me an example of [methodology] in action",
        icon="/public/icons/example.svg"
    ),
    cl.Starter(
        label="Apply to My Problem",
        message="I have a problem I want to analyze with [methodology]",
        icon="/public/icons/apply.svg"
    ),
]
```

#### Step 6: Define Workshop Phases
```python
# mindrian_chat.py → WORKSHOP_PHASES
WORKSHOP_PHASES["newbot"] = [
    {"name": "Introduction", "status": "ready"},
    {"name": "Phase 1 Name", "status": "pending"},
    {"name": "Phase 2 Name", "status": "pending"},
    {"name": "Synthesis", "status": "pending"},
]
```

#### Step 7: Add Video URLs
```python
# utils/media.py → WORKSHOP_VIDEOS
WORKSHOP_VIDEOS["newbot"] = {
    "intro": "https://youtube.com/watch?v=VIDEO_ID",
    "phase_1": "https://youtube.com/watch?v=PHASE1_ID",
    "phase_2": "https://youtube.com/watch?v=PHASE2_ID",
    # ... one per phase
}
```

#### Step 8: Add Audiobook Chapters
```python
# utils/media.py → AUDIOBOOK_CHAPTERS
AUDIOBOOK_CHAPTERS["newbot_topic"] = {
    "chapter_1": {
        "title": "Introduction to [Methodology]",
        "url": "",  # Add URL when available
        "duration": "15:00",
        "keywords": ["keyword1", "keyword2"],
        "bot_relevance": ["newbot"],
    },
    # ... more chapters
}
```

#### Step 9: Add Agent Trigger Keywords ⚠️ CRITICAL
```python
# mindrian_chat.py → AGENT_TRIGGERS
AGENT_TRIGGERS["newbot"] = {
    "keywords": ["keyword1", "keyword2", "methodology name", "relevant phrase"],
    "description": "Short description for suggestion button"
}
```
**WHY:** Without this, your bot will never be suggested during conversations!

#### Step 10: Add Switch Callback ⚠️ CRITICAL
```python
# mindrian_chat.py
@cl.action_callback("switch_to_newbot")
async def on_switch_to_newbot(action: cl.Action):
    await handle_agent_switch("newbot")
```
**WHY:** Without this, the "Switch to NewBot" button won't work!

#### Step 11: Add Dynamic Examples
```python
# utils/dynamic_examples.py → BOT_TO_METHODOLOGY
BOT_TO_METHODOLOGY["newbot"] = ["Methodology Name", "Alternate Name", "Key Concept"]

# utils/dynamic_examples.py → BOT_TO_CASE_TOPICS
BOT_TO_CASE_TOPICS["newbot"] = ["Case Study 1", "Case Study 2", "Company Name"]

# utils/dynamic_examples.py → STATIC_EXAMPLES
STATIC_EXAMPLES["newbot"] = [
    "**Example 1**: Description of a real-world application of the methodology...",
    "**Example 2**: Another case study showing the methodology in action...",
    "**Example 3**: A third example with specific details...",
    # Add 3-5 static examples as fallback
]
```

#### Step 12: Add Quality Scoring (Optional)
```python
# utils/quality_scorer.py → Add methodology-specific dimensions if needed
NEWBOT_QUALITY_DIMENSIONS = {
    "dimension_1": {
        "name": "Dimension Name",
        "description": "What this measures",
        "weight": 0.25,
        "positive_indicators": ["indicator1", "indicator2"],
        "negative_indicators": ["bad_indicator1"]
    },
    # ...
}
```

#### Step 13-15: Knowledge Base Setup

**Upload to File Search (T2_Tools):**
```bash
# Use upload script
python scripts/upload_workshop_materials.py newbot /path/to/materials/
```

**Add to Neo4j:**
```cypher
// Create case study nodes
CREATE (cs:CaseStudy {
    name: "Case Study Name",
    description: "Brief description",
    methodology: "newbot"
})

// Link to framework
MATCH (f:Framework {name: "Methodology Name"})
CREATE (cs)-[:APPLIED_FRAMEWORK]->(f)
```

**Create RAG Cache:**
```python
# utils/gemini_rag.py
def setup_newbot_cache():
    from prompts.newbot import NEWBOT_PROMPT

    file_paths = [
        "/path/to/lecture.txt",
        "/path/to/worksheet.txt",
    ]

    return create_workshop_cache(
        workshop_id="newbot",
        file_paths=file_paths,
        system_instruction=NEWBOT_PROMPT,
    )
```

---

### Quick Validation Checklist

After adding a new agent, verify:

- [ ] Bot appears in chat profile dropdown
- [ ] 4 conversation starters appear on empty chat
- [ ] Welcome message displays correctly
- [ ] Phases progress (if workshop bot)
- [ ] "Show Example" shows diverse examples
- [ ] "Deep Research" works
- [ ] Agent is suggested when relevant keywords are mentioned
- [ ] "Switch to [Bot]" button works from other bots
- [ ] Videos play (if URLs configured)
- [ ] Audio chapters available (if URLs configured)

---

## Adding Features

### Adding a New Action Button

1. Add to `on_chat_start()` actions list:
```python
cl.Action(
    name="my_action",
    payload={"action": "myaction"},
    label="My Action",
    description="What it does"
)
```

2. Create callback:
```python
@cl.action_callback("my_action")
async def on_my_action(action: cl.Action):
    # Your logic here
    await cl.Message(content="Result").send()
```

### Adding a New Tool

1. Create `tools/my_tool.py`:
```python
def my_tool_function(param1, param2):
    # Tool logic
    return result
```

2. Import and use in `mindrian_chat.py`:
```python
from tools.my_tool import my_tool_function

# In action callback or message handler:
result = my_tool_function(...)
```

### Adding a New Chart/Visualization

1. Add to `utils/charts.py`:
```python
async def create_my_chart(data, title="My Chart"):
    import plotly.graph_objects as go

    fig = go.Figure(...)
    # Configure chart

    return cl.Plotly(name="my_chart", figure=fig, display="inline")
```

2. Use in action callback:
```python
from utils.charts import create_my_chart

chart = await create_my_chart(data)
await cl.Message(content="Here's the chart:", elements=[chart]).send()
```

---

## Adding Custom UI Components (SKILL)

> **IMPORTANT:** When a new custom UI component is needed, consult `skills/chainlit-components.md` for best practices and patterns.

Mindrian uses Chainlit's custom elements system for interactive UI components. These are React JSX files in `public/elements/`.

### Quick Start

```bash
# Generate new component
python scripts/create_component.py ComponentName
python scripts/create_component.py ComponentName --template card
```

### Existing Components

| Component | Purpose | Location |
|-----------|---------|----------|
| `MermaidDiagram` | Mermaid diagrams (mindmaps, flowcharts) | `public/elements/MermaidDiagram.jsx` |
| `GradeReveal` | Soft-landing grade reveal | `public/elements/GradeReveal.jsx` |
| `ScoreBreakdown` | Interactive score drill-down | `public/elements/ScoreBreakdown.jsx` |
| `OpportunityCard` | Bank of opportunities | `public/elements/OpportunityCard.jsx` |

### Templates Available

| Template | Use For | Location |
|----------|---------|----------|
| `BasicCard` | Cards with actions | `public/elements/templates/BasicCard.jsx` |
| `FormCard` | Forms with validation | `public/elements/templates/FormCard.jsx` |
| `DataTable` | Sortable data tables | `public/elements/templates/DataTable.jsx` |
| `StatusTracker` | Progress visualization | `public/elements/templates/StatusTracker.jsx` |

### Key Rules

1. **JSX Only** - No TypeScript (`.jsx` not `.tsx`)
2. **Global Props** - `const { prop } = props || {}` (NOT function arguments)
3. **Default Export** - `export default function Name() {}`
4. **Check APIs** - Always check if Chainlit APIs exist before calling

### Pattern

```jsx
export default function MyComponent() {
  // Chainlit APIs (global)
  const { updateElement, callAction, sendUserMessage } = window.Chainlit || {}

  // Props (global)
  const { title = "Default", data = [] } = props || {}

  // Handler
  const handleClick = () => {
    if (callAction) {
      callAction({ name: "my_action", payload: { title } })
    }
  }

  return (
    <Card>
      <CardTitle>{title}</CardTitle>
      <Button onClick={handleClick}>Action</Button>
    </Card>
  )
}
```

### Python Integration

```python
# Send element
elements = [
    cl.CustomElement(
        name="MyComponent",  # Must match JSX filename!
        props={"title": "Hello", "data": [1, 2, 3]},
        display="inline"
    )
]
await cl.Message(content="Result:", elements=elements).send()

# Handle action
@cl.action_callback("my_action")
async def handle_my_action(action: cl.Action):
    title = action.payload.get("title")
    await cl.Message(content=f"Received: {title}").send()
```

### Full Documentation

- **Skill Guide:** `skills/chainlit-components.md`
- **Docs:** `docs/CHAINLIT_COMPONENTS.md`
- **Generator:** `scripts/create_component.py`

---

## Adding MCP Tools

MCP (Model Context Protocol) tools are configured in `.chainlit/config.toml`:

```toml
[features.mcp]
enabled = true
```

And in the user's Claude Desktop or environment config. The platform already has:
- Tavily Search (via `tools/tavily_search.py`)

To add more MCP tools:
1. Configure in MCP server settings
2. Access via Chainlit's MCP integration

---

## Environment Variables

Required:
- `GOOGLE_API_KEY` - AI model API key

Recommended:
- `TAVILY_API_KEY` - Web research
- `CHAINLIT_DATABASE_URL` - PostgreSQL for persistence

Optional:
- `ELEVENLABS_API_KEY` - Voice responses
- `ELEVENLABS_VOICE_ID` - Custom voice
- `SUPABASE_URL` - File storage
- `SUPABASE_SERVICE_KEY` - File storage auth
- `SUPABASE_BUCKET` - Storage bucket name

---

## Key Patterns

### Streaming Responses
```python
msg = cl.Message(content="")
await msg.send()

for chunk in response_stream:
    await msg.stream_token(chunk.text)

await msg.update()
```

### Using cl.Step for Chain of Thought
```python
async with cl.Step(name="Step Name", type="llm") as step:
    step.input = "What we're doing"
    # ... do work ...
    step.output = "Result"
```

### Context Preservation Across Bot Switches
```python
# On chat start, check for preserved context:
context_key = get_context_key()
preserved = context_store.get(context_key, {})

# After each message, sync history:
context_store[context_key] = {
    "bot_id": bot_id,
    "history": history.copy(),
}
```

### File Processing
```python
from utils.file_processor import process_uploaded_file, format_file_context

content, metadata = process_uploaded_file(file_path, file_name)
file_context = format_file_context(file_name, content, metadata)
```

---

## Common Tasks

### Run locally
```bash
chainlit run mindrian_chat.py --watch
```

### Deploy to Render
- Push to main branch
- Auto-deploys via webhook

### Add workshop materials to RAG
```bash
cd /home/jsagi/Mindrian/mindrian-langgraph
python upload_new_workshop.py
```

---

## Recent Changes (v3.1)

1. **Chain of Thought** - `@cl.step` for transparent reasoning
2. **Conversation Starters** - 4 per bot in STARTERS dict
3. **Chat Settings** - Research depth, examples, verbosity
4. **Session Persistence** - PostgreSQL via Supabase
5. **ElevenLabs Voice** - TTS integration (updated with streaming SDK)
6. **Document Processing** - PDF/DOCX extraction
7. **Context Preservation** - Maintain history across bot switches
8. **Stop Handler** - Graceful interruption
9. **DIKW Pyramid Chart** - Plotly visualization
10. **Synthesize & Download** - Larry synthesizes any conversation as downloadable MD
11. **LangExtract** - Zero-latency structured data extraction with Supabase persistence
12. **Video Tutorials** - "🎬 Watch Video" button for workshop phases
13. **User Feedback** - Thumbs up/down with Supabase storage for QA analytics
14. **PWS Audiobook Chapters** - "📖 Listen to Chapter" button for contextual audio content
15. **GraphRAG Lite** - Neo4j + vector hybrid for relationship-aware context enrichment
16. **Mermaid Diagrams** - Mindmaps and flowcharts via custom element + utils/diagrams.py

---

## Mermaid Diagrams - Idea Visualization

Render mindmaps, flowcharts, sequence diagrams, and more using Mermaid.js.

### Quick Usage

```python
from utils.diagrams import create_mindmap, create_flowchart, create_mermaid_element

# Create a mindmap
diagram = await create_mindmap(
    central_topic="AI in Education",
    branches={
        "Benefits": ["Personalized Learning", "Scalability"],
        "Challenges": ["Privacy", "Equity"],
        "Applications": ["Tutoring", "Assessment"]
    },
    title="Idea Map"
)
await cl.Message(content="Your ideas:", elements=[diagram]).send()

# Create a flowchart
steps = [
    {"id": "A", "label": "Start", "type": "start", "next": ["B"]},
    {"id": "B", "label": "Decision?", "type": "decision", "next": ["C", "D"]},
    {"id": "C", "label": "Yes Path", "type": "process", "next": ["E"]},
    {"id": "D", "label": "No Path", "type": "process", "next": ["E"]},
    {"id": "E", "label": "End", "type": "end", "next": []}
]
chart = await create_flowchart(steps, title="Process Flow")

# Raw Mermaid syntax
raw = await create_mermaid_element("""
mindmap
  root((Topic))
    Branch 1
      Item A
      Item B
    Branch 2
      Item C
""", title="Custom Diagram")
```

### Available Functions

| Function | Purpose |
|----------|---------|
| `create_mindmap()` | Structured mindmap from dict |
| `create_mindmap_from_ideas()` | Mindmap from idea list |
| `create_flowchart()` | Flowchart from step definitions |
| `create_process_flowchart()` | Simple linear process |
| `create_user_journey()` | User experience journey map |
| `create_sequence_diagram()` | Interaction sequences |
| `create_opportunity_map()` | PWS opportunity analysis |
| `create_assumption_map()` | Assumption categorization |
| `create_framework_flow()` | Pre-built PWS framework flows (tta, jtbd, dikw) |
| `create_mermaid_element()` | Raw Mermaid syntax |

### Action Button

Users can click "🗺️ Map Ideas" to auto-generate a mindmap from the conversation.

### Key Files

- `public/elements/MermaidDiagram.jsx` - React component
- `utils/diagrams.py` - Python generation utilities

---

## GraphRAG Lite - Knowledge Graph Integration

GraphRAG Lite combines **semantic vector search** with **graph-based relationships** for conversational context enrichment.

### Design Philosophy

For conversational coaching, **less is more**. GraphRAG returns hints, not lectures.

### When It Retrieves

- User asks "What is X?" → Concept lookup
- User mentions framework (turn 2+) → Framework suggestions
- User describes problem → Problem context + approaches
- User asks for next steps → Related exercises

### Integration

Auto-enabled when Neo4j environment variables are configured:

```python
# Imported at top of mindrian_chat.py
try:
    from tools.graphrag_lite import enrich_for_larry, enrich_for_bot
    GRAPHRAG_ENABLED = True
except ImportError:
    GRAPHRAG_ENABLED = False

# In @cl.on_message handler
if GRAPHRAG_ENABLED:
    hint = enrich_for_bot(message.content, turn_count, bot_id="lawrence")
    if hint:
        full_user_message += f"\n\n[GraphRAG context: {hint}]"
```

### Key Files

- `tools/graphrag_lite.py` - Core implementation
- `tools/pws_brain.py` - File Search integration
- `tools/neo4j_framework_discovery.py` - Neo4j utilities

### Example

```
User: "What framework should I use for customer research?"
GraphRAG: "Relevant frameworks: Jobs to Be Done, Customer Discovery"
Larry: "There's JTBD - asking what progress they're making. Have you talked to customers yet?"
```

See `R&D/09_graphrag_lite/README.md` for full documentation.

---

## Phase Insights - Intelligent Progress Surfacing

The Phase Insights system surfaces AI-analyzed progress to users in a non-intrusive, evidence-based way. It works with `smart_phase_tracker.py` to show users WHAT they've accomplished, not just progress percentages.

### Design Principles

1. **Show, don't force** — Surface what the AI knows, let user decide
2. **Evidence-based** — Always show WHY the AI thinks something
3. **Confidence-gated** — Only suggest when confidence is high
4. **Contextual** — Guidance appears naturally, not as interruptions
5. **Actionable** — Every insight comes with clear options

### Insight Types

| Type | When Shown | User Actions |
|------|------------|--------------|
| `READY` | Phase complete (confidence >0.8) | `next_phase`, `explore_more` |
| `GAP` | Almost complete, missing elements | `explore_gaps`, `next_phase` |
| `PROGRESS` | Making progress, encouragement | `continue`, `show_full_progress` |
| `NONE` | Not enough confidence or too early | (silent) |

### User Preferences

Users can configure insight frequency via `insight_mode` setting:

| Mode | Min Turns | Confidence Threshold | Shows |
|------|-----------|---------------------|-------|
| `minimal` | 8 | 0.9 | Only completion |
| `balanced` | 4 | 0.7 | Progress + completion |
| `detailed` | 2 | 0.5 | Frequent updates |

### Integration for New Workshop Bots

For a workshop bot to work with Phase Insights:

#### 1. Enable `has_phases: True` in BOTS dict
```python
BOTS["myworkshop"] = {
    "name": "My Workshop",
    "has_phases": True,  # REQUIRED for phase insights
    # ...
}
```

#### 2. Define phases with clear names in WORKSHOP_PHASES
```python
WORKSHOP_PHASES["myworkshop"] = [
    {"name": "Introduction", "status": "ready"},
    {"name": "Problem Discovery", "status": "pending"},
    {"name": "Solution Design", "status": "pending"},
    {"name": "Validation", "status": "pending"},
    {"name": "Synthesis", "status": "pending"},
]
```

#### 3. System prompt should reference phase goals
The bot's system prompt should include clear descriptions of what each phase accomplishes. This helps `smart_phase_tracker.py` detect completion:

```python
## Workshop Phases
1. **Introduction** - User introduces their problem domain and context
2. **Problem Discovery** - Identify root causes and stakeholders
3. **Solution Design** - Generate and evaluate alternatives
4. **Validation** - Test assumptions and gather evidence
5. **Synthesis** - Consolidate findings and next steps
```

#### 4. Completion evidence keywords
The smart phase tracker looks for evidence in conversation. Include methodology-specific keywords in your prompt that signal phase completion:

- Introduction: "context", "background", "domain", "industry"
- Problem phases: "root cause", "stakeholder", "constraint", "assumption"
- Solution phases: "alternative", "option", "approach", "design"
- Validation: "test", "evidence", "data", "confirmed"
- Synthesis: "summary", "conclusion", "next steps", "action items"

### Key Files

- `tools/phase_insights.py` - User-facing insight generation
- `tools/smart_phase_tracker.py` - LLM-based phase analysis
- `public/elements/WorkshopRoadmap.jsx` - Visual sidebar component

### Action Callbacks

Phase insights generate these action callbacks:

| Action | Handler | Purpose |
|--------|---------|---------|
| `next_phase` | `on_next_phase()` | Advance to next phase |
| `prev_phase` | `on_prev_phase()` | Go back to previous phase |
| `explore_gaps` | `on_explore_gaps()` | Explore missing elements |
| `explore_more` | `on_explore_more()` | Continue in current phase |
| `show_full_progress` | `on_show_full_progress()` | Detailed progress view |

### Example Insight Flow

```
User: [Completes discussing problem stakeholders]
AI Response: [Normal response about stakeholders]

[If confidence > 0.7 and gaps identified]
Phase Insight Message:
───── 📍 Problem Discovery Progress ─────

**Covered so far:**
• Identified key stakeholders
• Mapped decision-making process

**Still to explore:**
• Resource constraints
• Timeline pressures

*Would you like to dig into these, or move forward?*

[Buttons: 🎯 Explore Gaps | Next Phase →]
```

---

## Video Support

Tutorial videos can be embedded per workshop bot and phase.

### Configuring Videos

Edit `WORKSHOP_VIDEOS` in `utils/media.py`:

```python
WORKSHOP_VIDEOS = {
    "tta": {
        "intro": "https://youtube.com/watch?v=VIDEO_ID",
        "phase_1": "https://youtube.com/watch?v=PHASE1_ID",
        "phase_2": "https://vimeo.com/VIDEO_ID",
    },
    "ackoff": {
        "intro": "https://youtu.be/SHORT_ID",
        # ... phases
    },
}
```

### Supported Video Sources

- YouTube (full URL, short URL, embed)
- Vimeo
- Direct MP4 URLs
- Supabase Storage URLs

### Video Utility Functions

```python
from utils.media import (
    create_video_element,      # Create video from URL or path
    get_workshop_video,        # Get video for bot + phase
    set_workshop_video,        # Programmatically set video URL
    extract_youtube_id,        # Parse YouTube URLs
    get_youtube_thumbnail,     # Get video thumbnail
)
```

---

## LangExtract - Structured Data Extraction

Zero-latency extraction of structured insights from conversations, research, and documents.

### Two Modes

| Mode | Latency | How It Works |
|------|---------|--------------|
| `instant_extract()` | <5ms | Regex patterns - statistics, assumptions, questions |
| `background_extract()` | 0ms to chat | LLM-based, runs async after response |

### What Gets Extracted

- **Statistics**: Percentages, money, large numbers
- **Assumptions**: Stated and hidden assumptions
- **Problems/Solutions**: PWS-relevant elements
- **Questions**: Open questions raised
- **Sources**: Citations and quotes
- **PWS Quality Scores**: Problem clarity, data grounding, assumption awareness

### Storage

- **In-memory cache**: Fast access during session
- **Supabase bucket**: Persistent storage in `extractions/` folder as JSON

### Usage

```python
from tools.langextract import instant_extract, background_extract_conversation

# Instant (no API calls)
signals = instant_extract(text)

# Deep (runs in background)
structured = await background_extract_conversation(history, bot_name)
```

---

## User Feedback System (Native Chainlit)

Built-in human feedback system using Chainlit's native feedback collection with automatic UI.

### How It Works

1. **Automatic UI**: Chainlit shows thumbs up/down buttons on ALL AI messages automatically
2. **User clicks** to rate a response (and optionally add a comment)
3. **Native data layer** (`utils/data_layer.py`) handles storage via `upsert_feedback()`
4. **Multi-storage**: PostgreSQL (via SQLAlchemy), CSV export, and Supabase

### Configuration

**Step 1: Enable in Config** (already done)
```toml
# .chainlit/config.toml
[features]
feedback = true
```

**Step 2: Data Layer** (already configured)
The `MindrianDataLayer` in `utils/data_layer.py` extends Chainlit's SQLAlchemyDataLayer with:
- Automatic CSV export to `analytics/feedback_analytics.csv`
- Supabase storage in `feedback/{date}/{feedback_id}.json`
- In-memory cache for fast analytics

### Storage Locations

| Storage | Location | Purpose |
|---------|----------|---------|
| PostgreSQL | `DATABASE_URL` | Primary persistence (Chainlit native) |
| CSV | `analytics/feedback_analytics.csv` | Local analytics export |
| Supabase | `feedback/{date}/{id}.json` | Cloud backup |
| Memory | `data_layer.feedback_cache` | Session analytics |

### Feedback Data Structure

```json
{
  "feedback_id": "abc123...",
  "message_id": "msg456...",
  "value": 1,
  "comment": "Optional user comment",
  "timestamp": "2026-01-22T10:30:00Z",
  "date": "2026-01-22",
  "user_id": "user@email.com",
  "bot_id": "lawrence",
  "phase": "Introduction",
  "rating": "positive"
}
```

### Feedback Analytics

```python
# Access via data layer
data_layer = cl.data._data_layer
stats = data_layer.get_feedback_stats(date="2026-01-22", bot_id="lawrence")
# Returns: total, positive, negative, satisfaction_rate, by_bot, recent_negative

report = data_layer.export_feedback_report()  # Markdown report

# Or use standalone CSV function
from utils.data_layer import get_csv_feedback_stats
stats = get_csv_feedback_stats()
```

### Key Files

- `utils/data_layer.py` - MindrianDataLayer with feedback handling
- `.chainlit/config.toml` - `feedback = true` setting
- `analytics/feedback_analytics.csv` - Exported feedback data

---

## PWS Audiobook Chapters

Embed audio content from PWS course materials by topic and chapter.

### How It Works

1. User clicks "📖 Listen to Chapter" button
2. System analyzes conversation context for relevant chapters
3. Shows matching chapters or all chapters for current bot
4. User selects a chapter to play inline audio

### Configuring Chapters

Edit `AUDIOBOOK_CHAPTERS` in `utils/media.py`:

```python
AUDIOBOOK_CHAPTERS = {
    "pws_foundation": {
        "chapter_1": {
            "title": "Introduction to Problems Worth Solving",
            "url": "https://your-supabase-url/audio/pws_intro.mp3",
            "duration": "15:00",
            "keywords": ["problem", "worth solving", "introduction"],
            "bot_relevance": ["lawrence", "larry_playground"],
        },
        # ... more chapters
    },
    "trending_to_absurd": { ... },
    "jobs_to_be_done": { ... },
    "s_curve": { ... },
    "ackoffs_pyramid": { ... },
    "red_teaming": { ... },
}
```

### Programmatic Configuration

```python
from utils.media import set_audiobook_chapter

# Add or update a chapter
set_audiobook_chapter(
    topic="pws_foundation",
    chapter_id="chapter_1",
    url="https://storage.supabase.co/audio/pws_ch1.mp3",
    title="Introduction to PWS",
    duration="15:00",
    keywords=["problem", "introduction"]
)
```

### Utility Functions

```python
from utils.media import (
    get_audiobook_chapter,           # Get audio element for a chapter
    find_relevant_chapters,          # Find chapters matching conversation context
    get_chapters_for_bot,            # Get all chapters for a bot
    list_configured_audiobook_chapters,  # List all configured chapters
)
```

### Contextual Suggestions

The system automatically suggests relevant chapters based on:
1. **Bot relevance**: Each chapter lists which bots it's relevant to
2. **Keyword matching**: Conversation text is matched against chapter keywords
3. **Topic mapping**: Bots are mapped to relevant topics (e.g., TTA → trending_to_absurd)

---

## Debugging

### Check logs
```bash
# Render logs
render logs --service mindrian

# Local
chainlit run mindrian_chat.py  # stdout shows logs
```

### Common issues

1. **"API Key not found"** - Check .env file exists and has GOOGLE_API_KEY
2. **Database connection fails** - Verify CHAINLIT_DATABASE_URL format
3. **Voice not working** - Check ELEVENLABS_API_KEY
4. **Files not persisting** - Check Supabase storage config

---

## Multi-Agent System

The platform now supports multi-agent workflows where multiple agents collaborate on a single query.

### Agent Types

**Conversation Agents** (PWS methodology experts):
- lawrence, larry_playground, tta, jtbd, scurve, redteam, ackoff
- Each has a specialized system prompt
- Provide expert perspectives

**Background Agents** (with tool access):
- `research`: Web search via Tavily, multi-query planning
- `validation`: Camera Test, fact-checking, DIKW validation
- `analysis`: Pattern recognition, data extraction

### Triggering Multi-Agent Analysis

**User-triggered:**
1. User clicks "Multi-Agent Analysis" button
2. Chooses analysis type (Quick/Research/Validate/Full)
3. System runs agent pipeline
4. Results displayed with cl.Step visualization

**Preset workflows:**
```python
from agents.multi_agent_graph import (
    quick_analysis,           # Router picks agents
    research_and_explore,     # Research → TTA → Larry
    validated_decision,       # Validation → Ackoff → Red Team
    full_analysis_with_research  # All agents
)

result = await full_analysis_with_research("Should I pivot to AI?")
```

### Adding New Background Agents

1. Create class extending `BackgroundAgent`:
```python
class MyAgent(BackgroundAgent):
    def __init__(self):
        super().__init__(name="My Agent", description="...")

    async def run(self, query: str, context: dict = None) -> dict:
        # Your tool logic here
        return {"success": True, "result": "..."}
```

2. Register in `BACKGROUND_AGENTS`:
```python
BACKGROUND_AGENTS["myagent"] = MyAgent()
```

3. Use in workflows:
```python
result = await run_enhanced_workflow(
    query,
    conversation_agents=["lawrence"],
    background_agents=["myagent", "research"]
)
```

---

## A2A Protocol - Agent-to-Agent Communication

Structured handoff system using Markdown files for agent-to-agent communication.

> **IMPORTANT**: See `docs/A2A_PRACTICAL_ARCHITECTURE.md` for the latest architectural decisions including:
> - Two-stage classification (Cynefin + PWS) inline in Python
> - Artifacts vs Frames context separation
> - Red Team as cross-cutting middleware (not a stage)
> - Journey Mapping as cross-cutting view
> - MVP: 4 agents (TTA, JTBD, Red Team, Validation)

### Core Architectural Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| **Classification** | Two-stage inline | Cynefin (uncertainty) + PWS (lifecycle). No separate service until multiple clients need it. |
| **Context** | Artifacts vs Frames | Agent speculation stays scoped; validated insights persist. |
| **Red Team** | Middleware/checkpoint | Applies to ANY stage, not just a destination. |
| **Journey Mapping** | Cross-cutting view | Any agent can request user's journey context. |

### Core Concept

```
┌─────────────┐    ┌──────────────────┐    ┌─────────────┐
│   Agent A   │ -> │  handoff.md file │ -> │   Agent B   │
│  (Lawrence) │    │  (structured)    │    │    (TTA)    │
└─────────────┘    └──────────────────┘    └─────────────┘
```

### Handoff Types

| Type | Purpose | Return Expected |
|------|---------|-----------------|
| `SWITCH` | User moves to different agent | No |
| `DELEGATE` | Agent asks another for help | Yes |
| `CONSULT` | Quick question | Yes (immediate) |
| `RETURN` | Returning from delegation | No |

### Handoff MD File Structure

```markdown
---
protocol: a2a/v1
from_agent: lawrence
to_agent: tta
handoff_type: delegate
expects_return: true
---

# Agent Handoff: Lawrence → TTA

## Context Summary
User exploring urban farming. Need to stress-test assumption.

## Key Entities Extracted
- **Problem**: Urban farming economics
- **Assumption**: Vertical farming is too expensive

## Tasks for Receiving Agent
- [ ] Apply TTA framework to assumption
- [ ] Return synthesis when complete
```

### Context Journal

A living MD document that evolves with conversation, tracking thinking steps:

```markdown
### 💡 Insight (Lawrence) — Turn 5
*10:05:00*

User is conflating "urban farming" with "vertical farming".
This opens up the solution space significantly.

### ✅ Decision (TTA) — Turn 13
*10:18:00*

Reframe completed. User now sees this as a logistics problem.
```

### Integration

```python
from protocols import (
    create_switch_handoff,
    save_handoff,
    inject_handoff_context,
    get_journal,
    log_thinking,
)

# On agent switch
handoff = await create_switch_handoff(
    from_agent="lawrence",
    to_agent="tta",
    session_id=session_id,
    history=history,
    context_summary="User ready to stress-test assumptions"
)
save_handoff(handoff)

# Log thinking steps
journal = get_journal(session_id)
journal.log_insight("lawrence", "User conflating two problem spaces")

# Inject context into new agent
system_prompt = inject_handoff_context(handoff, TTA_PROMPT)
```

### Key Files

- `protocols/a2a_protocol.py` - Handoff creation, parsing, storage
- `protocols/context_journal.py` - Living document management
- `journals/` - Session journal files
- `handoffs/` - Handoff MD files

---

## Contact / Resources

- **GitHub:** https://github.com/jsagir/mindrian-deploy
- **Live Demo:** https://mindrian.onrender.com
- **Methodology:** Problems Worth Solving (PWS)
