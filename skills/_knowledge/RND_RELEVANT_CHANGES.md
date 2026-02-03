# R&D-Relevant Changes

*Auto-generated: 2026-02-03 17:22*

---

## 2026-02-03

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

### ✨ feat: Add server-side Mermaid rendering option

- **Commit:** `9d60c1ab`
- **Author:** jsagir
- **Files changed:** 2
  - public/elements/MermaidDiagram.jsx
  - utils/diagrams.py
- **Details:** - Support pre-rendered SVG via mermaid-cli (mmdc) if available

### ✨ feat: Add Mermaid diagram system for idea visualization

- **Commit:** `b9fa1b98`
- **Author:** jsagir
- **Files changed:** 5
  - CLAUDE.md
  - docs/GOOGLE_ECOSYSTEM_COMPLETE_GUIDE.md
  - mindrian_chat.py
  - public/elements/MermaidDiagram.jsx
  - utils/diagrams.py
- **Details:** - Add MermaidDiagram.jsx custom element for rendering mindmaps/flowcharts

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

### 📝 docs: Add research ideas and full meeting transcript

- **Commit:** `ce4a4e53`
- **Author:** jsagir
- **Files changed:** 2
  - docs/SHARED_FOLDER_RAG_ARCHITECTURE.md
  - docs/transcripts/TEAM_MEETING_FEB_2025_FULL.md
- **Details:** - Added 10 research ideas to Shared Folder RAG doc

### 📝 docs: Add Shared Folder RAG Architecture reference

- **Commit:** `ee2ee774`
- **Author:** jsagir
- **Files changed:** 1
  - docs/SHARED_FOLDER_RAG_ARCHITECTURE.md
- **Details:** Critical architectural decision for team collaboration:

### 📝 docs: Add R&D documentation from Feb 2025 team meeting

- **Commit:** `b27d79bc`
- **Author:** jsagir
- **Files changed:** 5
  - docs/GOOGLE_ECOSYSTEM_STRATEGY.md
  - docs/MEETING_INSIGHTS_FEB_2025.md
  - docs/ONBOARDING_SPEC.md
  - docs/PRODUCT_ROADMAP.md
  - docs/QA_ISSUES_TRACKER.md
- **Details:** - Meeting insights with architecture decisions and action items

### 📝 docs: Add QA Testing Guide for triple-mode-v1 release

- **Commit:** `430649a6`
- **Author:** jsagir
- **Files changed:** 1
  - docs/QA_TESTING_GUIDE.md
- **Details:** Comprehensive testing guide covering:

### ✨ feat: Enable A2A orchestration + Supabase storage

- **Commit:** `fa4e286f`
- **Author:** jsagir
- **Files changed:** 4
  - protocols/__init__.py
  - protocols/chat_integration.py
  - protocols/orchestrator.py
  - protocols/supabase_storage.py
- **Details:** Changes:

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

### ✨ feat: Implement A2A Practical Architecture with core protocols

- **Commit:** `5ec09e8b`
- **Author:** jsagir
- **Files changed:** 8
  - CLAUDE.md
  - docs/A2A_PRACTICAL_ARCHITECTURE.md
  - docs/A2A_WORKFLOW_ARCHITECTURE.md
  - docs/PWS_A2A_IMPLEMENTATION_PLAN.md
  - protocols/__init__.py
- **Details:** Architecture decisions consolidated:

### 📝 docs: Add comprehensive PWS A2A Implementation Plan

- **Commit:** `ba5ffae9`
- **Author:** jsagir
- **Files changed:** 1
  - docs/PWS_A2A_IMPLEMENTATION_PLAN.md
- **Details:** Complete architecture for implementing PWS methodology as A2A workflows:

### 📝 docs: Add A2A Workflow Architecture for PWS methodologies

- **Commit:** `8a879350`
- **Author:** jsagir
- **Files changed:** 1
  - docs/A2A_WORKFLOW_ARCHITECTURE.md
- **Details:** Research-based design for multi-agent orchestration using:

### ✨ feat: Add Nested Hierarchies agent (15th agent)

- **Commit:** `1b779664`
- **Author:** jsagir
- **Files changed:** 5
  - mindrian_chat.py
  - prompts/__init__.py
  - prompts/nested_hierarchies.py
  - protocols/agent_registry.py
  - scripts/neo4j_triple_mode_migration.py
- **Details:** Multi-level systems analysis workshop for finding leverage points.

### ✨ feat: Implement Triple-Mode Architecture with Agent Registry and Neo4j schema

