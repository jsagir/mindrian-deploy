# R&D-Relevant Changes

*Auto-generated: 2026-02-14 18:42*

---

## 2026-02-14

### 🔧 debug: Add verbose logging for Larry Mode + Claude guard checks

- **Commit:** `31cb5e06`
- **Author:** jsagir
- **Files changed:** 5
  - mindrian_chat.py
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** Adds print statements to diagnose whether Claude code path activates

### ✨ feat: Ask-Tell Dial refactor + Claude Sonnet 4.5 for Lawrence

- **Commit:** `de39dc9b`
- **Author:** jsagir
- **Files changed:** 15
  - mindrian_chat.py
  - prompts/larry_core.py
  - prompts/larry_skill/FRAMEWORK_CHAINS.md
  - prompts/larry_skill/INSIGHT_MODE.md
  - prompts/larry_skill/INVESTIGATIVE_MODE.md
- **Details:** Replace Larry's monolithic 170-line system prompt with a multi-file

## 2026-02-12

### 📝 docs: Add v3.2 changelog - Context Engine, KG-RAG patterns, prompt revert

- **Commit:** `2cb93852`
- **Author:** jsagir
- **Files changed:** 1
  - CLAUDE.md
- **Details:** Documents all recent changes so new Claude Code sessions understand:

### ✨ feat: Revert Larry prompt to v1 + add Context Engine with KG-RAG patterns

