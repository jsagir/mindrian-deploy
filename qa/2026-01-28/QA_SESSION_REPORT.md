# QA Session Report — January 28, 2026

**Source:** Lawrence Aronhime testing sessions
**Fixed by:** Sagir + Claude Code
**Deploy:** https://mindrian.onrender.com

---

## Bugs Reported & Resolutions

### Bug #1: Research Button Returns 0 Sources
**Severity:** CRITICAL
**Root Cause:** Two issues found:
1. **API key loading** — Keys were configured in Render but no diagnostic logging existed to verify they loaded at runtime.
2. **UX confusion** — Research button ran a full 7-phase Minto Pyramid pipeline (SCQA → Beautiful Questions → Sequential Thinking → Matrix → Tavily → Synthesis). Sources were fetched but buried inside a structured analysis. If any step failed silently, the result showed "Total sources: 0".

**Fix Applied:**
- Added startup API key diagnostic logging — all keys now print status on boot (masked for security)
- Added error logging to Tavily search calls inside the research pipeline
- See Bug #2 for the UX fix

**Files Changed:** `mindrian_chat.py` (lines 39-56, startup diagnostics)

---

### Bug #2: Research Button Does Wrong Thing (UX Mismatch)
**Severity:** CRITICAL
**What Lawrence Expected:** "Show me relevant sources with clickable links"
**What System Did:** Ran Minto Pyramid analysis with Beautiful Questions framework

**Fix Applied:** **Sources-First approach (Option B/C from QA report)**
- **Lawrence mode** (`simple_mode: True`): Research button now:
  1. Composes a search query from conversation context (via Gemini)
  2. Runs Tavily search (up to 8 results)
  3. Shows sources with **clickable links**, titles, and snippets
  4. Offers a **"Deep Analyze These Sources"** button for optional Minto Pyramid
- **Playground mode** (`simple_mode: False`): Unchanged — full Minto Pyramid pipeline

**Files Changed:** `mindrian_chat.py`
- New function: `_research_sources_first()` — sources-first pipeline
- New callback: `@cl.action_callback("deep_research_full")` — optional deep analysis
- Modified: `on_deep_research()` — routes to sources-first or full pipeline based on `simple_mode`

---

### Bug #3: "Next Phase" Announces Wrong Phase Number
**Severity:** CRITICAL (reported) → MEDIUM (actual)
**Root Cause:** **Not a code bug.** Phase counter is session-based and only increments when "Next Phase" is clicked. The conversation content may advance naturally past multiple phases, but the counter stays at the last clicked position. Lawrence saw "Phase 2" because he had only clicked Next Phase once.

**Fix Applied:** Improved phase announcement to be clearer:
- Now shows: `"Moving to Phase 3/8: Domain Mapping (2 of 8 phases completed)"`
- Shows progress fraction so users understand where they are
- Changed prompt from "Let's continue with the next phase" to "What would you like to explore in this phase?" (avoids confusion about needing to type "continue")

**Files Changed:** `mindrian_chat.py` (phase announcement in `on_next_phase`)

---

### Bug #4: API Keys Configured But Not Working
**Severity:** CRITICAL
**Root Cause:** Same as Bug #1. Keys were set in Render dashboard but no way to verify runtime loading.

**Fix Applied:** Startup diagnostic now logs all key statuses. Check Render logs after deploy to verify:
```
==================================================
API KEY DIAGNOSTIC
==================================================
  ✅ GOOGLE_API_KEY: AIzaSy...key_
  ✅ TAVILY_API_KEY: tvly-d...89ab
  ❌ SERPAPI_API_KEY: NOT FOUND
  ...
==================================================
```

**Verify after deploy:** Check Render logs for the diagnostic block. Any ❌ means the key isn't reaching the runtime.

---

### Bug #5: User Must Type "continue" After Button Click
**Severity:** HIGH
**Root Cause:** **Not a code requirement** — callbacks auto-return. But two text strings gave the impression:
1. Stop handler said: "You can continue or ask something else"
2. Phase transition said: "Let's continue with the next phase"

