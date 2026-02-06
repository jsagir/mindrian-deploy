# Recent Repository Changes

*Auto-generated: 2026-02-06 12:46*

---

## 2026-02-06

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

### ✨ feat: Add LightRAG opportunity bank review to daily summary email

- **Commit:** `5cbb0576`
- **Author:** jsagir
- **Files changed:** 4
  - scripts/daily_summary.py
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** - Query LightRAG knowledge graph for full Bank of Opportunities

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

### 🐛 fix: Rewrite ToolsPanel with inline styles for Chainlit compatibility

- **Commit:** `c4251fb2`
- **Author:** jsagir
- **Files changed:** 4
  - public/elements/ToolsPanel.jsx
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** - Replace shadcn/ui components with raw inline styles

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

### 🐛 fix: Critical PDF processing bug + streaming file upload feedback

- **Commit:** `7a3b7310`
- **Author:** jsagir
- **Files changed:** 4
  - mindrian_chat.py
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** Bug Fixes:

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

### 🐛 fix: QA UI/UX improvements - accessibility and error handling

- **Commit:** `cc1ed3ca`
- **Author:** jsagir
- **Files changed:** 8
  - mindrian_chat.py
  - public/elements/BusinessModelCanvas.jsx
  - public/elements/FloatingActionBar.jsx
  - public/elements/QuadrantChart.jsx
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
- **Details:** UI Accessibility (P1):

### ✨ feat: Security hardening and performance improvements

- **Commit:** `a8f90512`
- **Author:** jsagir
- **Files changed:** 14
  - mindrian_chat.py
  - scripts/lightrag_gentle_upload.py
  - scripts/lightrag_graph_push.py
  - scripts/push_opportunities_to_lightrag.py
  - scripts/push_qa_opportunities_to_lightrag.py
- **Details:** - Remove hardcoded LightRAG password defaults (7 files)

### 🐛 fix: Reduce log noise from expected errors

- **Commit:** `24623356`
- **Author:** jsagir
- **Files changed:** 5
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
  - tools/user_lazygraph.py
  - utils/context_persistence.py
- **Details:** - context_persistence: Suppress 400/Bad Request errors (expected for new users)

### 🐛 fix: Add immediate file upload feedback for better UX

- **Commit:** `23720333`
- **Author:** jsagir
- **Files changed:** 4
  - mindrian_chat.py
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** - Show "File received: filename - Processing..." immediately when file detected

### 🔧 debug: Add detailed file upload logging to diagnose processing issue

- **Commit:** `c320042e`
- **Author:** jsagir
- **Files changed:** 4
  - mindrian_chat.py
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** - Log message.elements count at on_message entry

### ✨ feat: Auto-push opportunities to LightRAG on every registration

- **Commit:** `3c31ad65`
- **Author:** jsagir
- **Files changed:** 4
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
  - tools/opportunity_bank.py
- **Details:** - Add store_opportunity_lightrag() using document ingestion API

### 🐛 fix: Resolve Chainlit 2.9 compatibility + module naming conflict

- **Commit:** `95c9ecb3`
- **Author:** jsagir
- **Files changed:** 8
  - backups/filesearch/store_manifest.json
  - intelligence/__init__.py
  - intelligence/research_tools.py
  - intelligence/tools.py
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
- **Details:** - data_layer.py: Handle removed BaseStorageClient with Protocol fallback

### 🐛 fix: Revert try-except that broke indentation

- **Commit:** `4e394e45`
- **Author:** jsagir
- **Files changed:** 4
  - mindrian_chat.py
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md

### 🐛 fix: Add file processing error handling and logging

- **Commit:** `0c461a2c`
- **Author:** jsagir
- **Files changed:** 4
  - mindrian_chat.py
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** - Add [FILE PROCESSING] log at start showing element count

### ✨ feat: Add LightRAG Bank of Opportunities + Per-User Memory

- **Commit:** `3b107f94`
- **Author:** jsagir
- **Files changed:** 12
  - mindrian_chat.py
  - qa/extracted_opportunities.json
  - scripts/populate_lightrag_from_qa.py
  - scripts/push_opportunities_to_lightrag.py
  - scripts/push_qa_opportunities_to_lightrag.py
- **Details:** LightRAG Integration:

### 🔧 build: Update render.yaml with poppler-utils in buildCommand

- **Commit:** `e90230f5`
- **Author:** jsagir
- **Files changed:** 4
  - render.yaml
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md

### 🔧 build: Add poppler-utils for PDF-to-image conversion

- **Commit:** `e4da460a`
- **Author:** jsagir
- **Files changed:** 5
  - build.sh
  - render.yaml
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** - build.sh: Install script with poppler-utils

### ✨ feat: Smart multi-model document processing (Gemini FREE first)

- **Commit:** `0b116abd`
- **Author:** jsagir
- **Files changed:** 6
  - intelligence/pipelines/file_processing.py
  - mindrian_chat.py
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** Fallback priority:

### ✨ feat: Claude Vision for document processing (replaces Document AI)

- **Commit:** `cd034edc`
- **Author:** jsagir
- **Files changed:** 7
  - intelligence/pipelines/file_processing.py
  - mindrian_chat.py
  - requirements.txt
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
- **Details:** Multi-model architecture:

### ✨ feat: Document AI as PRIMARY PDF processor (handwriting + equations)

- **Commit:** `3b3c3f88`
- **Author:** jsagir
- **Files changed:** 4
  - mindrian_chat.py
  - requirements.txt
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** - Added google-cloud-documentai to requirements.txt

### 📝 docs: Sync knowledge base (auto-generated)

- **Commit:** `8d639c09`
- **Author:** jsagir
- **Files changed:** 3
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md

### 🐛 fix: P0 - File uploads blocked when message short (e.g., "review !")

- **Commit:** `9920d572`
- **Author:** jsagir
- **Files changed:** 4
  - mindrian_chat.py
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** Root cause: auto_detect_entry_point returned should_show_selector=True

### 📝 docs: Add comprehensive Edwards onboarding guide

- **Commit:** `fc9b592a`
- **Author:** jsagir
- **Files changed:** 3
  - docs/EDWARDS_ONBOARDING.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** Complete technical overview covering:

### 📝 docs: Sync knowledge base

- **Commit:** `59c9dcb0`
- **Author:** jsagir
- **Files changed:** 3
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md

### 🐛 fix: Disable pyaudio (requires system portaudio not available on Render)

- **Commit:** `7a740d4a`
- **Author:** jsagir
- **Files changed:** 3
  - requirements.txt
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** pyaudio needs portaudio.h header file which is a system-level dependency.

### 📝 docs: Final knowledge sync

- **Commit:** `3da69419`
- **Author:** jsagir
- **Files changed:** 9
  - docs/CONDUCTOR_INTEGRATION_FEASIBILITY.md
  - docs/MINDRIAN_CHAT_STRUCTURE.md
  - public/elements/VoiceChat.jsx
  - realtime_voice.py
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
