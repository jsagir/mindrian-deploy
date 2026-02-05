# R&D-Relevant Changes

*Auto-generated: 2026-02-05 09:14*

---

## 2026-02-05

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

### 📝 docs: Add comprehensive Edwards onboarding guide

- **Commit:** `fc9b592a`
- **Author:** jsagir
- **Files changed:** 3
  - docs/EDWARDS_ONBOARDING.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** Complete technical overview covering:

### 📝 docs: Update README with Admin Tools, Memory, and v3.1 features

- **Commit:** `5b0c474d`
- **Author:** jsagir
- **Files changed:** 1
  - README.md
- **Details:** Added:

### ✨ feat: Add conversation sampler CLI + Streamlit admin dashboard

- **Commit:** `7e4fbee4`
- **Author:** jsagir
- **Files changed:** 5
  - scripts/admin_dashboard.py
  - scripts/conversation_sampler.py
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** New admin tools:

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

### ✨ feat: Integrate ALL LangGraph pipelines into chat flow

- **Commit:** `355bcde1`
- **Author:** jsagir
- **Files changed:** 26
  - mindrian_chat.py
  - prompts/agent_generator_meta.py
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** Pipeline Integrations:

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

### ✨ feat: Add Message Router pipeline + update README with Intelligence Layer

- **Commit:** `da768322`
- **Author:** jsagir
- **Files changed:** 6
  - README.md
  - intelligence/pipelines/__init__.py
  - intelligence/pipelines/message_router.py
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
- **Details:** New pipeline:

### 📝 docs: Add refactoring analysis + update skills with LangGraph pipelines

- **Commit:** `261cb0a3`
- **Author:** jsagir
- **Files changed:** 10
  - docs/REFACTORING_ANALYSIS.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
  - skills/langchain/SKILL.md
- **Details:** - REFACTORING_ANALYSIS.md: 10K line monolith → modular LangGraph architecture

### ✨ feat: Add LangGraph file processing pipeline with LazyGraph integration

- **Commit:** `2644dd52`
- **Author:** jsagir
- **Files changed:** 6
  - intelligence/__init__.py
  - intelligence/pipelines/__init__.py
  - intelligence/pipelines/file_processing.py
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
- **Details:** New file_processing.py pipeline:
