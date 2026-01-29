# QA Test Plan: P0-P2 Chainlit Features
**Date:** January 29, 2026
**Commit:** f8f3909
**Features:** Custom Elements, OAuth, LangGraph Viz, Forms

---

## Summary of Changes

This release adds advanced Chainlit features organized by priority:

| Priority | Feature | Status |
|----------|---------|--------|
| P0 | Custom JSX Elements | ✅ Done |
| P0 | ElementSidebar | ✅ Done |
| P1 | OAuth Authentication | ✅ Done |
| P1 | LangGraph Callback Handler | ✅ Done |
| P2 | OpenAI Realtime Evaluation | ✅ Documented |
| P2 | AskElementMessage Forms | ✅ Done |

---

## Test Cases

### TC-001: PhaseProgress Custom Element
**Priority:** High
**Feature:** Custom JSX Elements

**Steps:**
1. Select any workshop bot (e.g., Scenario Analysis)
2. Click "Show Progress" button

**Expected:**
- Interactive progress card appears
- Shows current phase highlighted with 🔵
- Completed phases show ✅
- "Help Me" and "Next Phase" buttons work
- Progress bar reflects completion percentage

**Fallback Test:**
- If JSX fails, text-based progress should appear

---

### TC-002: DIKWPyramid Interactive Element
**Priority:** High
**Feature:** Custom JSX Elements

**Steps:**
1. Select Ackoff bot
2. Click "Show DIKW Pyramid" button
3. Click on "Data" level in pyramid

**Expected:**
- Interactive pyramid appears with 4 levels
- Current phase highlighted (if applicable)
- Clicking level triggers `explore_dikw_level` callback
- Detailed explanation of clicked level appears
- "Back to Pyramid" button returns to main view

---

### TC-003: ElementSidebar for Workshop Bots
**Priority:** High
**Feature:** ElementSidebar

**Steps:**
1. Select Scenario Analysis bot
2. Look for sidebar on the right

**Expected:**
- Sidebar shows "📚 Scenario Analysis Resources"
- Quick reference section with methodology steps
- Phase checklist with current phase marked
- Checklist updates when advancing phases

**If no sidebar visible:**
- May require Chainlit 2.0+ with sidebar support
- Check `hide_cot` setting in config.toml

---

### TC-004: OAuth Authentication (Google)
**Priority:** High
**Feature:** OAuth
**Prerequisites:** Google OAuth configured in environment

**Steps:**
1. Clear browser cookies
2. Visit Mindrian
3. Click "Login with Google"
4. Complete Google authentication
5. Grant permissions

**Expected:**
- Redirect to Google login
- After auth, return to Mindrian
- User session established
- User metadata available (name, image)

**If OAuth not configured:**
- No login button should appear
- App should work without authentication

---

### TC-005: OAuth Authentication (GitHub)
**Priority:** High
**Feature:** OAuth
**Prerequisites:** GitHub OAuth configured in environment

**Steps:**
1. Clear browser cookies
2. Visit Mindrian
3. Click "Login with GitHub"
4. Complete GitHub authentication

**Expected:**
- Redirect to GitHub auth page
- After auth, return to Mindrian
- User session with GitHub username/avatar

---

### TC-006: Multi-Agent with Step Visualization
**Priority:** Medium
**Feature:** LangGraph Callback Handler

**Steps:**
1. Have a conversation about a problem
2. Click "Multi-Agent Analysis"
3. Select "Full Analysis"
4. Watch the UI during execution

**Expected:**
- Main step "Multi-Agent: Full Analysis" appears
- Nested steps for each agent execution
- Each agent step shows input/output
- Synthesis step at the end
- Final combined results message

---

### TC-007: Problem Definition Form
**Priority:** Medium
**Feature:** AskElementMessage Forms

**Steps:**
1. In any conversation, trigger problem form (developer action)
2. Or modify code to call `show_problem_form`

**Expected:**
- Form card appears with fields:
  - Problem Statement (required)
  - Who Experiences (required)
  - Impact
  - Current Solutions
  - Why Now
