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
| **Explore Ideas** | Sandbox | Open-ended exploration with coaching hints |
| **Get Feedback** | Workshop | Document analysis with structured diagnostic flow |
| **Build Venture** | Venture | Stage-aware guidance (ideation → validation → growth) |

---

## Available Bots (20)

### Core Thinking Partners

| Bot ID | Name | Type | Description |
|--------|------|------|-------------|
| `lawrence` | Lawrence | Core | Focused PWS thinking partner — concise, Socratic |
| `larry_playground` | Larry Playground | Core | Full-featured lab — all tools, research, multi-agent |
| `pws_consultant` | PWS Consultant | Diagnostic | Structured 3-stage diagnostic with expert panel building |

### Innovation Workshops (5-11 phases each)

| Bot ID | Name | Phases | Methodology |
|--------|------|--------|-------------|
| `tta` | Trending to the Absurd | 8 | Escape presentism, find future problems |
| `jtbd` | Jobs to Be Done | 7 | Discover what customers hire products for |
| `scurve` | S-Curve Analysis | 6 | Technology timing and disruption |
| `scenario` | Scenario Analysis | 6 | Shell Oil scenario planning methodology |
| `beautiful_question` | Beautiful Question | 11 | WHY → WHAT IF → HOW breakthrough questioning |
| `bono` | BONO Master | 10 | Six Thinking Hats + Minto Pyramid synthesis |
| `domain` | Domain Selection | 5 | Choose where to innovate (Interest-Knowledge-Access) |

### Critical Thinking Workshops

| Bot ID | Name | Phases | Methodology |
|--------|------|--------|-------------|
| `redteam` | Red Teaming | 7 | Stress-test assumptions as devil's advocate |
| `ackoff` | Ackoff's Pyramid | 8 | DIKW framework for validated understanding |
| `knowns` | Known-Unknowns | 8 | Rumsfeld Matrix for blind spot discovery |
| `nested_hierarchies` | Nested Hierarchies | 5 | Multi-level systems analysis for leverage points |

### Strategic & Validation

| Bot ID | Name | Phases | Methodology |
|--------|------|--------|-------------|
| `investment` | PWS Investment | 10 | Ten Questions + Investment Thesis evaluation |
| `validation` | Multi-Perspective Validation | 11 | Domain-specific Six Thinking Hats + research |

### Assessment Bots

| Bot ID | Name | Type | Purpose |
|--------|------|------|---------|
| `grading` | Problem Discovery Grading | Assessment | Grade student work with detailed rubric |
| `minto` | Minto Grading | Assessment | One-shot autonomous grading with Minto structure |

---

## Intelligence Pipelines (18+)

LangGraph StateGraph pipelines for complex analysis workflows:

### Core Pipelines

| Pipeline | What It Does | Key Feature |
|----------|-------------|-------------|
| **Deep Research** | Claude plans → Tavily searches → Gemini synthesizes | 3 depth tiers (basic/standard/deep) with reflection loops |
| **Minto Pyramid** | SCQA + Beautiful Question synthesis | Framework discovery + web research |
| **Genesis** | 7-stage expert breakdown | decompose → domains → personas → panel → synthesize |
| **Domain Discovery** | CV/background → IKA scoring → domain recommendations | Personalized domain map |
| **Reverse Salient** | Cross-domain pattern mining | Constraint detection in nested systems |
| **Oracle** | Prediction market formulation + resolution | Brier-scored calibrated forecasts |
| **Grading** | PWS quality scoring with bias detection | 8-phase rubric with evidence assessment |
| **BONO Innovation** | Six Thinking Hats + Lateral Thinking + Domain Personas | 7-phase creative analysis |
| **Sequential Thinking** | Real-time chain-of-thought reasoning | Self-prompting + tree-of-thoughts |
| **Message Router** | Intent-based routing to handler | feedback → research → synthesis → other |
| **File Processing** | Upload → extraction → embedding workflow | Multi-format document intelligence |

### Genesis Sub-Pipelines (7)

