# Mindrian - Multi-Bot PWS Platform

A conversational AI platform for Problem Worth Solving (PWS) methodology, featuring Larry (the core thinking partner) and specialized workshop bots.

## 🤖 Available Bots

| Bot | Purpose |
|-----|---------|
| 🧠 **Larry** | General PWS thinking partner - helps identify problems worth solving |
| 🔮 **Trending to the Absurd** | Guided workshop to escape presentism and find future problems |
| 🎯 **Jobs to Be Done** | Discover what customers really hire products for |
| 📈 **S-Curve Analysis** | Analyze technology timing and disruption cycles |
| 😈 **Red Teaming** | Devil's advocate to stress-test assumptions |

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone <your-repo-url>
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
# Edit .env and add your Google API key
```

Get your Google AI API key at: https://aistudio.google.com/apikey

### 5. Run Locally

```bash
chainlit run mindrian_chat.py
```

Open http://localhost:8000 in your browser.

## 📁 Project Structure

```
mindrian-deploy/
├── mindrian_chat.py      # Main Chainlit application
├── prompts/              # System prompts for each bot
│   ├── __init__.py
│   ├── larry_core.py     # Larry's conversational prompt
│   ├── tta_workshop.py   # Trending to the Absurd
│   ├── jtbd_workshop.py  # Jobs to Be Done
│   ├── scurve_workshop.py# S-Curve Analysis
│   └── redteam.py        # Red Teaming / Devil's Advocate
├── requirements.txt      # Python dependencies
├── .env.example          # Environment template
├── chainlit.md           # Welcome page content
└── README.md             # This file
```

## 🌐 Deployment Options

### Chainlit Cloud (Recommended)
```bash
chainlit deploy mindrian_chat.py
```

### Render
1. Push to GitHub
2. Create new Web Service on Render
3. Build command: `pip install -r requirements.txt`
4. Start command: `chainlit run mindrian_chat.py --host 0.0.0.0 --port $PORT`
5. Add `GOOGLE_API_KEY` environment variable

### Railway / Fly.io
Similar setup - use the start command above.

## 🔧 Configuration

### Model Selection

The default model is `gemini-3-flash-preview`. To change it, edit `mindrian_chat.py`:

```python
model="gemini-3-flash-preview",  # or gemini-2.5-flash, gemini-2.0-flash
```

### Adding New Bots

1. Create a new prompt file in `prompts/`
2. Add to `prompts/__init__.py`
3. Add bot config to `BOTS` dict in `mindrian_chat.py`
4. Add to `chat_profiles()` function

## 📖 About PWS

The Problem Worth Solving methodology was developed by Professor Lawrence Aronhime over 30+ years of teaching innovation at Johns Hopkins University.

**Core insight:** Most innovation fails not because of bad solutions, but because people solve the wrong problems.

---

Built with ❤️ using [Chainlit](https://chainlit.io) + [Google Gemini](https://deepmind.google/models/gemini/)
