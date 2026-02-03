# QA-Relevant Changes

*Auto-generated: 2026-02-04 00:48*

---

## 2026-02-04

### 🐛 fix: Robust PDF detection to prevent image misidentification

- **Commit:** `578b1adf`
- **Author:** jsagir
- **Files changed:** 4
  - mindrian_chat.py
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** PDFs were sometimes being misidentified as images due to Chainlit

## 2026-02-03

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

### 🐛 fix: Enforce English responses and improve PDF error handling (Bug 11)

- **Commit:** `0b36fb38`
- **Author:** Claude
- **Files changed:** 2
  - mindrian_chat.py
  - prompts/multi_perspective_validation.py
- **Details:** Root cause: When PDF extraction returned empty/minimal content, Gemini

### 🐛 fix: Replace HTML <details> with cl.Step for thinking display

- **Commit:** `3d867db6`
- **Author:** Claude
- **Files changed:** 1
  - mindrian_chat.py
- **Details:** Bug 10: The thinking stream was showing as raw markdown instead of

### 🐛 fix: Resolve session bugs from Nested Hierarchies analysis

- **Commit:** `323c8bc4`
- **Author:** Claude
- **Files changed:** 1
  - mindrian_chat.py
- **Details:** Bug fixes from second session analysis (Nested Hierarchies → MOTJ):

### 🐛 fix: Resolve critical session and truncation bugs from BONO Master analysis

- **Commit:** `fa1038a8`
- **Author:** Claude
- **Files changed:** 1
  - mindrian_chat.py
- **Details:** Bug fixes from session analysis (Larry Playground → BONO Master):

### 📝 docs: Add QA release notes for Feb 3 - Recursive Intelligence + Gemini 2.5

- **Commit:** `2895440b`
- **Author:** jsagir
- **Files changed:** 3
  - qa/2026-02-03/QA_RELEASE_NOTES_FEB3.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md

### 📝 docs: Add corrected QA analysis for Lawrence Aronhime test sessions

- **Commit:** `d579bb6a`
- **Author:** jsagir
- **Files changed:** 4
  - qa/2026-02-03/QA_ANALYSIS_LAWRENCE_ARONHIME_CORRECTED.md
  - skills/_knowledge/QA_RELEVANT_CHANGES.md
  - skills/_knowledge/RECENT_CHANGES.md
  - skills/_knowledge/RND_RELEVANT_CHANGES.md
- **Details:** Key corrections from Mindrian Team review:

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

### 🐛 fix: Add sendgrid package for daily summary emails

- **Commit:** `182162ae`
- **Author:** jsagir
- **Files changed:** 1
  - requirements.txt
- **Details:** Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>

## 2026-02-02

### 🐛 fix: Add Supabase blob storage and disable telemetry

- **Commit:** `96d3cb12`
- **Author:** jsagir
- **Files changed:** 2
  - utils/data_layer.py
- **Details:** - Add SupabaseBlobStorage class implementing Chainlit BaseStorageClient

### 🐛 fix: Resolve Neo4j driver 5.x parameter naming conflict

- **Commit:** `e0ea7f10`
- **Author:** jsagir
- **Files changed:** 1
  - tools/graphrag_lite.py
- **Details:** Renamed Cypher parameter from $query to $q to avoid conflict with

### 📝 docs: Add QA Testing Guide for triple-mode-v1 release

- **Commit:** `430649a6`
- **Author:** jsagir
- **Files changed:** 1
  - docs/QA_TESTING_GUIDE.md
- **Details:** Comprehensive testing guide covering:

### ✨ feat: Add A2A orchestration with smart routing and Red Team middleware

- **Commit:** `44fecb44`
- **Author:** jsagir
- **Files changed:** 5
  - protocols/__init__.py
  - protocols/chat_integration.py
  - protocols/orchestrator.py
  - tests/__init__.py
  - tests/test_classifier.py
- **Details:** What this adds:

### 🐛 fix: Complete venture stage mappings for agents

- **Commit:** `e408dbbb`
- **Author:** jsagir
- **Files changed:** 1
  - protocols/agent_registry.py
- **Details:** - Add "*" wildcard handling in get_agents_for_venture_stage()

### 🐛 fix: Improve entry point detection with keyword hints

- **Commit:** `e4cb33b4`
- **Author:** jsagir
- **Files changed:** 1
  - protocols/triple_mode.py
- **Details:** - Move "idea" from brainstorm to venture keywords (startup ideas → build_venture)
