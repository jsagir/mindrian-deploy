# Mindrian - Multi-Bot PWS Platform

A conversational AI platform for Problem Worth Solving (PWS) methodology, featuring Larry (the core thinking partner) and specialized workshop bots powered by Google Gemini with RAG-based knowledge retrieval.

**Live Demo:** https://mindrian.onrender.com

## Available Bots

| Bot | Purpose |
|-----|---------|
| **Larry** | General PWS thinking partner - helps identify problems worth solving |
| **Trending to the Absurd** | Guided 7-phase workshop to escape presentism and find future problems |
| **Jobs to Be Done** | 6-phase workshop to discover what customers really hire products for |
| **S-Curve Analysis** | 5-phase workshop to analyze technology timing and disruption |
| **Red Teaming** | 6-phase workshop to stress-test assumptions as devil's advocate |
| **Ackoff's Pyramid (DIKW)** | 8-phase workshop for validating understanding before action |

## Features

### Core Features
- **Real-time streaming** - Token-by-token response display
- **Chat profiles** - Switch between 6 specialized bots
- **Workshop phases** - Structured progress tracking with task lists
- **Action buttons** - Quick actions (Next Phase, Show Example, Show Progress)
- **RAG Knowledge Base** - Gemini File Search with PWS course materials

### Interactive Elements
- **Task Lists** - Track workshop progress through phases
- **Action Buttons** - Navigate workshops without typing
- **File Upload** - Attach documents to messages
- **Voice Input** - Speech-to-text support
- **Voice Output** - Text-to-speech support
- **Charts** - S-curve and comparison visualizations (Plotly)

### Research Tools
- **Tavily Search** - Web research for trend validation
- **Gemini File Search** - RAG retrieval from PWS knowledge base

---

## Gemini File Search / RAG Architecture

The platform uses **Gemini File Search** for retrieval-augmented generation (RAG), enabling bots to access the complete PWS course library.

### Knowledge Base Structure

```
fileSearchStores/pwsknowledgebase-a4rnz3u41lsn
│
├── T1_Knowledge/              (Tier 1: Core PWS Library)
│   ├── PWS_MasterIndex
│   ├── PWS_Book_Complete
│   ├── Lecture_Notes
│   └── Extended_Research
│
├── T2_Tools/                  (Tier 2: Workshop-Specific Materials)
│   │
│   ├── TrendingToAbsurd_*     (TTA Workshop)
│   │   ├── TrendingToAbsurd_Lecture_Complete
│   │   ├── TrendingToAbsurd_Workbook_Exercises
│   │   └── TrendingToAbsurd_SystemPrompt_Complete
│   │
│   ├── AckoffPyramid_*        (DIKW Workshop)
│   │   ├── AckoffPyramid_Lecture_DIKWValidation
│   │   ├── AckoffPyramid_Workbook_Exercises
│   │   ├── AckoffPyramid_SystemPrompt_Complete
│   │   └── AckoffPyramid_MaterialsGuide_CaseStudies
│   │
│   ├── ScenarioAnalysis_*     (Scenario Workshop)
│   │   ├── ScenarioAnalysis_Lecture
│   │   ├── ScenarioAnalysis_Workbook
│   │   └── ScenarioAnalysis_SystemPrompt
│   │
│   └── [Additional Workshops...]
│
└── T3_Cases/                  (Tier 3: Case Studies & Examples)
    ├── TargetCanada_$7B_Failure
    ├── Boeing737MAX_ValidationFailure
    ├── KaiserPermanente_$4B_Success
    └── SharpGrossmont_ED_52%Improvement
```

### Tier Descriptions

| Tier | Content | Chunking | Purpose |
|------|---------|----------|---------|
| **T1_Knowledge** | Core PWS book, lectures, research | 800 tok / 200 overlap | General knowledge for all bots |
| **T2_Tools** | Workshop-specific materials | 500 tok / 100 overlap | Precise retrieval for each workshop |
| **T3_Cases** | Detailed case studies | 500 tok / 100 overlap | Real-world examples and evidence |

### How RAG Works

1. **User asks question** → Gemini processes with file search enabled
2. **Vector search** → Finds relevant chunks from knowledge base
3. **Context injection** → Retrieved chunks added to prompt
4. **Response generation** → Model answers with grounded information

### Upload Scripts

Located in `/home/jsagi/Mindrian/mindrian-langgraph/`:

```bash
# Upload Trending to the Absurd materials
python upload_trending_to_absurd.py

# Upload Ackoff's Pyramid materials
python upload_ackoff_pyramid.py

# Upload Scenario Analysis materials
python upload_scenario_analysis.py
```

---

## Ackoff's Pyramid (DIKW) Workshop

A new workshop for validating understanding before taking action, based on Russell Ackoff's DIKW hierarchy.

### The DIKW Pyramid

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

### Two-Directional Validation

**CLIMB UP** - Build Understanding:
```
Data → Information → Knowledge → Understanding → Wisdom
  ↑         ↑            ↑             ↑            ↑
Observe  Patterns    Connect      Causation     Decide
```

**CLIMB DOWN** - Validate Decisions:
```
Wisdom → Understanding → Knowledge → Information → Data
   ↓          ↓             ↓            ↓          ↓
Decision  Causation     Expertise     Patterns   Ground
```

### Workshop Phases