- Camera Test button appears after typing 20+ chars
- Validation shows errors for empty required fields
- Submit triggers `form_submit` callback
- Data stored in session as `problem_definition`

---

### TC-008: Scenario Setup Form
**Priority:** Medium
**Feature:** AskElementMessage Forms

**Steps:**
1. Select Scenario Analysis bot
2. Trigger scenario form (if wired to action)

**Expected:**
- Form card with fields:
  - Domain (required)
  - Focal Question (required)
  - Time Horizon (dropdown: 2030-2050)
  - Stakeholders
  - Decision Context
- Submit advances to Phase 2
- Sidebar checklist updates

---

### TC-009: Form Validation
**Priority:** Medium
**Feature:** AskElementMessage Forms

**Steps:**
1. Open Problem Definition form
2. Leave Problem Statement empty
3. Click Submit

**Expected:**
- Error message appears under field
- Form does NOT submit
- After filling required fields, submit works

---

### TC-010: Sidebar Phase Update
**Priority:** Medium
**Feature:** ElementSidebar

**Steps:**
1. Select workshop bot
2. Note sidebar checklist state
3. Click "Next Phase"
4. Check sidebar

**Expected:**
- Previous phase shows ✅
- Current phase shows 🔵 Current
- Checklist reflects actual progress

---

## Regression Tests

### RT-001: Existing Workshop Bots Work
**Steps:**
1. Test TTA, JTBD, S-Curve, Ackoff, Red Team bots
2. Verify conversation works normally
3. Verify phase progression works

**Expected:**
- All existing functionality preserved
- No errors from new code

---

### RT-002: Non-Workshop Bots Unaffected
**Steps:**
1. Select Lawrence bot
2. Have a conversation
3. Verify no phase-related UI appears

**Expected:**
- Lawrence works normally
- No sidebar (non-workshop bot)
- No phase buttons

---

### RT-003: Multi-Agent Still Works Without Viz
**Steps:**
1. Trigger multi-agent analysis
2. Verify results appear

**Expected:**
- Multi-agent works with or without LangGraph
- Graceful fallback if visualization fails

---

## Environment Requirements

| Feature | Required Variables |
|---------|-------------------|
| OAuth (Google) | `CHAINLIT_AUTH_SECRET`, `OAUTH_GOOGLE_CLIENT_ID`, `OAUTH_GOOGLE_CLIENT_SECRET` |
| OAuth (GitHub) | `CHAINLIT_AUTH_SECRET`, `OAUTH_GITHUB_CLIENT_ID`, `OAUTH_GITHUB_CLIENT_SECRET` |
| Multi-Agent | None (uses existing Gemini) |
| Custom Elements | Chainlit 2.0+ |

---

## Known Limitations

1. **Custom Elements**: Require Chainlit 2.0+ with JSX support
2. **ElementSidebar**: May not be available in all Chainlit versions
3. **OAuth**: Requires HTTPS in production
4. **Forms**: Currently need manual trigger (not exposed as buttons yet)

---

## Files Changed

| File | Type | Description |
|------|------|-------------|
| `mindrian_chat.py` | Modified | OAuth callback, form handlers, sidebar |
| `agents/__init__.py` | Modified | New exports |
| `agents/multi_agent_graph.py` | Modified | Step visualization functions |
| `.env.example` | Modified | OAuth variables documented |
| `public/elements/*.jsx` | New | 5 custom elements |
| `R&D/04_voice_improvements/README.md` | Modified | OpenAI evaluation |

---

## Quick Verification Checklist

- [ ] Workshop bots load correctly
- [ ] PhaseProgress element displays
- [ ] DIKWPyramid is interactive (click levels)
- [ ] Sidebar appears for workshop bots
- [ ] Sidebar updates on phase change
- [ ] OAuth login works (if configured)
- [ ] Multi-agent shows nested steps
- [ ] Form validation works
- [ ] No console errors in browser

---

## Sign-off

| Tester | Date | Status |
|--------|------|--------|
| | | |

---

*Generated: 2026-01-29*
