# R&D-Relevant Changes

*Auto-generated: 2026-02-04 03:11*

---

## 2026-02-04

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

### ✨ feat: Add Recursive Intelligence - session learning system

- **Commit:** `0a4f6f34`
- **Author:** jsagir
- **Files changed:** 12
  - docs/RECURSIVE_INTELLIGENCE_IMPLEMENTATION.md
  - mindrian_chat.py
  - scripts/process_insights.py
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
- **Details:** Phase 1: Event Logging

### 📝 docs: Add corrected QA analysis for Lawrence Aronhime test sessions

- **Commit:** `d579bb6a`
- **Author:** jsagir
- **Files changed:** 4
  - qa/2026-02-03/QA_ANALYSIS_LAWRENCE_ARONHIME_CORRECTED.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** Key corrections from Mindrian Team review:

### ✨ feat: Rename all skills to Mindrian-Team-X convention + auto-update knowledge base

- **Commit:** `b268be7c`
- **Author:** jsagir
- **Files changed:** 19
  - scripts/update_consultant_knowledge.py
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
  - skills/chainlit-consultant/SKILL.md
- **Details:** - Renamed all skills to Mindrian-Team-{Function} naming convention:

### 🐛 fix: Move commands to .claude/skills for Claude Code recognition

- **Commit:** `e77af393`
- **Author:** jsagir
- **Files changed:** 201
  - backups/filesearch/local_pws_files.json
  - backups/filesearch/store_manifest.json
  - data/course_extractions/BONO__BONO_Innovation_Framework_Case_Studies_Reference_Library.md.json
  - data/course_extractions/BONO__BONO_Innovation_Framework_Complete_Workbook.md.json
  - data/course_extractions/BONO__BONO_Innovation_Framework_Materials_Guide.md.json
- **Details:** Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>

### ✨ feat: Add Claude Code skills and commands for Mindrian development

- **Commit:** `fe7bfeda`
- **Author:** jsagir
- **Files changed:** 34
  - skills/chainlit-consultant/SKILL.md
  - skills/chainlit-consultant/references/chainlit-features.md
  - skills/chainlit-consultant/references/mindrian-patterns.md
  - skills/chainlit-consultant/templates/solution-patterns.md
  - skills/mindrian-larry/SKILL.md
- **Details:** Skills added:

### 🐛 fix: Add sendgrid package for daily summary emails

- **Commit:** `182162ae`
- **Author:** jsagir
- **Files changed:** 1
  - requirements.txt
- **Details:** Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>

### ✨ feat: Add Document AI credentials from JSON env var

- **Commit:** `615603cf`
- **Author:** jsagir
- **Files changed:** 2
  - scripts/setup_document_ai.sh
  - tools/document_ai.py
- **Details:** - Handle GOOGLE_APPLICATION_CREDENTIALS_JSON for Render deployment

### ✨ feat: Add Document AI smart fallback for difficult documents

- **Commit:** `9076a7e8`
- **Author:** jsagir
- **Files changed:** 3
  - docs/DOCUMENT_AI_IMPLEMENTATION_PLAN.md
  - tools/document_ai.py
  - utils/file_processor.py
- **Details:** Automatic fallback to Google Document AI when standard extraction fails:

### 📝 docs: Add Document AI implementation plan

- **Commit:** `ca14ea4c`
- **Author:** jsagir
- **Files changed:** 1
  - docs/DOCUMENT_AI_IMPLEMENTATION_PLAN.md
- **Details:** Research and planning for Google Document AI integration:

### ✨ feat: Add QuadrantChart and BusinessModelCanvas visualizations

- **Commit:** `a4145e3f`
- **Author:** jsagir
- **Files changed:** 4
  - CLAUDE.md
  - public/elements/BusinessModelCanvas.jsx
  - public/elements/QuadrantChart.jsx
  - utils/diagrams.py
- **Details:** New components:
