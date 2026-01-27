# QA Feedback vs. Changes Made — 2026-01-27

## Status Key

| Symbol | Meaning |
|--------|---------|
| DONE | Fully implemented in today's commits |
| PARTIAL | Partially addressed by today's work |
| NOT CHANGED | Not addressed — remains as-is for future work |

---

## 1. Make the "detail/complexity slider" visible and usable

### 1a. Put slider on front/main page
- **Status:** NOT CHANGED
- **Current state:** Slider is in Chainlit Settings panel (`response_detail`, line 894). Initial value = 5, range 1-10.
- **What's needed:** Move slider to primary chat view header or input area. Requires Chainlit UI customization (not a Python-only change).
- **Gap:** Chainlit's settings panel is the only built-in location for sliders. Moving it to the main view requires custom JS/CSS or a Chainlit plugin.

### 1b. Default slider to 1
- **Status:** NOT CHANGED
- **Current state:** Default is `initial=5` (line 897 of `mindrian_chat.py`).
- **What's needed:** Change `initial=5` to `initial=1`. This is a one-line change but was not part of today's scope.
- **When expected:** Next UI pass.

---

## 2. Reduce button overload on main chat

### 2a. Remove/relocate most bottom buttons
- **Status:** NOT CHANGED
- **Current state:** All action buttons are created in `on_chat_start()` and shown on every message.
- **What's needed:** Reduce always-visible buttons to: Research, Synthesize, (optionally New Chat/Clear Context, Example). Move rest to "More options" menu.
- **Gap:** Requires refactoring `on_chat_start()` button creation + possibly Chainlit custom component for "More..." menu.

### 2b. Limit suggested agent buttons to 1-2
- **Status:** DONE (was already in place)
- **Current state:** `suggest_agents_from_context()` has `max_suggestions=2` (line 916). Called with `max_suggestions=2` at line 4486.
- **What today improved:** Extraction-driven scoring makes the 2 suggestions *smarter* — Red Team when assumptions pile up, Ackoff when solution-jumping, TTA when forward-looking.
- **What QA should see:** At most 2 agent suggestion buttons, now more contextually relevant.

### 2c. Move secondary actions into "More options" menu
- **Status:** NOT CHANGED
- **Current state:** Usage metrics, feedback analytics, etc. are all primary buttons.
- **What's needed:** Chainlit doesn't natively support kebab/dropdown menus for actions. Would need custom UI component.
- **Gap:** Chainlit limitation. Could group under a single "Advanced" action that shows sub-actions.

---

## 3. Fix naming confusion: Research vs Deep Research vs Think

### 3a. Rename/consolidate Research and Deep Research
- **Status:** NOT CHANGED
- **Current state:** Two separate callbacks: `deep_research` (line 3033) and `gemini_deep_research` (line 3695). Plus 6 new specific research tool buttons (ArXiv, Patents, Trends, Gov Data, Datasets, News).
- **What's needed:** Consolidate into one "Research" button with sub-modes, or remove the generic one.
- **Gap:** Today's work *added* more specific research buttons (which is good for precision) but didn't consolidate the existing generic ones. Net button count increased.

### 3b. Clarify what "Think" does
- **Status:** NOT CHANGED
- **Current state:** `think_through` callback at line 3906. No tooltip explaining what it does.
- **What's needed:** Add tooltip/description text, or move behind Advanced menu.

---

## 4. Keep "Synthesize" as core, always-available feature

### 4a. Pin Synthesize in main chat
- **Status:** DONE (already in place)
- **Current state:** `synthesize_conversation` callback at line 2755. Button created in `on_chat_start()`.
- **No change needed:** Already always visible.

### 4b. Improve naming: "Synthesize" vs "Summarize"
- **Status:** NOT CHANGED
- **Current state:** Button label says "Synthesize".
- **What's needed:** Team decision on label. Consider tooltip "Summary + next steps".

---

## 5. Move slider + button simplicity into a "User mode"

### 5a. Add Simple / Advanced mode toggle
- **Status:** NOT CHANGED
- **Current state:** No mode toggle exists. All users see the same buttons.
- **What's needed:** A toggle (or profile-based config) that:
  - Simple mode: slider=1, minimal buttons (Research, Synthesize, Example)
  - Advanced mode: all buttons visible, slider unlocked
- **Gap:** This is a significant UI architecture change. Could be implemented as two ChatProfiles (e.g., "Lawrence" vs "Larry Playground") or as a settings toggle.

---

## 6. Multi-agent analysis: integrate better or de-emphasize

### 6a. Reduce prominence of Multi-agent analysis
- **Status:** NOT CHANGED
- **Current state:** `multi_agent_analysis` button created in `on_chat_start()` (line 2032). Always visible.
- **What's needed:** Only show when high confidence it's useful; add preview text.

### 6b. Shorten output when slider is low
- **Status:** NOT CHANGED
- **Current state:** Multi-agent output does not respect `response_detail` slider.
- **What's needed:** Read slider value in multi-agent handler and adjust output length.

