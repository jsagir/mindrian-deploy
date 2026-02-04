To: User-Side Testers (QA)
Date: February 4, 2026
Branch: Triple-mode-v1---RENDER_DEPLOYMENT

================================================================================
                         MINDRIAN QA TESTING MEMO
================================================================================

What This Release Addresses
---------------------------

This release focuses on making Mindrian feel like a thinking partner, not a tool.
The core goal is to ensure that file processing, research, and expert analysis
all communicate clearly with users about what's happening and why.

Key areas addressed:

* NEW: Genesis Expert multi-agent pipeline (6-stage BONO Six Hats)
* Humanized file upload feedback (PWS/Lawrence-style language)
* Tools Panel UX clarity (always-visible advanced pipelines)
* Smart onboarding with humanized research contextualization
* Stability fixes (Oracle import, cronjob errors, PDF processing)
* Security hardening and performance improvements

================================================================================

KEY CHANGES READY TO TEST
================================================================================

1. NEW: Genesis Expert Breakdown Pipeline (PRIORITY 1)
------------------------------------------------------

A 6-stage, streaming expert panel pipeline using BONO Six Thinking Hats,
designed for complex, multi-domain problems.

Pipeline stages:
  1. Context Decomposition - segments text, extracts concepts
  2. Domain Discovery - matches against 24 domain patterns (14 tech, 10 non-tech)
  3. Persona Generation - creates experts with Six Hats enrichment
  4. Research Orchestration - plans collaboration matrix
  5. Expert Panel Discussion - 4-round multi-agent simulation via Gemini
  6. Breakthrough Synthesis - scores opportunities, generates roadmaps

How to test:
  1. Enter a 50+ character, multi-domain challenge, e.g.:
     "How can AI and blockchain transform supply chain transparency
      while addressing sustainability and labor concerns?"
  2. Click Tools Panel (bottom-right) > Advanced Pipelines > Genesis (brain icon)

Expected Result:
  * 6 stages stream visibly with progress updates
  * Expert personas show their assigned Six Thinking Hat
  * Final output includes:
    - Breakthrough opportunities with scores (0-10)
    - Implementation roadmaps with phases
    - Cross-domain connections identified

--------------------------------------------------------------------------------

2. Tools Panel UX Improvements (PRIORITY 1)
-------------------------------------------

Changes:
  * Advanced Pipelines section is ALWAYS VISIBLE (no toggle needed)
  * Hover tooltips now show three levels:
    - Tool name (bold white)
    - What it does (purple)
    - "Use when..." guidance (yellow italic)

How to test:
  1. Click the wrench icon (bottom-right floating button)
  2. Panel should show two sections immediately:
     - Core Frameworks (8 tools)
     - Advanced Pipelines (5 tools)
  3. Hover over any tool

Expected Result:
  * No toggle button to reveal advanced tools
  * Hover shows contextual "why this helps" guidance
  * Border highlights in tool's color on hover

Tools available:
  Core: Reverse Salient, JTBD, TTA, Red Team, S-Curve, DIKW, Scenario, Beautiful Question
  Advanced: Minto Pyramid, Multi-Validation, Domain Discovery, Oracle Foresight, Genesis Expert

--------------------------------------------------------------------------------

3. Humanized File Upload Feedback (PRIORITY 2)
----------------------------------------------

File uploads now provide PWS/Lawrence-style feedback instead of generic messages.

How to test:
  1. Upload a PDF, DOCX, or image file
  2. Watch the processing feedback

Expected Result:
  * Messages like "unpacking...", "following threads...", "what's the real job here..."
  * NOT robotic messages like "Processing..." or "Analyzing document..."
  * Feedback streams while file is being processed

--------------------------------------------------------------------------------

4. Smart Onboarding + Research Contextualization (PRIORITY 2)
-------------------------------------------------------------

New users get guided entry points, and research queries are humanized.

How to test:
  1. Start a new session (clear context if needed)
  2. Observe onboarding flow
  3. Ask a research question

Expected Result:
  * Onboarding presents clear entry points
  * Research queries feel reframed and intentional
  * Results emphasize interpretation, not just data dumps

--------------------------------------------------------------------------------

5. Oracle Pipeline Stability Fix (PRIORITY 3)
---------------------------------------------

Oracle no longer crashes the app at import time if GOOGLE_API_KEY is missing.