| Sub-Pipeline | Purpose |
|-------------|---------|
| Decompose | Break problems into components |
| Domains | Domain identification & classification |
| Orchestrate | Multi-stage workflow coordination |
| Panel | Expert panel discussion simulator |
| Personas | Dynamic persona generation |
| Pipeline | Main genesis orchestrator |
| Synthesize | Multi-perspective synthesis |

---

## Key Features

### Deep Research Pipeline (NEW)

Multi-model research with iterative reflection:
- **Claude** plans search queries (preserves user's exact key terms)
- **Tavily** executes parallel web searches
- **Claude** reflects on coverage gaps and plans follow-up queries
- **Gemini** synthesizes final report with PWS framing
- 3 depth tiers: basic (no reflection), standard (1 round), deep (up to 3 rounds)

### Creative Leaps

Every 4th conversational turn, the knowledge graph fires a cross-domain spark — a "What if...?" provocation from an unexpected domain. Uses Neo4j community detection to find distant but substantive connections.

### Convergence & Saturation Detection

After 8+ turns of Socratic questioning, pure-Python heuristics detect conversation saturation (repetition, shrinking messages, circular topics). Suggests the "Give me your answer" button for direct synthesis.

### Background ERIC

Nightly enrichment pipeline: Claude analyzes recent conversations for knowledge gaps → Tavily researches them → writes new concepts to Neo4j. Zero latency impact on live conversations.

### Multi-Agent System

Background agents (research, validation, analysis) collaborate on complex queries:
- **Quick Analysis**: Router picks agents automatically
- **Research & Explore**: Research → TTA → Larry pipeline
- **Validated Decision**: Validation → Ackoff → Red Team pipeline
- **Full Analysis**: All agents in sequence

### A2A Protocol (Agent-to-Agent Communication)

Structured Markdown handoffs between agents:
- **Two-stage classification**: Cynefin (uncertainty) + PWS (lifecycle)
- **Red Team middleware**: Cross-cutting challenge layer
- **Context separation**: Artifacts (validated facts) vs Frames (agent speculation)
- **Context Journal**: Living document tracking thinking steps

### GraphRAG Lite

Hybrid semantic + graph retrieval combining Neo4j relationships with vector search:
- Concept matching, framework suggestions, creative leaps
- ~100-200ms per query (bounded, no LLM call)

### Smart Phase Tracker

LLM-based phase analysis for workshop progression:
- Evidence-based phase completion detection
- Gap analysis (what's covered vs. missing)
- Confidence-gated suggestions (only shows when confident)

---

## Architecture

### Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Chainlit 2.9+ with 44 custom JSX components |
| **AI Models** | Gemini 2.0-flash (front), Claude Sonnet (background planning) |
| **Orchestration** | LangGraph StateGraph + LangChain tools |
| **Knowledge Base** | Neo4j GraphRAG + Gemini File Search + LightRAG |
| **Database** | PostgreSQL (Supabase) with per-user isolation |
| **Auth** | Supabase Auth (OAuth, password, guest) |
| **Storage** | Supabase Storage + Cloud buckets |
| **Voice** | ElevenLabs TTS + STT |
| **Research** | Tavily, arXiv, Google Patents, FRED, News, Trends |
| **Deployment** | Render (auto-deploy from main) |

### Project Structure

```
mindrian-deploy/
├── mindrian_chat.py          # Main Chainlit app (16,200+ lines)
├── prompts/                  # 23 system prompts for all bots
├── intelligence/
│   ├── pipelines/            # 11 LangGraph pipelines + 7 Genesis sub-pipelines
│   ├── agents/               # Multi-agent orchestration
│   ├── tools/                # Oracle tools, Text2Cypher
│   └── schemas.py            # Pydantic models
├── tools/                    # 39 tool modules (search, AI, knowledge, workflows)
├── utils/                    # 45 utility modules
├── protocols/                # 17 files: A2A, context, orchestration, routing
├── memory/                   # Checkpointer, user journey tracking
├── agents/                   # Multi-agent graph workflows
├── skills/                   # 21 skill directories
├── scripts/                  # 23 admin/dev scripts
├── public/elements/          # 44 custom React JSX components
├── R&D/                      # 32 research tracks
├── docs/                     # Technical documentation
└── qa/                       # QA test suites
```

### Module Counts

| Category | Count |
|----------|-------|
| Bots | 20 (2 core + 15 workshop + 2 assessment + 1 diagnostic) |
| Pipelines | 18 (11 main + 7 Genesis sub-pipelines) |
| Tools | 39 modules across 5 categories |
| Utilities | 45 modules across 9 categories |
| UI Components | 44 JSX (39 active + 4 templates + 1 archive) |
| Prompts | 23 system prompt files |
| Skills | 21 directories + 19 Claude skill markdown files |
| Scripts | 23 admin/development scripts |
| Protocols | 17 files (A2A, routing, orchestration) |
| R&D Tracks | 32 active research projects |

---

## Privacy & Context Isolation

- **Per-user sessions**: Conversation context isolated to your session
- **Supabase Auth**: OAuth login with secure session management
- **No cross-user sharing**: Context, artifacts, and history never shared
- **PostgreSQL persistence**: Session data stored securely per user ID

---

## Development

### Run Locally
```bash
chainlit run mindrian_chat.py --watch
```

### Health Check
```bash
python scripts/health_check.py
```

### Generate New Bot
```bash
python scripts/generate_agent.py newbot "New Bot Name" --workshop --phases 5
```

### Deploy
Push to main branch — auto-deploys via Render webhook.

### Documentation

| Document | Purpose |
|----------|---------|
| [CLAUDE.md](./CLAUDE.md) | Technical reference for AI developers (42KB) |
| [DEVELOPMENT.md](./DEVELOPMENT.md) | Development guide (24KB) |
| [docs/A2A_PRACTICAL_ARCHITECTURE.md](./docs/A2A_PRACTICAL_ARCHITECTURE.md) | A2A protocol design |
| [docs/CHAINLIT_COMPONENTS.md](./docs/CHAINLIT_COMPONENTS.md) | Custom UI component guide |
| [docs/TRIPLE_MODE_ARCHITECTURE_SPEC.md](./docs/TRIPLE_MODE_ARCHITECTURE_SPEC.md) | Entry point routing spec |

---

## New in v4.1 (February 2026)

### Deep Research Pipeline
Multi-model research with Claude planning, Tavily searching, and Gemini synthesizing. Iterative reflection loops catch coverage gaps.

### Creative Leaps
Cross-domain sparks every 4th turn from the knowledge graph — unexpected connections that provoke new thinking.

### Convergence Mechanism
Saturation detection after 8+ turns with "Give me your answer" direct synthesis mode.

### Background ERIC
Nightly graph enrichment — Claude analyzes conversations for knowledge gaps, Tavily researches them, writes to Neo4j.

### Smart Resume
Returning users get a concise recap of their conversation instead of a bare "Welcome back."

### 8 New Bots Since v4.0
BONO Master, Known-Unknowns, Nested Hierarchies, Domain Selection, PWS Investment, Scenario Analysis, Multi-Perspective Validation, Beautiful Question.

### 44 Custom UI Components
Interactive React components: MermaidDiagram, QuadrantChart, BusinessModelCanvas, ThinkingPanel, WorkshopRoadmap, IdeaCanvas, and more.

### LangGraph Intelligence Layer
18 production pipelines including the new Deep Research Pipeline and Genesis sub-pipelines.

---

## Legal Disclaimers

### Research Results
Research results are for informational purposes only — not legal, financial, or professional advice. Results may be incomplete or time-sensitive. Always verify from primary sources.

### Platform
Mindrian is an educational tool. It does not guarantee accuracy or completeness. Not a substitute for professional advice. User-uploaded content remains user property. AI-generated content is provided as-is.

### Intellectual Property
PWS methodology is based on coursework from Johns Hopkins University.

---

## About

Mindrian was developed to support the **Problems Worth Solving** methodology created by Professor Lawrence Aronhime at Johns Hopkins University. The platform applies 30+ years of innovation teaching to help users discover valuable problems.

**Core Insight:** Most innovation fails not because of bad solutions, but because people solve the wrong problems.

---

Built with Chainlit + LangGraph + Google Gemini + Anthropic Claude + Neo4j + LightRAG + Supabase

*v4.1 - February 2026*
