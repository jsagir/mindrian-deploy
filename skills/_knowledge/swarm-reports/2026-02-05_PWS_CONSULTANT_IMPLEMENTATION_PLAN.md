# Swarm Report: PWS Consultant Implementation Plan

**Date:** 2026-02-05
**Agents:** UI Architect (Lead), Larry (Pedagogy), Stack Architect, Red Team, QA
**Subject:** Consolidated implementation plan for all PWS Consultant gaps (reference comparison + earlier swarm insights)
**Status:** Awaiting user approval before implementation

---

## Input Sources

1. **Reference JSX app comparison** — Standalone React prototype with richer data, workshop views, intro textarea
2. **Earlier swarm design review** — P1/P2 items: reclassify, synthesize, adaptive diagnostic, Opportunity Strategist, batched queries
3. **Existing implementation** — 7 created files, 3 modified files, agent registered

## Key Design Decisions

- **Three-view switching (chat/workshops/tools) DEFERRED to future** — architecturally complex in Chainlit, replaced by inline WorkshopTimeline component
- **Post-diagnosis logic extracted into shared function** — enables reuse by diagnostic completion, direct type selection, and reclassify callbacks
- **Data enrichment before UI** — enrich PROBLEM_TYPES before building components that consume them
- **Direct type selection included but de-emphasized** — "Or if you already know:" with muted styling, preserves pedagogical flow

## Final Plan: 12 Tasks, 3 Phases

### Phase A: Foundation

**Task 1: Extract Post-Diagnosis Completion Logic**
- Files: `mindrian_chat.py`
- Extract `if question_number >= 5:` block into `async def _complete_pws_diagnosis(diagnosis, answers, challenge_description)`
- Enables reuse by submit_challenge, direct_select_type, reclassify_problem
- Risk: MODERATE

**Task 2: Enrich PROBLEM_TYPES + Add WORKSHOPS + SELECTION_CRITERIA**
- Files: `pws_consultant.py`, `__init__.py`
- Add per-type: cynefin_domain, innovation_tools (15 for ill-defined), workshop_phase, techniques
- Add WORKSHOPS (8 curriculum workshops with deliverables, mechanisms, tools)
- Add SELECTION_CRITERIA (5 filtering criteria from Workshop 3)
- Risk: SAFE

**Task 3: Create ChallengeIntro.jsx + Callbacks**
- Files: NEW `ChallengeIntro.jsx`, `mindrian_chat.py`
- Textarea + submit button → `submit_challenge` callback
- 4 muted type cards → `direct_select_type` callback
- Wire into on_chat_start for pws_consultant
- Risk: MODERATE

### Phase B: Core Features

**Task 4: Add Opportunity Strategist (Yellow Hat)**
- Files: `pws_consultant.py` build_expert_specs()
- 6th expert archetype: upside identification, value creation, competitive advantage
- Risk: SAFE

**Task 5: Reclassify Escape Hatch**
- Files: `DiagnosisResult.jsx`, `mindrian_chat.py`
- "This doesn't feel right" button → shows 4 type cards → `reclassify_problem` callback
- Calls shared `_complete_pws_diagnosis()` with new type
- Risk: LOW

**Task 6: Interpretive Bridge Message**
- Files: `pws_consultant.py`, `mindrian_chat.py`
- New function `build_bridge_prompt()` using enriched data (Cynefin, tools, workshops)
- Larry-voice: "Very simply, based on what you've told me..."
- Risk: LOW

**Task 7: WorkshopTimeline.jsx**
- Files: NEW `WorkshopTimeline.jsx`, `mindrian_chat.py`
- Horizontal scrollable 8-workshop bar, active workshops highlighted by problem type
- Inline in chat after diagnosis
- Risk: LOW

**Task 8: Wire Background Expert Panel into submit_challenge**
- Files: `mindrian_chat.py`
- Launch expert panel build as asyncio.create_task from submit_challenge
- Check task.done() in _complete_pws_diagnosis, update with correct problem type
- Risk: MODERATE

### Phase C: Polish

**Task 9: Synthesize Expert Inputs Button (Minto Pyramid)**
- Files: `ExpertPanel.jsx`, `mindrian_chat.py`
- "Synthesize All Perspectives" button appears after 2+ expert consults
- `synthesize_expert_inputs` callback structures via Minto Pyramid
- Risk: LOW

**Task 10: ConsultantBadge.jsx**
- Files: NEW `ConsultantBadge.jsx`, `mindrian_chat.py`
- Persistent problem type badge on consulting phase messages
- Risk: LOW

**Task 11: Batch Neo4j Queries**
- Files: `pws_consultant_pipeline.py`
- asyncio.gather with run_in_executor for parallel cypher execution
- Risk: MODERATE

**Task 12: Adaptive Diagnostic Q1 (Future)**
- Files: `mindrian_chat.py`, `pws_consultant.py`
- instant_extract() signals adjust first diagnostic question
- Risk: MODERATE

## Dependency Chain

```
Task 2 (data) ──┬──> Task 3 (ChallengeIntro) ──> Task 8 (expert wiring) ──> Task 12 (adaptive)
                │
Task 1 (refactor) ──┬──> Task 3
                    ├──> Task 5 (reclassify)
                    ├──> Task 6 (bridge)
                    └──> Task 7 (timeline)

Task 4 (Opportunity Strategist) ──> independent
Task 9 (synthesize) ──> independent
Task 10 (badge) ──> after Task 1
Task 11 (batch queries) ──> independent
```

## Execution Order

2 → 1 → 4 → 3 → 6 → 5 → 8 → 7 → 9 → 10 → 11 → 12

## Totals

- 3 new JSX components (ChallengeIntro, WorkshopTimeline, ConsultantBadge)
- 2 modified JSX (DiagnosisResult, ExpertPanel)
- 4 new action callbacks
- 0 HIGH risk tasks
