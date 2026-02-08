# R&D-Relevant Changes

*Auto-generated: 2026-02-08 21:28*

---

## 2026-02-08

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

### ✨ feat: Add /api/init-db endpoint to manually create tables

- **Commit:** `ea7f9a71`
- **Author:** jsagir
- **Files changed:** 5
  - mindrian_chat.py
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>

### ✨ feat: Add tables list to /api/health endpoint

- **Commit:** `ddce8741`
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

### 🐛 fix: Resolve pipeline import issues (Minto/Oracle/Genesis)

- **Commit:** `1749e0ac`
- **Author:** jsagir
- **Files changed:** 7
  - intelligence/__init__.py
  - intelligence/agents/research_agent.py
  - intelligence/tools/text2cypher.py
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
- **Details:** - text2cypher.py: Lazy-initialize genai.Client to avoid import-time

### ✨ feat: Implement Waves 2, 3, 4 - Forking, Canvas, Auto-Orchestration

- **Commit:** `93cf83bc`
- **Author:** jsagir
- **Files changed:** 15
  - docs/WAVE2_FORKING_DESIGN.md
  - docs/WAVE3_CANVAS_DESIGN.md
  - docs/WAVE4_ORCHESTRATION_DESIGN.md
  - protocols/__init__.py
  - protocols/auto_orchestrator.py
- **Details:** Wave 2 - Conversation Forking:

## 2026-02-06

### ✨ feat: Add /api/health endpoint for debugging

- **Commit:** `e50607aa`
- **Author:** jsagir
- **Files changed:** 5
  - mindrian_chat.py
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** Shows database connection status, env var configuration.

### 🐛 fix: Add null checks to all auth handlers + improve SDK loading (v4)

- **Commit:** `08043165`
- **Author:** jsagir
- **Files changed:** 5
  - public/login.html
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** - Add requireSupabase() helper with user-friendly error message

### 🐛 fix: Add proper timeout and safety fallback to login page

- **Commit:** `e4e69043`
- **Author:** jsagir
- **Files changed:** 5
  - public/login.html
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** - Use AbortController for proper fetch timeout (2s)

### ✨ feat: Implement AGENTS.md patterns for PWS Consultant

- **Commit:** `771a4648`
- **Author:** jsagir
- **Files changed:** 7
  - mindrian_chat.py
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** Complete implementation of A2A architecture patterns for the PWS Consultant:

### 🐛 fix: Update stale Supabase anon key + add env-based config injection

- **Commit:** `47130a8b`
- **Author:** jsagir
- **Files changed:** 6
  - mindrian_chat.py
  - public/login.html
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
- **Details:** CRITICAL FIX: Login page was stuck on "Checking session..." because

### ✨ feat: Wire two-stage classifier (Cynefin + PWS) to PWS Consultant

- **Commit:** `4bcbdf45`
- **Author:** jsagir
- **Files changed:** 6
  - R&D/10_agents_md_architecture/README.md
  - mindrian_chat.py
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
- **Details:** Quick wins from AGENTS.md architecture analysis:

### ✨ feat: Add LangGraph-style PWS state management module

- **Commit:** `783b3b54`
- **Author:** jsagir
- **Files changed:** 6
  - mindrian_chat.py
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** - Create utils/pws_state.py with formal TypedDict schema

### ✨ feat: Add Context Manager + Commit Expert skills

- **Commit:** `83392ea1`
- **Author:** jsagir
- **Files changed:** 14
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/KNOWLEDGE_INDEX.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** Context Manager skill:

### 🐛 fix: Add guest mode + session timeout for login page

- **Commit:** `16079714`
- **Author:** jsagir
- **Files changed:** 5
  - auth/supabase_auth.py
  - public/login.html
  - skills/mindrian-stack/SKILL.md
  - skills/neo4j-schema-navigator/SKILL.md
  - skills/qa-consultant/SKILL.md
- **Details:** - Add 5-second timeout for Supabase session check (prevents infinite "Checking session...")

### ✨ feat: Add Supabase Auth + Login Page + PWS Consultant + Context Fix

