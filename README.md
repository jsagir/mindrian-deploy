# Mindrian - Multi-Bot PWS Platform

A conversational AI platform for Problem Worth Solving (PWS) methodology, featuring Larry (the core thinking partner) and specialized workshop bots.

**Live Demo:** https://mindrian.onrender.com

## 🤖 Available Bots

| Bot | Purpose |
|-----|---------|
| 🧠 **Larry** | General PWS thinking partner - helps identify problems worth solving |
| 🔮 **Trending to the Absurd** | Guided 7-phase workshop to escape presentism and find future problems |
| 🎯 **Jobs to Be Done** | 6-phase workshop to discover what customers really hire products for |
| 📈 **S-Curve Analysis** | 5-phase workshop to analyze technology timing and disruption |
| 😈 **Red Teaming** | 6-phase workshop to stress-test assumptions as devil's advocate |

## ✨ Features

### Core Features
- **Real-time streaming** - Token-by-token response display
- **Chat profiles** - Switch between 5 specialized bots
- **Workshop phases** - Structured progress tracking with task lists
- **Action buttons** - Quick actions (Next Phase, Show Example, Show Progress)

### Interactive Elements
- 📊 **Task Lists** - Track workshop progress through phases
- 🔘 **Action Buttons** - Navigate workshops without typing
- 📎 **File Upload** - Attach documents to messages
- 🎤 **Voice Input** - Speech-to-text support
- 🔊 **Voice Output** - Text-to-speech support
- 📈 **Charts** - S-curve and comparison visualizations (Plotly)

### Research Tools
- 🔍 **Tavily Search** - Web research for trend validation
- 🧠 **Sequential Thinking** - Structured reasoning (coming soon)

## 🚀 Quick Start

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

## 📁 Project Structure

```
mindrian-deploy/
├── mindrian_chat.py          # Main Chainlit application
├── prompts/                  # System prompts for each bot
│   ├── __init__.py
│   ├── larry_core.py         # Larry's conversational prompt
│   ├── tta_workshop.py       # Trending to the Absurd (7 phases)
│   ├── jtbd_workshop.py      # Jobs to Be Done (6 phases)
│   ├── scurve_workshop.py    # S-Curve Analysis (5 phases)
│   └── redteam.py            # Red Teaming (6 phases)
├── tools/                    # MCP tools and integrations
│   ├── __init__.py
│   └── tavily_search.py      # Web research capabilities
├── utils/                    # Utility functions
│   ├── __init__.py
│   └── charts.py             # Plotly chart generators
├── .chainlit/
│   └── config.toml           # Chainlit configuration
├── requirements.txt          # Python dependencies
├── .env.example              # Environment template
├── chainlit.md               # Welcome page content
└── README.md                 # This file
```

## 🔧 Configuration

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

## 🌐 Deployment

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

### Other Platforms

**Railway / Fly.io:**
```bash
# Build command
pip install -r requirements.txt

# Start command
chainlit run mindrian_chat.py --host 0.0.0.0 --port $PORT -h
```

## 📚 Workshop Phases

### 🔮 Trending to the Absurd
1. Introduction
2. Domain & Trends
3. Deep Research
4. Absurd Extrapolation
5. Problem Hunting
6. Opportunity Validation
7. Action Planning
8. Reflection

### 🎯 Jobs to Be Done
1. Introduction
2. Struggling Moment
3. Functional Job
4. Emotional Job
5. Social Job
6. Competing Solutions
7. Job Statement

### 📈 S-Curve Analysis
1. Introduction
2. Technology Identification
3. Era Assessment
4. Evidence Gathering
5. Ecosystem Readiness
6. Timing Decision

### 😈 Red Teaming
1. Introduction
2. Assumption Extraction
3. Assumption Ranking
4. Attack Mode
5. Competition & Alternatives
6. Failure Modes
7. Strengthening

## 🛠️ Adding New Bots

1. Create prompt file in `prompts/` following existing patterns
2. Add to `prompts/__init__.py`
3. Add bot config to `BOTS` dict in `mindrian_chat.py`
4. Add phases to `WORKSHOP_PHASES` if applicable
5. Add to `chat_profiles()` function

## 📖 About PWS

The Problem Worth Solving methodology was developed by Professor Lawrence Aronhime over 30+ years of teaching innovation at Johns Hopkins University.

**Core insight:** Most innovation fails not because of bad solutions, but because people solve the wrong problems.

---

Built with ❤️ using [Chainlit](https://chainlit.io) + [Google Gemini](https://deepmind.google/models/gemini/)
