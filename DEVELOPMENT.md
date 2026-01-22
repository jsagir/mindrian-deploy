# Mindrian Development Guide

Complete guide for extending and maintaining the Mindrian platform.

---

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Adding New Bots/Agents](#adding-new-botsagents)
3. [Adding New Features](#adding-new-features)
4. [Adding Tools & Integrations](#adding-tools--integrations)
5. [Working with the UI](#working-with-the-ui)
6. [Database & Persistence](#database--persistence)
7. [Voice & Audio](#voice--audio)
8. [Charts & Visualizations](#charts--visualizations)
9. [Testing](#testing)
10. [Deployment](#deployment)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          MINDRIAN ARCHITECTURE                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  USER INPUT                                                              │
│  ├── Text messages → @cl.on_message                                     │
│  ├── Voice input → @cl.on_audio_start/chunk/end                         │
│  ├── File uploads → Processed in @cl.on_message                         │
│  └── Button clicks → @cl.action_callback("action_name")                 │
│                                                                          │
│  SESSION MANAGEMENT                                                      │
│  ├── @cl.on_chat_start → Initialize new session                         │
│  ├── @cl.on_chat_resume → Restore from database                         │
│  ├── @cl.on_stop → Handle cancellation                                  │
│  └── context_store → Cross-bot context preservation                     │
│                                                                          │
│  AI PROCESSING                                                           │
│  ├── System prompts → prompts/*.py                                      │
│  ├── Gemini API → google.genai.Client                                   │
│  ├── RAG → Gemini File Search                                           │
│  └── Research → Tavily Search API                                       │
│                                                                          │
│  OUTPUT                                                                  │
│  ├── Streaming text → cl.Message with stream_token()                    │
│  ├── Steps/CoT → cl.Step context manager                                │
│  ├── Charts → cl.Plotly elements                                        │
│  ├── Files → cl.File, cl.Pdf elements                                   │
│  └── Voice → ElevenLabs TTS → cl.Audio                                  │
│                                                                          │
│  PERSISTENCE                                                             │
│  ├── Conversations → SQLAlchemy → Supabase PostgreSQL                   │
│  ├── Files → Supabase Storage                                           │
│  └── Context → In-memory context_store (per server instance)            │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Adding New Bots/Agents

### Step 1: Create the System Prompt

Create `prompts/my_workshop.py`:

```python
MY_WORKSHOP_PROMPT = """
# My Workshop Bot

You are [Bot Name], an expert in [methodology/domain].

## Your Role
- Guide users through [specific process]
- Ask probing questions to understand context
- Provide structured frameworks and examples

## Workshop Phases
1. **Introduction**: Understand the user's context
2. **Analysis**: Apply the framework
3. **Synthesis**: Draw conclusions
4. **Action**: Define next steps

## Interaction Style
- Ask one question at a time
- Wait for responses before moving forward
- Provide examples when helpful
- Challenge assumptions constructively

## Key Frameworks
[Describe the methodology, tools, or frameworks this bot uses]

## Example Dialogue
User: I want to analyze X
You: Before we dive in, I need to understand...
"""
```

### Step 2: Export the Prompt

Edit `prompts/__init__.py`:

```python
from .larry_core import LARRY_RAG_SYSTEM_PROMPT
from .tta_workshop import TTA_WORKSHOP_PROMPT
from .jtbd_workshop import JTBD_WORKSHOP_PROMPT
from .scurve_workshop import SCURVE_WORKSHOP_PROMPT
from .redteam import REDTEAM_PROMPT
from .ackoff_workshop import ACKOFF_WORKSHOP_PROMPT
from .my_workshop import MY_WORKSHOP_PROMPT  # Add this line
```

### Step 3: Register the Bot

In `mindrian_chat.py`, add to the imports:

```python
from prompts import (
    LARRY_RAG_SYSTEM_PROMPT,
    TTA_WORKSHOP_PROMPT,
    # ... existing imports ...
    MY_WORKSHOP_PROMPT,  # Add this
)
```

Add to `BOTS` dict:

```python
BOTS = {
    # ... existing bots ...
    "mybot": {
        "name": "My Workshop Bot",
        "icon": "🔧",
        "description": "Workshop for [purpose]",
        "system_prompt": MY_WORKSHOP_PROMPT,
        "has_phases": True,
        "welcome": """🔧 **My Workshop**

Hello! I'm here to help you with [purpose].

Before we start, tell me:
1. What's your goal?
2. What have you tried?
3. What's at stake?

I'm listening."""
    }
}
```

### Step 4: Add Workshop Phases

```python
WORKSHOP_PHASES = {
    # ... existing phases ...
    "mybot": [
        {"name": "Introduction", "status": "ready"},
        {"name": "Analysis", "status": "pending"},
        {"name": "Synthesis", "status": "pending"},
        {"name": "Action Planning", "status": "pending"},
    ],
}
```

### Step 5: Add Conversation Starters

```python
STARTERS = {
    # ... existing starters ...
    "mybot": [
        cl.Starter(
            label="Analyze something",
            message="I want to analyze [topic] using your framework.",
            icon="/public/icons/analyze.svg",
        ),
        cl.Starter(
            label="Get started",
            message="Walk me through how this workshop works.",
            icon="/public/icons/start.svg",
        ),
        cl.Starter(
            label="See an example",
            message="Show me an example of this methodology in action.",
            icon="/public/icons/example.svg",
        ),
        cl.Starter(
            label="Quick assessment",
            message="I have a situation I need to assess quickly.",
            icon="/public/icons/quick.svg",
        ),
    ],
}
```

### Step 6: Add Chat Profile

In `chat_profiles()` function:

```python
@cl.set_chat_profiles
async def chat_profiles():
    return [
        # ... existing profiles ...
        cl.ChatProfile(
            name="mybot",
            markdown_description=BOTS["mybot"]["description"],
            icon=BOTS["mybot"]["icon"],
        ),
    ]
```

### Step 7: Add Agent Trigger Keywords (REQUIRED!)

**⚠️ CRITICAL: This enables dynamic "Switch to X" buttons based on conversation context.**

Add to `AGENT_TRIGGERS` dict in `mindrian_chat.py`:

```python
AGENT_TRIGGERS = {
    # ... existing agents ...
    "mybot": {
        "keywords": ["keyword1", "keyword2", "relevant phrase", "domain term"],
        "description": "One-line description shown on suggestion button"
    },
}
```

**Why this matters:**
- The system scans conversation for these keywords
- When found, a "Switch to MyBot" button appears dynamically
- Without this, your agent will NEVER be suggested mid-conversation

**Good keyword examples:**
- TTA: `["trend", "future", "extrapolate", "disruption", "10 years"]`
- Red Team: `["assumption", "risk", "fail", "challenge", "attack"]`
- Ackoff: `["validate", "data", "evidence", "ground truth", "dikw"]`


### Step 8: Add Switch Callback (REQUIRED!)

**⚠️ CRITICAL: This makes the "Switch to X" button actually work.**

Add this callback in `mindrian_chat.py`:

```python
@cl.action_callback("switch_to_mybot")
async def on_switch_to_mybot(action: cl.Action):
    await handle_agent_switch("mybot")
```

**Why this matters:**
- When user clicks "Switch to MyBot", this callback fires
- `handle_agent_switch()` preserves context and switches the active bot
- Without this, clicking the switch button does nothing!

**The callback name MUST follow this pattern:** `switch_to_{agent_id}`


### Step 9: Add Examples (Optional)

In `on_show_example()`, add examples for your bot:

```python
example_prompts = {
    # ... existing examples ...
    "mybot": [
        "Example for phase 1: Here's how to approach the introduction...",
        "Example for phase 2: When analyzing, look for these patterns...",
        "Example for phase 3: To synthesize, connect these dots...",
        "Example for phase 4: For action planning, consider these steps...",
    ],
}
```

---

## Checklist for Adding New Agents

Use this checklist every time you add a new bot:

- [ ] Step 1: System prompt created in `prompts/`
- [ ] Step 2: Prompt exported in `prompts/__init__.py`
- [ ] Step 3: Bot added to `BOTS` dict
- [ ] Step 4: Phases added to `WORKSHOP_PHASES` (if applicable)
- [ ] Step 5: Starters added to `STARTERS` dict
- [ ] Step 6: Chat profile added in `chat_profiles()`
- [ ] **Step 7: Agent triggers added to `AGENT_TRIGGERS`** ⚠️
- [ ] **Step 8: Switch callback added** ⚠️
- [ ] Step 9: Examples added (optional)
- [ ] SVG icons created (if needed)

**Missing Steps 7-8 = Dynamic switching won't work for your new agent!**

---

## Adding New Features

### Adding an Action Button

1. **Define the action** in `on_chat_start()`:

```python
actions.append(cl.Action(
    name="my_new_action",
    payload={"action": "my_action"},
    label="My Action",
    description="What this button does"
))
```

2. **Create the callback**:

```python
@cl.action_callback("my_new_action")
async def on_my_new_action(action: cl.Action):
    """Handle my new action button."""

    # Get context
    history = cl.user_session.get("history", [])
    bot = cl.user_session.get("bot", BOTS["larry"])

    # Do something with cl.Step for visibility
    async with cl.Step(name="Processing", type="run") as step:
        step.input = "Starting my action..."

        # Your logic here
        result = await do_something()

        step.output = "Completed!"

    # Send result
    await cl.Message(content=f"Result: {result}").send()
```

### Adding a Settings Option

1. **Add widget** in `get_settings_widgets()`:

```python
async def get_settings_widgets():
    return [
        # ... existing widgets ...
        Select(
            id="my_setting",
            label="My Setting",
            values=["option1", "option2", "option3"],
            initial_value="option1",
            description="What this setting controls",
        ),
    ]
```

2. **Use in message handler**:

```python
settings = cl.user_session.get("settings", {})
my_setting = settings.get("my_setting", "option1")

if my_setting == "option1":
    # Behavior for option 1
elif my_setting == "option2":
    # Behavior for option 2
```

### Adding File Type Support

1. **Update config.toml**:

```toml
[features.spontaneous_file_upload]
accept = ["...", "application/new-type", ".newext"]
```

2. **Add processor** in `utils/file_processor.py`:

```python
def extract_text_from_newtype(file_path: str) -> Tuple[str, dict]:
    """Extract text from new file type."""
    try:
        # Your extraction logic
        content = "extracted content"
        metadata = {"type": "newtype", "char_count": len(content)}
        return content, metadata
    except Exception as e:
        return "", {"error": str(e)}
```

3. **Register in processor**:

```python
def process_uploaded_file(file_path: str, file_name: str):
    ext = Path(file_name).suffix.lower()

    if ext == ".newext":
        return extract_text_from_newtype(file_path)
    # ... existing handlers
```

---

## Adding Tools & Integrations

### Creating a New Tool Module

1. **Create `tools/my_tool.py`**:

```python
"""
My Tool - Description of what it does
"""

import os
from typing import Dict, Any, Optional

# API configuration
MY_API_KEY = os.getenv("MY_API_KEY")

def my_tool_function(
    param1: str,
    param2: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Description of the function.

    Args:
        param1: What this parameter does
        param2: Optional parameter description

    Returns:
        Dictionary with results
    """
    if not MY_API_KEY:
        return {"error": "MY_API_KEY not configured"}

    try:
        # Your logic here
        result = call_external_api(param1, param2)
        return {"success": True, "data": result}
    except Exception as e:
        return {"error": str(e)}
```

2. **Use in mindrian_chat.py**:

```python
from tools.my_tool import my_tool_function

@cl.action_callback("use_my_tool")
async def on_use_my_tool(action: cl.Action):
    async with cl.Step(name="Using My Tool", type="tool") as step:
        result = my_tool_function("input")
        step.output = str(result)

    await cl.Message(content=f"Result: {result}").send()
```

### Adding MCP Server Integration

MCP tools are external servers. To integrate:

1. **Configure MCP server** (user's machine or cloud)

2. **Enable in config.toml**:
```toml
[features.mcp]
enabled = true
```

3. **Access via Chainlit's MCP client** (automatic)

---

## Working with the UI

### Chainlit Elements Reference

```python
# Text message
await cl.Message(content="Hello").send()

# Message with actions
await cl.Message(
    content="Choose an option:",
    actions=[cl.Action(name="opt1", ...), cl.Action(name="opt2", ...)]
).send()

# Streaming message
msg = cl.Message(content="")
await msg.send()
for chunk in stream:
    await msg.stream_token(chunk)
await msg.update()

# Step (Chain of Thought)
async with cl.Step(name="Thinking", type="llm") as step:
    step.input = "Input data"
    step.output = "Result"

# Chart (Plotly)
fig = go.Figure(...)
await cl.Message(elements=[cl.Plotly(figure=fig)]).send()

# PDF inline
await cl.Message(elements=[cl.Pdf(path="file.pdf", display="side")]).send()

# Audio
await cl.Message(elements=[cl.Audio(path="audio.mp3")]).send()

# File download
await cl.Message(elements=[cl.File(path="file.md", name="download.md")]).send()

# Image
await cl.Message(elements=[cl.Image(path="img.png", display="inline")]).send()

# Task list
task_list = cl.TaskList()
await task_list.add_task(cl.Task(title="Step 1", status=cl.TaskStatus.DONE))
await task_list.add_task(cl.Task(title="Step 2", status=cl.TaskStatus.RUNNING))
await task_list.send()
```

### Customizing config.toml

```toml
[project]
enable_telemetry = true
session_timeout = 3600      # Session timeout in seconds
allow_origins = ["*"]       # CORS origins

[features]
edit_message = true         # Allow message editing
multi_modal = true          # Allow file attachments

[features.spontaneous_file_upload]
enabled = true
accept = ["*/*"]            # Accepted MIME types
max_files = 10
max_size_mb = 50

[features.audio]
enabled = true
min_decibels = -45          # Silence threshold
max_duration = 15000        # Max recording ms

[UI]
name = "Mindrian"
description = "..."
hide_cot = false            # Show chain of thought
cot = "full"                # "full" or "tool_call"
github = "https://..."

[UI.theme.light]
background = "#fafafa"
paper = "#ffffff"

[UI.theme.dark]
background = "#1a1a2e"
paper = "#16213e"
```

---

## Database & Persistence

### Supabase PostgreSQL Setup

1. Create project at https://supabase.com
2. Get connection string: Project Settings → Database → URI
3. Set environment variable:
```bash
CHAINLIT_DATABASE_URL=postgresql://postgres:password@db.xxx.supabase.co:5432/postgres
```

### How Persistence Works

```python
# In mindrian_chat.py initialization:
if DATABASE_URL:
    from chainlit.data.sql_alchemy import SQLAlchemyDataLayer

    # Convert to asyncpg format
    db_url = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

    cl.data._data_layer = SQLAlchemyDataLayer(
        conninfo=db_url,
        ssl_require=True
    )
```

Chainlit automatically:
- Saves threads (conversations)
- Saves messages
- Saves user info
- Enables `@cl.on_chat_resume`

### Storing Custom Metadata

```python
# Store in thread metadata
cl.user_session.set("thread_metadata", {
    "chat_profile": "ackoff",
    "current_phase": 3,
    "phases": phases,
    "settings": settings,
})

# Retrieve on resume
metadata = thread.get("metadata", {})
```

---

## Voice & Audio

### ElevenLabs TTS

```python
# utils/media.py
from elevenlabs.client import ElevenLabs

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "default_voice")

async def text_to_speech(text: str) -> Optional[cl.Audio]:
    if not ELEVENLABS_API_KEY:
        return None

    client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

    audio = client.generate(
        text=text,
        voice=ELEVENLABS_VOICE_ID,
        model="eleven_monolingual_v1"
    )

    # Save to temp file
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        for chunk in audio:
            f.write(chunk)
        return cl.Audio(path=f.name, display="inline")
```

### Audio Input Processing

```python
@cl.on_audio_start
async def on_audio_start():
    cl.user_session.set("audio_chunks", [])
    return True  # Accept audio

@cl.on_audio_chunk
async def on_audio_chunk(chunk: cl.InputAudioChunk):
    chunks = cl.user_session.get("audio_chunks", [])
    chunks.append(chunk.data)
    cl.user_session.set("audio_chunks", chunks)

@cl.on_audio_end
async def on_audio_end(elements: list):
    chunks = cl.user_session.get("audio_chunks", [])
    audio_data = b"".join(chunks)

    # Transcribe with Gemini
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[
            types.Part.from_bytes(data=audio_data, mime_type="audio/webm"),
            types.Part(text="Transcribe this audio exactly.")
        ]
    )
    transcription = response.text

    # Process transcription as message...
```

---

## Charts & Visualizations

### utils/charts.py Patterns

```python
import plotly.graph_objects as go
import chainlit as cl

async def create_my_chart(data, title="My Chart"):
    """Create a custom Plotly chart."""

    fig = go.Figure()

    # Add traces
    fig.add_trace(go.Bar(x=data['x'], y=data['y']))

    # Configure layout
    fig.update_layout(
        title=title,
        xaxis_title="X Axis",
        yaxis_title="Y Axis",
        template="plotly_white"
    )

    return cl.Plotly(name="my_chart", figure=fig, display="inline")

async def create_dataframe_element(data: list) -> cl.Plotly:
    """Display data as a table using Plotly."""
    import pandas as pd

    df = pd.DataFrame(data)

    fig = go.Figure(data=[go.Table(
        header=dict(values=list(df.columns)),
        cells=dict(values=[df[col] for col in df.columns])
    )])

    return cl.Plotly(name="table", figure=fig, display="inline")
```

---

## Testing

### Local Testing

```bash
# Basic run
chainlit run mindrian_chat.py

# With hot reload
chainlit run mindrian_chat.py --watch

# Different port
chainlit run mindrian_chat.py --port 8001
```

### Test Checklist

- [ ] All bots load correctly
- [ ] Conversation starters appear
- [ ] Phase navigation works
- [ ] File upload processes correctly
- [ ] Voice input transcribes
- [ ] Database persistence saves/restores
- [ ] Context preservation works across bot switches
- [ ] Charts render inline
- [ ] Action buttons trigger correctly

---

## Deployment

### Render Configuration

**Build Command:**
```bash
pip install -r requirements.txt
```

**Start Command:**
```bash
chainlit run mindrian_chat.py --host 0.0.0.0 --port $PORT -h
```

**Environment Variables:**
- `GOOGLE_API_KEY` (required)
- `TAVILY_API_KEY` (recommended)
- `CHAINLIT_DATABASE_URL` (recommended)
- `ELEVENLABS_API_KEY` (optional)
- `ELEVENLABS_VOICE_ID` (optional)
- `SUPABASE_URL` (optional)
- `SUPABASE_SERVICE_KEY` (optional)
- `SUPABASE_BUCKET` (optional)

### Updating Production

```bash
git add .
git commit -m "Description of changes"
git push origin main
# Render auto-deploys on push
```

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| "API Key not found" | Missing env var | Check `.env` has `GOOGLE_API_KEY` |
| Database won't connect | Wrong URL format | Use `postgresql://` not `postgres://` |
| Voice not working | Missing API key | Set `ELEVENLABS_API_KEY` |
| Files disappear | No storage configured | Set up Supabase Storage |
| Bot switch loses context | Server restart | Context is in-memory; consider DB storage |

### Debugging

```python
# Add print statements for debugging
print(f"Bot: {cl.user_session.get('bot_id')}")
print(f"History length: {len(cl.user_session.get('history', []))}")
print(f"Settings: {cl.user_session.get('settings')}")
```

### Logs

- Render: Dashboard → Service → Logs
- Local: stdout when running chainlit

---

## Resources

- **Chainlit Docs:** https://docs.chainlit.io
- **Gemini API:** https://ai.google.dev/gemini-api/docs
- **Plotly Python:** https://plotly.com/python/
- **ElevenLabs API:** https://elevenlabs.io/docs
- **Supabase:** https://supabase.com/docs
