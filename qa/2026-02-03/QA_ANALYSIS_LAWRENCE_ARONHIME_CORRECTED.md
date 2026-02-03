# QA Analysis: Lawrence Aronhime Test Sessions (CORRECTED)
**Date:** February 3, 2026
**Original Analyst:** Mindrian-Team-QA-Analyzer
**Reviewed By:** Mindrian-Team-Stack-Architect, Mindrian-Team-Chainlit-Consultant
**Sessions Reviewed:** 3 (one multi-bot session + Think button test)
**Topic:** Higher Education in the Age of AI

---

## Executive Summary

9 issues identified across 3 test sessions. **The core conversational AI quality is strong** — the tester explicitly noted that the Nested Hierarchies bot's "questions and answers were really good" and the conversation "went on for much more than this." The issues are concentrated in the **tooling layer** (research, diagrams, phase tracking) rather than bot intelligence, which is good news — tooling bugs are more straightforward to fix.

---

## Issues by Priority

### 🔴 P0 — CRITICAL (1 issue)

#### Issue #1: Research Workflow Completely Broken
- **Severity:** P0 — Core feature unusable
- **Failure Mode:** Logic Failure
- **Reproducibility:** Always (100% — all 4 queries failed in both attempts)
- **Affects:** Research button, Minto Pyramid, Deep Analyze, any research-dependent action
- **Symptom:** All research results return: *"Error: Query cannot consist only of site: operators. Please provide search terms."*

**Root Cause (CORRECTED):**
The error occurs in the `deep_extract()` function, NOT in query decomposition. The function uses `site:{url}` without any search terms when extracting content from individual URLs.

**Location:** `tools/research_orchestrator.py:453-457`

```python
# CURRENT (broken) - Line 455
context = get_search_context(
    query=f"site:{source.url}",  # ❌ Only site: operator, no search terms
    max_results=1,
    max_tokens=3000,
)
```

**Recommended Fix:**
```python
# FIXED - Add source title as search context
from urllib.parse import urlparse
domain = urlparse(source.url).netloc
context = get_search_context(
    query=f"{source.title} site:{domain}",  # ✅ Title + site operator
    max_results=1,
    max_tokens=3000,
)
```

- **Fix Complexity:** Low (1-line change)
- **Confidence:** High
- **Impact:** This blocks ALL research functionality across all bots. No user can perform web research until fixed.

---

### 🟠 P1 — MAJOR (3 issues)

#### Issue #2: Mind Mapping / Idea Map Error — ⚠️ NEEDS STACK TRACE
- **Severity:** P1
- **Failure Mode:** Logic Failure (code error)
- **Reproducibility:** Always
- **Symptom:** `Mapping error: name 'model' is not defined`

**Root Cause (CORRECTED):**
**Original diagnosis was incorrect.** The `utils/diagrams.py` file does NOT contain an undefined `model` variable. The error likely occurs in:
1. The calling code path in `mindrian_chat.py` where mindmap generation is triggered
2. Where `generate_mindmap_prompt()` result is consumed and sent to Gemini
3. A different file entirely that calls diagram utilities

**Location:** Unknown — `utils/diagrams.py` confirmed NOT the source

**Action Required:**
- **Request full stack trace from Lawrence Aronhime**
- Search for where mindmap generation calls Gemini model
- Check `@cl.action_callback("map_ideas")` or similar handler

**Fix Complexity:** Medium (needs investigation first)

---

#### Issue #3: Think Button Response Truncation
- **Severity:** P1
- **Failure Mode:** UX Friction
- **Reproducibility:** Sometimes
- **Symptom:** Think It Through response cuts off mid-sentence at "Basic Understanding of AI Capabilities:" — the "Suggested Next Steps" and "Knowledge Analysis" sections were incomplete.

**Root Cause:** Either (a) `max_output_tokens` too low for the think_through action, or (b) streaming not completing final `await msg.update()`.

**Location:** `mindrian_chat.py:7161` — `@cl.action_callback("think_through")`

**Recommended Fix:**
```python
# In think_through handler
config={"max_output_tokens": 4000}  # Increase from default
# ... after streaming ...
await msg.update()  # Ensure this is called
```