---

## 7. Dropdown agents: keep but improve discovery

### 7a. Keep dropdown for power users
- **Status:** DONE (already in place)
- **Current state:** ChatProfile dropdown contains all 11 bots. Always available.

### 7b. Make hover descriptions contextual
- **Status:** PARTIAL
- **Current state:** Dropdown descriptions are static (set in `BOTS` dict). But today's extraction-driven agent suggestions now include contextual reason tooltips.
- **What improved:** Suggested agent buttons show *why* they're suggested based on conversation content. The dropdown itself is still static.
- **Gap:** Dropdown descriptions can't dynamically change in Chainlit.

### 7c. Plan for 50 agents (search + favorites + recommended)
- **Status:** NOT CHANGED
- **Current state:** 11 bots, flat dropdown.
- **What's needed:** Future architecture consideration. Not urgent at current scale.

---

## 8. PDF/Images limitations: set expectations clearly

### 8a. Communicate that images inside PDFs not supported
- **Status:** NOT CHANGED
- **Current state:** PDF text extraction works (`utils/file_processor.py`). No warning about embedded images.
- **What's needed:** On upload, show: "Text extracted. Images inside PDFs not supported yet."
- **Gap:** Small change in file upload handler. Not part of today's scope.

---

## 9. Voice input: stabilize + add reliable stop control

### 9a. Clear Stop/Cancel for voice mode
- **Status:** NOT CHANGED
- **Current state:** Voice handlers exist (`on_audio_start/chunk/end`). Stop behavior relies on Chainlit's built-in controls.
- **What's needed:** Prominent stop button, ESC key handler, no stuck states.
- **Gap:** Requires Chainlit UI customization or bug fixes in audio handling.

### 9b. "Voice is experimental" messaging
- **Status:** NOT CHANGED
- **What's needed:** Add banner or tooltip when voice mode is activated.

---

## 10. Links in research output: usability improvement

### 10a. Make links clickable, add "copy citations" button
- **Status:** PARTIAL
- **Current state:** Research results are rendered as markdown, which Chainlit renders with clickable links. The new research tools (ArXiv, Patents, etc.) include formatted links.
- **What improved:** New research tool outputs include structured markdown with clickable URLs and source attribution.
- **Gap:** No "copy all citations" button. Would need a post-processing action.

---

## 11. Metrics/feedback controls: hide from normal users

### 11a. Move Usage metrics / Feedback analytics out of primary UI
- **Status:** NOT CHANGED
- **Current state:** `show_feedback_dashboard` (line 2068) and `show_usage_metrics` (line 2084) are action callbacks, presumably shown as buttons.
- **What's needed:** Move behind Admin/Dev menu or remove from default button set.

---

## 12. MVP UI proposal: clean + minimal + context suggestions

### Status: PARTIAL (backend intelligence improved, UI layout unchanged)

| MVP Element | Status |
|-------------|--------|
| Always visible: Research, Synthesize, New Chat | NOT CHANGED (all buttons still visible) |
| Context-suggested: 1-2 agent buttons | DONE (max_suggestions=2, now smarter with extraction) |
| Dropdown: agents list for power users | DONE (already exists) |
| Slider: visible + default 1 | NOT CHANGED (hidden in settings, default=5) |

**What today's work contributes to MVP:**
- The intelligence layer makes context-suggested agents significantly better (item 2b, 7b)
- Research tool suggestions are now data-driven, not just keyword-based
- Coaching quality improves without any UI changes

**What still needs a UI pass:**
- Button reduction (items 2a, 2c, 3a, 6a, 11a)
- Slider visibility + default (items 1a, 1b)
- Simple/Advanced mode (item 5a)
- Voice stability (item 9)
- PDF upload messaging (item 8)

---

## Summary: What Was Done vs What Was Requested

| Category | Requested Items | Done | Partial | Not Changed |
|----------|----------------|------|---------|-------------|
| Slider visibility/default | 2 | 0 | 0 | 2 |
| Button overload reduction | 3 | 1 | 0 | 2 |
| Research naming confusion | 2 | 0 | 0 | 2 |
| Synthesize pinning | 2 | 1 | 0 | 1 |
| Simple/Advanced mode | 1 | 0 | 0 | 1 |
| Multi-agent de-emphasis | 2 | 0 | 0 | 2 |
| Agent dropdown improvement | 3 | 1 | 1 | 1 |
| PDF upload messaging | 1 | 0 | 0 | 1 |
| Voice stabilization | 2 | 0 | 0 | 2 |
| Link usability | 1 | 0 | 1 | 0 |
| Metrics/feedback hiding | 1 | 0 | 0 | 1 |
| MVP UI layout | 1 | 0 | 1 | 0 |
| **TOTAL** | **21** | **3** | **3** | **15** |

**Today's focus was backend intelligence, not UI layout.** The 15 "not changed" items are primarily UI/UX changes that require a dedicated UI refactoring pass.
