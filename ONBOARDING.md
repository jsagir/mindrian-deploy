# Mindrian Developer Onboarding Guide

Welcome to the Mindrian platform! This guide will help you set up your development environment and understand the core concepts.

## Quick Start (5 minutes)

```bash
# 1. Clone and enter
git clone https://github.com/jsagir/mindrian-deploy.git
cd mindrian-deploy

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy environment template
cp .env.example .env

# 5. Add your API key (minimum required)
echo "GOOGLE_API_KEY=your-gemini-api-key" >> .env

# 6. Run the app
chainlit run mindrian_chat.py --watch
```

Open http://localhost:8000 in your browser.

---

## Environment Variables

### Required

| Variable | Purpose | How to Get |
|----------|---------|------------|
| `GOOGLE_API_KEY` | Gemini AI model | [Google AI Studio](https://aistudio.google.com/apikey) |

### Recommended

| Variable | Purpose | How to Get |
|----------|---------|------------|
| `TAVILY_API_KEY` | Web research | [Tavily](https://tavily.com/) |
| `CHAINLIT_DATABASE_URL` | Session persistence | PostgreSQL connection string |

### Optional

| Variable | Purpose |
|----------|---------|
| `ELEVENLABS_API_KEY` | Voice responses |
| `SUPABASE_URL` | File storage |
| `SUPABASE_SERVICE_KEY` | Storage auth |
| `NEO4J_URI` | Knowledge graph |
| `NEO4J_USER` / `NEO4J_PASSWORD` | Graph auth |

---

## Project Structure

```
mindrian-deploy/
├── mindrian_chat.py      # Main app (Chainlit handlers)
├── prompts/              # System prompts for each bot
├── tools/                # External tool integrations
├── utils/                # Utility functions
├── protocols/            # A2A communication protocol
├── governance/           # AI monitoring & safety
├── public/elements/      # Custom UI components (JSX)
├── R&D/                  # Research documentation
└── CLAUDE.md             # AI assistant instructions
```

### Key Files to Understand First

1. **`CLAUDE.md`** — Complete project guide (read this!)
2. **`mindrian_chat.py`** — Main application entry point
3. **`prompts/larry_core.py`** — Primary bot system prompt
4. **`tools/graphrag_lite.py`** — Knowledge graph integration

---

## Core Concepts

### 1. Bots / Agents

Mindrian has multiple specialized AI agents:

| Bot | Purpose | File |
|-----|---------|------|
| `lawrence` | Default PWS thinking partner | `prompts/larry_core.py` |
| `tta` | Trending to the Absurd | `prompts/tta_workshop.py` |
| `jtbd` | Jobs to Be Done | `prompts/jtbd_workshop.py` |
| `ackoff` | Ackoff's DIKW Pyramid | `prompts/ackoff_workshop.py` |

### 2. Workshop Phases

Workshop bots guide users through structured phases:

```python
WORKSHOP_PHASES["tta"] = [
    {"name": "Introduction", "status": "ready"},
    {"name": "Setup", "status": "pending"},
    {"name": "Extrapolation", "status": "pending"},
    {"name": "Analysis", "status": "pending"},
    {"name": "Synthesis", "status": "pending"},
]
```

### 3. A2A Protocol

Agents can hand off to each other using structured Markdown files:

```python
from protocols import create_switch_handoff, save_handoff

handoff = await create_switch_handoff(
    from_agent="lawrence",
    to_agent="tta",
    session_id=session_id,
    history=history
)
save_handoff(handoff)
```

### 4. Context Journal

A living document that tracks AI reasoning:

```python
from protocols import get_journal

journal = get_journal(session_id)
journal.log_insight("lawrence", "User conflating two problem spaces")
```

---

## Adding a New Bot

Use the generator script:

```bash
python scripts/generate_agent.py mybot "My Bot Name"
```

This creates all boilerplate. Manual steps in `CLAUDE.md` → "Adding a New Bot/Agent".

---

## Running Tests

```bash
# Health check (API, database, etc.)
python scripts/health_check.py

# Syntax validation
python -m py_compile mindrian_chat.py
```

---

## Common Tasks

### Add a new action button

```python
# In mindrian_chat.py

# 1. Add button to message
await cl.Message(
    content="Result",
    actions=[cl.Action(name="my_action", payload={}, label="Click Me")]
).send()

# 2. Add callback
@cl.action_callback("my_action")
async def on_my_action(action: cl.Action):
    await cl.Message(content="Button clicked!").send()
```

### Add a new tool

```python
# 1. Create tools/my_tool.py
def my_tool(param):
    return result

# 2. Import in mindrian_chat.py
from tools.my_tool import my_tool

# 3. Use in callback or message handler
result = my_tool(param)
```

### Add a custom UI component

```bash
python scripts/create_component.py MyComponent
```

See `skills/chainlit-components.md` for patterns.

---

## Debugging

### View logs

```bash
# Local
chainlit run mindrian_chat.py  # Logs to stdout

# Check specific module
python -c "from tools.graphrag_lite import *; print('OK')"
```

### Common issues

| Issue | Solution |
|-------|----------|
| "API Key not found" | Check `.env` has `GOOGLE_API_KEY` |
| Database connection fails | Verify `CHAINLIT_DATABASE_URL` format |
| Import error | Run `pip install -r requirements.txt` |

---

## Code Style

- **Docstrings**: Required for public functions
- **Type hints**: Encouraged but not enforced
- **Inline styles**: Required for JSX components (no shadcn imports)

---

## Getting Help

1. **Read `CLAUDE.md`** — Comprehensive project documentation
2. **Check `R&D/` folder** — Feature research and design docs
3. **Ask in Slack** — #mindrian-dev channel

---

## Next Steps

1. Run the health check: `python scripts/health_check.py`
2. Try switching between bots in the UI
3. Read through `prompts/larry_core.py` to understand the AI persona
4. Make a small change and test it locally

Welcome to the team!
