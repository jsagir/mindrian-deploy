# Claude Code Project Guide - Mindrian

This file is for AI assistants (Claude Code, etc.) to quickly understand this project and continue development effectively.

---

## Quick Context

**What is Mindrian?**
A Chainlit-based multi-bot platform for PWS (Problems Worth Solving) methodology workshops. Users chat with specialized AI bots (Larry, Ackoff, TTA, etc.) to work through structured innovation frameworks.

**Tech Stack:**
- **Frontend/UI:** Chainlit 2.9+
- **AI Model:** Google Gemini (gemini-3-flash-preview, gemini-2.0-flash)
- **RAG:** Gemini File Search
- **Database:** Supabase PostgreSQL (via SQLAlchemy + asyncpg)
- **Storage:** Supabase Storage
- **Voice:** ElevenLabs TTS
- **Research:** Tavily Search API

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
│   └── tavily_search.py     # Tavily web search wrapper
├── utils/                   # Utility modules
│   ├── charts.py            # Plotly visualizations (DIKW pyramid, S-curve, DataFrames)
│   ├── gemini_rag.py        # Gemini File Search cache utilities
│   ├── file_processor.py    # PDF/DOCX/TXT extraction
│   ├── media.py             # ElevenLabs TTS, file exports
│   └── storage.py           # Supabase Storage integration
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
    "larry": { "name": "Larry", "icon": "🧠", "system_prompt": LARRY_PROMPT, ... },
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
    "larry": [cl.Starter(label="...", message="...", icon="..."), ...],
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

### Adding a New Bot/Agent

**⚠️ CRITICAL: Follow ALL 9 steps. Missing steps 7-8 will break dynamic agent switching!**

1. **Create system prompt** in `prompts/new_bot.py`:
```python
NEW_BOT_PROMPT = """
You are [name], specialized in [methodology].
...
"""
```

2. **Export in `prompts/__init__.py`**:
```python
from .new_bot import NEW_BOT_PROMPT
```

3. **Add to BOTS dict** in `mindrian_chat.py`:
```python
BOTS["newbot"] = {
    "name": "New Bot Name",
    "icon": "🆕",
    "description": "What this bot does",
    "system_prompt": NEW_BOT_PROMPT,
    "has_phases": True,  # or False for non-workshop bots
    "welcome": "Welcome message..."
}
```

4. **Add phases** (if workshop bot):
```python
WORKSHOP_PHASES["newbot"] = [
    {"name": "Phase 1", "status": "ready"},
    {"name": "Phase 2", "status": "pending"},
    # ...
]
```

5. **Add starters**:
```python
STARTERS["newbot"] = [
    cl.Starter(label="Option 1", message="...", icon="/public/icons/icon.svg"),
    cl.Starter(label="Option 2", message="...", icon="/public/icons/icon.svg"),
    cl.Starter(label="Option 3", message="...", icon="/public/icons/icon.svg"),
    cl.Starter(label="Option 4", message="...", icon="/public/icons/icon.svg"),
]
```

6. **Add chat profile** in `chat_profiles()`:
```python
cl.ChatProfile(
    name="newbot",
    markdown_description=BOTS["newbot"]["description"],
    icon=BOTS["newbot"]["icon"],
),
```

7. **⚠️ REQUIRED: Add agent trigger keywords** in `AGENT_TRIGGERS` dict:
```python
AGENT_TRIGGERS = {
    # ... existing agents ...
    "newbot": {
        "keywords": ["keyword1", "keyword2", "relevant phrase"],
        "description": "Short description for suggestion button"
    },
}
```
**WHY THIS MATTERS:** The system analyzes conversation context and suggests relevant agents via buttons. Without trigger keywords, your new agent will never be suggested dynamically.

8. **⚠️ REQUIRED: Add switch callback** for dynamic agent switching:
```python
@cl.action_callback("switch_to_newbot")
async def on_switch_to_newbot(action: cl.Action):
    await handle_agent_switch("newbot")
```
**WHY THIS MATTERS:** When users click "Switch to NewBot" button during a conversation, this callback handles the switch while preserving context. Without it, the button click does nothing!

9. **Create SVG icons** in `public/icons/` if needed

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
- `GOOGLE_API_KEY` - Google AI API key

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

## Recent Changes (v3.0)

1. **Chain of Thought** - `@cl.step` for transparent reasoning
2. **Conversation Starters** - 4 per bot in STARTERS dict
3. **Chat Settings** - Research depth, examples, verbosity
4. **Session Persistence** - PostgreSQL via Supabase
5. **ElevenLabs Voice** - TTS integration
6. **Document Processing** - PDF/DOCX extraction
7. **Context Preservation** - Maintain history across bot switches
8. **Stop Handler** - Graceful interruption
9. **DIKW Pyramid Chart** - Plotly visualization

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

## Contact / Resources

- **GitHub:** https://github.com/jsagir/mindrian-deploy
- **Live Demo:** https://mindrian.onrender.com
- **Course:** EN.663.635 Problems Worth Solving - JHU
