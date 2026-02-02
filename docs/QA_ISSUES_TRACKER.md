# Mindrian QA: Issue Tracker (Feb 2025)

## Source
Team meeting with user feedback from: Lucas (researcher), Database Guy (unnamed), Contessa St. Clair (student)

---

## Issue Summary

| Priority | Count | Status |
|----------|-------|--------|
| Critical | 4 | Open |
| High | 4 | Open |
| Medium | 4 | Open |
| **Total** | **12** | **Open** |

---

## Critical Issues (Fix Before Budapest)

### QA-001: No default selection in Red Team menu
- **Reporter:** Database Guy
- **Severity:** Critical
- **Status:** Open
- **Description:** When entering Red Team menu, nothing is selected by default. New users expect to be "red teamed" immediately without additional configuration.
- **Expected:** Click "Red Team" → Get red teamed
- **Actual:** Click "Red Team" → Blank state → Must select something → Returns to main if nothing selected
- **Fix:** Add default selection or auto-detect what to red team from conversation context

### QA-002: Required buttons not marked as required
- **Reporter:** Database Guy
- **Severity:** Critical
- **Status:** Open
- **Description:** Buttons that must be clicked are not visually distinguished from optional buttons. Users don't know what's required.
- **Fix:** Add visual indicator (asterisk, color, or text) for required selections

### QA-004: New users don't know what to do
- **Reporter:** Database Guy
- **Severity:** Critical
- **Status:** Open
- **Description:** First-time users arrive at interface with no guidance on what to click or how to start.
- **Quote:** "I had no idea what to do."
- **Fix:** Add onboarding flow with clear entry point selection

### QA-009: Non-PWS users can't start
- **Reporter:** Contessa St. Clair
- **Severity:** Critical
- **Status:** Open
- **Description:** Users unfamiliar with PWS methodology don't know what workshops are or where to begin.
- **Quote:** "For someone who hasn't been in any of professor Aronhime's classes, doesn't know what these different workshops are... they don't know what the content is and if they were shown this, how would they know where to start?"
- **Fix:** Create simple onboarding that doesn't assume PWS knowledge

---

## High Priority Issues (Fix for MVP)

### QA-003: Unexpected navigation back to main screen
- **Reporter:** Database Guy
- **Severity:** High
- **Status:** Open
- **Description:** When user doesn't select required options, system silently returns to main screen without explanation.
- **Fix:** Show error message or prompt user to make selection

### QA-005: Build Venture hard to find
- **Reporter:** Contessa St. Clair
- **Severity:** High
- **Status:** Open
- **Description:** Build Venture feature is hidden in menu, not visible on landing.
- **Quote:** "I didn't know how to get here"
- **Fix:** Make all three entry points visible on first screen

### QA-006: Button purpose unclear
- **Reporter:** Contessa St. Clair
- **Severity:** High
- **Status:** Open
- **Description:** Spawned buttons don't explain what they do or why they appeared.
- **Quote:** "I'm not sure what to do with" (buttons)
- **Fix:** Add hover explanations showing why button appeared and what it does

### QA-008: Export format (.md only)
- **Reporter:** Contessa St. Clair
- **Severity:** High
- **Status:** Open
- **Description:** Download only exports .md files, but users need .docx/.pdf for sharing.
- **Fix:** Add .docx and .pdf export options

---

## Medium Priority Issues (Fix Post-MVP)

### QA-007: General button confusion
- **Reporter:** Contessa St. Clair
- **Severity:** Medium
- **Status:** Open
- **Description:** Too many buttons, users don't know which to press.
- **Quote:** "Didn't know what buttons to press"
- **Fix:** Reduce button count, improve visual hierarchy

### QA-010: Right panel doesn't update during workflow
- **Reporter:** Observation from demo
- **Severity:** Medium
- **Status:** Open
- **Description:** Progress indicator on right side doesn't reflect current workflow state.
- **Fix:** Real-time sync of progress panel with conversation state

### QA-011: "Continue domain extension" not rendered as button
- **Reporter:** Observation from demo
- **Severity:** Medium
- **Status:** Open
- **Description:** Text that should be a clickable button renders as plain text.
- **Fix:** Parse and render action text as buttons