- **Commit:** `d3e38935`
- **Author:** jsagir
- **Files changed:** 17
  - QA_REPORT_PHASE_TRANSITIONS.txt
  - R&D/25_triple_mode_architecture/README.md
  - R&D/25_triple_mode_architecture/neo4j_analysis.py
  - docs/DUAL_MODE_ARCHITECTURE_PLAN.md
  - docs/TRIPLE_MODE_ARCHITECTURE_SPEC.md
- **Details:** - Add protocols layer: agent_registry (14 agents), triple_mode (entry points,

### ✨ feat: Add lazy embedding cache and Google LangExtract integration

- **Commit:** `bb5e841c`
- **Author:** jsagir
- **Files changed:** 3
  - requirements.txt
  - tools/google_langextract.py
  - tools/opportunity_bank.py
- **Details:** - opportunity_bank.py: Implement lazy cache pattern for embeddings

### ✨ feat: PWS-compliant Bank of Opportunities with Supabase table storage

- **Commit:** `19ad86c2`
- **Author:** jsagir
- **Files changed:** 3
  - scripts/daily_summary.py
  - sql/opportunity_bank.sql
  - tools/opportunity_bank.py
- **Details:** This commit implements the full Bank of Opportunities registry as specified

### ✨ feat: Enhance daily summary with opportunity content and fix yesterday counts

- **Commit:** `f81537e6`
- **Author:** Claude
- **Files changed:** 1
  - scripts/daily_summary.py
- **Details:** - Fix date counting: today and yesterday counts are now separate (not combined in 'last 24h')

## 2026-02-01

### ✨ feat: Add /api/daily-summary endpoint for external cron

- **Commit:** `98ed87d7`
- **Author:** Claude
- **Files changed:** 1
  - mindrian_chat.py
- **Details:** - Adds GET /api/daily-summary endpoint callable by cron-job.org

### 🔧 chore: Add logs/*.log to gitignore

- **Commit:** `ca69a60d`
- **Author:** Claude
- **Files changed:** 1
- **Details:** https://claude.ai/code/session_01LSScnDkHM5RfFnzKKFCey2

### ✨ feat: Add scheduler service for daily email summaries

- **Commit:** `1eb14e49`
- **Author:** Claude
- **Files changed:** 2
  - logs/.gitkeep
  - scheduler_service.py
- **Details:** - Add scheduler_service.py for Render.com Background Worker

### 📝 docs: Add JSON schema validation, onboarding guide, and ADR

- **Commit:** `1c105601`
- **Author:** Claude
- **Files changed:** 6
  - ONBOARDING.md
  - docs/adr/001-a2a-protocol-markdown.md
  - protocols/__init__.py
  - protocols/a2a_protocol.py
  - protocols/schemas/__init__.py
- **Details:** Implementing code review recommendations:

### ✨ feat: Enhanced Context Journal with Supabase persistence and rich UI

- **Commit:** `1b92be85`
- **Author:** Claude
- **Files changed:** 4
  - mindrian_chat.py
  - protocols/context_journal.py
  - public/elements/EnhancedJournalViewer.jsx
  - sql/journal_entries.sql
- **Details:** Multi-skill implementation integrating mindrian-stack, chainlit-consultant,

### ✨ feat: Add A2A Protocol for agent-to-agent communication via MD files

- **Commit:** `049a6a25`
- **Author:** Claude
- **Files changed:** 6
  - CLAUDE.md
  - journals/example_session.md
  - protocols/__init__.py
  - protocols/a2a_protocol.py
  - protocols/context_journal.py
- **Details:** Implements structured handoff system between agents:

### ✨ feat: Integrate Phase Insights for intelligent progress surfacing

- **Commit:** `36a0ed5f`
- **Author:** Claude
- **Files changed:** 3
  - CLAUDE.md
  - mindrian_chat.py
  - tools/phase_insights.py
- **Details:** - Add tools/phase_insights.py module that transforms smart_phase_tracker

### ✨ feat: Custom WorkshopRoadmap sidebar (Option B implementation)

- **Commit:** `ece59912`
- **Author:** Claude
- **Files changed:** 2
  - mindrian_chat.py
  - public/elements/WorkshopRoadmap.jsx
- **Details:** Implements the interactive phase sidebar to replace TaskList:

### ✨ feat: Quick Win - Soft phase transitions + back navigation

- **Commit:** `77109b23`
- **Author:** Claude
- **Files changed:** 1
  - mindrian_chat.py
- **Details:** UX improvements per PM analysis (80% improvement, 2% effort):

### 📝 docs: Add QA Analyzer & PM Advisor Instructions

- **Commit:** `be1a6942`
- **Author:** Claude
- **Files changed:** 1
  - qa/QA_ANALYZER_INSTRUCTIONS.md
- **Details:** Comprehensive guide for AI assistants to:
