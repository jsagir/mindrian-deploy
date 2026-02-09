# Recent Repository Changes

*Auto-generated: 2026-02-09 14:05*

---

## 2026-02-09

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

### 🐛 fix: Data layer registration + MIME types for file upload

- **Commit:** `41f14e01`
- **Author:** jsagir
- **Files changed:** 6
  - mindrian_chat.py
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** Data Layer:

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

### 🐛 fix: Auth - use Chainlit native password auth, disable auth-bridge

- **Commit:** `224b729d`
- **Author:** jsagir
- **Files changed:** 6
  - mindrian_chat.py
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** - Add Supabase password_auth_callback (when SUPABASE_AUTH_ENABLED)

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

### 🐛 fix: Remove password_auth_callback to prevent double login screen

- **Commit:** `0fd72710`
- **Author:** jsagir
- **Files changed:** 5
  - mindrian_chat.py
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** Chainlit was showing its built-in login screen because @cl.password_auth_callback

### 🐛 fix: Disable SSL for Render internal database connections

- **Commit:** `4d9f675c`
- **Author:** jsagir
- **Files changed:** 5
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
  - utils/data_layer.py
- **Details:** Render internal database URLs (dpg-xxx-a without .render.com) don't

### 🐛 fix: Rename supabase variable to sbClient to avoid SDK conflict (v6)

- **Commit:** `fc8ed89a`
- **Author:** jsagir
- **Files changed:** 5
  - public/login.html
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** The Supabase CDN + jsDelivr was declaring a global 'supabase' variable,

### 🐛 fix: Switch back to sync SDK loading (v5)

- **Commit:** `f0d50869`
- **Author:** jsagir
- **Files changed:** 5
  - public/login.html
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** The async loading was causing timing issues where window.supabase

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

### 🐛 fix: Make Supabase script async + robust initialization

- **Commit:** `59435d56`
- **Author:** jsagir
- **Files changed:** 5
  - public/login.html
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** - Load Supabase SDK with async to prevent page blocking

### 🐛 fix: Guard onAuthStateChange against null supabase client

- **Commit:** `52269a0a`
- **Author:** jsagir
- **Files changed:** 5
  - public/login.html
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** The auth state listener was being registered unconditionally, which

### 🐛 fix: Simplify login page - remove config fetch, use direct initialization

- **Commit:** `4d144d94`
- **Author:** jsagir
- **Files changed:** 5
  - public/login.html
  - skills/_knowledge/COMMIT_EXPERT_CHANGES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** - Remove async config fetch (was causing issues with Chainlit routing)

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
