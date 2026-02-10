---
description: Team meeting insights (Feb 2025) — validated user feedback and strategic direction
---

# Mindrian Development Brief: Team Meeting Insights to Action

**Source:** Team meeting (Feb 2025) with Lawrence Aronhime (lead tester/professor), Contessa St. Clair (student tester), Jonathan Edwards (developer), David Calvo (developer), Leah (tester), Yonatan Sagir (lead developer).

**Purpose:** Validated user feedback and strategic direction extracted from a live team meeting. Use to drive both immediate bug fixes and longer-term R&D decisions.

---

## PART 1: IMMEDIATE ACTIONS (This Sprint)

### 1.1 [P0] Research Button — Unreliable Source Quality

**What testers said:**
- Contessa: "Sometimes works, sometimes doesn't. There was one time where I clicked it pretty early on and it showed up with two sources, but they weren't real sources."
- Lawrence: "The research button has never worked like it should."
- Contessa noted that having more conversation context before clicking Research improved results.

**Action:**
- Check how conversation history is passed to the research call
- Add URL validation — reject results pointing to domain homepages
- Add minimum-context guard: if < 3 exchanges, warn or auto-summarize
- **NOTE:** The new Deep Research Pipeline (R&D/11) addresses this with Claude planning + fidelity anchoring

**Files:** `intelligence/pipelines/research_pipeline.py`, `mindrian_chat.py` (Research callback)

### 1.2 [P0] Fork — Cannot Navigate Back

**What testers said:**
- Lawrence: "It does know how to fork, but it's hard to go back."
- Leah: "I could not get back."

**Action:**
- Implement "Return to main thread" button after forking
- Store pre-fork state in `context_store`

**Files:** `mindrian_chat.py` (fork callbacks, `context_store` line 303)

### 1.3 [P1] Think Button — Indistinguishable from Main Chat

**What testers said:**
- Lawrence: "I can't figure out what THINK does."

**Recommendation:** Remove Think button. Fold reasoning behavior into main chat.

### 1.4 [P1] Visualization Export Buttons — Non-Functional

**What testers said:**
- Contessa: "I couldn't copy the code or export it."

**Action:** Fix copy/export on Mermaid diagram elements.

**Files:** Custom JSX elements, visualization callbacks

### 1.5 [P1] Synthesize Download — Not Working

**Action:** Fix download/export for synthesized output.

### 1.6 [P2] File Upload — PowerPoint Not Supported

**Action:** Add `.pptx` support via `python-pptx`.

---

## PART 2: UX ARCHITECTURE CHANGES (Next Sprint)

### 2.1 Embed Agents into Main Chat Flow

**Strongest team consensus.** Every tester independently said the same thing:
- Lawrence: "All those agents are useful for my class, but they really have to be embedded in the conversation."
- Contessa: "A lot of the user interface is kind of complicated."
- Leah: "I tried using a handful of them and honestly it was just confusing."

**Implementation:**
- Remove agent dropdown from default UI (keep as hidden/advanced toggle)
- Surface capabilities as contextual suggestions by function
- Rename: "Trending to the Absurd" → "Explore extreme scenarios", "Red Team" → "Challenge this", etc.
- Classroom mode toggle preserves full dropdown

### 2.2 "Stop Circling" — Convergence Mechanism

- Lawrence: "It needs to say, I'm done asking you questions. Just give me the answer."
- David: "Sometimes it doesn't get that it's made its point."

**Action:** Add saturation detection in `smart_phase_tracker.py`, convergence button, prompt instructions.

### 2.3 Better Onboarding / First-Time User Experience

- Contessa: "If someone new came to use this, they don't know what all these different terms are."

**Action:** Interactive onboarding flow, conversational introduction, quick-start templates.

### 2.4 Response Detail Slider — PROTECT IT

- Lawrence: "The one button I use all the time is response detail, and that works well."
- **DO NOT CHANGE THIS.** Power user endorsement.

---

## PART 3: R&D DIRECTION (Future Sprints)

### 3.1 MCP Server Architecture

- David: "Wrapping this entire thing as an MCP server. Very shallow interfaces, very deep functionality."
- Yonatan: "Wrapping it up as a set of skills as well."

**MCP tools to expose:** `mindrian_explore()`, `mindrian_research()`, `mindrian_breakthrough()`, `mindrian_invest()`, `mindrian_grade()`, `mindrian_redteam()`

### 3.2 LangGraph as Orchestration Standard

Standardize on LangGraph for all agent orchestration and state management.

### 3.3 Three Market Verticals

| Vertical | Primary User | Core Workflow |
|----------|-------------|---------------|
| Academic/Curriculum | Students, faculty | Problem exploration → refinement → validation |
| Tech Transfer/IP | University offices | Patent/disclosure → market analysis → commercialization |
| Consulting/Startup | Accelerators, investors | Pitch analysis → red team → investment decision |

### 3.4 Core Differentiator: "Sparks, Not Friends"

- Austin: "I get ideas that aren't even on the screen, but it's gotten me to think about things in ways that impact my work."
- Lawrence: "They're not looking for a friend. They're looking for sparks."

**ALL prompts must embody this.** Not agreeable, not chatty — a thinking partner that offers unexpected perspectives.

### 3.5 Pricing Model Direction

Freemium for students, BYOK for enterprise, simple usage tracking.

---

## EXECUTION ORDER

**Week 1:** Fix Research, Fork, visualization export, synthesize download, Think button
**Week 2:** Embed agents, convergence mechanism, onboarding, PowerPoint support
**Week 3+:** MCP interfaces, LangGraph standardization, usage metering

---

## SKILLS TO CONSULT

| Area | Skill |
|------|-------|
| Bug fixes | qa-analyzer |
| UI changes | chainlit-consultant |
| Architecture | mindrian-stack |
| MCP server | mcp-builder |
| Prompts | mindrian-larry |
| Graph ops | neo4j-schema-navigator |
