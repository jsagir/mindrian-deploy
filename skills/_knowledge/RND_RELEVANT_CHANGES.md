# R&D-Relevant Changes

*Auto-generated: 2026-02-04 09:47*

---

## 2026-02-04

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

### ✨ feat: Add Oracle Foresight Engine + Intelligence Layer

- **Commit:** `fcc9613d`
- **Author:** jsagir
- **Files changed:** 22
  - intelligence/__init__.py
  - intelligence/agents/__init__.py
  - intelligence/agents/multi_agent.py
  - intelligence/agents/research_agent.py
  - intelligence/pipelines/__init__.py
- **Details:** Complete Oracle prediction market system with:

## 2026-02-03

### ✨ feat: Add sticky action buttons above chat input

- **Commit:** `725babf7`
- **Author:** jsagir
- **Files changed:** 7
  - mindrian_chat.py
  - public/custom.css
  - public/elements/FloatingActionBar.jsx
  - public/elements/StickyActionsInjector.jsx
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
- **Details:** Created StickyActionsInjector custom element that injects CSS to make

### ✨ feat: Intelligent diagram type selection for Visualize button

- **Commit:** `96515813`
- **Author:** jsagir
- **Files changed:** 4
  - mindrian_chat.py
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** Replaced simple mindmap-only "Map Ideas" with intelligent visualization that

### ✨ feat: Complete Opportunity Bank UI integration

- **Commit:** `0a564a26`
- **Author:** jsagir
- **Files changed:** 4
  - mindrian_chat.py
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** Added missing UI integration for Opportunity Bank feature:

### 📝 docs: Update README with v3.1 features + improve agent welcome messages

- **Commit:** `c1ed47c9`
- **Author:** jsagir
- **Files changed:** 5
  - README.md
  - mindrian_chat.py
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** README updates:

### 🐛 fix: Add missing pws_brain search functions for assessment engine

- **Commit:** `76efb851`
- **Author:** jsagir
- **Files changed:** 5
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
  - tools/graphrag_lite.py
  - tools/pws_brain.py
- **Details:** The assessment_engine.py was importing semantic_search and

### ✨ feat: Add comprehensive AGENT_GENERATOR_META_PROMPT v2.0

- **Commit:** `80824830`
- **Author:** Claude
- **Files changed:** 2
  - prompts/__init__.py
  - prompts/agent_generator_meta.py
- **Details:** - Complete meta-prompt for generating Mindrian agent configurations

### ✨ feat: Integrate ThinkingPanel custom element for rich thinking display

- **Commit:** `98678f56`
- **Author:** Claude
- **Files changed:** 2
  - mindrian_chat.py
  - public/elements/ThinkingPanel.jsx
- **Details:** Enhancement: Replace cl.Step with ThinkingPanel custom element for

### 🐛 fix: Enforce English responses and improve PDF error handling (Bug 11)

- **Commit:** `0b36fb38`
- **Author:** Claude
- **Files changed:** 2
  - mindrian_chat.py
  - prompts/multi_perspective_validation.py
- **Details:** Root cause: When PDF extraction returned empty/minimal content, Gemini

### 📝 docs: Add QA release notes for Feb 3 - Recursive Intelligence + Gemini 2.5

- **Commit:** `2895440b`
- **Author:** jsagir
- **Files changed:** 3
  - qa/2026-02-03/QA_RELEASE_NOTES_FEB3.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md

### ✨ feat: Upgrade to Gemini 2.5-flash + UI improvements + new utilities

- **Commit:** `5974ff8e`
- **Author:** jsagir
- **Files changed:** 41
  - agents/multi_agent_graph.py
  - docs/LANGEXTRACT_RECURSIVE_INTELLIGENCE_PLAN.md
  - governance/audit_trail.py
  - governance/eval_suite.py
  - prompts/__init__.py
- **Details:** Model Upgrades (gemini-2.0-flash → gemini-2.5-flash):
