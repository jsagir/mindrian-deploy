# QA Testing Memo - February 8, 2026

---
  To: User-Side Testers (QA)
  Date: February 8, 2026
  Branch: Triple-mode-v1---RENDER_DEPLOYMENT

  ================================================================================
                           MINDRIAN QA TESTING MEMO
  ================================================================================

  ## Executive Summary

  This release addressed critical infrastructure issues that were blocking user
  sessions (database errors, login loops, unresponsive buttons) while also adding
  new user-facing features for the Bank of Opportunities.

  **Key accomplishments:**
  * FIXED: "User not found" / "threads 404" login loop (database schema mismatch)
  * FIXED: Entry point selector buttons not responding (replaced with native starters)
  * FIXED: Pipeline import errors (Oracle, Genesis, Minto)
  * NEW: Bank of Opportunities notifications (users now see extracted opportunities)
  * NEW: LightRAG health check in system monitoring
  * NEW: Updated README reflecting v4.0 architecture
  * NEW: Conversation Forking (UX-001) - Fork button in action bar
  * NEW: Idea Canvas (UX-002) - Ideas button in action bar
  * NEW: Agent Attribution Badges (UX-006) - Bot name/icon on responses
  * NEW: Idea Tagging/Rating (UX-007) - Star and prune actions in canvas

  **Still pending from user testing (see Section 4):**
  * Topic blacklist UI management (detection exists, no management UI)

  ================================================================================

  ## Section 1: CRITICAL INFRASTRUCTURE FIXES (Priority 0)
  ================================================================================

  ### 1.1 Database Schema Fix (Chainlit Compatibility)

  **Problem:** Users stuck in "User not found" / "threads 404" blinking loop after OAuth.

  **Root Cause:** Chainlit expects TEXT columns for IDs and timestamps, but we had
  UUID and TIMESTAMP types.

  **Fix Applied:**
  - Dropped and recreated all tables with correct schema
  - Added /api/init-db endpoint for manual reinitialization
  - Added tables list to /api/health for debugging

  **How to Test:**
  1. Go to https://mindrian.onrender.com
  2. Log in with Supabase OAuth
  3. Verify you reach the chat interface without blinking errors
  4. Check /api/health endpoint shows 5 tables: users, threads, steps, elements, feedbacks

  **Expected Result:** Login works, conversation loads, no 404 errors

  | Test | Expected | Pass |
  |------|----------|------|
  | OAuth login | Reaches chat interface | [ ] |
  | /api/health tables | Shows 5 tables | [ ] |
  | New conversation | Creates thread, persists | [ ] |
  | Return visit | Sees previous conversations | [ ] |

  --------------------------------------------------------------------------------

  ### 1.2 Entry Point Navigation Fix

  **Problem:** Custom entry point selector buttons (Explore Ideas, Get Feedback,
  Build Venture) did nothing when clicked.

  **Fix Applied:**
  - Replaced CustomElement + callAction with native Chainlit starters
  - Added fallback: if detection fails, defaults to "brainstorming" mode
  - Entry point options now appear as conversation starters

  **How to Test:**
  1. Start a new conversation with PWS Consultant
  2. Observe the 4 starter buttons:
     - "Explore a challenge"
     - "Get feedback on my work"
     - "Build a venture"
     - "Not sure where to start"
  3. Click any starter

  **Expected Result:** Starter triggers appropriate mode and shows initial prompt

  | Test | Expected | Pass |
  |------|----------|------|
  | Starters visible | 4 buttons appear | [ ] |
  | Click starter | Sends message, conversation begins | [ ] |
  | Typing directly | Works without clicking starter | [ ] |

  --------------------------------------------------------------------------------

  ### 1.3 Auth Flow Stabilization

  **Problem:** Double login screens, auth-bridge causing 404s

  **Fix Applied:**
  - Disabled auth-bridge.js interference
  - Using Chainlit native password auth when Supabase not available
  - /api/health and /api/public-config moved to middleware (bypass auth)

  **How to Test:**
  1. Visit app in incognito mode
  2. Verify single login screen appears
  3. Log in with valid credentials
  4. Verify no redirect loops

  ================================================================================

  ## Section 2: NEW FEATURES
  ================================================================================

  ### 2.1 Bank of Opportunities Notifications

  **Description:** When opportunities are extracted from conversation, users now see
  a notification: "💡 X opportunities captured" with a "View Bank" button.

  **How to Test:**
  1. Have a substantive conversation (5+ turns) about a problem domain
  2. Mention potential opportunities, problems worth solving, or market gaps
  3. Watch for notification after response
  4. Click "View Bank" to see captured opportunities

  **Expected Result:**
  - Notification appears when opportunities extracted
  - View Bank shows OpportunityCard components
  - Each card has "Explore" and "Remove" actions

  | Test | Expected | Pass |
  |------|----------|------|
  | 5+ turn conversation | Notification appears | [ ] |
  | View Bank click | Shows OpportunityCard list | [ ] |
  | Explore opportunity | Opens detailed exploration | [ ] |

  **Note:** Requires LIGHTRAG_PASSWORD env var for full functionality.

  --------------------------------------------------------------------------------

  ### 2.2 LightRAG Health Check

  **Description:** System health check now includes LightRAG status.

  **How to Test:**
  ```bash
  python scripts/health_check.py
  ```

  **Expected Result:**
  - Section 12 shows LightRAG server health
  - Auth status (will fail if LIGHTRAG_PASSWORD not set)
  - Integration module import check

  --------------------------------------------------------------------------------

  ### 2.3 Updated README (v4.0 Architecture)

  **Description:** README now documents:
  - Triple-Mode Architecture (sandbox, workshop, venture)
  - PWS Consultant 3-stage flow
  - Intelligence Pipelines (10 pipelines)
  - A2A Protocol
  - Privacy & Context Isolation section

  **How to Test:** Read README.md and verify accuracy against running system.

  ================================================================================

  ## Section 3: PIPELINE IMPORT FIXES
  ================================================================================

  **Problem:** Several intelligence pipelines failed to import due to missing
  dependencies or incorrect import paths.

  **Fixes Applied:**
  - text2cypher.py: Lazy-initialize genai.Client
  - research_agent.py: Fixed import path for ALL_RESEARCH_TOOLS
  - __init__.py: Added missing Genesis pipeline exports

  **How to Test:**
  ```python
  python3 -c "
  from intelligence import (
      run_minto_pipeline,
      run_genesis_pipeline,
      run_oracle_formulation,
      create_grading_pipeline
  )
  print('All pipelines import OK')
  "
  ```

  **Expected Result:** No import errors

  ================================================================================

  ## Section 4: PENDING FROM USER TESTING SESSION
  ================================================================================

  The February 8 user testing session identified the following issues. This section
  tracks implementation status.

  ### 4.1 Addressed in This Release

  | Issue ID | Description | Status | Notes |
  |----------|-------------|--------|-------|
  | BUG-002 | No conversation save | ✅ FIXED | Database now works, sessions persist |
  | BUG-003 | No topic blacklist | ⚠️ PARTIAL | detect_topic_exclusion() exists, needs UI |
  | UX-005 | No export capability | ✅ EXISTS | Synthesize action creates markdown |

  --------------------------------------------------------------------------------

  ### 4.2 Implemented This Session

  | Issue ID | Description | Status | How to Test |
  |----------|-------------|--------|-------------|
  | UX-001 | Conversation branching | ✅ IMPLEMENTED | See Section 8.1 |
  | UX-002 | Idea visualization | ✅ IMPLEMENTED | See Section 8.2 |
  | UX-006 | Agent attribution badges | ✅ IMPLEMENTED | See Section 8.3 |
  | UX-007 | Idea tagging/rating | ✅ IMPLEMENTED | See Section 8.4 |

  **Note:** Wave 2, 3, 4 protocols are now wired to UI via action buttons.

  --------------------------------------------------------------------------------

  ### 4.3 Not Yet Addressed

  | Issue ID | Description | Priority | Effort |
  |----------|-------------|----------|--------|
  | BUG-001 | Context persistence (avoided topics returning) | P0 | Medium |
  | UX-003 | Project organization | P1 | High |
  | UX-004 | Research results persistence | P1 | Medium |
  | FR-004 | Notion/Miro export | P2 | Medium |

  ================================================================================

  ## Section 5: QUICK TEST CHECKLIST
  ================================================================================

  | # | Area | What to Verify | Pass |
  |---|------|----------------|------|
  | 1 | Login | OAuth works, no blinking loop | [ ] |
  | 2 | Database | /api/health shows 5 tables | [ ] |
  | 3 | Session | Conversation persists across refresh | [ ] |
  | 4 | Starters | 4 conversation starters appear | [ ] |
  | 5 | Starters | Clicking starter begins conversation | [ ] |
  | 6 | Opportunities | Notification appears after 5+ turns | [ ] |
  | 7 | View Bank | OpportunityCards display properly | [ ] |
  | 8 | Pipeline imports | All 10 pipelines import without error | [ ] |
  | 9 | Health check | python scripts/health_check.py passes | [ ] |
  | 10 | Fork | 🍴 Fork button visible, creates branch | [ ] |
  | 11 | Ideas | 💡 Ideas button visible, shows canvas | [ ] |
  | 12 | Agent Badge | Response shows agent icon + name | [ ] |
  | 13 | Star/Prune | Idea actions work in canvas | [ ] |

  ================================================================================

  ## Section 6: KNOWN LIMITATIONS
  ================================================================================

  * **LightRAG requires password:** Set LIGHTRAG_PASSWORD in Render for full
    Bank of Opportunities functionality
  * **Opportunity extraction is async:** Notifications appear on NEXT message,
    not immediately after extraction
  * **Topic blacklist needs UI:** detect_topic_exclusion() works but no
    management interface exists

  ================================================================================

  ## Section 8: NEWLY WIRED UX FEATURES
  ================================================================================

  The following features from user testing feedback have been wired and are now
  testable. These use Chainlit's action buttons and custom elements.

  ### 8.1 Conversation Forking (UX-001)

  **Description:** Git-like branching for conversations. Users can explore
  alternative directions without losing their main conversation.

  **How to Test:**
  1. Start a conversation with any agent (5+ messages)
  2. Look for the "🍴 Fork" button in the action bar
  3. Click Fork - creates a new branch
  4. Continue the conversation in the new branch
  5. Click "View All Branches" to see branch tree
  6. Switch between branches to verify history

  | Test | Expected | Pass |
  |------|----------|------|
  | Fork button visible | 🍴 Fork in action bar | [ ] |
  | Create branch | Shows "Branch Created: [title]" | [ ] |
  | View branches | BranchSelector shows all branches | [ ] |
  | Switch branch | History changes to selected branch | [ ] |

  --------------------------------------------------------------------------------

  ### 8.2 Idea Canvas (UX-002)

  **Description:** Visual canvas showing extracted ideas from conversation.
  Ideas are auto-classified as problems, insights, or questions.

  **How to Test:**
  1. Have a substantive conversation (5+ turns)
  2. Look for the "💡 Ideas" button in the action bar
  3. Click Ideas - shows IdeaCanvas with extracted ideas
  4. Click star on promising ideas
  5. Click prune on dead ends
  6. Click Refresh to re-extract
  7. Click Export to get markdown summary

  | Test | Expected | Pass |
  |------|----------|------|
  | Ideas button visible | 💡 Ideas in action bar | [ ] |
  | Canvas displays | Shows extracted nodes | [ ] |
  | Star idea | Toggles star, shows confirmation | [ ] |
  | Prune idea | Marks as dead end | [ ] |
  | Export | Generates markdown grouped by type | [ ] |

  --------------------------------------------------------------------------------

  ### 8.3 Agent Attribution Badges (UX-006)

  **Description:** AI responses now show which agent responded with their
  icon and name in the message header.

  **How to Test:**
  1. Start conversation with Lawrence
  2. Observe response shows "🧑‍🏫 Lawrence" as author
  3. Switch to Larry Playground
  4. Observe response shows "🧪 Larry Playground"
  5. Try other agents (TTA, Ackoff, etc.)

  | Test | Expected | Pass |
  |------|----------|------|
  | Lawrence response | Shows 🧑‍🏫 Lawrence as author | [ ] |
  | Larry Playground | Shows 🧪 Larry Playground | [ ] |
  | TTA response | Shows appropriate icon + name | [ ] |

  --------------------------------------------------------------------------------

  ### 8.4 Idea Tagging/Rating (UX-007)

  **Description:** Within the Idea Canvas, users can star (mark as promising)
  or prune (mark as dead end) individual ideas.

  **How to Test:**
  1. Open Idea Canvas (💡 Ideas button)
  2. Find an idea node
  3. Click star icon - should toggle star status
  4. Click prune icon - should mark as dead end
  5. Pruned ideas should be visually dimmed
  6. Starred ideas appear first in exports

  | Test | Expected | Pass |
  |------|----------|------|
  | Star idea | Shows "⭐ Starred: [preview]" | [ ] |
  | Unstar idea | Shows "Unstarred: [preview]" | [ ] |
  | Prune idea | Shows "🗑️ Pruned: [preview]" | [ ] |
  | Export starred | Starred items have ⭐ prefix | [ ] |

  ================================================================================

  ## Section 7: ENVIRONMENT REQUIREMENTS
  ================================================================================

  Required for full functionality:
  ```
  GOOGLE_API_KEY          - Core LLM
  DATABASE_URL            - PostgreSQL (Chainlit persistence)
  SUPABASE_URL            - Auth + Storage
  SUPABASE_ANON_KEY       - Auth (public key)
  ```

  Recommended:
  ```
  LIGHTRAG_PASSWORD       - Bank of Opportunities
  TAVILY_API_KEY          - Web research
  NEO4J_URI/USER/PASSWORD - GraphRAG
  ```

  ================================================================================
  END OF MEMO
  ================================================================================

  Commits covered (last 24 hours):
  - 67cde4e feat: Add LightRAG health check + Bank of Opportunities UX notifications
  - 9e7786f fix: Remove broken entry selector, use starters instead
  - 52de710 fix: Use separate action callbacks for each entry point
  - f6100de fix: Replace EntryPointSelector with native Chainlit Action buttons
  - c6e5161 fix: Use TEXT columns for Chainlit compatibility
  - 6290e5e fix: Execute SQL statements one at a time for asyncpg
  - 4c7d8e0 fix: Use raw SQL for Chainlit database table creation
  - de2a5fc fix: Add database initialization to create Chainlit tables
  - 1749e0a fix: Resolve pipeline import issues (Minto/Oracle/Genesis)
  - 224b729 fix: Auth - use Chainlit native password auth
  - 93cf83b feat: Implement Waves 2, 3, 4 - Forking, Canvas, Auto-Orchestration

  Generated: February 8, 2026
  Prepared by: Claude Code Automation
