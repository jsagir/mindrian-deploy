# Welcome to Mindrian

**AI-Powered Innovation Workshop Platform with Multi-Agent Orchestration**

Mindrian is an advanced multi-agent platform for innovation methodology, built on LangGraph orchestration and the A2A (Agent-to-Agent) Protocol. It combines structured thinking frameworks with intelligent routing, expert panels, and collaborative agent workflows.

**Live Demo:** https://mindrian.onrender.com
**Course:** EN.663.635 Problems Worth Solving - Johns Hopkins University

---

## Triple-Mode Architecture

Mindrian uses intelligent entry point detection to route users to the right experience:

| Entry Point | Mode | What Happens |
|------------|------|--------------|
| 🧠 **Explore Ideas** | Sandbox | Open-ended exploration with coaching hints |
| 📄 **Get Feedback** | Workshop | Document analysis with structured diagnostic flow |
| 🚀 **Build Venture** | Venture | Stage-aware guidance (ideation → validation → growth) |

---

## PWS Consultant (Primary Bot)

The **PWS Consultant** is a structured 3-stage process that adapts to your problem type:

### Stage 1: Challenge Introduction
- You describe your challenge
- Background pipelines run: LangExtract, GraphRAG, domain discovery, expert panel building

### Stage 2: Problem Diagnostic
- 5 MCQ questions scored automatically
- Classification into 4 problem types:
  - **Un-Defined** → Exploration mode
  - **Ill-Defined** → Framework selection
  - **Well-Defined** → Solution refinement
  - **Wicked** → Multi-perspective synthesis

### Stage 3: Guided Consulting
- Framework-guided conversation with dynamically built expert panel
- Context-driven tool offering (research, visualization, synthesis)

---

## Available Workshops

| Workshop | What It Does | Best For |
|----------|-------------|----------|
| **PWS Consultant** | Structured diagnostic + expert panel consulting | Primary entry, all problem types |
| **Lawrence** | Focused thinking partner for discovering problems | Quick guidance, general exploration |
| **Larry Playground** | Full-featured lab with all tools enabled | Deep research, complex problems |
| **Trending to the Absurd (TTA)** | Take trends to extremes to find future problems | Spotting emerging opportunities |
| **Jobs to Be Done (JTBD)** | Discover what customers actually hire products for | Customer research, product design |
| **S-Curve Analysis** | Analyze technology timing and disruption | Market timing, investment decisions |
| **Red Teaming** | Stress-test assumptions as devil's advocate | Validating ideas, finding weaknesses |
| **Ackoff's Pyramid** | DIKW framework for validated understanding | Decision-making, avoiding blind spots |
| **Scenario Analysis** | Explore multiple plausible futures | Strategic planning |
| **Beautiful Question** | WHY → WHAT IF → HOW methodology | Breaking assumptions |

---

## Intelligence Pipelines

Mindrian includes production-grade LangGraph pipelines for complex analysis:

| Pipeline | What It Does | Output |
|----------|-------------|--------|
| **Minto Pyramid** | SCQA + Beautiful Question synthesis | Structured problem definition |
| **Genesis** | 6-stage expert breakdown (decompose → domains → personas → panel → synthesize) | Multi-expert synthesis |
| **Domain Discovery** | CV/background analysis → IKA scoring → domain recommendations | Personalized domain map |
| **Reverse Salient** | Cross-domain pattern mining | Innovation opportunities |
| **Oracle** | Prediction market formulation + resolution | Calibrated forecasts |
| **Grading** | PWS quality scoring with bias detection | Grade breakdown |

---

## A2A Protocol (Agent-to-Agent Communication)

Agents communicate via structured Markdown handoffs:

```
┌─────────────┐    ┌──────────────────┐    ┌─────────────┐
│   Agent A   │ -> │  handoff.md file │ -> │   Agent B   │
│  (Lawrence) │    │  (structured)    │    │    (TTA)    │
└─────────────┘    └──────────────────┘    └─────────────┘
```

- **Two-stage classification**: Cynefin (uncertainty) + PWS (lifecycle)
- **Red Team middleware**: Cross-cutting challenge layer for all outputs
- **Context separation**: Artifacts (validated facts) vs Frames (agent speculation)
- **Journey mapping**: Any agent can request user's full journey context

---

