# QA-Relevant Changes

*Auto-generated: 2026-02-04 03:15*

---

## 2026-02-04

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