**Fix Complexity:** Low
**Tester Note:** "Worked well as a summary and starting point. But it did not finish."

---

#### Issue #4: Phase Sidebar Out of Sync
- **Severity:** P1
- **Failure Mode:** UX Friction
- **Reproducibility:** Always (for Nested Hierarchies bot)
- **Symptom:** The checklist/roadmap on the right side "did not match anything" in the conversation.

**Root Cause (CORRECTED):**
Classic "new bot, forgot the plumbing" pattern. The Nested Hierarchies bot was added on **Feb 2** (commit `1b779664`), but the supporting infrastructure wasn't fully wired:

1. `WORKSHOP_PHASES["nested_hierarchies"]` may not exist in `mindrian_chat.py:428`
2. `smart_phase_tracker.py` lacks patterns for this bot's phases
3. `WorkshopRoadmap.jsx` receives incorrect or empty phase data

**Location:** Multiple files:
- `mindrian_chat.py:428` — `WORKSHOP_PHASES` dict
- `tools/smart_phase_tracker.py` — phase detection patterns
- `public/elements/WorkshopRoadmap.jsx` — sidebar rendering

**Recommended Fix:**
1. Add `WORKSHOP_PHASES["nested_hierarchies"]` with correct phase definitions
2. Add phase detection keywords to `smart_phase_tracker.py`
3. Verify sidebar receives phase data for this bot

**Fix Complexity:** Medium

---

### 🟡 P2 — MODERATE (2 issues)

#### Issue #5: Unwanted Auto-Switch from JTBD to Lawrence — ⚠️ SUSPICIOUS
- **Severity:** P2
- **Failure Mode:** UX Friction
- **Reproducibility:** Once (needs investigation)
- **Symptom:** After ~20 messages in JTBD, the system automatically switched to Lawrence without user action. Message displayed: *"🧠 Lawrence is now active. Context preserved from Jobs to Be Done (20 messages)"*

**Root Cause (CORRECTED):**
**Red flag: A 20-message threshold is NOT a documented feature.** This is suspicious behavior.

Possible causes:
1. **Undocumented message limit** — someone added a threshold without documentation
2. **Error handler fallback** — JTBD error silently falling back to Lawrence
3. **Graph router re-scoring** — `graph_router.py` deciding Lawrence is better fit
4. **Memory/context limit** — hitting a limit and resetting

**Location:** Investigate:
- `mindrian_chat.py:3581` — `handle_agent_switch()`
- `tools/graph_router.py` — any message count thresholds
- Error handlers that default to Lawrence

**Action Required:** Search codebase for:
```bash
grep -n "20\|twenty\|message.*count\|fallback.*lawrence" mindrian_chat.py tools/graph_router.py
```

**Fix Complexity:** Medium (needs investigation)

---

#### Issue #6: Reverse Salients Methodology Concern
- **Severity:** P2
- **Failure Mode:** Hidden Logic
- **Symptom:** Nested Hierarchies bot uses "Find Reverse Salients" as a phase, and the tester noted: *"AI mentioned reverse salients and it is looking for leverage points. But leverage points belong to wicked problems."*
- **Analysis:** The use of reverse salients within nested hierarchies analysis is actually defensible — it's finding the lagging component at each hierarchical level. However, the tester's point is valid from PWS methodology: leverage points (Donella Meadows) are specifically for wicked/complex problems. The prompt could be more precise about which concept it's applying and why.
- **Location:** `prompts/nested_hierarchies.py` — phase definitions
- **Recommended Fix:** Clarify in the prompt that the bot is using "reverse salient" in the Hughes/systems sense (lagging component), not conflating it with Meadows' "leverage points."

---

### 🟢 P3 — ENHANCEMENT (2 issues)

#### Issue #7: JTBD Framework Doesn't Fit Education Policy Topic
- **Severity:** P3 (methodology design)
- **Symptom:** Tester notes: *"I do not think it really works here."* The JTBD bot kept pushing "struggling moment" analysis when the topic (macro education policy) doesn't naturally fit a customer-centric product framework.
- **Analysis:** JTBD is designed for product/service innovation, not policy analysis. The bot correctly maintained its identity but created friction by forcing the lens on an ill-fitting topic.
- **Location:** `prompts/jtbd_workshop.py`
- **Recommended Fix:** Add a "framework fit" detection — when the topic is clearly better suited to another framework (e.g., Nested Hierarchies, Scenario Analysis), the bot should suggest switching rather than forcing JTBD.