**Fix Applied:**
- Stop message changed to: "Ready for your next message." + Research/Synthesize buttons
- Phase transition changed to: "What would you like to explore in this phase?"
- No text anywhere now suggests typing "continue"

**Files Changed:** `mindrian_chat.py` (stop handler, phase announcement)

---

### Bug #6: Task Panel Not Synced With Conversation
**Severity:** HIGH
**Root Cause:** Task panel was only updated when "Next Phase" button was clicked. Normal messages didn't refresh the panel, so spinning indicators could get stale.

**Fix Applied:** Task panel now refreshes on every message for workshop bots:
- After each response, if the bot has phases, the task list is rebuilt from session state
- Completed phases show ✅, current phase shows 🔄, upcoming shows ⚪
- This ensures the panel always reflects the current state

**Files Changed:** `mindrian_chat.py` (added task panel refresh in `on_message` handler)

---

## Architectural Questions — Status

| Question | Answer |
|----------|--------|
| How should LangExtract integrate with Neo4j LazyGraph? | **Already integrated.** LangExtract's `instant_extract()` IS Layer 0 (regex, <5ms). Neo4j LazyGraph is Layer 1. They already run together on every message. |
| Should we use LangExtract + Neo4j, or + FileSearch, or all three? | **All three already wired.** The Example button demonstrates the full hybrid: LazyGraph → FileSearch → Tavily → Gemini synthesis. |
| What structured fields should LangExtract pull? | Currently extracts: statistics, assumptions, problems, solutions, questions, sources, confidence signals. This is sufficient for button spawning. |

---

## Summary of All Changes in This Session

| Commit | What Changed |
|--------|-------------|
| Previous session | Slider default→1, simple_mode wiring, Research+Deep Research merge, Example button 5-step pipeline |
| This session | API diagnostics, Sources-First research, phase clarity, "continue" removal, task panel sync |

---

## Updated Test Guide

### Test 1: API Keys Verified
1. Deploy to Render
2. Check Render logs (App tab)
3. **You should see:** API KEY DIAGNOSTIC block with ✅ for configured keys

### Test 2: Research Shows Sources (Lawrence)
1. Open Mindrian, stay on Lawrence
2. Discuss a topic (e.g., "urban farming economics")
3. Click 🔍 Research
4. **You should see:**
   - [ ] Search query displayed
   - [ ] 5-8 sources with **clickable links**
   - [ ] Title + snippet for each source
   - [ ] "Deep Analyze" button offered (optional)

### Test 3: Research Full Pipeline (Playground)
1. Switch to Larry Playground
2. Click 🔍 Research
3. **You should see:**
   - [ ] Full Minto Pyramid pipeline (SCQA, Beautiful Questions, etc.)
   - [ ] Sources > 0 (if Tavily key is configured)

### Test 4: Phase Tracking Clear
1. Open a workshop bot (TTA, JTBD, etc.)
2. Click Next Phase
3. **You should see:**
   - [ ] "Moving to Phase 2/8: [Name]" (with fraction)
   - [ ] "(1 of 8 phases completed)"
   - [ ] Task panel updates on the right
   - [ ] No instruction to type "continue"

### Test 5: Task Panel Stays Synced
1. In a workshop bot, send 3-4 messages
2. **You should see:**
   - [ ] Task panel refreshes after each message
   - [ ] Current phase indicator stays accurate
   - [ ] No stale spinning indicators

### Test 6: No "Continue" Required
1. Click any button (Research, Next Phase, Example)
2. **You should see:**
   - [ ] Results appear immediately
   - [ ] No prompt to type "continue"
   - [ ] Buttons offered for next actions

---

## Known Issues (Don't Report These)

- Slider is still in Settings, not on the main page (known, pending)
- After a server deploy/restart, refresh the page — old session buttons won't work (Render limitation)
- Voice input is experimental
- SERPAPI, FRED, BLS, Kaggle keys may not be configured yet (research buttons for those APIs will show errors)

---

*Report generated: 2026-01-28. Covers fixes for all 6 bugs from Lawrence's testing session.*
