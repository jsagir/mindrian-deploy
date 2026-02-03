# QA-Relevant Changes

*Auto-generated: 2026-02-03 17:22*

---

## 2026-02-03

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

### 🐛 fix: Write errors to stderr for proper cron endpoint error reporting

- **Commit:** `fddda5a8`
- **Author:** Claude
- **Files changed:** 3
  - mindrian_chat.py
  - scripts/daily_summary.py
  - utils/email_sender.py
- **Details:** The daily summary cron endpoint was returning "Unknown error" because

### ✨ feat: Enhance daily summary with opportunity content and fix yesterday counts

- **Commit:** `f81537e6`
- **Author:** Claude
- **Files changed:** 1
  - scripts/daily_summary.py
- **Details:** - Fix date counting: today and yesterday counts are now separate (not combined in 'last 24h')

## 2026-02-01

### 🐛 fix: Use middleware for cron endpoint to bypass Chainlit routing

- **Commit:** `de9c90fd`
- **Author:** Claude
- **Files changed:** 1
  - mindrian_chat.py
- **Details:** - APIRouter approach didn't work (Chainlit catch-all still intercepted)

### 🐛 fix: Register cron endpoint at import time before Chainlit catch-all

- **Commit:** `2ad73173`
- **Author:** Claude
- **Files changed:** 1
  - mindrian_chat.py
- **Details:** - Move /api/daily-summary registration to top of file

### 🐛 fix: TaskList for_id compatibility in grading flow

- **Commit:** `1d004506`
- **Author:** Claude
- **Files changed:** 1
  - mindrian_chat.py
- **Details:** - Send TaskList separately instead of as Message element

### 🐛 fix(security): Remove shell injection vulnerability and weak hash

- **Commit:** `d99e0cc6`
- **Author:** Claude
- **Files changed:** 3
  - protocols/context_journal.py
  - scripts/lazy_graphrag_index.py
  - scripts/lightrag_graph_push.py
- **Details:** CRITICAL SECURITY FIXES from code review:

### 🐛 fix: Critical - Fix infinite recursion in safe_task_list_send()

- **Commit:** `47429322`
- **Author:** Claude
- **Files changed:** 1
  - mindrian_chat.py
- **Details:** The function was calling itself recursively instead of calling

### 🐛 fix: Prevent maximum recursion depth in validation bot and JSON encoder

- **Commit:** `0f6f558a`
- **Author:** Claude
- **Files changed:** 2
  - mindrian_chat.py
  - utils/context_persistence.py
- **Details:** - Replace storing complex ValidationState dataclass with simple dict summary
