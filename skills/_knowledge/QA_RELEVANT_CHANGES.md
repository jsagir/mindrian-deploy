# QA-Relevant Changes

*Auto-generated: 2026-02-06 09:20*

---

## 2026-02-06

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

### 🐛 fix: Critical PDF processing bug + streaming file upload feedback

- **Commit:** `7a3b7310`
- **Author:** jsagir
- **Files changed:** 4
  - mindrian_chat.py
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** Bug Fixes:

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

### 🐛 fix: P0 - File uploads blocked when message short (e.g., "review !")

- **Commit:** `9920d572`
- **Author:** jsagir
- **Files changed:** 4
  - mindrian_chat.py
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** Root cause: auto_detect_entry_point returned should_show_selector=True

### 🐛 fix: Disable pyaudio (requires system portaudio not available on Render)

- **Commit:** `7a740d4a`
- **Author:** jsagir
- **Files changed:** 3
  - requirements.txt
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** pyaudio needs portaudio.h header file which is a system-level dependency.

### 📝 docs: Add QA feedback from excellent Nested Hierarchies session

- **Commit:** `23243f47`
- **Author:** jsagir
- **Files changed:** 4
  - qa/2026-02-04/QA_FEEDBACK_NESTED_HIERARCHIES.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** Session highlights:

### 🐛 fix: Hide ThinkingPanel when no steps returned

- **Commit:** `94e0af20`
- **Author:** jsagir
- **Files changed:** 5
  - R&D/12_conversation_sampler_dashboard/README.md
  - mindrian_chat.py
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** QA feedback: Lawrence's Thinking boxes showing 0/0 - Waiting for

### 🐛 fix: Address all QA issues + add LangGraph sequential thinking

- **Commit:** `cb013db9`
- **Author:** jsagir
- **Files changed:** 19
  - callbacks/__init__.py
  - callbacks/agent_switch.py
  - callbacks/research.py
  - intelligence/pipelines/__init__.py
  - intelligence/pipelines/minto_pyramid.py
- **Details:** QA Fixes (Feb 3 report):

### 🐛 fix: Critical context management and research query bugs

- **Commit:** `4df6d1e0`
- **Author:** jsagir
- **Files changed:** 6
  - intelligence/pipelines/__init__.py
  - intelligence/pipelines/bono_innovation.py
  - mindrian_chat.py
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
- **Details:** Bug fixes:
