# PWS Consultant: Final Revised Implementation Plan

**Date:** 2026-02-05
**Sources:** Swarm implementation plan (5 agents), LangGraph architectural review (Opus 4.5), codebase analysis
**Architecture Decision:** STRUCTURED PROCESS (stage state machine with deterministic transitions), NOT WORKSHOP (loose conversational phases with LLM-detected transitions)
**Status:** Ready for implementation

---

## Executive Summary

The PWS Consultant is architecturally unique among Mindrian bots. Where workshops like TTA and JTBD use open-ended conversational phases tracked by LLM heuristics (`smart_phase_tracker.py`, `WorkshopRoadmap.jsx`), the PWS Consultant has **deterministic stage transitions**: intro leads to diagnostic (5 scored MCQs), which leads to consulting (open-ended). Forcing this through the workshop machinery causes a category error.

This plan replaces the workshop phase approach with a **3-stage state machine** managed via `cl.user_session`, adds the swarm's gap-closure tasks, and incorporates LangGraph-informed design improvements.

---

## LangGraph Expert Analysis (7 Questions)

### 1. State Machine Correctness

The proposed 3-stage linear graph (intro -> diagnostic -> consulting) is **correct and appropriate**. In LangGraph terms this would be a `StateGraph` with three nodes and two conditional edges. The key validation: each stage has a fundamentally different interaction pattern (free-form capture, structured MCQ, augmented consulting), which justifies discrete nodes rather than a single node with mode flags.

**Recommendation adopted:** Keep the 3-stage model. Do NOT collapse stages into flags.

### 2. Intro-to-Diagnostic Transition

Three options evaluated:

| Approach | Pros | Cons | Verdict |
|----------|------|------|---------|
| **Turn count (after 1-2 turns)** | Predictable, simple | User may not have described enough | Fragile |
| **LLM-based detection** | Semantically aware | Latency, non-deterministic, expensive per turn | Overkill |
| **User button click ("I'm ready for diagnosis")** | Deterministic, user controls pacing | Requires explicit UI | **RECOMMENDED** |

**Recommendation adopted:** Hybrid approach. After the first substantive user message about their challenge (turn 1+), show a "Ready for Diagnosis" button. The button is the trigger, but it only appears after the system has captured at least one challenge message. This maps to LangGraph's `interrupt_before` pattern (human-in-the-loop checkpoint before transitioning). The `submit_challenge` callback from `ChallengeIntro.jsx` already implements this pattern.

### 3. Consulting Sub-Modes