### QA-013: Settings slider visual bug
- **Reporter:** Observation from demo
- **Severity:** Medium
- **Status:** Open
- **Description:** Settings slider doesn't visually update when changed.
- **Fix:** Fix slider component state management

---

## User Personas

### Persona 1: The Researcher (Lucas)
- **Goal:** Get feedback on existing work, find new directions
- **Pain:** Needs actionable follow-up, not just challenges
- **Quote:** "Bad at the task to pursue those goals"
- **Needs:** Follow-up questions that lead to specific actions

### Persona 2: The Expert Builder (Database Guy)
- **Goal:** Validate business plan, red team assumptions
- **Pain:** Expects system to "just work" without configuration
- **Quote:** "I'm expecting me red teamed in some way without pressing any other buttons"
- **Needs:** Zero-config default behavior

### Persona 3: The Student (Contessa)
- **Goal:** Learn methodology, apply to class projects
- **Pain:** Unfamiliar with PWS, needs guidance
- **Quote:** "For someone who hasn't been in any of professor Aronhime's classes..."
- **Needs:** Onboarding for non-PWS users

### Persona 4: The Adam Peters (Startup from Scratch)
- **Goal:** Build startup from zero
- **Pain:** (Needs testing)
- **Needs:** Full venture builder flow

### Persona 5: The Established Founder
- **Goal:** Has solution, needs business case
- **Pain:** Starting from middle, not beginning
- **Needs:** Ability to skip early stages

---

## Usability Heuristic Scores

| Heuristic | Score | Issues |
|-----------|-------|--------|
| 1. Visibility of system status | 3/5 | Progress unclear, no clear feedback |
| 2. Match between system and real world | 4/5 | Good language, but PWS terms confuse newcomers |
| 3. User control and freedom | 2/5 | Hard to undo, unclear navigation |
| 4. Consistency and standards | 2/5 | Buttons behave differently |
| 5. Error prevention | 2/5 | Easy to click wrong thing |
| 6. Recognition rather than recall | 3/5 | Too many options to remember |
| 7. Flexibility and efficiency | 4/5 | Power users can do a lot |
| 8. Aesthetic and minimalist design | 2/5 | Too cluttered |
| 9. Help users recognize errors | 2/5 | Unclear when something fails |
| 10. Help and documentation | 1/5 | No onboarding, no help |

**Overall Score: 25/50 (Needs significant improvement)**

---

## Test Results

### Task: Start Red Team Analysis
- **User:** Database Guy (expert)
- **Failure Rate:** 100% (1/1 users failed)
- **Root Cause:** No default selection

### Task: Find Build Venture Feature
- **User:** Contessa (novice)
- **Failure Rate:** 66% partial (found but struggled)
- **Root Cause:** Hidden in menu

### Task: Download Chat for Sharing
- **User:** Contessa
- **Failure Rate:** 66% partial (got .md, needed .docx)
- **Root Cause:** Wrong export format

---

## Metrics to Track

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Time to first meaningful output | < 2 min | Unknown | Needs measurement |
| Task completion rate (Red Team) | > 90% | 0% | Critical |
| Feature discovery (Build Venture) | < 30 sec | > 2 min | Needs fix |
| User satisfaction (Build Venture) | 4/5 | ~3/5 | Needs improvement |

---

## Key Quotes for Reference

**On confusion:**
> "I had no idea what to do." - Database Guy

**On buttons:**
> "I'm not sure what to do with them." - Contessa

**On onboarding:**
> "How would they know where to start?" - Contessa

**On expectations:**
> "I'm expecting me red teamed... without pressing any other buttons." - Database Guy

**On value:**
> "So impressed... the research part was amazing." - Contessa

**On methodology barrier:**
> "For someone who hasn't been in any of professor Aronhime's classes, doesn't know what these different workshops are." - Contessa

---

## Closing Issues

When closing an issue, update this document with:
1. Resolution date
2. Fix description
3. Commit hash or PR link
