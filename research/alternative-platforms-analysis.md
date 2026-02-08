# Alternative Platform Research: Mindrian Restructuring Analysis

**Branch:** `claude/create-median-branch-B3KVS` (Alternative Research)
**Date:** 2026-02-08
**Purpose:** Evaluate three open-source platforms as potential UI/backend alternatives for Mindrian

---

## Executive Summary

Three platforms were evaluated as potential alternatives for Mindrian's Chainlit-based architecture. **None are suitable as direct replacements** — all three are desktop AI agent applications (alternatives to Claude's "Cowork" product), not web-based multi-bot workshop platforms. However, several architectural patterns are worth adopting.

The star counts and some feature claims in the original brief were significantly inflated (5-17x) compared to verified GitHub data.

---

## Current Mindrian Stack (Baseline)

| Layer | Technology | Notes |
|-------|-----------|-------|
| Frontend/UI | Chainlit 2.9+ | Web-served, multi-modal, real-time streaming |
| AI Model | Google Gemini (gemini-3-flash-preview, gemini-2.0-flash) | Primary LLM |
| RAG | Gemini File Search + Neo4j GraphRAG Lite | Semantic + structural retrieval |
| Database | PostgreSQL (SQLAlchemy + asyncpg) | Session persistence via Supabase |
| Storage | Supabase Storage | Files, extractions, feedback |
| Voice | ElevenLabs TTS + Deepgram STT | Streaming WebSocket |
| Search | Tavily, arXiv, SerpApi, NewsAPI | Multi-source research |
| Charts | Plotly | DIKW Pyramid, S-Curve, DataFrames |
| Deploy | Render | Auto-deploy on git push |
| Architecture | Multi-bot (7+ personas), workshop phases, context preservation | Production v3.1 |

---

## Platform 1: Open Cowork (OpenCoworkAI)