The consulting phase has three sub-modes: `expert_mode`, `tool_mode`, `synthesis`. In LangGraph, these would be modeled as **self-loop edges returning to the same node** (like a ReAct agent's tool loop), NOT as separate graph nodes.

**Recommendation adopted:** Sub-modes are flags within the consulting stage, not separate stages. The state holds `consulting_sub_mode: "normal" | "expert" | "tool" | "synthesis"` and the sub-mode reverts to `"normal"` after each interaction. This avoids state explosion.

### 4. Background Pipeline Modeling

In LangGraph, domain discovery and expert panel building would be **parallel fan-out nodes** using `asyncio.gather` that merge results into state before the next node executes. In Chainlit, the equivalent is `asyncio.create_task` with result collection.

**Recommendation adopted (revised from swarm):** The background pipeline currently fires in `process_consultant_turn()` during intro/diagnostic phases. The improvement is to:
1. Fire `build_expert_panel()` as a background task from `submit_challenge` callback (already in swarm Task 8)
2. Store the task handle in `cl.user_session.set("expert_panel_task", task)`
3. At diagnostic completion, `await` the task if not done, or read cached result if done
4. **Re-fire** expert panel with correct `problem_type_key` after diagnosis (currently fires with "undefined" default)

### 5. Equivalent LangGraph Graph

If this were LangGraph, the graph would be:

```
START -> intro_node -> [interrupt_before: human confirms challenge] -> diagnostic_node -> [conditional: q_count < 5 -> self-loop, q_count == 5 -> score_and_classify] -> consulting_node -> [conditional: sub_mode routing] -> consulting_node (self-loop) / END
                                                                                            |
                                                                                     parallel fan-out:
                                                                                     - domain_discovery
                                                                                     - expert_panel_build
                                                                                     (merge into state)
```

The Chainlit equivalent uses session state + action callbacks to achieve the same topology without a graph runtime.

### 6. AgentRole.STRUCTURED_PROCESS

The swarm proposed adding `AgentRole.STRUCTURED_PROCESS` to the `AgentRole` enum in `protocols/agent_registry.py`. LangGraph perspective: this is the **correct abstraction**. The distinction between `WORKSHOP` (phases tracked by LLM heuristics, user can skip/revisit) and `STRUCTURED_PROCESS` (deterministic stage transitions, action-callback-driven) is real and meaningful.

**Recommendation adopted:** Add `STRUCTURED_PROCESS = "structured_process"` to `AgentRole` enum. Change pws_consultant registration from `AgentRole.WORKSHOP` to `AgentRole.STRUCTURED_PROCESS`. This signals to the system that `smart_phase_tracker`, `WorkshopRoadmap`, and `phase_insights` should NOT be applied.

### 7. Anti-Patterns Identified

| Anti-Pattern | Where | Fix |
|-------------|-------|-----|
| **Workshop phases for non-workshop agent** | `WORKSHOP_PHASES["pws_consultant"]` has 6 phases, `smart_phase_tracker` will fire | Remove from `WORKSHOP_PHASES`, set `has_phases: False` (use stage machine instead) |
| **Session var read but never written** | `pws_challenge_description` read at line 4734 but never set | Set in `submit_challenge` callback (Task N1) |
| **Fire-and-forget without await** | Expert panel task created but `task.done()` never checked | Add explicit collection at diagnostic completion |
| **Unbounded consulting phase** | No exit condition, no session summary trigger | Add turn-count check + synthesis prompt after 15+ consulting turns |
| **Monolithic state** | All data in flat `cl.user_session` keys | Namespace PWS keys: `pws_stage`, `pws_diagnosis`, `pws_experts`, etc. |

---

## Consolidated State Schema

All PWS Consultant session state keys, namespaced to prevent collision:

```python
# Stage machine
cl.user_session.set("pws_stage", "intro")           # "intro" | "diagnostic" | "consulting"
cl.user_session.set("pws_sub_mode", "normal")        # "normal" | "expert" | "tool" | "synthesis"
cl.user_session.set("pws_intro_turn_count", 0)       # Turns in intro stage

# Challenge capture
cl.user_session.set("pws_challenge_description", "") # User's challenge text
cl.user_session.set("pws_challenge_signals", {})     # LangExtract instant signals

# Diagnostic
cl.user_session.set("pws_diagnostic_answers", [])    # List of answer dicts
cl.user_session.set("pws_diagnosis", {})             # score_diagnostic() result
cl.user_session.set("pws_diagnostic_context", "")    # Built context string for LLM

# Background pipelines
cl.user_session.set("pws_expert_panel_task", None)   # asyncio.Task handle
cl.user_session.set("pws_expert_panel_data", {})     # Completed expert panel
cl.user_session.set("pws_domain_discovery", {})      # Domain/subdomains
cl.user_session.set("pws_hybrid_context", "")        # Cached hybrid retrieval

# Consulting phase
cl.user_session.set("pws_consulting_turn_count", 0)  # Turns in consulting stage
cl.user_session.set("pws_expert_consult_count", 0)   # Number of expert consultations
```

---

## Final Task List: 18 Tasks, 4 Phases

### Phase 0: Architecture (New Tasks from Swarm + LangGraph)

---

#### Task N1: Add STRUCTURED_PROCESS Role + Stage State Machine
- **Files to modify:** `protocols/agent_registry.py`, `mindrian_chat.py`
- **Changes:**
  1. Add `STRUCTURED_PROCESS = "structured_process"` to `AgentRole` enum in `agent_registry.py`
  2. Change pws_consultant registration: `roles=[AgentRole.STRUCTURED_PROCESS, AgentRole.SUB_AGENT]`
  3. Set `has_phases=False` in pws_consultant registration (stage machine replaces phases)
  4. Add `CONSULTANT_STAGES` dict at module level in `mindrian_chat.py`:
     ```python
     CONSULTANT_STAGES = {
         'intro': {'name': 'Challenge Description', 'next': 'diagnostic', 'trigger': 'submit_challenge'},
         'diagnostic': {'name': 'Problem Diagnostic', 'next': 'consulting', 'trigger': 'diagnostic_answer'},
         'consulting': {'name': 'Guided Consulting', 'next': None, 'trigger': None},
     }
     ```
  5. Initialize `pws_stage = "intro"` in `on_chat_start` when `chat_profile == "pws_consultant"`
- **Dependencies:** None (first task)
- **Risk:** LOW -- enum addition is additive; registration change is safe

---

#### Task N2: Remove PWS Consultant from Workshop Machinery
- **Files to modify:** `mindrian_chat.py`
- **Changes:**
  1. Remove `"pws_consultant"` entry from `WORKSHOP_PHASES` dict (lines ~1043-1049)
  2. In `on_chat_start`, skip `create_workshop_roadmap()` call when `chat_profile == "pws_consultant"`
  3. In `on_message`, skip `smart_phase_tracker` / `phase_insights` logic when bot_id is `pws_consultant`
  4. Keep the `PWS_CONSULTANT_PHASES` list in `prompts/pws_consultant.py` as documentation but mark it deprecated
- **Dependencies:** N1
- **Risk:** LOW -- removing from dicts, adding skip conditions

---

#### Task N3: Add Stage-Aware Branch in on_message Handler
- **Files to modify:** `mindrian_chat.py`
- **Changes:**
  Add a stage-aware branch before the generic message handling for pws_consultant:
  ```python
  if chat_profile == "pws_consultant":
      stage = cl.user_session.get("pws_stage", "intro")
      if stage == "intro":
          # Capture challenge description, run instant_analyze, append to pws_challenge_description
          # Show "Ready for Diagnosis" button after first substantive message
          # Fire background pipelines (hybrid_retrieve, domain_discovery)
      elif stage == "diagnostic":
          # MCQ is handled by action callbacks; any free text here gets acknowledged
          # "The diagnostic questions are active -- please click your answer above"
      elif stage == "consulting":
          # Augment system prompt with pws_diagnostic_context + hybrid_context + expert panel
          # Increment pws_consulting_turn_count
          # At turn 15+, offer synthesis button
          # Normal streaming response with augmented prompt
  ```
  This replaces the generic `on_message` flow for this bot only.
- **Dependencies:** N1, N2
- **Risk:** MODERATE -- touches the main message handler; needs careful branching

---

#### Task N4: Fix pws_challenge_description Session Variable
- **Files to modify:** `mindrian_chat.py`
- **Changes:**
  1. In the intro stage branch of on_message (Task N3), set:
     ```python
     existing = cl.user_session.get("pws_challenge_description", "")
     cl.user_session.set("pws_challenge_description", existing + "\n" + message.content)
     ```
  2. Also set when `submit_challenge` callback fires (Task 1/3)
  3. Run `instant_analyze()` on the challenge text and store signals:
     ```python
     from tools.pws_consultant_pipeline import instant_analyze
     signals = instant_analyze(message.content, turn_count)
     cl.user_session.set("pws_challenge_signals", signals)
     ```
- **Dependencies:** N3
- **Risk:** LOW -- adding session writes that were missing

---

#### Task N5: Add Consulting Phase Exit Condition
- **Files to modify:** `mindrian_chat.py`
- **Changes:**
  1. Track `pws_consulting_turn_count` in consulting stage branch
  2. After 15+ turns, append to response: "We've covered a lot of ground. Would you like me to synthesize what we've discussed?"
  3. Show "Synthesize & Download" button automatically at turn 15+
  4. This prevents the LangGraph anti-pattern of infinite loops without exit conditions
- **Dependencies:** N3
- **Risk:** LOW

---

#### Task N6: Namespace All PWS Session Keys
- **Files to modify:** `mindrian_chat.py`
- **Changes:**
  1. Rename `diagnostic_answers` -> `pws_diagnostic_answers`
  2. Rename `pws_diagnosis` stays (already namespaced)
  3. Rename `expert_panel_data` -> `pws_expert_panel_data`
  4. Rename `pws_diagnostic_context` stays (already namespaced)
  5. Update all reads/writes across callbacks (`diagnostic_answer`, `consult_expert`, `submit_challenge`)
- **Dependencies:** N3, N4
- **Risk:** MODERATE -- touches multiple callbacks; search-and-replace across mindrian_chat.py

---

### Phase A: Foundation (Swarm Tasks, Revised)

---

#### Task 1: Extract Post-Diagnosis Completion Logic
- **Files to modify:** `mindrian_chat.py`
- **Changes:**
  Extract the `if question_number >= 5:` block (lines ~4646-4774) into:
  ```python
  async def _complete_pws_diagnosis(diagnosis: dict, answers: list, challenge_description: str):
  ```
  This function:
  - Sets diagnosis in session
  - Shows DiagnosisResult component
  - Builds tool actions
  - Collects expert panel (await task if running, or build fresh)
  - Shows ExpertPanel component
  - Builds diagnostic context for LLM
  - Transitions stage: `cl.user_session.set("pws_stage", "consulting")`
  - Streams Larry's diagnosis bridge message

  Enables reuse by: `diagnostic_answer` (normal flow), `direct_select_type` (skip diagnostic), `reclassify_problem` (redo)
- **Dependencies:** N1-N6
- **Risk:** MODERATE -- refactoring existing callback logic

---

#### Task 2: Enrich PROBLEM_TYPES + Add WORKSHOPS + SELECTION_CRITERIA
- **Files to modify:** `prompts/pws_consultant.py`
- **Changes:**
  1. Add per problem type: `cynefin_domain`, `innovation_tools` (list of 10-15 tools), `workshop_phase`, `techniques`
  2. Add `WORKSHOPS` dict (8 PWS curriculum workshops with deliverables, mechanisms, tools)
  3. Add `SELECTION_CRITERIA` dict (5 filtering criteria from Workshop 3)
  4. Export all new constants from `prompts/__init__.py`
- **Dependencies:** None (data-only, can run in parallel with N1-N6)
- **Risk:** SAFE -- additive data, no logic changes

---

#### Task 3: Create ChallengeIntro.jsx + Callbacks
- **Files to create:** `public/elements/ChallengeIntro.jsx`
- **Files to modify:** `mindrian_chat.py`
- **Changes:**
  1. JSX component with:
     - Multi-line textarea for challenge description
     - "Begin Diagnosis" submit button -> `submit_challenge` action callback
     - 4 muted type cards below ("Or if you already know your problem type:") -> `direct_select_type` callback
  2. In `on_chat_start` for pws_consultant: send ChallengeIntro element after welcome message
  3. `submit_challenge` callback:
     - Stores challenge in `pws_challenge_description`
     - Transitions `pws_stage` to `"diagnostic"`
     - Fires background expert panel task
     - Shows first DiagnosticFlow question
  4. `direct_select_type` callback:
     - Stores challenge (if provided) in `pws_challenge_description`
     - Skips diagnostic, calls `_complete_pws_diagnosis()` with manually selected type
     - Transitions `pws_stage` to `"consulting"`
- **Dependencies:** Task 1, Task 2, N1-N4
- **Risk:** MODERATE -- new JSX component + 2 new callbacks

---

### Phase B: Core Features (Swarm Tasks, Revised)

---

#### Task 4: Add Opportunity Strategist (Yellow Hat Expert)
- **Files to modify:** `prompts/pws_consultant.py` -> `build_expert_specs()`
- **Changes:**
  Add 6th expert archetype between Cross-Domain Innovator and type-specific expert:
  ```python
  {
      "role": "Opportunity Strategist",
      "icon": "\U0001F31F",
      "color": "#FFD700",
      "focus": f"Upside identification and value creation in {domain}",
      "approach": "Edward de Bono Yellow Hat, opportunity mapping, strategic positioning",
      "questions": [
          f"What's the biggest upside if this problem is solved in {domain}?",
          "Who would pay the most for this solution, and why?",
      ],
  }
  ```
- **Dependencies:** None (independent)
- **Risk:** SAFE -- additive to archetypes list

---

#### Task 5: Reclassify Escape Hatch
- **Files to modify:** `public/elements/DiagnosisResult.jsx`, `mindrian_chat.py`
- **Changes:**
  1. Add "This doesn't feel right" button to DiagnosisResult component
  2. Button triggers `reclassify_problem` action callback
  3. Callback shows 4 problem type cards for manual selection
  4. On selection, calls `_complete_pws_diagnosis()` with new type
  5. Re-fires expert panel with correct problem_type_key
  6. Stage stays at `"consulting"` (or transitions to it if still in diagnostic)
- **Dependencies:** Task 1, Task 3
- **Risk:** LOW

---

#### Task 6: Interpretive Bridge Message
- **Files to modify:** `prompts/pws_consultant.py`, `mindrian_chat.py`
- **Changes:**
  1. New function `build_bridge_prompt(diagnosis, challenge, enriched_type_data)`:
     - Uses enriched PROBLEM_TYPES data (Cynefin domain, tools, workshops)
     - Generates Larry-voice transition: "Very simply, based on what you've told me..."
     - Maps problem type to Cynefin quadrant
     - Suggests top 3 relevant workshops
     - Names the 2-3 most applicable tools
  2. Called from `_complete_pws_diagnosis()` after diagnosis reveal, before consulting begins
  3. Bridge message replaces the current generic "Now guide me using frameworks" prompt
- **Dependencies:** Task 1, Task 2
- **Risk:** LOW

---

#### Task 7: WorkshopTimeline.jsx
- **Files to create:** `public/elements/WorkshopTimeline.jsx`
- **Files to modify:** `mindrian_chat.py`
- **Changes:**
  1. Horizontal scrollable bar showing 8 PWS workshops
  2. Active/highlighted workshops based on diagnosed problem type (from `WORKSHOPS` data)
  3. Click a workshop -> suggestion to user (not navigation, since these are separate bots)
  4. Rendered inline after bridge message in `_complete_pws_diagnosis()`
  5. Uses data from Task 2's `WORKSHOPS` dict
- **Dependencies:** Task 2, Task 6
- **Risk:** LOW

---

#### Task 8: Wire Background Expert Panel into submit_challenge
- **Files to modify:** `mindrian_chat.py`
- **Changes:**
  1. In `submit_challenge` callback, launch expert panel build:
     ```python
     task = asyncio.create_task(build_expert_panel(
         user_message=challenge_text,
         problem_type_key="undefined",  # Updated later after diagnosis
         conversation_context="",
     ))
     cl.user_session.set("pws_expert_panel_task", task)
     ```
  2. In `_complete_pws_diagnosis()`, collect the task:
     ```python
     task = cl.user_session.get("pws_expert_panel_task")
     if task and not task.done():
         try:
             panel_data = await asyncio.wait_for(task, timeout=5.0)
         except asyncio.TimeoutError:
             panel_data = None
     elif task and task.done():
         panel_data = task.result()
     ```
  3. After diagnosis, **re-fire** expert panel with correct problem_type_key:
     ```python
     # Update experts with actual problem type
     updated_panel = await build_expert_panel(
         user_message=challenge_text,
         problem_type_key=diagnosis["primary"],
     )
     cl.user_session.set("pws_expert_panel_data", updated_panel)
     ```
  4. This follows LangGraph's pattern of parallel fan-out with state merge
- **Dependencies:** Task 1, Task 3, N4
- **Risk:** MODERATE -- async task management, race conditions possible

---

### Phase C: Polish (Swarm Tasks)

---

#### Task 9: Synthesize Expert Inputs Button (Minto Pyramid)
- **Files to modify:** `public/elements/ExpertPanel.jsx`, `mindrian_chat.py`
- **Changes:**
  1. Add "Synthesize All Perspectives" button to ExpertPanel component
  2. Button appears after 2+ expert consultations (`pws_expert_consult_count >= 2`)
  3. `synthesize_expert_inputs` callback structures synthesis via Minto Pyramid:
     - Governing Thought (what's the answer?)
     - Key Arguments (from each expert consulted)
     - Supporting Data (from research, diagnostic answers)
  4. Result streamed as Larry's synthesis with downloadable markdown
- **Dependencies:** Independent (but logically after expert panel works)
- **Risk:** LOW

---

#### Task 10: ConsultantBadge.jsx
- **Files to create:** `public/elements/ConsultantBadge.jsx`
- **Files to modify:** `mindrian_chat.py`
- **Changes:**
  1. Persistent badge showing diagnosed problem type on consulting phase messages
  2. Small colored indicator: icon + type name + confidence
  3. Rendered as inline element on each consulting-phase response
  4. Badge data from `cl.user_session.get("pws_diagnosis")`
- **Dependencies:** Task 1
- **Risk:** LOW

---

#### Task 11: Batch Neo4j Queries
- **Files to modify:** `tools/pws_consultant_pipeline.py`
- **Changes:**
  1. Replace sequential `query_neo4j()` calls in `execute_cypher_queries()` with:
     ```python
     async def execute_cypher_queries_parallel(queries):
         loop = asyncio.get_event_loop()
         tasks = [loop.run_in_executor(None, query_neo4j, q["cypher"], q["params"]) for q in queries if q["cypher"] != "__LAZY_LOOKUP__"]
         results = await asyncio.gather(*tasks, return_exceptions=True)
     ```
  2. Handle exceptions per-query (don't let one failure block others)
  3. Target: 5 queries in parallel instead of sequential = ~100ms instead of ~500ms
- **Dependencies:** Independent
- **Risk:** MODERATE -- changes async execution pattern, needs error handling

---

#### Task 12: Adaptive Diagnostic Q1 (Future/Deferred)
- **Files to modify:** `mindrian_chat.py`, `prompts/pws_consultant.py`
- **Changes:**
  1. After `submit_challenge`, use `instant_extract()` signals to adjust Q1
  2. If signals indicate high data/specificity -> bias Q1 toward well-defined detection
  3. If signals indicate future-oriented language -> bias Q1 toward undefined detection
  4. Requires signal-to-question mapping (new function in `pws_consultant.py`)
- **Dependencies:** Task 3, N4
- **Risk:** MODERATE -- alters diagnostic flow based on heuristics

---

### Phase D: Integration Validation

---

#### Task 13: End-to-End Flow Test
- **Files to create:** `tests/test_pws_consultant_flow.py` (if tests dir exists) or manual test script
- **Changes:**
  Verify complete flow:
  1. Start pws_consultant profile -> see ChallengeIntro
  2. Type challenge -> intro stage captures text, shows "Ready for Diagnosis"
  3. Click submit -> transitions to diagnostic, first MCQ appears
  4. Answer 5 MCQs -> scoring, DiagnosisResult, bridge message, ExpertPanel
  5. Stage = consulting, augmented prompt, tool buttons work
  6. Consult expert -> sub-mode switches and returns
  7. Reclassify -> re-runs diagnosis
  8. Turn 15+ -> synthesis offered
  9. WorkshopRoadmap does NOT appear (stage machine, not workshop)
  10. Phase tracker does NOT fire for pws_consultant
- **Dependencies:** All previous tasks
- **Risk:** LOW

---

## Dependency Chain

```
Phase 0 (Architecture):
  N1 (role + stages) -> N2 (remove workshop) -> N3 (on_message branch) -> N4 (fix session var)
  N5 (exit condition) depends on N3
  N6 (namespace keys) depends on N3, N4

Phase A (Foundation):
  Task 2 (enrich data) -- independent, start immediately
  Task 1 (extract function) depends on N1-N6
  Task 3 (ChallengeIntro) depends on Task 1, Task 2, N1-N4

Phase B (Core Features):
  Task 4 (Yellow Hat) -- independent, start anytime
  Task 5 (reclassify) depends on Task 1, Task 3
  Task 6 (bridge) depends on Task 1, Task 2
  Task 7 (timeline) depends on Task 2, Task 6
  Task 8 (expert wiring) depends on Task 1, Task 3, N4

Phase C (Polish):
  Task 9 (synthesize) -- independent
  Task 10 (badge) depends on Task 1
  Task 11 (batch queries) -- independent

Phase D:
  Task 12 (adaptive Q1) depends on Task 3, N4
  Task 13 (integration test) depends on all
```

## Recommended Execution Order

```
2 -> N1 -> N2 -> 4 -> N3 -> N4 -> N5 -> N6 -> 1 -> 3 -> 6 -> 5 -> 8 -> 7 -> 9 -> 10 -> 11 -> 12 -> 13
```

Rationale:
- Task 2 (data enrichment) has no dependencies and other tasks consume it
- N1-N6 establish the architectural foundation before any feature work
- Task 4 is independent and safe, slot it early
- Task 1 (refactor) unlocks Tasks 3, 5, 6, 8
- Task 3 (ChallengeIntro) is the critical path -- unlocks the full flow
- Tasks 9, 10, 11 are independent polish items
- Task 12 is deferred/future
- Task 13 validates everything

## Risk Summary

| Risk Level | Count | Tasks |
|-----------|-------|-------|
| SAFE | 2 | Task 2, Task 4 |
| LOW | 8 | N1, N2, N4, N5, Task 5, Task 7, Task 9, Task 10, Task 13 |
| MODERATE | 7 | N3, N6, Task 1, Task 3, Task 8, Task 11, Task 12 |
| HIGH | 0 | -- |

## Files Summary

### New Files (4)
| File | Task | Purpose |
|------|------|---------|
| `public/elements/ChallengeIntro.jsx` | Task 3 | Textarea + submit + direct-select type cards |
| `public/elements/WorkshopTimeline.jsx` | Task 7 | Horizontal 8-workshop bar |
| `public/elements/ConsultantBadge.jsx` | Task 10 | Problem type badge on messages |
| `tests/test_pws_consultant_flow.py` | Task 13 | End-to-end validation |

### Modified Files (6)
| File | Tasks | Nature of Changes |
|------|-------|-------------------|
| `protocols/agent_registry.py` | N1 | Add STRUCTURED_PROCESS enum, update pws_consultant registration |
| `mindrian_chat.py` | N1-N6, 1, 3, 5, 6, 8, 9, 10 | Stage machine, on_message branch, callbacks, remove workshop machinery |
| `prompts/pws_consultant.py` | 2, 4, 6 | Enrich data, Yellow Hat expert, bridge prompt builder |
| `prompts/__init__.py` | 2 | Export new constants |
| `tools/pws_consultant_pipeline.py` | 11 | Parallel Neo4j queries |
| `public/elements/DiagnosisResult.jsx` | 5 | Add reclassify button |
| `public/elements/ExpertPanel.jsx` | 9 | Add synthesize button |

### Removed/Deprecated
| Item | Task | Reason |
|------|------|--------|
| `WORKSHOP_PHASES["pws_consultant"]` | N2 | Replaced by CONSULTANT_STAGES |
| `PWS_CONSULTANT_PHASES` in pws_consultant.py | N2 | Deprecated, kept as documentation |
| WorkshopRoadmap rendering for pws_consultant | N2 | Stage machine uses inline UI, not sidebar |
| smart_phase_tracker for pws_consultant | N2 | Deterministic transitions, not LLM-detected |

## Key Architectural Differences from Original Swarm Plan

| Aspect | Original Swarm Plan | Revised (with LangGraph input) |
|--------|-------------------|-------------------------------|
| Intro transition | "manual" (vague) | User button click (ChallengeIntro submit), maps to LangGraph interrupt_before |
| Consulting sub-modes | Not addressed | Explicit: flags in session state, self-loop pattern |
| Expert panel re-fire | Build once with "undefined" | Build early, re-fire with correct problem type after diagnosis |
| Exit condition | Not addressed | Turn 15+ offers synthesis (prevents infinite consulting loop) |
| Session keys | Mixed namespacing | All prefixed with `pws_` |
| AgentRole | Proposed but not detailed | Full enum addition + registration change + has_phases=False |
| Task count | 12 tasks | 18 tasks (6 architectural + 12 original, 1 test added) |
| Phase count | 3 phases (A/B/C) | 4 phases (0/A/B/C + D for validation) |