## Privacy & Context Isolation

**Your data is yours:**

- **Per-user sessions**: Your conversation context is isolated to your session only
- **Supabase Auth**: OAuth login with secure session management
- **No cross-user sharing**: Context, artifacts, and history are never shared between users
- **PostgreSQL persistence**: Session data stored securely per user ID
- **GDPR-aligned**: User data is associated with your account only

---

## How to Use Mindrian

### Getting Started

1. **Visit** https://mindrian.onrender.com
2. **Log in** with your account (or continue as guest)
3. **Choose your entry point**: Explore Ideas, Get Feedback, or Build Venture
4. **Follow the diagnostic flow** or start with conversation starters
5. **Use action buttons** for research, synthesis, and visualization

### Tips for Best Results

- **Upload documents** - PDFs, Word docs, images, and code files are supported
- **Be specific** - More context enables better guidance
- **Use the buttons** - Action buttons trigger specialized agent workflows
- **Adjust settings** - Use Settings gear to control response detail level
- **Ask for examples** - Request real-world examples from the knowledge base

### Features

- **Voice input** - Click the microphone to speak
- **Document analysis** - Upload and analyze PDFs, Word docs, presentations
- **Multi-agent analysis** - Get perspectives from multiple specialized agents
- **Research tools** - Patents, news, academic papers, trends, government data
- **Progress tracking** - Visual progress through workshop phases
- **Bank of Opportunities** - Extracted opportunities stored across sessions
- **Expert panels** - Dynamically assembled based on your problem domain
- **Visualizations** - Mermaid diagrams, quadrant charts, canvases

---

## Research Tools

Mindrian includes 16+ LangChain-wrapped tools for comprehensive research:

| Tool | What It Searches | Use For |
|------|-----------------|---------|
| **Deep Research** | Web (Tavily), PWS knowledge base | General exploration |
| **Patent Search** | Google Patents | Innovation landscape, prior art |
| **News Search** | NewsMesh, Tavily | Current events, market signals |
| **Academic Search** | arXiv | Research papers, scientific findings |
| **Trends Search** | SerpAPI Google Trends | Market interest, timing |
| **Government Data** | FRED, World Bank | Economic indicators, statistics |
| **Dataset Search** | Kaggle, Socrata | Data for analysis |
| **Neo4j GraphRAG** | PWS knowledge graph | Frameworks, case studies, concepts |
| **LangExtract** | Structured extraction | Statistics, assumptions, signals |
| **Text2Cypher** | Natural language → Cypher | Query the knowledge graph |

### Smart Research Contextualization

Research results are analyzed for relevance to YOUR specific problem:
- Relevance scoring for each result
- PWS-grounded recommendations
- Integration with your Bank of Opportunities

---

## Frequently Asked Questions

**Q: What is PWS?**
A: Problems Worth Solving - a framework for finding problems valuable enough to actually solve. Instead of building solutions for problems nobody cares about, PWS helps you identify high-value opportunities.

**Q: What's the difference between Lawrence and Larry Playground?**
A: Lawrence is the focused thinking partner - concise, conversational. Larry Playground has all the tools enabled: research, multi-agent analysis, visualizations. Use Lawrence for quick guidance, Larry Playground for deep exploration.

**Q: Can I upload files?**
A: Yes! PDFs, Word documents, PowerPoint, images, text files, and code files are all supported. Just drag and drop or use the paperclip icon.

**Q: Is my conversation saved?**
A: Yes, conversations persist across sessions. You can close your browser and return later to continue.

**Q: How do I get more detailed responses?**
A: Use the Settings gear (top-right) and increase the "Response Detail" slider.

**Q: Can I use voice input?**
A: Yes! Click the microphone icon to speak instead of type.

---

## New in v4.0 (February 2026)

### Triple-Mode Architecture
Intelligent entry point detection routes users to the right experience based on their intent and attachments.

### PWS Consultant Bot
Structured 3-stage diagnostic flow with automated problem classification and expert panel building.

### A2A Protocol
Agent-to-agent communication via structured Markdown handoffs with two-stage classification (Cynefin + PWS).

### Wave 2-4 Features
- **Wave 2**: Conversation forking and branch management
- **Wave 3**: Idea Canvas for visual collaboration
- **Wave 4**: Auto-orchestration with intent-based workflow selection

