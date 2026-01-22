# Mindrian - Multi-Bot PWS Platform

A conversational AI platform for Problem Worth Solving (PWS) methodology, featuring Larry (the core thinking partner) and specialized workshop bots powered by Google Gemini with RAG-based knowledge retrieval.

**Live Demo:** https://mindrian.onrender.com
**Repository:** https://github.com/jsagir/mindrian-deploy
**Course:** EN.663.635 Problems Worth Solving - Johns Hopkins University

---

## Table of Contents
1. [Overview](#overview)
2. [Available Bots](#available-bots)
3. [Features](#features)
4. [New in v3.0](#new-in-v30)
5. [Architecture](#architecture)
6. [Gemini File Search / RAG](#gemini-file-search--rag)
7. [Project Structure](#project-structure)
8. [Quick Start](#quick-start)
9. [Configuration](#configuration)
10. [Environment Variables](#environment-variables)
11. [Deployment](#deployment)
12. [Workshop Details](#workshop-details)
13. [Development Guide](#development-guide)
14. [Project History](#project-history)

---

## Overview

Mindrian is a Chainlit-based multi-bot platform that guides users through structured innovation workshops using the PWS (Problems Worth Solving) methodology. Each bot specializes in a different PWS tool:

- **Larry** - The core conversational partner
- **Trending to the Absurd (TTA)** - Escape presentism, find future problems
- **Jobs to Be Done (JTBD)** - Discover what customers hire products for
- **S-Curve Analysis** - Analyze technology timing and disruption
- **Red Teaming** - Stress-test assumptions as devil's advocate
- **Ackoff's Pyramid (DIKW)** - Validate understanding before action

The platform uses **Gemini 3 Flash** with **Gemini File Search** (RAG) to retrieve context from the complete PWS course library.

---

## Available Bots

| Bot ID | Name | Icon | Phases | Purpose |
|--------|------|------|--------|---------|
| `larry` | Larry | brain | N/A | General PWS thinking partner |
| `tta` | Trending to the Absurd | crystal_ball | 8 | Escape presentism, find future problems |
| `jtbd` | Jobs to Be Done | dart | 7 | Discover customer jobs |
| `scurve` | S-Curve Analysis | chart_increasing | 6 | Technology timing analysis |
| `redteam` | Red Teaming | smiling_imp | 7 | Stress-test assumptions |
| `ackoff` | Ackoff's Pyramid | pyramid | 8 | DIKW validation methodology |

---

## Features

### Core Platform Features
- **Real-time streaming** - Token-by-token response display via Chainlit
- **Chat profiles** - Switch between 6 specialized bots
- **Workshop phases** - Structured progress tracking with task lists
- **Action buttons** - Quick actions (Next Phase, Show Example, Show Progress)
- **RAG Knowledge Base** - Gemini File Search with PWS course materials

### Interactive Elements
- **Conversation Starters** - 4 clickable starter prompts per bot
- **Chat Settings** - Configurable research depth, examples, verbosity
- **Task Lists** - Track workshop progress through phases
- **Action Buttons** - Navigate workshops without typing
- **File Upload** - PDF, DOCX, TXT, Markdown, Code files (max 10 files, 50MB each)
- **Voice Input** - Real-time audio streaming with Gemini transcription
- **Voice Output** - ElevenLabs text-to-speech with custom voice
- **Charts & Visualizations** - DIKW Pyramid, S-Curve, DataFrames via Plotly

### Research Tools
- **Tavily Search** - Web research for trend validation
- **Gemini File Search** - RAG retrieval from PWS knowledge base

### Data Persistence
- **PostgreSQL Database** - Supabase-powered conversation history
- **Session Resume** - Continue conversations across devices and sessions
- **Supabase Storage** - Persistent file uploads

---

## New in v3.0

This version introduces significant enhancements to the Chainlit experience:

### Chain of Thought Visualization (`@cl.step`)

See HOW Larry thinks, not just what. Collapsible nested steps show intermediate reasoning in real-time:

```
▼ Planning Research [2.3s]
  ├── Analyzing query context [0.8s]
  ├── Formulating search strategies [1.1s]
  └── Prioritizing sources [0.4s]
▼ Executing Searches [5.2s]
  ├── Search: healthcare AI trends [2.1s]
  ├── Search: preventive care innovation [1.8s]
  └── Synthesizing results [1.3s]
Response generated ✓
```

**Why this matters:**
- **Transparency** - Shows the reasoning process
- **Educational** - Students learn PWS methodology by observing
- **Debugging** - When errors occur, see where reasoning failed

### Conversation Starters

Each bot now shows 4 clickable starter prompts on empty chat:

**Larry:**
- "Help me find a problem worth solving"
- "I have a solution - help me validate it"
- "Explain the PWS methodology"
- "Help me think through a decision"

**Ackoff's Pyramid:**
- "I have a solution to validate"
- "I'm exploring a problem"
- "Show me the DIKW pyramid"
- "Give me an example"

**Why this matters:**
- Eliminates blank-page syndrome for new users
- Guides users to valid workshop starting points
- One-click engagement

### Chat Settings Panel

Gear icon reveals configurable options:

| Setting | Type | Purpose |
|---------|------|---------|
| Research Depth | Select | Basic/Standard/Deep web research |
| Show Examples | Toggle | Auto-show phase examples |
| Response Detail | Slider | 1-10 verbosity level |
| Workshop Mode | Select | Guided (strict phases) vs Freeform |

### Session Persistence

- **PostgreSQL via Supabase** - Conversations saved automatically
- **Resume Handler** - Close browser, return later, continue where you left off
- **Phase Progress** - Workshop progress persists across sessions

### ElevenLabs Voice Integration

- **Text-to-Speech** - Click speaker button for voice responses
- **Custom Voice** - Configurable voice ID for brand consistency
- **Audio Streaming** - Real-time voice input transcription

### Document Processing

Upload and analyze documents directly:

| Format | Processing |
|--------|------------|
| PDF | Full text extraction via PyPDF2 |
| DOCX | Word document parsing via python-docx |
| TXT/MD | Plain text reading |
| CSV/JSON | Data file handling |
| Code files | .py, .js syntax preserved |

### Supabase Storage

Persistent file storage for:
- Uploaded documents
- Exported workshop summaries
- Generated reports and assets

### Stop Handler

Click STOP button during generation:
- Graceful stream termination
- "[Response stopped]" indicator
- Continue or ask something else

### DIKW Pyramid Visualization

Interactive Plotly chart of Ackoff's DIKW pyramid with:
- Color-coded levels (Data → Wisdom)
- Clickable for explanation
- Inline display in chat

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          MINDRIAN PLATFORM v3.0                           │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌─────────────────┐    ┌─────────────────────────────────────────────┐  │
│  │    Chainlit     │    │              Google Gemini                   │  │
│  │       UI        │───▶│  Model: gemini-3-flash-preview              │  │
│  │                 │    │                                              │  │
│  │ - Chat Profiles │    │  ┌─────────────────────────────────────────┐│  │
│  │ - @cl.step      │    │  │        Gemini File Search               ││  │
│  │ - Starters      │    │  │   fileSearchStores/pwsknowledge...      ││  │
│  │ - Settings      │    │  │                                         ││  │
│  │ - Audio Stream  │    │  │  T1_Knowledge/  Core PWS Library        ││  │
│  │ - TaskLists     │    │  │  T2_Tools/      Workshop Materials      ││  │
│  │ - Actions       │    │  │  T3_Cases/      Case Studies            ││  │
│  │ - File Upload   │    │  └─────────────────────────────────────────┘│  │
│  └─────────────────┘    └─────────────────────────────────────────────┘  │
│           │                                                               │
│           ▼                                                               │
│  ┌─────────────────┐    ┌─────────────────────────────────────────────┐  │
│  │    Supabase     │    │              ElevenLabs                      │  │
│  │                 │    │                                              │  │
│  │ - PostgreSQL DB │    │  - Text-to-Speech API                       │  │
│  │ - Storage Bucket│    │  - Custom Voice ID                          │  │
│  │ - Session Data  │    │  - Audio Streaming                          │  │
│  └─────────────────┘    └─────────────────────────────────────────────┘  │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │                       SYSTEM PROMPTS                                 │ │
│  │  prompts/                                                            │ │
│  │  ├── larry_core.py        General thinking partner                  │ │
│  │  ├── tta_workshop.py      Trending to the Absurd                    │ │
│  │  ├── jtbd_workshop.py     Jobs to Be Done                           │ │
│  │  ├── scurve_workshop.py   S-Curve Analysis                          │ │
│  │  ├── redteam.py           Red Teaming                               │ │
│  │  └── ackoff_workshop.py   Ackoff's Pyramid (650+ lines)            │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │                      TOOLS & UTILS                                   │ │
│  │  tools/tavily_search.py     Web research                            │ │
│  │  utils/charts.py            Plotly visualizations + DataFrames      │ │
│  │  utils/gemini_rag.py        File Search cache utilities             │ │
│  │  utils/file_processor.py    PDF/DOCX/TXT extraction                 │ │
│  │  utils/media.py             ElevenLabs TTS, exports                 │ │
│  │  utils/storage.py           Supabase Storage integration            │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Gemini File Search / RAG

The platform uses **Gemini File Search** for retrieval-augmented generation (RAG), enabling bots to access the complete PWS course library.

### File Search Store

```
Store ID: fileSearchStores/pwsknowledgebase-a4rnz3u41lsn
```

### Knowledge Base Structure

```
pwsknowledgebase-a4rnz3u41lsn/
│
├── T1_Knowledge/                    (Tier 1: Core PWS Library)
│   ├── PWS_MasterIndex              Master index of all materials
│   ├── PWS_Book_Complete            Full PWS innovation book
│   ├── Lecture_Notes                Course lecture notes
│   └── Extended_Research            Research foundations
│
├── T2_Tools/                        (Tier 2: Workshop-Specific Materials)
│   │
│   ├── TrendingToAbsurd_*           (TTA Workshop)
│   │   ├── TrendingToAbsurd_Lecture_Complete
│   │   ├── TrendingToAbsurd_Workbook_Exercises
│   │   └── TrendingToAbsurd_SystemPrompt_Complete
│   │
│   ├── AckoffPyramid_*              (DIKW Workshop)
│   │   ├── AckoffPyramid_Lecture_DIKWValidation
│   │   ├── AckoffPyramid_Workbook_Exercises
│   │   ├── AckoffPyramid_SystemPrompt_Complete
│   │   └── AckoffPyramid_MaterialsGuide_CaseStudies (158K chars)
│   │
│   ├── ScenarioAnalysis_*           (Scenario Workshop)
│   │   ├── ScenarioAnalysis_Lecture
│   │   ├── ScenarioAnalysis_Workbook
│   │   └── ScenarioAnalysis_SystemPrompt
│   │
│   └── [Additional workshops to be added...]
│
└── T3_Cases/                        (Tier 3: Case Studies)
    ├── TargetCanada_$7B_Failure
    ├── Boeing737MAX_ValidationFailure
    ├── KaiserPermanente_$4B_Success
    └── SharpGrossmont_ED_52%Improvement
```

### Tier Configuration

| Tier | Content | Chunking | Purpose |
|------|---------|----------|---------|
| **T1_Knowledge** | Core PWS book, lectures, research | 800 tok / 200 overlap | General knowledge for all bots |
| **T2_Tools** | Workshop-specific materials | 500 tok / 100 overlap | Precise retrieval for each workshop |
| **T3_Cases** | Detailed case studies | 500 tok / 100 overlap | Real-world examples and evidence |

---

## Project Structure

```
mindrian-deploy/
├── mindrian_chat.py              # Main Chainlit application (800+ lines)
│   ├── BOTS dict                 # Bot configurations
│   ├── STARTERS dict             # Conversation starters per bot
│   ├── WORKSHOP_PHASES dict      # Phase definitions per bot
│   ├── @cl.set_starters          # Starter buttons
│   ├── @cl.on_settings_update    # Settings panel handler
│   ├── @cl.on_chat_start         # Session initialization
│   ├── @cl.on_chat_resume        # Session restoration
│   ├── @cl.on_message            # Message handling with Gemini
│   ├── @cl.on_stop               # Stop button handler
│   ├── @cl.on_audio_start/chunk/end  # Audio streaming
│   └── Action handlers           # Button callbacks
│
├── prompts/                      # System prompts for each bot
│   ├── __init__.py               # Exports all prompts
│   ├── larry_core.py             # Larry's conversational prompt
│   ├── tta_workshop.py           # Trending to the Absurd (7 phases)
│   ├── jtbd_workshop.py          # Jobs to Be Done (6 phases)
│   ├── scurve_workshop.py        # S-Curve Analysis (5 phases)
│   ├── redteam.py                # Red Teaming (6 phases)
│   └── ackoff_workshop.py        # Ackoff's Pyramid DIKW (650+ lines)
│
├── tools/                        # External tool integrations
│   ├── __init__.py
│   └── tavily_search.py          # Tavily web search wrapper
│
├── utils/                        # Utility functions
│   ├── __init__.py
│   ├── charts.py                 # Plotly charts + DIKW pyramid + DataFrames
│   ├── gemini_rag.py             # Gemini File Search utilities
│   ├── file_processor.py         # PDF/DOCX/TXT extraction
│   ├── media.py                  # ElevenLabs TTS, exports
│   └── storage.py                # Supabase Storage integration
│
├── public/                       # Static assets
│   └── icons/                    # 21 SVG icons for starters
│
├── .chainlit/
│   └── config.toml               # Chainlit configuration (v2.9.5 format)
│
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment template
├── chainlit.md                   # Welcome page content
└── README.md                     # This file
```

---

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/jsagir/mindrian-deploy
cd mindrian-deploy
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 4. Run Locally

```bash
chainlit run mindrian_chat.py
```

Open http://localhost:8000

---

## Environment Variables

### Required

| Variable | Description | Get it at |
|----------|-------------|-----------|
| `GOOGLE_API_KEY` | Google AI API key | https://aistudio.google.com/apikey |

### Recommended

| Variable | Description | Get it at |
|----------|-------------|-----------|
| `TAVILY_API_KEY` | Web research API | https://tavily.com |
| `CHAINLIT_DATABASE_URL` | PostgreSQL connection | See Supabase setup |

### Voice (Optional)

| Variable | Description | Get it at |
|----------|-------------|-----------|
| `ELEVENLABS_API_KEY` | Text-to-speech API | https://elevenlabs.io |
| `ELEVENLABS_VOICE_ID` | Custom voice ID | ElevenLabs voice library |

### Storage (Optional)

| Variable | Description | Get it at |
|----------|-------------|-----------|
| `SUPABASE_URL` | Project URL | Supabase Dashboard > Settings > API |
| `SUPABASE_SERVICE_KEY` | Service role key | Supabase Dashboard > Settings > API |
| `SUPABASE_BUCKET` | Storage bucket name | Default: `mindrian-files` |

### Example .env

```bash
# Required
GOOGLE_API_KEY=AIzaSy...

# Web Research
TAVILY_API_KEY=tvly-...

# Database (Supabase PostgreSQL)
CHAINLIT_DATABASE_URL=postgresql://postgres:password@db.xxxx.supabase.co:5432/postgres

# Voice
ELEVENLABS_API_KEY=sk_...
ELEVENLABS_VOICE_ID=SGh5MKvZcSYNF0SZXlAg

# Storage
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...
SUPABASE_BUCKET=mindrian-files
```

---

## Configuration

### .chainlit/config.toml (v2.9.5 format)

```toml
[project]
enable_telemetry = true
session_timeout = 3600
allow_origins = ["*"]

[features]
edit_message = true
multi_modal = true

[features.spontaneous_file_upload]
enabled = true
accept = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/*", "image/*", "application/json", ".md", ".csv", ".py", ".js"]
max_files = 10
max_size_mb = 50

[features.audio]
enabled = true
min_decibels = -45
initial_silence_timeout = 3000
silence_timeout = 1500
max_duration = 15000
chunk_duration = 1000
sample_rate = 24000

[features.mcp]
enabled = true

[features.speech_to_text]
enabled = true
provider = "browser"

[features.text_to_speech]
enabled = true
provider = "browser"

[UI]
name = "Mindrian"
description = "Multi-Bot PWS Platform - Larry Core + Specialized Workshop Bots"
github = "https://github.com/jsagir/mindrian-deploy"
hide_cot = false
cot = "full"

[UI.theme.light]
background = "#fafafa"
paper = "#ffffff"

[UI.theme.dark]
background = "#1a1a2e"
paper = "#16213e"
```

---

## Deployment

### Render (Current Production)

**Service:** https://dashboard.render.com/web/srv-d5ni8v24d50c73fqdpug
**URL:** https://mindrian.onrender.com

**Configuration:**
- Runtime: Python
- Build: `pip install -r requirements.txt`
- Start: `chainlit run mindrian_chat.py --host 0.0.0.0 --port $PORT -h`
- Auto-deploy: Yes (on push to main)

**Environment Variables in Render Dashboard:**

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | Yes | Google AI API key |
| `TAVILY_API_KEY` | Recommended | Web research |
| `CHAINLIT_DATABASE_URL` | Recommended | PostgreSQL for persistence |
| `ELEVENLABS_API_KEY` | Optional | Voice responses |
| `ELEVENLABS_VOICE_ID` | Optional | Custom voice |
| `SUPABASE_URL` | Optional | File storage |
| `SUPABASE_SERVICE_KEY` | Optional | File storage |
| `SUPABASE_BUCKET` | Optional | Storage bucket name |

### Supabase Setup

1. Create project at https://supabase.com
2. Go to **Project Settings > Database**
3. Copy connection string (URI format)
4. Set `CHAINLIT_DATABASE_URL` in Render
5. (Optional) Create storage bucket `mindrian-files`
6. (Optional) Copy service_role key for file storage

### Local Development

```bash
chainlit run mindrian_chat.py --watch
```

The `--watch` flag enables hot reloading.

---

## Workshop Details

### Ackoff's Pyramid (DIKW)

**Purpose:** Validate understanding before taking action

**DIKW Pyramid:**
```
                    ╱╲
                   ╱  ╲
                  ╱ W  ╲         WISDOM
                 ╱──────╲        "What should we do?"
                ╱   U    ╲       UNDERSTANDING
               ╱──────────╲      "Why does it work this way?"
              ╱     K      ╲     KNOWLEDGE
             ╱──────────────╲    "How do these patterns connect?"
            ╱       I        ╲   INFORMATION
           ╱──────────────────╲  "What patterns emerge?"
          ╱         D          ╲ DATA
         ╱______________________╲"What do we actually observe?"
```

**Two-Directional Validation:**

```
CLIMB UP (Build Understanding):
Data → Information → Knowledge → Understanding → Wisdom
  ↑         ↑            ↑             ↑            ↑
Observe  Patterns    Connect      Causation     Decide

CLIMB DOWN (Validate Decisions):
Wisdom → Understanding → Knowledge → Information → Data
   ↓          ↓             ↓            ↓          ↓
Decision  Causation     Expertise     Patterns   Ground
```

**Phases:**
1. Team Onboarding - Set context and problem
2. Direction Choice - Climb Up or Climb Down?
3. Data Level - Raw observations (Camera Test)
4. Information Level - Pattern recognition
5. Knowledge Level - Expert connections
6. Understanding Level - Causal mechanisms (5 Whys)
7. Wisdom Level - Actionable decisions
8. Validation & Action - Final climb-down verification

**Case Studies in Materials:**

| Case | Industry | Outcome | Key Lesson |
|------|----------|---------|------------|
| Target Canada | Retail | $7B loss | Data quality (30% vs 98%) |
| Boeing 737 MAX | Aerospace | 346 deaths | Single sensor validation failure |
| Kodak | Technology | Bankruptcy | Wisdom paralysis despite data |
| Kaiser Permanente | Healthcare | $500M savings | Full pyramid validation |
| Sharp Grossmont ED | Healthcare | 52% improvement | DIKW process optimization |
| Walmart RFID | Retail | Transformation | 20-year phased validation |

### Other Workshops

**Trending to the Absurd (8 phases):**
1. Introduction → 2. Domain & Trends → 3. Deep Research → 4. Absurd Extrapolation → 5. Problem Hunting → 6. Opportunity Validation → 7. Action Planning → 8. Reflection

**Jobs to Be Done (7 phases):**
1. Introduction → 2. Struggling Moment → 3. Functional Job → 4. Emotional Job → 5. Social Job → 6. Competing Solutions → 7. Job Statement

**S-Curve Analysis (6 phases):**
1. Introduction → 2. Tech Identification → 3. Era Assessment → 4. Evidence → 5. Ecosystem Readiness → 6. Timing Decision

**Red Teaming (7 phases):**
1. Introduction → 2. Assumption Extraction → 3. Ranking → 4. Attack Mode → 5. Competition → 6. Failure Modes → 7. Strengthening

---

## Development Guide

### Adding a New Workshop Bot

1. **Create prompt file** in `prompts/`:
```python
# prompts/new_workshop.py
NEW_WORKSHOP_PROMPT = """
# Your comprehensive system prompt here
...
"""
```

2. **Add to prompts/__init__.py**:
```python
from .new_workshop import NEW_WORKSHOP_PROMPT
```

3. **Add bot config** to `mindrian_chat.py`:
```python
BOTS["new_bot"] = {
    "name": "New Workshop",
    "icon": "icon_name",
    "model": "gemini-3-flash-preview",
    "prompt": NEW_WORKSHOP_PROMPT,
    "greeting": "Welcome to the new workshop...",
    "examples": ["Example 1", "Example 2", "Example 3"]
}
```

4. **Add starters** to `STARTERS` dict:
```python
STARTERS["new_bot"] = [
    cl.Starter(label="Option 1", message="...", icon="/public/icons/icon1.svg"),
    cl.Starter(label="Option 2", message="...", icon="/public/icons/icon2.svg"),
    cl.Starter(label="Option 3", message="...", icon="/public/icons/icon3.svg"),
    cl.Starter(label="Option 4", message="...", icon="/public/icons/icon4.svg"),
]
```

5. **Add phases** to `WORKSHOP_PHASES`:
```python
WORKSHOP_PHASES["new_bot"] = [
    {"name": "Phase 1", "status": "ready"},
    {"name": "Phase 2", "status": "pending"},
    ...
]
```

6. **Add chat profile** in `chat_profiles()` function

7. **Upload materials** to Gemini File Search

### Modifying Existing Bots

- Edit system prompts in `prompts/` directory
- Phases are in `WORKSHOP_PHASES` dict
- Starters are in `STARTERS` dict
- Bot metadata in `BOTS` dict
- Re-upload materials to File Search if content changes

---

## Project History

### v1.0 - Initial Build
- Larry core thinking partner
- Basic chat profiles
- Simple system prompts

### v1.5 - Workshop Features
- Added TTA, JTBD, S-Curve, Red Team workshops
- Task lists for phase tracking
- Action buttons
- File upload, voice I/O

### v2.0 - RAG Integration
- Gemini File Search integration
- T1/T2/T3 tier knowledge base structure
- Workshop materials upload scripts
- Ackoff's Pyramid (DIKW) workshop with 650+ line prompt

### v3.0 - Chainlit Enhanced Experience (Current)

**Chain of Thought Visualization:**
- `@cl.step` decorator for nested collapsible steps
- Real-time timing display
- Transparent reasoning process

**Conversation Starters:**
- `@cl.set_starters` with 4 prompts per bot (24 total)
- Custom SVG icons in `public/icons/`
- One-click engagement

**Chat Settings:**
- Research depth (Basic/Standard/Deep)
- Show examples toggle
- Response detail slider (1-10)
- Workshop mode (Guided/Freeform)

**Session Persistence:**
- PostgreSQL via Supabase
- `@cl.on_chat_resume` handler
- Phase progress restoration
- `@cl.on_stop` for graceful interruption

**Voice Integration:**
- ElevenLabs text-to-speech
- Real-time audio streaming handlers
- Gemini transcription for voice input

**Document Processing:**
- `utils/file_processor.py` for PDF/DOCX/TXT
- PyPDF2 and python-docx integration
- Automatic context injection

**Rich Media:**
- DIKW pyramid visualization (Plotly)
- DataFrame display as Plotly tables
- Image and file exports

**Supabase Storage:**
- `utils/storage.py` for persistent uploads
- Unique filename generation
- MIME type detection

### Remaining Workshops to Add
From PWS curriculum:
- Scenario Analysis
- Minto Pyramid
- Reverse Salient
- Market Timing
- [Others from course materials]

---

## Dependencies

```
# Core
chainlit>=2.9.0
google-genai>=1.0.0
python-dotenv>=1.0.0

# Document Processing
PyPDF2>=3.0.0
python-docx>=1.1.0

# Data & Visualization
pandas>=2.0.0
numpy>=1.24.0
plotly>=5.18.0

# Voice
elevenlabs>=1.0.0

# Database
sqlalchemy[asyncio]>=2.0.0
psycopg2-binary>=2.9.0
asyncpg>=0.29.0

# Storage
supabase>=2.0.0

# Research
tavily-python>=0.5.0
```

---

## Related Repositories

- **mindrian-langgraph**: Upload scripts for Gemini File Search
- **mindrian-agno-ui**: Agno-based alternative UI (experimental)
- **mindrian-platform**: Previous iteration

---

## About PWS

The **Problem Worth Solving** methodology was developed by Professor Lawrence Aronhime over 30+ years of teaching innovation at Johns Hopkins University.

**Core insight:** Most innovation fails not because of bad solutions, but because people solve the wrong problems.

---

## Support

- **Course:** EN.663.635 Problems Worth Solving
- **Institution:** Johns Hopkins University
- **GitHub Issues:** https://github.com/jsagir/mindrian-deploy/issues

---

---

## Developer Documentation

- **[CLAUDE.md](./CLAUDE.md)** - Quick reference for AI assistants (Claude Code, etc.)
- **[DEVELOPMENT.md](./DEVELOPMENT.md)** - Comprehensive development guide

### Adding New Agents Checklist

When adding a new bot, follow ALL these steps:

1. Create system prompt in `prompts/`
2. Export in `prompts/__init__.py`
3. Add to `BOTS` dict
4. Add to `WORKSHOP_PHASES` (if applicable)
5. Add to `STARTERS` dict
6. Add to `chat_profiles()`
7. **Add to `AGENT_TRIGGERS`** (enables dynamic switching)
8. **Add switch callback** (`switch_to_newbot`)
9. Create SVG icons (optional)

**Missing steps 7-8 = Dynamic agent switching won't work!**

---

Built with Chainlit + Google Gemini + Gemini File Search RAG + Supabase + ElevenLabs
