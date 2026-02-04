# Edwards Onboarding Guide - Mindrian Codebase

**Date:** February 4, 2026
**Purpose:** Complete technical overview for Jonathan Edwards to understand and work on the Mindrian codebase

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Architecture Overview](#architecture-overview)
3. [Infrastructure Stack](#infrastructure-stack)
4. [Repository Structure](#repository-structure)
5. [The Monolith Problem](#the-monolith-problem)
6. [Key Files Deep Dive](#key-files-deep-dive)
7. [The Lazy Graph Breakthrough](#the-lazy-graph-breakthrough)
8. [Skills System](#skills-system)
9. [Protocol Governance](#protocol-governance)
10. [Frontend vs Backend Challenge](#frontend-vs-backend-challenge)
11. [Development Workflow](#development-workflow)
12. [Recommended Approach](#recommended-approach)

---

## Quick Start

### Deployment Branch
```
Triple-mode-v1---RENDER_DEPLOYMENT
```
This is the **currently deployed branch**. Always branch from this.

### Local Development
```bash
# Clone and checkout deployment branch
git clone https://github.com/jsagir/mindrian-deploy
cd mindrian-deploy
git checkout Triple-mode-v1---RENDER_DEPLOYMENT

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run locally
chainlit run mindrian_chat.py --watch
```

### Access Credentials
You should have been invited to:
- **Render** - Compute/deployment dashboard
- **Supabase** - Database/storage dashboard

API keys are managed in Render's environment variables (no local `.env` needed for production, but create one for local dev from `.env.example`).

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MINDRIAN ARCHITECTURE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                 │
│  │   ChainLit   │     │    Render    │     │   Supabase   │                 │
│  │   (Chat UI)  │────▶│  (Compute)   │────▶│  (Storage)   │                 │
│  │   Python     │     │  Serverless  │     │  PostgreSQL  │                 │
│  └──────────────┘     └──────────────┘     └──────────────┘                 │
│         │                                          │                         │
│         │                                          │                         │
│         ▼                                          ▼                         │
│  ┌──────────────┐                          ┌──────────────┐                 │
│  │   LangGraph  │                          │    Neo4j     │                 │
│  │ (Orchestration)                         │(Lazy Graph)  │                 │
│  │  Pipelines   │◀────────────────────────▶│ Relationships│                 │
│  └──────────────┘                          └──────────────┘                 │
│         │                                                                    │
│         ▼                                                                    │
│  ┌──────────────┐                                                           │
│  │ Google Gemini│                                                           │
│  │  (LLM API)   │                                                           │
│  └──────────────┘                                                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Purpose | Key Detail |
|-----------|---------|------------|
| **ChainLit** | Chat UI framework | Like Streamlit but for chatbots. Python-based. |
| **Render** | Compute & deployment | Auto-deploys on every push. 2GB memory limit. |
| **Supabase** | Database & file storage | PostgreSQL + blob storage. Content lives here. |
| **Neo4j** | Knowledge graph | Relationships ONLY (not embeddings). Fast lookups. |
| **LangGraph** | Agent orchestration | Multi-step pipelines, state management. |
| **Google Gemini** | LLM API | Primary AI model (gemini-2.5-flash). |

---

## Infrastructure Stack

### Render (Compute)
- **URL:** https://dashboard.render.com
- **Service:** Web service running Python
- **Deploy:** Auto-deploy on push to `Triple-mode-v1---RENDER_DEPLOYMENT`
- **Memory:** 2GB (upgraded from 512MB ceiling)
- **Start command:** `chainlit run mindrian_chat.py --host 0.0.0.0 --port $PORT -h`

### Supabase (Storage)
- **URL:** https://supabase.com/dashboard
- **Database:** PostgreSQL (conversation history, feedback, sessions)
- **Storage:** Blob storage for files, exports, audit logs
- **Tables:** threads, steps, feedback, session_events, etc.

### Neo4j (Graph)
- **Purpose:** Relationship mapping (the "intelligent" layer)
- **Architecture:** "Lazy Graph" - stores relationships, not embeddings
- **Query flow:** Graph finds relationships → Supabase fetches content

### Environment Variables (in Render)
```bash
GOOGLE_API_KEY          # Gemini API
TAVILY_API_KEY          # Web research
DATABASE_URL            # PostgreSQL connection
SUPABASE_URL            # Supabase project URL
SUPABASE_SERVICE_KEY    # Supabase auth
NEO4J_URI               # Neo4j connection
NEO4J_USER              # Neo4j auth
NEO4J_PASSWORD          # Neo4j auth
ELEVENLABS_API_KEY      # Voice (optional)
```

---

## Repository Structure

```
mindrian-deploy/
│
├── mindrian_chat.py          # ⚠️ THE MONOLITH - Main app (10K+ lines)
│                              # Contains: routing, agents, UI, everything
│
├── prompts/                   # 🍞 System prompts for all 17 bots
│   ├── larry_core.py          # Lawrence's personality
│   ├── tta_workshop.py        # Trending to the Absurd
│   ├── jtbd_workshop.py       # Jobs to Be Done
│   └── [14 more...]
│
├── skills/                    # 🤖 Claude Code skills (auto-updating)
│   ├── _knowledge/            # Auto-generated change logs
│   ├── langgraph/             # LangGraph patterns
│   └── mindrian-stack/        # Architecture reference
│
├── intelligence/              # 🧠 LangGraph pipelines
│   ├── pipelines/
│   │   ├── message_router.py  # Routes by intent
│   │   ├── file_processing.py # Upload → Extract → Embed
│   │   ├── sequential_thinking.py # ThinkingPanel analysis
│   │   └── [more pipelines...]
│   └── agents/                # Multi-agent orchestration
│
├── tools/                     # 🔧 External integrations
│   ├── tavily_search.py       # Web research
│   ├── graphrag_lite.py       # Neo4j + vector hybrid
│   ├── pws_brain.py           # Gemini File Search
│   └── langextract.py         # Structured extraction
│
├── memory/                    # 💾 Persistent user journeys
│   ├── user_journey.py        # Journey tracking
│   └── checkpointer.py        # LangGraph state persistence
│
├── callbacks/                 # 🔘 Action button handlers (extracted)
│   ├── agent_switch.py        # Bot switching logic
│   └── research.py            # Research workflows
│
├── protocols/                 # 📋 Governance & quality gates
│   ├── a2a_protocol.py        # Agent-to-agent handoffs
│   └── triple_mode.py         # Entry point handling
│
├── utils/                     # 🛠️ Utilities
│   ├── charts.py              # Plotly visualizations
│   ├── diagrams.py            # Mermaid diagram generation
│   ├── file_processor.py      # PDF/DOCX extraction
│   ├── data_layer.py          # Database + feedback
│   └── session_logger.py      # Event tracking
│
├── public/elements/           # 🎨 Custom UI components (JSX)
│   ├── ThinkingPanel.jsx      # AI reasoning display
│   ├── MermaidDiagram.jsx     # Mind maps
│   └── WorkshopRoadmap.jsx    # Phase sidebar
│
├── scripts/                   # 📊 Admin & utility scripts
│   ├── conversation_sampler.py # CLI for browsing conversations
│   ├── admin_dashboard.py     # Streamlit analytics dashboard
│   ├── daily_summary.py       # Email reports
│   └── health_check.py        # System verification
│
├── governance/                # 🛡️ Safety & compliance
│   ├── audit_trail.py         # Response logging
│   └── ai_monitor.py          # Safety checks
│
├── R&D/                       # 📝 Research notes (markdown only)
│   └── [exploration ideas...]
│
├── qa/                        # 🐛 QA feedback by date
│   └── 2026-02-04/
│
└── docs/                      # 📚 Documentation
    ├── EDWARDS_ONBOARDING.md  # THIS FILE
    ├── MINDRIAN_CHAT_STRUCTURE.md
    └── [more docs...]
```

---

## The Monolith Problem

### The Challenge

`mindrian_chat.py` has grown to **10,000+ lines** and contains:

1. **Routing logic** - Decides which agent handles what
2. **Agent orchestration** - LangGraph-style state management
3. **UI elements** - ChainLit components, buttons, panels
4. **Business logic** - Workshop phases, progress tracking
5. **Action callbacks** - 70+ button handlers
6. **Data persistence** - Context saving, session management

### Why It's Hard to Refactor

1. **Interdependencies** - Everything references everything
2. **ChainLit quirks** - Some "backend" code is actually UI (like `cl.Step`)
3. **Unknown deletability** - Can't tell what's safe to remove
4. **AI-generated code** - Generated fast, maintenance is hard

### Current State

```python
# mindrian_chat.py structure (simplified)

# Lines 1-500: Imports, configs, BOTS dict
BOTS = {"lawrence": {...}, "tta": {...}, ...}  # 17 agents
STARTERS = {...}  # Conversation starters
WORKSHOP_PHASES = {...}  # Phase definitions

# Lines 500-1000: Utility functions
async def capture_reasoning_steps(...)  # ThinkingPanel
async def show_thinking_panel(...)
context_store = {}  # In-memory context

# Lines 1000-3000: ChainLit decorators
@cl.on_chat_start
@cl.on_message
@cl.on_chat_resume
@cl.on_stop

# Lines 3000-8000: Action callbacks
@cl.action_callback("next_phase")
@cl.action_callback("deep_research")
# ... 70+ more callbacks

# Lines 8000-10000: Main message handler
# The beast - handles everything
```

### Refactoring Strategy

See `docs/MINDRIAN_CHAT_STRUCTURE.md` for a detailed breakdown of what each section does.

**Recommended approach:**
1. Don't delete anything yet
2. Extract callbacks to `callbacks/` (already started)
3. Extract pipelines to `intelligence/pipelines/` (already started)
4. Keep `mindrian_chat.py` as the orchestrator
5. Test thoroughly after each extraction

---

## Key Files Deep Dive

### mindrian_chat.py (The Monolith)

**Purpose:** Main application entry point and orchestrator

**Key sections:**
| Lines | Content | Can Extract? |
|-------|---------|--------------|
| 1-100 | Imports | No |
| 100-500 | BOTS, STARTERS, PHASES dicts | Maybe → `config/bots.py` |
| 500-600 | ThinkingPanel functions | Done → `intelligence/pipelines/sequential_thinking.py` |
| 600-1000 | Context preservation | Maybe → `memory/context.py` |
| 1000-1500 | `@cl.on_chat_start` | No (ChainLit decorator) |
| 1500-3000 | `@cl.on_message` | No (ChainLit decorator) |
| 3000-8000 | Action callbacks | Partially done → `callbacks/` |
| 8000+ | Helper functions | Case by case |

### prompts/ (System Prompts)

**Purpose:** Define each bot's personality and behavior

**Structure:**
```python
# prompts/larry_core.py
LARRY_RAG_SYSTEM_PROMPT = """
You are Lawrence, a PWS methodology expert...
"""
```

These are the "bread and butter" - they define what each agent does.

### intelligence/pipelines/ (LangGraph Workflows)

**Purpose:** Multi-step processing workflows

**Key pipelines:**
| Pipeline | Purpose |
|----------|---------|
| `message_router.py` | Routes by intent (feedback/image/file/grading) |
| `file_processing.py` | Upload → Extract → Chunk → Embed |
| `sequential_thinking.py` | 5-step analysis for ThinkingPanel |
| `minto_pyramid.py` | SCQA deep research |
| `grading.py` | Assessment with evidence |

### tools/ (External Integrations)

**Purpose:** Connect to external services

| Tool | Service | Purpose |
|------|---------|---------|
| `tavily_search.py` | Tavily API | Web research |
| `graphrag_lite.py` | Neo4j | Hybrid RAG (relationships + vectors) |
| `pws_brain.py` | Gemini File Search | Course material retrieval |
| `langextract.py` | Google | Structured extraction |

### public/elements/ (Custom UI)

**Purpose:** React/JSX components for ChainLit

**Important:** These are JSX files, not Python. ChainLit renders them.

```jsx
// public/elements/ThinkingPanel.jsx
export default function ThinkingPanel({ steps, botId, ... }) {
  // React component
}
```

**Limitation:** ChainLit's React integration is "not good" - components sometimes work, sometimes don't.

---

## The Lazy Graph Breakthrough

### Before (Slow)
```
User Input → Neo4j (embeddings + relationships) → Response
             ↑
        Everything stored in graph
        Slow queries, big graph
```

### After (Fast - Current Architecture)
```
User Input → Neo4j (relationships ONLY) → Find related concepts
                    ↓
             Supabase (actual content) → Fetch relevant text
                    ↓
                Response
```

### Why It's Better

1. **Neo4j is lightweight** - Only stores relationships, not content
2. **Supabase handles content** - Optimized for text retrieval
3. **Queries are fast** - Graph traversal is quick
4. **Scalable** - Can add content without bloating the graph

### Implementation

```python
# tools/graphrag_lite.py

async def enrich_for_larry(message: str, turn_count: int) -> Optional[str]:
    """
    Hybrid RAG: Neo4j for relationships, Supabase for content.

    1. Query Neo4j for related concepts/frameworks
    2. Use those relationships to fetch actual content from Supabase
    3. Return enriched context
    """
```

---

## Skills System

### What It Is

The `skills/` folder contains instructions that Claude Code reads at session start. Every time a Claude coding session begins, it loads these skills to understand the codebase.

### Auto-Updating

A git hook (`scripts/update_consultant_knowledge.py`) runs on every commit:
1. Analyzes recent commits
2. Updates `skills/_knowledge/RECENT_CHANGES.md`
3. Updates `skills/_knowledge/QA_RELEVANT_CHANGES.md`
4. Updates `skills/_knowledge/RND_RELEVANT_CHANGES.md`

### Using Skills

```bash
# In Claude Code session:
"Load the Mindrian skills and help me understand the message router"
```

Claude will read the skills and have full context of the codebase patterns.

---

## Protocol Governance

### What It Is

The `protocols/` folder contains governance rules. Before code changes are implemented, they're checked against these protocols.

### Key Protocols

| File | Purpose |
|------|---------|
| `a2a_protocol.py` | Agent-to-agent handoff rules |
| `triple_mode.py` | Entry point handling (Problem/Topic/File) |
| `context_journal.py` | Living document tracking thinking steps |

### How It Works

```python
# Example: Before switching agents
from protocols import create_switch_handoff

handoff = await create_switch_handoff(
    from_agent="lawrence",
    to_agent="tta",
    session_id=session_id,
    history=history,
)
# Protocol validates the switch and creates proper handoff document
```

---

## Frontend vs Backend Challenge

### The Problem

ChainLit blurs the line between frontend and backend:

```python
# This looks like backend code...
async with cl.Step(name="Thinking", type="llm") as step:
    step.output = "Analysis complete"
# ...but it renders UI elements!
```

### What's Actually UI

| Code | Looks Like | Actually Is |
|------|------------|-------------|
| `cl.Message()` | Backend | UI (chat bubble) |
| `cl.Step()` | Backend | UI (collapsible panel) |
| `cl.Action()` | Backend | UI (button) |
| `cl.TaskList()` | Backend | UI (progress tracker) |
| `@cl.action_callback` | Backend | UI event handler |
| `cl.CustomElement()` | Backend | UI (renders JSX) |

### What's Actually Backend

| Code | Purpose |
|------|---------|
| `intelligence/pipelines/*` | Processing workflows |
| `tools/*` | External API calls |
| `memory/*` | State persistence |
| `prompts/*` | System prompts (text only) |

### Recommendation

When classifying code:
1. Anything with `cl.` prefix is UI-related
2. Anything in `public/elements/` is pure UI
3. Anything that "renders" or "displays" is UI
4. Everything else is backend

---

## Development Workflow

### Branching Strategy

```
main                          # Original Detroit demo (stable)
  │
  └── Triple-mode-v1          # Development branch
        │
        └── Triple-mode-v1---RENDER_DEPLOYMENT  # DEPLOYED BRANCH
              │
              └── your-feature-branch  # Work here
```

### Making Changes

1. **Branch from deployment:**
   ```bash
   git checkout Triple-mode-v1---RENDER_DEPLOYMENT
   git pull
   git checkout -b edwards/feature-name
   ```

2. **Make changes and test locally:**
   ```bash
   chainlit run mindrian_chat.py --watch
   ```

3. **Commit and push:**
   ```bash
   git add .
   git commit -m "feat: Description"
   git push origin edwards/feature-name
   ```

4. **Merge to deployment (or create PR):**
   ```bash
   git checkout Triple-mode-v1---RENDER_DEPLOYMENT
   git merge edwards/feature-name
   git push
   # Render auto-deploys
   ```

### Testing

```bash
# Health check
python scripts/health_check.py

# Run conversation sampler to browse sessions
python scripts/conversation_sampler.py

# Run Streamlit dashboard
streamlit run scripts/admin_dashboard.py
```

---

## Recommended Approach

### Phase 1: Understanding (Week 1)

1. **Read this document completely**
2. **Run the app locally** - Click through all 17 agents
3. **Read `MINDRIAN_CHAT_STRUCTURE.md`** - Understand the monolith
4. **Browse `prompts/`** - See how agents are defined
5. **Ask questions** - Jonathan is "very responsive"

### Phase 2: Mapping (Week 2)

1. **Use an LLM to analyze the repo:**
   ```
   "Analyze mindrian_chat.py and categorize each function as:
   - UI (renders something)
   - Backend (processes data)
   - Mixed (does both)"
   ```

2. **Create a map** of what depends on what
3. **Identify safe extraction candidates**

### Phase 3: Extraction (Week 3+)

1. **Start with callbacks** - Already partially done in `callbacks/`
2. **Extract one thing at a time**
3. **Test after each extraction**
4. **Don't delete anything until confirmed working**

### What NOT to Do

- ❌ Don't delete code you don't understand
- ❌ Don't refactor the main message handler yet
- ❌ Don't change the ChainLit decorator structure
- ❌ Don't touch protocol governance without discussion

### What TO Do

- ✅ Extract callbacks to `callbacks/`
- ✅ Move utility functions to `utils/`
- ✅ Create clear interfaces between components
- ✅ Add comments explaining what you learn
- ✅ Document any "gotchas" you discover

---

## Contact & Support

**Jonathan Sagir:** Available for questions (very responsive)

**Key Resources:**
- `docs/MINDRIAN_CHAT_STRUCTURE.md` - Detailed code breakdown
- `CLAUDE.md` - Quick reference for AI assistants
- `skills/` - Auto-updating knowledge base

**Live App:** https://mindrian.onrender.com

---

## Summary

| Aspect | Status |
|--------|--------|
| **Core app** | Working but monolithic |
| **Architecture** | Solid (Lazy Graph is good) |
| **Code quality** | Needs cleanup |
| **Documentation** | Improving |
| **Near-term goal** | Separate UI from backend |
| **Long-term goal** | Sellable product |

The system works. The code needs organization. The opportunity is real.

Welcome aboard! 🚀