- **Commit:** `7281c2df`
- **Author:** jsagir
- **Files changed:** 9
  - docs/KG_RAG_RETRIEVAL_PATTERNS.md
  - mindrian_chat.py
  - prompts/larry_core.py
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
- **Details:** - Revert prompts/larry_core.py to pre-v2.0 (users preferred the natural

## 2026-02-11

### ✨ feat: Add interactive QA feedback form with contextual questions

- **Commit:** `1bd5c045`
- **Author:** jsagir
- **Files changed:** 2
  - mindrian_chat.py
  - public/elements/QAFeedbackForm.jsx
- **Details:** Add "Rate Session" button that opens a contextual QA survey adapted to

### ✨ feat: Button-less orchestration + unified registry + 3 new workshop agents

- **Commit:** `fe50f946`
- **Author:** jsagir
- **Files changed:** 17
  - agents/multi_agent_graph.py
  - mindrian_chat.py
  - prompts/__init__.py
  - prompts/dominant_designs.py
  - prompts/macro_changes.py
- **Details:** Adds human-in-the-loop orchestration detection (DETECT → RECOMMEND → CONFIRM → EXECUTE),

### 🐛 fix: 5 bugs from Lawrence QA — history format, grounding spam, research freeze, synthesize

- **Commit:** `81f9743a`
- **Author:** jsagir
- **Files changed:** 5
  - mindrian_chat.py
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** BUG-1: GroundingPrompt appearing twice — add 3-turn cooldown per reason

## 2026-02-10

### ✨ feat: Upgrade research pipeline to Claude Sonnet 4.5

- **Commit:** `f6fcc653`
- **Author:** jsagir
- **Files changed:** 6
  - intelligence/pipelines/research_pipeline.py
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** Switch all 6 Claude calls in research_pipeline.py and the routing

### ✨ feat: Upgrade Larry prompt v2.1 — intelligent pedagogical arc

- **Commit:** `eb23e56a`
- **Author:** jsagir
- **Files changed:** 5
  - prompts/larry_core.py
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** Transform the one-liner pedagogical arc into an intelligent conversational

### ✨ feat: Add invisible agent routing, Larry v2.0 unified prompt, and research error fix

- **Commit:** `53f9058b`
- **Author:** jsagir
- **Files changed:** 7
  - agents/invisible_router.py
  - mindrian_chat.py
  - prompts/larry_core.py
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
- **Details:** - agents/invisible_router.py (NEW): LangGraph StateGraph for invisible methodology

### 🐛 fix: Add defensive error handling to Research and Breakthrough buttons

- **Commit:** `2837fdc8`
- **Author:** jsagir
- **Files changed:** 5
  - mindrian_chat.py
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** Research button: wrap import in try/except with user-facing error message

### 🐛 fix: Resolve 3 known issues — thread_id security, PgBouncer crash, graph write node

- **Commit:** `35138915`
- **Author:** jsagir
- **Files changed:** 2
  - intelligence/pipelines/research_pipeline.py
  - memory/checkpointer.py
- **Details:** 1. Fix shared "research_default" thread_id (P2 security):

### ✨ feat: Add creative leaps, convergence, background ERIC, resume fix, and updated READMEs

- **Commit:** `81faad9c`
- **Author:** jsagir
- **Files changed:** 21
  - CLAUDE.md
  - README.md
  - backups/filesearch/store_manifest.json
  - chainlit.md
  - docs/DEMO_PWS_NAVIGATOR.md
- **Details:** - Creative leaps auto-injection every 4th turn via Neo4j cross-domain sparks

### ✨ feat: Add 4 new skills, ERIC orchestration R&D, and v4 plan files

- **Commit:** `628f3db3`
- **Author:** jsagir
- **Files changed:** 21
  - R&D/26_eric_orchestration/README.md
  - R&D/26_eric_orchestration/eric.sh
  - plans/mindrian-v4/00-team-meeting-brief.md
  - plans/mindrian-v4/01-lazy-graph-idea-engine.md
  - plans/mindrian-v4/02-agentic-tool-selection.md
- **Details:** New skills (18 total):

### ✨ feat: Add LangGraph deep research pipeline — Claude plans, Tavily searches, Gemini synthesizes

- **Commit:** `32e86d7c`
- **Author:** jsagir
- **Files changed:** 11
  - agents/multi_agent_graph.py
  - intelligence/agents/research_agent.py
  - intelligence/pipelines/__init__.py
  - intelligence/pipelines/minto_pyramid.py
  - intelligence/pipelines/research_pipeline.py
- **Details:** Replace the Gemini-only research orchestrator with a proper LangGraph StateGraph

## 2026-02-09

### ✨ feat: Add Creative Leaps feature based on Granmoe's network research

- **Commit:** `40b52641`
- **Author:** jsagir
- **Files changed:** 6
  - mindrian_chat.py
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** Implements Austin Granmoe's "Large Scale Networks for Idea Generation" concept:

### 🐛 fix: Demo-critical bugs for University of Sao Paolo presentation

- **Commit:** `99c6262e`
- **Author:** jsagir
- **Files changed:** 8
  - mindrian_chat.py
  - public/elements/IdeaCanvas.jsx
  - qa/2026-02-09/USER_FEEDBACK_ARONHIME_FEB9_V2.md
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
- **Details:** BUG-001: Session Restore Spam

### 🐛 fix: Larry teach me refusal bug + add explicit teaching detection

- **Commit:** `2e6b7a27`
- **Author:** jsagir
- **Files changed:** 6
  - mindrian_chat.py
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** BUG FIXES:

### ✨ feat: Upgrade "Larry teach me" to Cognitive Intervention Engine

- **Commit:** `41bc8cdd`
- **Author:** jsagir
- **Files changed:** 6
  - mindrian_chat.py
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** CORE PHILOSOPHY:

### ✨ feat: Add Quick Lecture feature with "Larry teach me" button

- **Commit:** `1c11966d`
- **Author:** jsagir
- **Files changed:** 6
  - mindrian_chat.py
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** Creates mini audio lectures using:

### ✨ feat: Add /api/embed-opportunities endpoint

- **Commit:** `d1bfd40f`
- **Author:** jsagir
- **Files changed:** 5
  - mindrian_chat.py
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** Trigger opportunity embedding via API:

### ✨ feat: Add opportunity embedding script + fix daily_summary LightRAG auth

- **Commit:** `c23a38a4`
- **Author:** jsagir
- **Files changed:** 6
  - scripts/daily_summary.py
  - scripts/embed_all_opportunities.py
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
- **Details:** 1. scripts/embed_all_opportunities.py - NEW

### ✨ feat: Add /api/lightrag-health endpoint

- **Commit:** `71833cc8`
- **Author:** jsagir
- **Files changed:** 5
  - mindrian_chat.py
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** Tests LightRAG connection with:

### 🐛 fix: Add X-API-Key header to all LightRAG connections

- **Commit:** `4576f32a`
- **Author:** jsagir
- **Files changed:** 7
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
  - tools/opportunity_bank.py
- **Details:** LightRAG requires both OAuth2 Bearer token AND X-API-Key header.

### 🐛 fix: Update Claude opportunity attribution to 'CL-Mindrian'

- **Commit:** `8bd2d7c3`
- **Author:** jsagir
- **Files changed:** 5
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
  - tools/opportunity_bank.py
- **Details:** Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>

### ✨ feat: Add Hybrid LLM Router + Claude for Bank of Opportunities

- **Commit:** `617331fd`
- **Author:** jsagir
- **Files changed:** 10
  - mindrian_chat.py
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** Implements the hybrid LLM strategy:

### 🐛 fix: Deep Research fallback now generates actual queries

- **Commit:** `4710da34`
- **Author:** jsagir
- **Files changed:** 5
  - mindrian_chat.py
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** When the LLM fails to produce valid JSON for the research matrix,

### 🐛 fix: Research button 'stream_token' error - variable shadowing bug

- **Commit:** `18745cb5`
- **Author:** jsagir
- **Files changed:** 5
  - mindrian_chat.py
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** The loop variable `msg` was overwriting the cl.Message object created at

### 📝 docs: Add QA Testing Memo for Feb 9 release

- **Commit:** `2d47a9f3`
- **Author:** jsagir
- **Files changed:** 5
  - qa/2026-02-09/QA_TESTING_MEMO_FEB9.md
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** Comprehensive testing guide for Adam & Austin covering:

### ✨ feat: Add Idea Filtering + Swarm Orchestrator Skill

- **Commit:** `0860d5d1`
- **Author:** jsagir
- **Files changed:** 18
  - mindrian_chat.py
  - protocols/agent_registry.py
  - public/elements/IdeaCanvas.jsx
  - qa/2026-02-09/USER_FEEDBACK_ARONHIME_FEB9.md
  - skills/SKILLS_GUIDE.md
- **Details:** Idea Filtering (Apply to AI):

### 🐛 fix: Address Lawrence Aronhime QA feedback

- **Commit:** `f5c6a54e`
- **Author:** jsagir
- **Files changed:** 17
  - intelligence/pipelines/__init__.py
  - journals/pws_consultant_simulation.md
  - mindrian_chat.py
  - mindrian_chat.py.backup_before_exclusions
  - public/elements/IdeaCanvas.jsx
- **Details:** P0 Fixes:

### ✨ feat: Add Breakthrough button + improve Research error logging

- **Commit:** `a3282c77`
- **Author:** jsagir
- **Files changed:** 5
  - mindrian_chat.py
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** Wave 4: Auto-Orchestration

### ✨ feat: Wire UX features - Fork, Ideas, Agent Attribution

- **Commit:** `c92c9d4b`
- **Author:** jsagir
- **Files changed:** 6
  - mindrian_chat.py
  - qa/2026-02-08/QA_TESTING_MEMO_FEB8.md
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
- **Details:** UX-001: Conversation Forking

## 2026-02-08

### 📝 docs: Add QA Testing Memo for Feb 8, 2026 release

- **Commit:** `bad0e6b6`
- **Author:** jsagir
- **Files changed:** 5
  - qa/2026-02-08/QA_TESTING_MEMO_FEB8.md
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** Covers:

### ✨ feat: Add LightRAG health check + Bank of Opportunities UX notifications

- **Commit:** `67cde4ea`
- **Author:** jsagir
- **Files changed:** 8
  - README.md
  - mindrian_chat.py
  - scripts/health_check.py
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
- **Details:** README:

### 🔧 debug: Add logging to select_entry_point callback

- **Commit:** `6b698370`
- **Author:** jsagir
- **Files changed:** 5
  - mindrian_chat.py
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** Helps diagnose why button clicks aren't working.
