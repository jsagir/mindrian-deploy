# QA Test Plan: Smart Phase Transitions
**Date:** January 29, 2026
**Feature:** Smart Phase Transitions for Scenario Analysis Bot
**Commit:** e00313d

---

## Summary of Changes

The "Next Phase" button in Scenario Analysis now:
1. Validates if user completed current phase deliverables
2. Shows what's missing if incomplete
3. Generates smart transition with context from Neo4j, News, and Trends
4. Persists phase progress when switching bots

---

## Test Cases

### TC-001: Basic Phase Advancement
**Priority:** High
**Steps:**
1. Select "Scenario Analysis" bot from profile dropdown
2. Say: "I want to explore the future of renewable energy to decide if I should invest. Looking at 2035."
3. Click "Next Phase" button

**Expected:**
- See spinner: "Checking Phase Completion"
- See spinner: "Preparing Next Phase"
- See transition message with:
  - Summary of what you established (domain, question, time horizon)
  - Description of "Domain & Driving Forces" phase
  - Clear instructions (5 STEEP categories)
  - Opening question about SOCIAL forces

---

### TC-002: Incomplete Phase Warning
**Priority:** High
**Steps:**
1. Select "Scenario Analysis" bot
2. Say: "hello"
3. Immediately click "Next Phase"

**Expected:**
- See "Phase Progress: XX%" message
- See what's missing (domain, focal question, time horizon)
- See "Proceed Anyway" button
- Clicking "Proceed Anyway" advances to next phase

---

### TC-003: Phase Persistence Across Bot Switch
**Priority:** Critical
**Steps:**
1. Select "Scenario Analysis" bot
2. Complete phases 1-3 (Introduction through Uncertainty)
3. Switch to "JTBD" bot
4. Switch BACK to "Scenario Analysis" bot

**Expected:**
- Phase progress is RESTORED (showing Phase 3/4 as current)
- Task list shows correct completion status (phases 1-2 marked done)
- NOT reset to Phase 1

---

### TC-004: News Enrichment
**Priority:** Medium
**Prerequisite:** NEWSMESH_API_KEY environment variable set
**Steps:**
1. Select "Scenario Analysis" bot
2. Say: "I want to explore the future of artificial intelligence"
3. Click "Next Phase" to go to Driving Forces

**Expected:**
- Transition message includes "Recent News (artificial intelligence):"
- Shows 2-3 news headlines with sources
- Headlines are relevant to AI domain

**If API key not set:**
- News section simply not shown (no error)

---

### TC-005: Trends Enrichment
**Priority:** Medium
**Prerequisite:** SERPAPI_API_KEY environment variable set
**Steps:**
1. Select "Scenario Analysis" bot
2. Say: "I want to explore the future of electric vehicles"
3. Click "Next Phase"

**Expected:**
- Transition message includes "Current Trends:"
- Shows trend direction (Rising/Stable/Declining)
- Shows rising related queries

**If API key not set:**
- Trends section simply not shown (no error)

---

### TC-006: Research Button Tooltips
**Priority:** Medium
**Steps:**
1. Select "Scenario Analysis" bot
2. Start a conversation about any domain
3. Hover over research buttons

**Expected:**
- See scenario-specific tooltips:
  - "Scenario Analysis - validate uncertainty axes with Google Trends"
  - "Scenario Analysis - current events inform scenario drivers"

---

### TC-007: Workshop Completion
**Priority:** Medium
**Steps:**
1. Select "Scenario Analysis" bot
2. Advance through all 6 phases (clicking "Next Phase" or "Proceed Anyway")
3. Click "Next Phase" on final phase

**Expected:**
- See "Workshop Complete!" message
- See options: "Review Progress" and "Start Fresh"

---

### TC-008: Task List Updates
**Priority:** Medium
**Steps:**
1. Select "Scenario Analysis" bot
2. Watch the task list panel as you advance phases

**Expected:**
- Phase 1 shows as "Running" initially
- After clicking Next Phase, Phase 1 shows "Done", Phase 2 shows "Running"
- Completed phases stay marked as "Done"

---

## Regression Tests

### RT-001: Other Workshop Bots Still Work
**Steps:**
1. Test TTA bot - click Next Phase
2. Test JTBD bot - click Next Phase
3. Test Ackoff bot - click Next Phase

**Expected:**
- All bots still show phase transitions (may be basic without smart enrichment)
- No errors or crashes

---

### RT-002: Non-Workshop Bots Unaffected
**Steps:**
1. Select "Lawrence" bot
2. Have a conversation
3. Verify no phase-related buttons or errors

**Expected:**
- Lawrence works normally without phase features

---

## Environment Requirements

| Variable | Required for Test |
|----------|-------------------|
| NEWSMESH_API_KEY | TC-004 (News) |
| SERPAPI_API_KEY | TC-005 (Trends) |
| NEO4J_URI | Framework enrichment |

All tests should pass even without these keys (graceful degradation).

---

## Known Limitations

1. Smart transitions only work for Scenario Analysis bot currently
2. Pattern matching may not catch all phrasings
3. "Proceed Anyway" always allows advancement

---

## Files Changed

| File | Change |
|------|--------|
| mindrian_chat.py | Rewrote on_next_phase() handler |
| prompts/scenario_phases.py | NEW - Phase definitions |
| tools/phase_validator.py | NEW - Completion validation |
| tools/phase_enricher.py | NEW - Context enrichment |
| prompts/__init__.py | Added exports |
| tools/__init__.py | Added exports |

---

## Sign-off

| Tester | Date | Status |
|--------|------|--------|
| | | |