**GitHub:** [github.com/OpenCoworkAI/open-cowork](https://github.com/OpenCoworkAI/open-cowork)
**License:** MIT | **Language:** TypeScript | **Stars:** ~120-218 (claimed 3.5k)

### Verified Architecture

- **Desktop framework:** Electron
- **Frontend:** React + Tailwind CSS
- **Backend:** Node.js (Electron main process)
- **Database:** SQLite (local)
- **Sandbox:** WSL2 (Windows), Lima VM (macOS)

### Verified Features

| Claimed Feature | Status | Notes |
|----------------|--------|-------|
| One-click install | Confirmed | Pre-built installers for Win/Mac |
| GUI operation | Confirmed | Electron desktop app |
| Skills system | Confirmed | Modular `.claude/skills/` files |
| OpenRouter + Anthropic | Confirmed | Claude 4.5 Sonnet, OpenRouter |
| Chinese models | Confirmed | GLM-4.7, MiniMax, Kimi |
| PPTX/DOCX/XLSX | Confirmed | Document generation skills |
| Full rebrand | Partial | Customizable but fundamentally a Claude Cowork clone |

### Fit Assessment for Mindrian

| Mindrian Need | Fit | Rating |
|---------------|-----|--------|
| Multi-bot workshop platform | No multi-bot concept | Poor |
| Web-based multi-user access | Desktop-only, single-user | Poor |
| Gemini integration | Not supported | Poor |
| RAG (File Search + Neo4j) | No RAG system | Poor |
| Voice (TTS/STT) | No voice features | None |
| Structured workshop phases | No phase concept | None |
| Session persistence (PostgreSQL) | SQLite local only | Poor |

### Transferable Ideas

- **Skills system** — Modular skill files that extend agent capabilities. Could inspire a plugin architecture for Mindrian's tools.
- **VM-level sandboxing** — WSL2/Lima isolation for command execution.
- **Real-time Trace Panel** — Visualization of AI reasoning steps (Mindrian already has `cl.Step` but could be richer).

---

## Platform 2: KIRA (Krafton Intelligence Rookie Agent)

**GitHub:** [github.com/krafton-ai/KIRA](https://github.com/krafton-ai/KIRA)
**Docs:** [kira.krafton-ai.com](https://kira.krafton-ai.com)
**License:** Apache 2.0 | **Language:** Python + Electron | **Stars:** ~585 (claimed 2k)

### Verified Architecture

- **Backend:** Python 3.10+ (AI server)
- **Frontend:** Electron (desktop shell)
- **Interface:** Slack-native (primary), desktop app (secondary)
- **Multi-agent:** Sophisticated pipeline with per-channel worker queues

### Multi-Agent Pipeline (Most Interesting Feature)

KIRA's tiered model usage for cost optimization:

| Task Complexity | Model Used | Examples |
|----------------|-----------|----------|
| Simple | Claude Haiku | Bot call detection, classification |
| Moderate | Claude Sonnet | Memory management, summarization, proactive suggestions |
| Complex | Claude Opus | Core task execution with tools |

Worker queue architecture:
- **Per-channel queues:** 8 workers for parallel processing
- **Orchestrator queue:** 3 workers for task coordination
- **Sequential memory queue:** 1 worker for memory consistency

### Verified Features

| Claimed Feature | Status | Notes |
|----------------|--------|-------|
| Proactive suggestions | Confirmed | Sonnet generates suggestions |
| Smart memory | Confirmed | Local memory, persists across conversations |
| Slack-native | Confirmed | Primary interface is Slack |
| Claude-focused | Confirmed | Exclusively Anthropic models |
| Enterprise integrations | Confirmed | Perplexity, DeepL, Outlook, Confluence, Jira, GitLab via MCP |

### Fit Assessment for Mindrian

| Mindrian Need | Fit | Rating |
|---------------|-----|--------|
| Multi-bot workshop platform | Internal agents only, not user-facing personas | Partial |
| Web-based multi-user access | Desktop + Slack | Partial |
| Gemini integration | Claude-only, hardcoded | None |
| RAG | No RAG system | Poor |
| Voice | Clova Speech input only, no TTS | Poor |
| Structured workshop phases | No phase concept | None |
| Multi-agent collaboration | Strong pipeline architecture | Good |
| Proactive suggestions | Built-in | Good |

### Transferable Ideas

- **Tiered model routing** — Use cheap models (Gemini Flash) for classification/routing, expensive models for core reasoning. Mindrian could route simple queries to Gemini Flash Lite and complex workshop analysis to Gemini Pro.
- **Per-channel worker queues** — If Mindrian scales to many concurrent users, this queue architecture prevents bottlenecks.
- **Proactive suggestion engine** — After a user response, generate 2-3 "what you might want to explore next" suggestions. Mindrian already has starters, but mid-conversation suggestions could improve engagement.
- **Memory consistency queue** — Dedicated single-worker queue for memory writes to prevent race conditions during concurrent bot switches.

---

## Platform 3: Kuse Cowork

**GitHub:** [github.com/kuse-ai/kuse_cowork](https://github.com/kuse-ai/kuse_cowork)
**Website:** [kuse.ai/open-cowork/features](https://www.kuse.ai/open-cowork/features)
**License:** MIT | **Language:** Rust + TypeScript | **Stars:** ~378-420 (claimed 1k)

### Verified Architecture

- **Backend/Agent:** Pure Rust (zero external dependencies for agent core)
- **Frontend:** SolidJS + TypeScript
- **Desktop framework:** Tauri (NOT web-based as claimed)
- **Database:** SQLite (local)
- **Containerization:** Docker for sandboxed execution
- **Binary size:** ~10-16MB compiled

### Verified Features

| Claimed Feature | Status | Notes |
|----------------|--------|-------|
| Rust-native speed | Confirmed | Pure Rust agent, ~10-16MB binary |
| Docker sandboxing | Confirmed | All commands execute in Docker containers |
| Web-based | **INCORRECT** | It's a Tauri desktop app |
| OpenAI/Anthropic/Ollama | Confirmed | Also supports Gemini and LM Studio |
| PDF/Excel | Confirmed | DOCX, PDF, PPTX, XLSX via skills |
| Tiny binary | Confirmed | ~10-16MB |

### Fit Assessment for Mindrian

| Mindrian Need | Fit | Rating |
|---------------|-----|--------|
| Multi-bot workshop platform | Single-agent desktop app | Poor |
| Web-based multi-user access | Desktop-only (Tauri) | Poor |
| Gemini integration | Supported as a provider | Good |
| RAG | No RAG system | Poor |
| Voice | No voice features | None |
| Workshop phases | No phase concept | None |
| Document generation | DOCX/PDF/PPTX/XLSX skills | Good |

### Transferable Ideas

- **Docker-sandboxed code execution** — If Mindrian ever adds a "run user code" feature for workshops, Docker isolation is the right pattern.
- **Broadest model support pattern** — Kuse's provider abstraction supports any OpenAI-compatible endpoint. Could inform a model-agnostic layer for Mindrian.
- **Document generation skills** — The skill-based approach to generating PPTX/DOCX/XLSX could enhance Mindrian's current PDF/MD export capabilities.

---

## Comparative Matrix

| Dimension | Open Cowork | KIRA | Kuse Cowork | Mindrian |
|-----------|-------------|------|-------------|----------|
| **Verified Stars** | ~120-218 | ~585 | ~378-420 | Production |
| **License** | MIT | Apache 2.0 | MIT | Proprietary |
| **Language** | TypeScript | Python | Rust | Python |
| **Deployment** | Desktop (Electron) | Desktop + Slack | Desktop (Tauri) | **Web (Chainlit)** |
| **Multi-User** | No | Via Slack | No | **Yes** |
| **Multi-Bot** | No | Internal only | No | **Yes (7+)** |
| **Gemini** | No | No | Yes | **Yes (primary)** |
| **RAG** | No | No | No | **Yes** |
| **Voice** | No | Input only | No | **Yes (TTS+STT)** |
| **Phases** | No | No | No | **Yes** |
| **Doc Gen** | PPTX/DOCX/XLSX | Via tools | DOCX/PDF/PPTX/XLSX | PDF/DOCX/MD |
| **Maturity** | v2.0.0 | Beta v0.1.47 | v0.0.2 | **v3.1** |

---

## Recommendations

### Verdict: None are viable replacements

All three platforms solve a fundamentally different problem (desktop AI coding assistant) than Mindrian (web-based multi-bot workshop platform). A migration to any of these would require rebuilding every core feature from scratch.

### What IS worth adopting from this research:

#### 1. Tiered Model Routing (from KIRA)
**Effort: Medium | Impact: High (cost reduction)**

Route different task types to different Gemini model tiers:
- **Flash Lite** — Classification, trigger detection, simple Q&A
- **Flash** — Standard workshop conversations (current default)
- **Pro** — Multi-agent analysis, deep research synthesis, complex reasoning

#### 2. Proactive Mid-Conversation Suggestions (from KIRA)
**Effort: Low | Impact: Medium (engagement)**

After key workshop moments (phase completion, insight capture), generate 2-3 contextual suggestions like:
- "Explore this with Red Team analysis"
- "Run a JTBD lens on this problem"
- "Deep dive into the S-Curve implications"

This extends Mindrian's existing agent trigger system.

#### 3. Document Generation Skills (from Kuse Cowork)
**Effort: Medium | Impact: Medium (user value)**

Add PPTX and XLSX export alongside existing PDF/MD. Workshop participants often need slide decks summarizing their PWS analysis.

#### 4. Plugin/Skills Architecture (from Open Cowork)
**Effort: High | Impact: High (maintainability)**

Refactor Mindrian's monolithic `mindrian_chat.py` (1600+ lines) into a modular skills/plugin system:
- Each bot as a self-contained skill module
- Tools as pluggable skill extensions
- Standardized skill interface for easy addition of new bots

This is the restructuring that would have the most architectural impact.

### Better Alternatives to Investigate

If genuinely considering a platform migration, these are more aligned with Mindrian's needs:

| Platform | Why It Fits |
|----------|-------------|
| **Chainlit** (current) | Already production, active development, best fit for the use case |
| **Open WebUI** | Multi-model web chat with plugin system, closer to Mindrian's architecture |
| **Streamlit + LangGraph** | Python-native, composable agents, web-served |
| **Gradio** | Rapid UI prototyping, better for demo/workshop scenarios |
| **Next.js + Vercel AI SDK** | If migrating to TypeScript, full-stack web with streaming |

---

## Sources

- [OpenCoworkAI/open-cowork](https://github.com/OpenCoworkAI/open-cowork)
- [krafton-ai/KIRA](https://github.com/krafton-ai/KIRA)
- [KIRA Documentation](https://kira.krafton-ai.com)
- [kuse-ai/kuse_cowork](https://github.com/kuse-ai/kuse_cowork)
- [Kuse Cowork Features](https://www.kuse.ai/open-cowork/features)
- [Kuse Cowork HN Discussion](https://news.ycombinator.com/item?id=46677860)
