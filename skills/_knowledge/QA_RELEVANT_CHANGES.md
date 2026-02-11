# QA-Relevant Changes

*Auto-generated: 2026-02-11 11:01*

---

## 2026-02-11

### 🐛 fix: Defensive error handler + natural language summarize detection

- **Commit:** `d27afb52`
- **Author:** jsagir
- **Files changed:** 5
  - mindrian_chat.py
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** BUG-2 (P0): Main error handler now wraps msg.update() in try/except

### 🐛 fix: Normalize history role format — "assistant" → "model" for Gemini API

- **Commit:** `59b6b064`
- **Author:** jsagir
- **Files changed:** 5
  - mindrian_chat.py
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** Gemini expects role="user" or role="model" but 2 places appended with

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

### 🐛 fix: Context bleed, Clear Context, and truncated examples

- **Commit:** `14f80253`
- **Author:** jsagir
- **Files changed:** 1
  - mindrian_chat.py
- **Details:** 1. Fix context bleed into new conversations:

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

## 2026-02-09

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

### 🐛 fix: Increase LightRAG health check timeout to 30s

- **Commit:** `a194ecab`
- **Author:** jsagir
- **Files changed:** 5
  - mindrian_chat.py
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** Handle cold start timeouts gracefully - login and query

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

### 🐛 fix: Remove broken entry selector, use starters instead

- **Commit:** `9e7786fd`
- **Author:** jsagir
- **Files changed:** 5
  - mindrian_chat.py
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** - Don't show entry point selector (was unreliable)

### 🐛 fix: Use separate action callbacks for each entry point

- **Commit:** `52de710f`
- **Author:** jsagir
- **Files changed:** 6
  - mindrian_chat.py
  - protocols/triple_mode.py
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
- **Details:** Separate callbacks (ep_brainstorming, ep_document_review, ep_build_venture)

### 🐛 fix: Replace EntryPointSelector with native Chainlit Action buttons

- **Commit:** `f6100de3`
- **Author:** jsagir
- **Files changed:** 5
  - protocols/triple_mode.py
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** CustomElement + callAction was unreliable. Using native cl.Action

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

### 🐛 fix: Use TEXT columns for Chainlit compatibility (not UUID/TIMESTAMP)

- **Commit:** `c6e51612`
- **Author:** jsagir
- **Files changed:** 6
  - mindrian_chat.py
  - scripts/init_database.py
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
- **Details:** Chainlit's SQLAlchemyDataLayer expects:

### 🐛 fix: Execute SQL statements one at a time for asyncpg compatibility

- **Commit:** `6290e5e9`
- **Author:** jsagir
- **Files changed:** 6
  - mindrian_chat.py
  - scripts/init_database.py
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
- **Details:** asyncpg doesn't support multiple statements in a single execute() call.

### 🐛 fix: Use raw SQL for Chainlit database table creation

- **Commit:** `4c7d8e07`
- **Author:** jsagir
- **Files changed:** 6
  - mindrian_chat.py
  - scripts/init_database.py
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
- **Details:** Chainlit doesn't export a Base class from sql_alchemy, so we can't use

### 🐛 fix: Remove await from sync get_data_layer() call

- **Commit:** `9b90ac28`
- **Author:** jsagir
- **Files changed:** 5
  - mindrian_chat.py
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>

### 🐛 fix: Add database initialization to create Chainlit tables

- **Commit:** `de2a5fc6`
- **Author:** jsagir
- **Files changed:** 6
  - build.sh
  - scripts/init_database.py
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
- **Details:** The PostgreSQL database was empty - Chainlit's users, threads, steps,

### 🐛 fix: EntryPointSelector - clickable cards + side-by-side layout

- **Commit:** `a97ba57b`
- **Author:** jsagir
- **Files changed:** 5
  - public/elements/EntryPointSelector.jsx
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** 1. Fix click handler to use window.Chainlit.callAction (not global)

### 🐛 fix: Use sync function for @cl.data_layer decorator

- **Commit:** `306188c3`
- **Author:** jsagir
- **Files changed:** 5
  - mindrian_chat.py
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>

### 🐛 fix: Move /api/health and /api/public-config to middleware

- **Commit:** `2f08c187`
- **Author:** jsagir
- **Files changed:** 5
  - mindrian_chat.py
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** These endpoints were being blocked by Chainlit's auth. Moving them to