How to test:
  1. App should start without errors
  2. Oracle only fails when actually invoked without a key

Expected Result:
  * App loads normally regardless of API key state
  * Oracle shows error only when clicked without valid key

--------------------------------------------------------------------------------

6. Daily Summary Cronjob Fix (PRIORITY 3)
-----------------------------------------

The /api/daily-summary endpoint now returns helpful errors.

How to test:
  * Without email config: Should return 503 with message:
    "Email not configured. Set SMTP_USER/SMTP_PASSWORD or SENDGRID_API_KEY"
  * With email config: Should send summary and return 200

--------------------------------------------------------------------------------

7. PDF Processing Bug Fix (PRIORITY 3)
--------------------------------------

Critical fix for PDF processing that was failing silently.

How to test:
  1. Upload various PDF types (text-heavy, image-heavy, mixed)
  2. Verify content is extracted and discussed

Expected Result:
  * PDF content appears in context
  * No silent failures or empty extractions

================================================================================

QUICK TEST CHECKLIST
================================================================================

| #  | Area              | What to Verify                              | Pass |
|----|-------------------|---------------------------------------------|------|
| 1  | Genesis Pipeline  | 6 stages stream, personas show hats         | [ ]  |
| 2  | Genesis Output    | Opportunities have scores + roadmaps        | [ ]  |
| 3  | Tools Panel       | Opens with floating button click            | [ ]  |
| 4  | Tools Panel       | Advanced Pipelines visible without toggle   | [ ]  |
| 5  | Tools Hover       | Shows "Use when..." yellow guidance         | [ ]  |
| 6  | File Upload       | PWS-style feedback (not "Processing...")    | [ ]  |
| 7  | PDF Processing    | Content extracted and discussed             | [ ]  |
| 8  | Smart Onboarding  | Entry points presented for new users        | [ ]  |
| 9  | Oracle Startup    | App loads even if API key missing           | [ ]  |
| 10 | Cronjob Error     | Returns 503 with clear message if no email  | [ ]  |

================================================================================

COMMITS INCLUDED (Last 18 Hours)
================================================================================

e2b7984 fix: Configure Gemini API key in Genesis panel.py
1500522 feat: Add Genesis Expert Breakdown pipeline + UI improvements
376c18d docs: Add R&D/21_genesis_expert_breakdown for Swarm+LangGraph integration
0ef8019 docs: Add R&D/20_pws_thinking_streamer for future reference
ac991a2 feat: Add Claude Code-style thinking streamer for file processing
c4251fb fix: Rewrite ToolsPanel with inline styles for Chainlit compatibility
e897e3e feat: Add floating PWS Tools Panel with contextual tooltips
1a22055 feat: Humanize file upload feedback with PWS/Lawrence-style language
593f368 docs: User-friendly README + legal disclaimers
7a3b731 fix: Critical PDF processing bug + streaming file upload feedback
2d0b0fb feat: Smart onboarding + humanized research contextualization
7c31f26 feat: API health monitoring, daily digest email, and smart onboarding
cc1ed3c fix: QA UI/UX improvements - accessibility and error handling
a8f9051 feat: Security hardening and performance improvements

================================================================================

KNOWN LIMITATIONS
================================================================================

* Genesis requires valid GOOGLE_API_KEY (set on Render)
* Genesis requires 50+ character challenge description
* Daily Summary cronjob requires email credentials (SMTP or SendGrid)
* Voice integration still partially implemented

================================================================================

FILES CHANGED
================================================================================

New Files (Genesis Pipeline):
  intelligence/pipelines/genesis/__init__.py
  intelligence/pipelines/genesis/decompose.py
  intelligence/pipelines/genesis/domains.py
  intelligence/pipelines/genesis/personas.py
  intelligence/pipelines/genesis/orchestrate.py
  intelligence/pipelines/genesis/panel.py
  intelligence/pipelines/genesis/synthesize.py
  intelligence/pipelines/genesis/pipeline.py

Modified Files:
  mindrian_chat.py                           - Genesis callback + cronjob fix
  intelligence/pipelines/__init__.py         - Genesis exports
  intelligence/pipelines/oracle_pipeline.py  - Lazy client init
  public/elements/ToolsPanel.jsx             - UI improvements

================================================================================

END OF MEMO
================================================================================