- **Commit:** `f48e3f2a`
- **Author:** jsagir
- **Files changed:** 19
  - auth/__init__.py
  - auth/supabase_auth.py
  - mindrian_chat.py
  - prompts/__init__.py
  - prompts/pws_consultant.py
- **Details:** ## Supabase Authentication

## 2026-02-05

### ✨ feat: Add Neo4j PWS methodology consultant to daily summary email

- **Commit:** `300c98dc`
- **Author:** jsagir
- **Files changed:** 4
  - scripts/daily_summary.py
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** Query Neo4j knowledge graph for PWS methodology context (Opportunity

### ✨ feat: Add LightRAG opportunity bank review to daily summary email

- **Commit:** `5cbb0576`
- **Author:** jsagir
- **Files changed:** 4
  - scripts/daily_summary.py
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** - Query LightRAG knowledge graph for full Bank of Opportunities

## 2026-02-04

### 📝 docs: Add QA Testing Memo for Feb 4, 2026 release

- **Commit:** `b7a74bbf`
- **Author:** jsagir
- **Files changed:** 4
  - docs/QA_TESTING_MEMO_FEB4.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** Covers all changes from last 18 hours including Genesis pipeline,

### ✨ feat: Add Genesis Expert Breakdown pipeline + UI improvements

- **Commit:** `1500522c`
- **Author:** jsagir
- **Files changed:** 15
  - intelligence/pipelines/__init__.py
  - intelligence/pipelines/genesis/__init__.py
  - intelligence/pipelines/genesis/decompose.py
  - intelligence/pipelines/genesis/domains.py
  - intelligence/pipelines/genesis/orchestrate.py
- **Details:** Genesis Pipeline (NEW):

### 📝 docs: Add R&D/21_genesis_expert_breakdown for Swarm+LangGraph integration

- **Commit:** `376c18d8`
- **Author:** jsagir
- **Files changed:** 11
  - R&D/21_genesis_expert_breakdown/README.md
  - R&D/21_genesis_expert_breakdown/SKILL.md
  - R&D/21_genesis_expert_breakdown/agent_config.py
  - R&D/21_genesis_expert_breakdown/decompose_context.py
  - R&D/21_genesis_expert_breakdown/generate_personas.py
- **Details:** Genesis Engine multi-agent system from agents-midrian:

### 📝 docs: Add R&D/20_pws_thinking_streamer for future reference

- **Commit:** `0ef80191`
- **Author:** jsagir
- **Files changed:** 4
  - R&D/20_pws_thinking_streamer/README.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** Documents the PWS-style thinking streamer pipeline:

### ✨ feat: Add Claude Code-style thinking streamer for file processing

- **Commit:** `ac991a2f`
- **Author:** jsagir
- **Files changed:** 4
  - mindrian_chat.py
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** - Add PWS_THINKING_TOKENS with Larry-style vocabulary

### ✨ feat: Add floating PWS Tools Panel with contextual tooltips

- **Commit:** `e897e3ec`
- **Author:** jsagir
- **Files changed:** 5
  - mindrian_chat.py
  - public/elements/ToolsPanel.jsx
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** - Add ToolsPanel.jsx floating component (bottom-right) showing PWS methodology tools

### ✨ feat: Humanize file upload feedback with PWS/Lawrence-style language

- **Commit:** `1a220553`
- **Author:** jsagir
- **Files changed:** 4
  - mindrian_chat.py
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** Replace robotic processing messages with conversational, thinking-out-loud style:

### 📝 docs: User-friendly README + legal disclaimers

- **Commit:** `593f3685`
- **Author:** jsagir
- **Files changed:** 6
  - README.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
  - utils/research_contextualizer.py
- **Details:** README Update:

### ✨ feat: Smart onboarding + humanized research contextualization

- **Commit:** `2d0b0fbc`
- **Author:** jsagir
- **Files changed:** 7
  - docs/EDWARDS_ONBOARDING.md
  - mindrian_chat.py
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** Smart Onboarding (utils/smart_onboarding.py):

### ✨ feat: API health monitoring, daily digest email, and smart onboarding

- **Commit:** `7c31f267`
- **Author:** jsagir
- **Files changed:** 8
  - scripts/daily_cron.py
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
  - sql/api_health_log.sql
- **Details:** New Systems:
