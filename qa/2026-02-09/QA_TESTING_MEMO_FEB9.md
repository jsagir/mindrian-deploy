# MINDRIAN QA TESTING MEMO
## February 9, 2026 Release

**@Adam Peters @Austin Granmoe**

This release addresses Lawrence Aronhime's comprehensive testing feedback (16 issues) plus adds new capabilities. Here's what changed, why, and what to test.

---

## WHAT'S NEW IN THIS RELEASE

### Summary of Changes (Last 3 Hours)

| Commit | What | Why |
|--------|------|-----|
| `0860d5d` | Idea Filtering + Swarm Orchestrator | User can star/prune ideas and apply as AI context |
| `f5c6a54` | Aronhime QA Fixes | 52 ideas → 10, toolbar contrast, scroll, star/prune callbacks |
| `a3282c7` | Breakthrough Button + Research Logging | Auto-orchestration trigger, better error messages |

---

## YOUR FEEDBACK → OUR RESPONSE

### From Adam & Austin (Feb 8)

| Feedback | Response | Status |
|----------|----------|--------|
| "Can't branch off to explore ideas" | Added 🍴 Fork button | ✅ Shipped |
| "Ideas get lost in conversation" | Added 💡 Ideas canvas | ✅ Shipped |
| "Which agent is responding?" | Added agent badges | ✅ Shipped |
| "Can't mark ideas as good/bad" | Added ⭐ star and 🗑️ prune | ✅ Fixed callbacks |
| "Login keeps blinking/looping" | Fixed database schema | ✅ Shipped |

### From Lawrence Aronhime (Feb 9) - NEW

