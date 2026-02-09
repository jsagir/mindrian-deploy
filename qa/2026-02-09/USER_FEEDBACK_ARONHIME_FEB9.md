# User Feedback Report - Lawrence Aronhime
**Date:** February 9, 2026
**Tester:** Lawrence Aronhime (Professor, Fashion Design)
**Session Type:** Side hustle exploration + technical testing

---

## Executive Summary

Testing revealed **16 issues** across 7 categories. Most critical: Ideas extraction produces 52 items (too many), star/X buttons don't work, and phase navigation provides no feedback.

---

## Issues by Priority

### P0 - CRITICAL (Blocking User Flow)

| ID | Issue | Description | Expected | Actual |
|----|-------|-------------|----------|--------|
| BUG-101 | Star/X buttons don't work | Clicked star and X on idea nodes | Toggle star, mark as pruned | Nothing happens |
| BUG-102 | Fork missing "View All Branches" | After clicking Fork | Show "View All Branches" button | No button appears |
| BUG-103 | Ideas not auto-extracting | Ideas button says "No ideas extracted" | Auto-extract from conversation | Must click "Extract Ideas Now" manually |

### P1 - HIGH (Major UX Problems)

| ID | Issue | Description | Expected | Actual |
|----|-------|-------------|----------|--------|
| BUG-104 | 52 ideas extracted - too many | Extraction produces overwhelming list | 5-10 key ideas | 52 ideas, not prioritized |
| BUG-105 | JTBD provides no guidance | Clicked JTBD, unclear what to do | Guided workflow | "1 of 7 phases completed" with no info |
| BUG-106 | Example too concise | Clicked Example multiple times | Detailed example with context | "Larry's Avant-Garde Solution (2023)..." one sentence |
| BUG-107 | Conversation lost but context kept | Multiple sessions | Continuous conversation | "Welcome back! Your conversation has been restored" x5 |
| BUG-108 | Canvas doesn't scroll horizontally | Long node content | Scrollable canvas | Information cut off |

### P2 - MEDIUM (UX Polish)

| ID | Issue | Description | Expected | Actual |
|----|-------|-------------|----------|--------|
| BUG-109 | Canvas toolbar hard to see | Top toolbar visibility | High contrast, visible | Light gray on white background |
| BUG-110 | Blue "analyzing" box unnecessary | Thinking indicator | Subtle or optional | Blue/white box feels redundant |
| BUG-111 | Copy shows white-on-black | Highlight text to copy | Plain text appearance | White text on black background |
| BUG-112 | Can't copy entire conversation | Export functionality | Copy full conversation | Only individual responses |

### P3 - LOW (Feature Requests)

| ID | Issue | Description | Suggestion |
|----|-------|-------------|------------|
| FR-101 | Click node to bring forward | Node visibility | Click should elevate node, not require drag |
| FR-102 | Mermaid diagram type selection | Visualization | Use mindmap when relevant to context |
| FR-103 | Opportunity extraction definition | PWS methodology | Extract "problems worth solving" per FileSearch definition |

---

## Detailed Issue Analysis

### 1. Ideas/Canvas System (BUG-101, 103, 104, 108, 109)

**Root Cause Analysis:**
- `star_idea` and `prune_idea` callbacks exist but may not be triggered correctly from IdeaCanvas.jsx
- Extraction uses simple pattern matching, not PWS-aware filtering
- Canvas lacks horizontal scroll CSS
- Toolbar uses low-contrast colors

**Recommended Fixes:**
```python
# Limit extraction to top 10 ideas by confidence
nodes = sorted(nodes, key=lambda x: x['confidence'], reverse=True)[:10]

# Add PWS filtering
pws_keywords = ["problem", "opportunity", "gap", "need", "pain point"]
```

```css
/* Canvas horizontal scroll */
.idea-canvas-container {
  overflow-x: auto;
  min-width: 100%;
}

/* Toolbar contrast fix */
.canvas-toolbar {
  background: #1a1a2e;
  color: #ffffff;
}
```

### 2. Fork System (BUG-102)

**Root Cause:** The "View All Branches" button uses `show_branch_selector` action name but the Fork confirmation message uses `show_branches`.

**Code Location:** `mindrian_chat.py` line 5500 vs line 14741 (now removed but may have left inconsistency)

### 3. JTBD/Workshop Flow (BUG-105)

**Root Cause:** Workshop phase transitions show status but don't provide guidance or content.

**User Quote:** "I clicked next phase and again it didn't give me any information; it just said '1 of 7 phases completed'"

**Recommended Fix:** Each phase transition should include:
1. What was accomplished
2. What's coming next
3. A guiding question or prompt

### 4. Example System (BUG-106)

**Root Cause:** Example retrieval returns truncated results.

**User Quote:** "I usually get a reference, but no detail, so it doesn't help me."

**Code Location:** `on_show_example` callback - needs to return full example content, not just title.

### 5. Session Persistence (BUG-107)

**User Quote:** "The context remained, but the conversation was lost"

**Evidence:** Multiple "Welcome back! Your conversation has been restored" messages appearing consecutively.

---

## Positive Feedback

| Feature | User Comment |
|---------|--------------|
| Node dragging | "It was really cool that I could move the nodes where I wanted them" |
| View formats | "I loved that I could view the idea chart in different formats" |
| Synthesize | "The synthesize button worked well. It downloaded a file and also included the synthesis in the main chat" |
| Fork | "I tried fork and it did work" |

---

## Test Scenario

**User Context:**
- 3 kids, full-time professor
- Fashion design program (technical illustration, concept development, capstone)
- Seeking $2000/month side income
- 2-4 hours daily available
- Prefers minimal people interaction
- Evening work required

**Conversation Flow:**
1. Uploaded resume → Lawrence responded with focused question
2. Identified tech illustration as evening-friendly skill
3. Explored where to find clients (Reddit groups)
4. Clicked JTBD → confusing output
5. Clicked Example → minimal content
6. Clicked Fork → worked but no branch management
7. Clicked Ideas → had to manually extract, got 52 ideas
8. Star/X buttons failed
9. Canvas toolbar invisible

---

## Action Items

| Priority | Item | Owner | Estimate |
|----------|------|-------|----------|
| P0 | Fix star/X button callbacks in IdeaCanvas.jsx | Dev | 30 min |
| P0 | Add "View All Branches" to Fork confirmation | Dev | 15 min |
| P0 | Auto-extract ideas (no manual click needed) | Dev | 1 hr |
| P1 | Limit ideas to top 10 with PWS filtering | Dev | 2 hr |
| P1 | Add phase guidance content to JTBD | Dev | 3 hr |
| P1 | Expand Example output (full content) | Dev | 1 hr |
| P2 | Fix canvas toolbar contrast | Dev | 15 min |
| P2 | Add horizontal scroll to canvas | Dev | 15 min |
| P2 | Investigate session duplication messages | Dev | 2 hr |

---

## Appendix: User Quotes

> "I clicked jobs to be done and it didn't really give me anything - I'm unsure if that was the right button to use but if it's not the right button then why is it an option?"

> "Each node had a star and X and neither button worked"

> "the top toolbar of the idea canvas is very difficult to see - it as light gray on a white background"

> "When you highlight and then copy all or part of a conversation, it would be nice if it showed up as normal plain text instead of white text on a black background"

---

*Generated: February 9, 2026*
*Based on: User testing session feedback*