#### Issue #8: JTBD Bot Too Rigid — Won't Provide Direct Answers
- **Severity:** P3 (UX design)
- **Symptom:** User repeatedly asked for direct input ("you tell me", "so what are the AI-proof jobs") and the bot deflected each time with framework language: *"That's the product-thinking trap, right there!"*
- **Analysis:** This is the Identity Preservation vs. UX Friction tension. The bot maintained its JTBD persona perfectly but frustrated the user. Workshop bots need a mode where they can provide substantive content WHILE maintaining their framework lens.
- **Location:** `prompts/jtbd_workshop.py`
- **Recommended Fix:** Add prompt guidance: "When the user asks you to provide your perspective directly, give a substantive answer THROUGH the JTBD lens rather than deflecting. Apply the framework yourself as a demonstration."

---

## Positive Findings

| What Worked Well | Details |
|---|---|
| **Nested Hierarchies conversation quality** | "Questions and answers were really good" — bot successfully guided hierarchical mapping of university system |
| **5-level hierarchy mapping** | Bot produced a clear, useful L1-L5 mapping when asked |
| **Reverse salient analysis** | Despite methodology concern, the actual analysis at each level was valuable |
| **Think button structure** | Good structured breakdown before truncation |
| **Context handoff** | When bot-switching occurred, context was preserved (20 messages transferred) |
| **Phase transition UX** | Phase 2/5 cards with progress indicators displayed correctly |

---

## Corrected Fix Priority Roadmap

| Priority | Issue | Location | Fix Complexity | Confidence | Fix First? |
|---|---|---|---|---|---|
| **P0** | Research Workflow broken | `research_orchestrator.py:455` | **Low** | ✅ High | ✅ YES |
| **P1** | Think button truncation | `mindrian_chat.py:7161` | **Low** | ✅ High | ✅ YES |
| **P1** | Phase sidebar sync | `WORKSHOP_PHASES` + `smart_phase_tracker` | **Medium** | ✅ High | Next |
| **P1** | Mind map `model` undefined | **Unknown** — needs stack trace | **Medium** | ⚠️ Low | ⏳ BLOCKED |
| **P2** | Auto-switch JTBD→Lawrence | Needs investigation | **Medium** | ⚠️ Low | Investigate |
| **P2** | Reverse salients methodology | `prompts/nested_hierarchies.py` | **Low** | ✅ High | Backlog |
| **P3** | JTBD framework fit detection | `prompts/jtbd_workshop.py` + routing | **Medium** | ✅ High | Backlog |
| **P3** | JTBD rigidity | `prompts/jtbd_workshop.py` | **Low** | ✅ High | Backlog |

---

## Action Items

### Immediate (Today)
- [ ] **Fix P0 Research** — Add `source.title` to `deep_extract()` query
- [ ] **Fix P1 Think Button** — Increase `max_output_tokens` to 4000+

### Requires More Info
- [ ] **P1 Mind Map** — Request full stack trace from Lawrence Aronhime
- [ ] **P2 Auto-Switch** — Investigate 20-message threshold source

### This Week
- [ ] **P1 Phase Sidebar** — Add `WORKSHOP_PHASES["nested_hierarchies"]`

---

## Patterns Observed

1. **Tooling > Intelligence:** All bugs are in the tooling/infrastructure layer, not in bot conversational quality. This is architecturally healthy — the AI reasoning is working well.
2. **Research system is a single point of failure:** Multiple features (Research, Minto, Deep Analyze, Mind Map) all depend on research_orchestrator.py. When it breaks, it cascades.
3. **New bot plumbing gap:** The Nested Hierarchies bot was added Feb 2 but supporting infrastructure (WORKSHOP_PHASES, phase tracker) wasn't fully wired. Classic pattern.
4. **Bot personality vs. helpfulness tension:** JTBD shows the friction between strict framework adherence and user-friendly content delivery. This is a design challenge, not a bug.

---

*Report corrected by Mindrian-Team-QA-Analyzer with input from Mindrian-Team-Stack-Architect*