### 40+ Custom UI Components
Interactive React components for visualizations, forms, and workflows:
- MermaidDiagram, QuadrantChart, BusinessModelCanvas
- OpportunityCard, ScoreBreakdown, GradeReveal
- IdeaCanvas, BranchSelector, CommandCenter
- ThinkingPanel, VoiceChat, WorkshopRoadmap

### LangGraph Intelligence Layer
10 production pipelines: Minto, Genesis, Oracle, Grading, Domain Discovery, Reverse Salient, BONO, File Processing, and more.

### Bank of Opportunities
Multi-backend storage (Supabase, Neo4j, LightRAG, FileSearch) for extracted opportunities with 40+ fields per opportunity.

---

## Legal Disclaimers

### Research Results Disclaimer

Research results provided by Mindrian (including patent searches, news articles, academic papers, government data, and trend analysis) are:

- **For informational purposes only** - Not legal, financial, or professional advice
- **Potentially incomplete** - Results depend on third-party APIs and may not include all relevant sources
- **Time-sensitive** - Information may become outdated; verify current status for important decisions
- **AI-analyzed** - Relevance assessments are generated by AI and may contain errors

**Always verify important information** from primary sources before making decisions.

### General Platform Disclaimer

Mindrian is an educational tool designed to support innovation thinking. The platform:

- Does not guarantee the accuracy, completeness, or timeliness of any information
- Is not a substitute for professional advice (legal, financial, business, medical, etc.)
- May experience service interruptions or data loss
- Stores conversation data for session persistence and quality improvement

Use of this platform constitutes acceptance of these terms.

### Intellectual Property

- User-uploaded content remains the property of the user
- AI-generated content is provided as-is without warranty
- PWS methodology is based on coursework from Johns Hopkins University

---

## Technical Details

### Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Chainlit 2.9+ with 40+ custom JSX components |
| **AI Model** | Google Gemini 2.5-flash / 3-flash-preview |
| **Orchestration** | LangGraph StateGraph + LangChain tools |
| **Knowledge Base** | Neo4j GraphRAG + Gemini File Search + LightRAG |
| **Database** | PostgreSQL (Supabase) with per-user isolation |
| **Auth** | Supabase Auth (OAuth, password, guest) |
| **Storage** | Supabase Storage + Cloud buckets |
| **Deployment** | Render (auto-deploy from main) |

### Architecture Highlights

- **Protocols Package**: A2A handoffs, context journals, agent registry, phase manager
- **Intelligence Package**: 16 tools, 12 schemas, 10 pipelines, 7 agents
- **Skills System**: 16+ Claude Code skills for development assistance
- **R&D Folder**: 25+ research tracks with implementations

### Documentation

| Document | Purpose |
|----------|---------|
| [CLAUDE.md](./CLAUDE.md) | Technical reference for developers |
| [docs/A2A_PRACTICAL_ARCHITECTURE.md](./docs/A2A_PRACTICAL_ARCHITECTURE.md) | A2A protocol design decisions |
| [docs/CHAINLIT_COMPONENTS.md](./docs/CHAINLIT_COMPONENTS.md) | Custom UI component guide |
| [docs/TRIPLE_MODE_ARCHITECTURE_SPEC.md](./docs/TRIPLE_MODE_ARCHITECTURE_SPEC.md) | Entry point routing specification |

### Repository
- **GitHub:** https://github.com/jsagir/mindrian-deploy
- **Issues:** https://github.com/jsagir/mindrian-deploy/issues

---

## About

Mindrian was developed to support the **Problems Worth Solving** methodology created by Professor Lawrence Aronhime at Johns Hopkins University. The platform applies 30+ years of innovation teaching to help users discover valuable problems.

**Core Insight:** Most innovation fails not because of bad solutions, but because people solve the wrong problems.

### Project Philosophy

- **Per-user context isolation** - Your data is never shared with other users
- **Structured over freeform** - Explicit state machines over loose conversational phases
- **Evidence over opinion** - Always show WHY the AI thinks something
- **Artifacts vs Frames** - Validated facts persist; agent speculation stays scoped
- **Red Team everything** - Cross-cutting challenge layer for all outputs

---

Built with Chainlit + LangGraph + Google Gemini + Neo4j + LightRAG + Supabase

*v4.0 - February 2026*