1. **Team Onboarding** - Set context and problem
2. **Direction Choice** - Climb Up or Climb Down?
3. **Data Level** - Raw observations (Camera Test)
4. **Information Level** - Pattern recognition
5. **Knowledge Level** - Expert connections
6. **Understanding Level** - Causal mechanisms (5 Whys)
7. **Wisdom Level** - Actionable decisions
8. **Validation & Action** - Final climb-down verification

### Case Studies Included

| Case | Industry | Outcome | Key Lesson |
|------|----------|---------|------------|
| Target Canada | Retail | $7B loss | Data quality matters (30% vs 98%) |
| Boeing 737 MAX | Aerospace | 346 deaths | Single sensor validation failure |
| Kodak | Technology | Bankruptcy | Wisdom paralysis despite data |
| Kaiser Permanente | Healthcare | $500M savings | Full pyramid validation success |
| Sharp Grossmont ED | Healthcare | 52% improvement | Process optimization through DIKW |
| Walmart RFID | Retail | Industry transformation | Phased validation over 20 years |

---

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/jsagir/mindrian-deploy
cd mindrian-deploy
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your API keys
```

**Required:**
- `GOOGLE_API_KEY` - Get at https://aistudio.google.com/apikey

**Optional but recommended:**
- `TAVILY_API_KEY` - Get at https://tavily.com (for web research)

### 5. Run Locally

```bash
chainlit run mindrian_chat.py
```

Open http://localhost:8000 in your browser.

---

## Project Structure

```
mindrian-deploy/
├── mindrian_chat.py          # Main Chainlit application
├── prompts/                  # System prompts for each bot
│   ├── __init__.py
│   ├── larry_core.py         # Larry's conversational prompt
│   ├── tta_workshop.py       # Trending to the Absurd (7 phases)
│   ├── jtbd_workshop.py      # Jobs to Be Done (6 phases)
│   ├── scurve_workshop.py    # S-Curve Analysis (5 phases)
│   ├── redteam.py            # Red Teaming (6 phases)
│   └── ackoff_workshop.py    # Ackoff's Pyramid DIKW (8 phases)
├── tools/                    # MCP tools and integrations
│   ├── __init__.py
│   └── tavily_search.py      # Web research capabilities
├── utils/                    # Utility functions
│   ├── __init__.py
│   ├── charts.py             # Plotly chart generators
│   └── gemini_rag.py         # Gemini File Search utilities
├── .chainlit/
│   └── config.toml           # Chainlit configuration
├── requirements.txt          # Python dependencies
├── .env.example              # Environment template
├── chainlit.md               # Welcome page content
└── README.md                 # This file
```

---

## Configuration

### Enable/Disable Features

Edit `.chainlit/config.toml`:

```toml
[features]
spontaneous_file_upload = true   # File attachments
audio = true                      # Voice input/output
mcp = true                        # MCP tools support
multi_modal = true                # Images in messages
```

### Model Selection

Default model is `gemini-3-flash-preview`. To change, edit `mindrian_chat.py`:

```python
model="gemini-3-flash-preview",  # or gemini-2.5-flash, etc.
```

### File Search Configuration

The Gemini File Search store is configured via environment variable:

```bash
GEMINI_FILE_SEARCH_STORE=fileSearchStores/pwsknowledgebase-a4rnz3u41lsn
```

---

## Deployment

### Render (Current)

The app auto-deploys from GitHub. To update:

```bash
git add .
git commit -m "Update features"
git push
```

Add environment variables in Render Dashboard → Environment:
- `GOOGLE_API_KEY`
- `TAVILY_API_KEY` (optional)
- `GEMINI_FILE_SEARCH_STORE` (optional, uses default if not set)

### Other Platforms

**Railway / Fly.io:**
```bash
# Build command
pip install -r requirements.txt

# Start command
chainlit run mindrian_chat.py --host 0.0.0.0 --port $PORT -h
```

---

## All Workshop Phases

### Trending to the Absurd
1. Introduction
2. Domain & Trends
3. Deep Research
4. Absurd Extrapolation
5. Problem Hunting
6. Opportunity Validation
7. Action Planning
8. Reflection

### Jobs to Be Done
1. Introduction
2. Struggling Moment
3. Functional Job
4. Emotional Job
5. Social Job
6. Competing Solutions
7. Job Statement

### S-Curve Analysis
1. Introduction
2. Technology Identification
3. Era Assessment
4. Evidence Gathering
5. Ecosystem Readiness
6. Timing Decision

### Red Teaming
1. Introduction
2. Assumption Extraction
3. Assumption Ranking
4. Attack Mode
5. Competition & Alternatives
6. Failure Modes
7. Strengthening

### Ackoff's Pyramid (DIKW)
1. Team Onboarding
2. Direction Choice
3. Data Level
4. Information Level
5. Knowledge Level
6. Understanding Level
7. Wisdom Level
8. Validation & Action

---

## Adding New Bots

1. Create prompt file in `prompts/` following existing patterns
2. Add to `prompts/__init__.py`
3. Add bot config to `BOTS` dict in `mindrian_chat.py`
4. Add phases to `WORKSHOP_PHASES` if applicable
5. Add to `chat_profiles()` function
6. Upload materials to Gemini File Search (T2_Tools tier)

---

## About PWS

The Problem Worth Solving methodology was developed by Professor Lawrence Aronhime over 30+ years of teaching innovation at Johns Hopkins University.

**Core insight:** Most innovation fails not because of bad solutions, but because people solve the wrong problems.

---

Built with Chainlit + Google Gemini + Gemini File Search RAG

Course: EN.663.635 Problems Worth Solving
Institution: Johns Hopkins University