| Issue | Fix | Logic |
|-------|-----|-------|
| **BUG-101: Star/X buttons don't work** | Added error logging + try/except to callbacks | Buttons were calling actions but no feedback. Now shows confirmation message. |
| **BUG-104: 52 ideas extracted** | PWS-aware ranking + limit to 10 | Algorithm scores ideas by PWS keywords (opportunity, gap, pain), penalizes vague words (maybe, perhaps). Top 10 only. |
| **BUG-108: Canvas doesn't scroll** | Changed overflow to "auto" | CSS fix in IdeaCanvas.jsx |
| **BUG-109: Toolbar hard to see** | Dark theme (#1f2937) | Changed from light gray (#f9fafb) to dark background with white text |

### NEW FEATURE: Apply Ideas to AI

| What | Why | How |
|------|-----|-----|
| **🎯 Apply to AI** button | User asked "starred ideas should focus AI, pruned should be avoided" | Starred → "FOCUS AREAS" in system prompt. Pruned → "AVOID TOPICS" in system prompt. |

**User Flow:**
1. Extract ideas (💡 Ideas button)
2. Star ⭐ ideas worth exploring
3. Prune 🗑️ dead-end ideas
4. Click 🎯 Apply to AI
5. AI now prioritizes starred, avoids pruned

---

## WHAT TO TEST (Priority Order)

### 1. IDEA CANVAS FIXES (P0)

**WHY:** Lawrence reported star/prune buttons did nothing, 52 ideas overwhelmed, toolbar invisible.

**TEST IT:**
1. Have a 5+ turn conversation mentioning problems, opportunities, assumptions
2. Click 💡 Ideas
3. Verify **10 or fewer ideas** appear (not 52)
4. Verify **toolbar is dark** with white text (not light gray)
5. Click ⭐ on an idea → Should see "⭐ Starred: [idea text]..." confirmation
6. Click ❌ on an idea → Should see "🗑️ Pruned: [idea text]..." confirmation
7. Scroll horizontally if many nodes

**✅ PASS IF:**
- [ ] 10 or fewer ideas extracted
- [ ] Toolbar clearly visible (dark background)
- [ ] Star button shows confirmation message
- [ ] Prune button shows confirmation message
- [ ] Canvas scrolls horizontally

---

### 2. APPLY IDEAS TO AI (NEW FEATURE)

**WHY:** User requested: "starred ideas as positive context, pruned as negative prompt"

**TEST IT:**
1. Extract ideas, star 2-3, prune 2-3
2. Click 🎯 Apply to AI button (in canvas footer)
3. Verify confirmation shows:
   - "🎯 Focus areas: [starred ideas]"
   - "🚫 Avoiding: [pruned ideas]"
4. Ask a follow-up question
5. Verify AI response focuses on starred topics, avoids pruned ones

**✅ PASS IF:**
- [ ] 🎯 Apply button visible in canvas footer
- [ ] Confirmation shows focus + avoid lists
- [ ] AI response reflects the filtering

---

### 3. BREAKTHROUGH BUTTON (NEW)

**WHY:** Auto-orchestration was designed but not wired to UI.

**TEST IT:**
1. Have a conversation about a problem
2. Look for 🚀 Breakthrough in action bar
3. Click it
4. Watch for multi-agent orchestration (shows stages, agents running)

**✅ PASS IF:**
- [ ] 🚀 Breakthrough button appears
- [ ] Clicking shows orchestration progress
- [ ] Final synthesis appears

---

### 4. CONVERSATION FORKING (From Feb 8)

**WHY:** You asked to explore "what if" directions.

**TEST IT:**
1. Start conversation (5+ messages)
2. Click 🍴 Fork
3. Chat in the fork
4. Look for "View All Branches" to switch back

**✅ PASS IF:**
- [ ] Fork creates separate branch
- [ ] Can switch between branches
- [ ] Each branch has distinct history

---

### 5. AGENT ATTRIBUTION (From Feb 8)

**WHY:** "Which agent said this?"

**TEST IT:**
1. Chat with Lawrence, then switch to TTA
2. Look at response headers

**✅ PASS IF:**
- [ ] Every AI response shows icon + name (e.g., "🧑‍🏫 Lawrence")

---

### 6. RESEARCH ERROR MESSAGES (Improved)

**WHY:** Previously showed generic "unexpected issue occurred"

**TEST IT:**
1. Click 🔍 Research on any topic
2. If it fails, check that error shows actual reason (not generic)

**✅ PASS IF:**
- [ ] Error messages are specific, not generic

---

## QUICK CHECKLIST (Print & Check)

```
IDEA CANVAS (Aronhime Fixes):
[ ] Ideas limited to ~10 (not 52)
[ ] Toolbar dark, text white
[ ] Star shows confirmation
[ ] Prune shows confirmation
[ ] Horizontal scroll works

APPLY TO AI (New):
[ ] 🎯 button in canvas footer
[ ] Shows focus/avoid summary
[ ] AI respects the filtering

BREAKTHROUGH (New):
[ ] 🚀 button in action bar
[ ] Shows orchestration stages
[ ] Produces synthesis

FORKING (Feb 8):
[ ] 🍴 Fork works
[ ] Branch switching works

ATTRIBUTION (Feb 8):
[ ] Agent icon+name on responses

LOGIN (Feb 8):
[ ] No blinking loop
[ ] Session persists
```

---

## STILL ON THE LIST (Not in This Release)

| Feature | Status | Notes |
|---------|--------|-------|
| BUG-102: "View All Branches" button | 🔍 Investigating | May be UI rendering issue |
| BUG-105: JTBD no guidance | Planned | Phase content enhancement |
| BUG-106: Example too concise | Planned | Expand example retrieval |
| BUG-107: Session duplication messages | 🔍 Investigating | "Welcome back" appearing multiple times |
| Topic blacklist UI | Backend ready | Frontend pending |
| Project folders | Wave 5 | Not started |

---

## THE LOGIC BEHIND THE FIXES

### Why PWS-Aware Ranking?

```python
def pws_score(idea):
    score = idea.confidence

    # Boost PWS-relevant ideas
    if "opportunity" in content: score += 0.1
    if "gap" in content: score += 0.1
    if "pain" in content: score += 0.1

    # Penalize vague ideas
    if "maybe" in content: score -= 0.1
    if "perhaps" in content: score -= 0.1

    return score
```

**Result:** Problems worth solving rise to top. Filler drops.

### Why Apply to AI?

The user insight was brilliant: "What if starred ideas became focus areas and pruned ideas became things to avoid?"

This maps directly to system prompt injection:

```
[FOCUS AREAS] (user-starred)
- The customer acquisition cost is too high
- There's an underserved market segment

[AVOID TOPICS] (user-pruned)
- We assumed pricing was the issue (dead end)
```

The AI now has explicit guidance on what the user cares about.

---

## IF SOMETHING BREAKS

1. Note exact steps
2. Screenshot if possible
3. Check `/api/health` (should show database connected)
4. Report in Slack or GitHub issue

---

**Questions? Ping the channel. Thanks for testing!**

*Generated: February 9, 2026*
*Commits: 0860d5d, f5c6a54, a3282c7*
