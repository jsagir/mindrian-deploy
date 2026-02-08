# QA-Relevant Changes

*Auto-generated: 2026-02-08 23:45*

---

## 2026-02-08

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

### 🐛 fix: Rename Tools Panel to Agentic Actions with robot icon

- **Commit:** `0984b021`
- **Author:** jsagir
- **Files changed:** 4
  - public/elements/ToolsPanel.jsx
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** - Panel title: "PWS Tools" -> "Agentic Actions"

### 🐛 fix: Attach ToolsPanel to welcome message instead of empty message

- **Commit:** `072993dc`
- **Author:** jsagir
- **Files changed:** 4
  - mindrian_chat.py
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** ToolsPanel was sent in cl.Message(content="") which Chainlit skips rendering.

### 🐛 fix: Migrate to google-genai SDK + fix SendGrid sender email

- **Commit:** `db5a3b25`
- **Author:** jsagir
- **Files changed:** 6
  - intelligence/pipelines/genesis/panel.py
  - scripts/daily_summary.py
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** - panel.py: Replace old google.generativeai with google-genai SDK (lazy client init)

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

### 🐛 fix: Configure Gemini API key in Genesis panel.py

- **Commit:** `e2b79845`
- **Author:** jsagir
- **Files changed:** 4
  - intelligence/pipelines/genesis/panel.py
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** Genesis expert panel was missing genai.configure() call,

### 🐛 fix: Rewrite ToolsPanel with inline styles for Chainlit compatibility

- **Commit:** `c4251fb2`
- **Author:** jsagir
- **Files changed:** 4
  - public/elements/ToolsPanel.jsx
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** - Replace shadcn/ui components with raw inline styles
