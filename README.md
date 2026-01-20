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
4. [Architecture](#architecture)
5. [Gemini File Search / RAG](#gemini-file-search--rag)
6. [Project Structure](#project-structure)
7. [Quick Start](#quick-start)
8. [Configuration](#configuration)
9. [Deployment](#deployment)
10. [Workshop Details](#workshop-details)
11. [Development Guide](#development-guide)
12. [Project History](#project-history)

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
- **Task Lists** - Track workshop progress through phases
- **Action Buttons** - Navigate workshops without typing
- **File Upload** - Attach documents to messages (max 5 files, 20MB each)
- **Voice Input** - Speech-to-text via browser
- **Voice Output** - Text-to-speech via browser
- **Charts** - S-curve and comparison visualizations using Plotly

### Research Tools
- **Tavily Search** - Web research for trend validation (requires `TAVILY_API_KEY`)
- **Gemini File Search** - RAG retrieval from PWS knowledge base

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         MINDRIAN PLATFORM                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐    ┌─────────────────────────────────────────┐ │
│  │   Chainlit  │    │              Google Gemini               │ │
│  │     UI      │───▶│  Model: gemini-3-flash-preview          │ │
│  │             │    │                                          │ │
│  │ - Profiles  │    │  ┌─────────────────────────────────────┐ │ │
│  │ - TaskLists │    │  │        Gemini File Search           │ │ │
│  │ - Actions   │    │  │   fileSearchStores/pwsknowledge...  │ │ │
│  │ - Audio     │    │  │                                     │ │ │
│  │ - Upload    │    │  │  T1_Knowledge/  Core PWS Library    │ │ │
│  └─────────────┘    │  │  T2_Tools/      Workshop Materials  │ │ │
│                      │  │  T3_Cases/      Case Studies        │ │ │
│                      │  └─────────────────────────────────────┘ │ │
│                      └─────────────────────────────────────────┘ │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    SYSTEM PROMPTS                           │ │
│  │  prompts/                                                   │ │
│  │  ├── larry_core.py        General thinking partner          │ │
│  │  ├── tta_workshop.py      Trending to the Absurd           │ │
│  │  ├── jtbd_workshop.py     Jobs to Be Done                   │ │
│  │  ├── scurve_workshop.py   S-Curve Analysis                  │ │
│  │  ├── redteam.py           Red Teaming                       │ │
│  │  └── ackoff_workshop.py   Ackoff's Pyramid (650+ lines)    │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                      TOOLS & UTILS                          │ │
│  │  tools/tavily_search.py   Web research                      │ │
│  │  utils/charts.py          Plotly chart generators           │ │
│  │  utils/gemini_rag.py      File Search cache utilities       │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
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
│   ├── AckoffPyramid_*              (DIKW Workshop) [NEWLY ADDED]
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

### How RAG Works

1. **User asks question** → Gemini processes with file_search tool enabled
2. **Vector search** → Finds relevant chunks from knowledge base
3. **Context injection** → Retrieved chunks added to prompt
4. **Response generation** → Model answers with grounded information

### Upload Scripts

Located in `/home/jsagi/Mindrian/mindrian-langgraph/`:

```bash
# Upload Trending to the Absurd materials
python upload_trending_to_absurd.py

# Upload Ackoff's Pyramid materials (4 files)
python upload_ackoff_pyramid.py

# Upload Scenario Analysis materials
python upload_scenario_analysis.py

# Upload PWS Lectures
python upload_pws_lectures.py
```

Each script uses:
- `google.genai.Client` for API access
- `client.file_search_stores.upload_to_file_search_store()` for uploads
- Configurable chunk sizes (max_tokens_per_chunk, max_overlap_tokens)

---

## Project Structure

```
mindrian-deploy/
├── mindrian_chat.py              # Main Chainlit application (600+ lines)
│   ├── BOTS dict                 # Bot configurations
│   ├── WORKSHOP_PHASES dict      # Phase definitions per bot
│   ├── @cl.on_chat_start         # Session initialization
│   ├── @cl.on_message            # Message handling with Gemini
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
│   ├── charts.py                 # Plotly chart generators
│   └── gemini_rag.py             # Gemini File Search utilities
│
├── .chainlit/
│   └── config.toml               # Chainlit configuration (v2.9.5 format)
│
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment template
├── chainlit.md                   # Welcome page content
└── README.md                     # This file
```

### Key Files Deep Dive

#### mindrian_chat.py

```python
# Bot configuration structure
BOTS = {
    "bot_id": {
        "name": "Display Name",
        "icon": "emoji_name",
        "model": "gemini-3-flash-preview",
        "prompt": PROMPT_CONSTANT,
        "greeting": "Welcome message...",
        "examples": ["Example 1", "Example 2", "Example 3"]
    }
}

# Workshop phase structure
WORKSHOP_PHASES = {
    "bot_id": [
        {"name": "Phase 1", "status": "ready"},
        {"name": "Phase 2", "status": "pending"},
        ...
    ]
}
```

#### prompts/ackoff_workshop.py (Newest Addition)

650+ line comprehensive system prompt including:
- DIKW Pyramid ASCII diagrams
- Climb Up methodology (Data → Wisdom)
- Climb Down validation (Wisdom → Data)
- Challenge protocols (Camera Test, 5 Whys)
- 6+ detailed case studies with outcomes
- Mental models (Assumption Iceberg, Validation Tax)
- Special protocols for pushback, gaps, skip requests

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
```

**Required variables:**
```
GOOGLE_API_KEY=your_google_ai_api_key
```

**Optional variables:**
```
TAVILY_API_KEY=your_tavily_api_key
GEMINI_FILE_SEARCH_STORE=fileSearchStores/pwsknowledgebase-a4rnz3u41lsn
```

### 4. Run Locally

```bash
chainlit run mindrian_chat.py
```

Open http://localhost:8000

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
accept = ["*/*"]
max_files = 5
max_size_mb = 20

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
description = "Multi-Bot PWS Platform"
github = "https://github.com/jsagir/mindrian-deploy"
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

**Environment Variables in Render:**
- `GOOGLE_API_KEY` (required)
- `TAVILY_API_KEY` (optional)
- `GEMINI_FILE_SEARCH_STORE` (optional)

### Local Development

```bash
chainlit run mindrian_chat.py --watch
```

The `--watch` flag enables hot reloading.

---

## Workshop Details

### Ackoff's Pyramid (DIKW) - Newest Workshop

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

4. **Add phases** to `WORKSHOP_PHASES`:
```python
WORKSHOP_PHASES["new_bot"] = [
    {"name": "Phase 1", "status": "ready"},
    {"name": "Phase 2", "status": "pending"},
    ...
]
```

5. **Add chat profile** in `chat_profiles()` function

6. **Upload materials** to Gemini File Search:
```bash
cd /home/jsagi/Mindrian/mindrian-langgraph
# Create upload_new_workshop.py following existing pattern
python upload_new_workshop.py
```

### Modifying Existing Bots

- Edit system prompts in `prompts/` directory
- Phases are in `WORKSHOP_PHASES` dict
- Bot metadata in `BOTS` dict
- Re-upload materials to File Search if content changes

### File Search Material Updates

```bash
cd /home/jsagi/Mindrian/mindrian-langgraph

# Edit upload script to add/modify files
vim upload_ackoff_pyramid.py

# Re-run upload
python upload_ackoff_pyramid.py
```

---

## Project History

### Initial Build (v1.0)
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

### Current Session - Ackoff Addition
- **Added Ackoff's Pyramid (DIKW) workshop**
  - 650+ line comprehensive system prompt
  - 8-phase workshop structure
  - 6 detailed case studies
  - Climb Up / Climb Down methodology
- **Uploaded 4 files to T2_Tools:**
  - AckoffPyramid_Lecture_DIKWValidation
  - AckoffPyramid_Workbook_Exercises
  - AckoffPyramid_SystemPrompt_Complete
  - AckoffPyramid_MaterialsGuide_CaseStudies (158K chars, full case study library)
- **Fixed Chainlit v2.9.5 config** (object format for features)
- **Updated README** with complete documentation

### Remaining Workshops to Add
From PWS curriculum:
- Scenario Analysis
- Minto Pyramid
- Reverse Salient
- Market Timing
- [Others from course materials]

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

Built with Chainlit + Google Gemini + Gemini File Search RAG
