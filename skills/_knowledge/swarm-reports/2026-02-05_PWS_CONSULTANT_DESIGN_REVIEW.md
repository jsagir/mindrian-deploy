# Swarm Report: PWS Consultant Design Review

**Date:** 2026-02-05
**Agents:** Larry (Pedagogy), Red Team, Ackoff (DIKW), Stack Architect, QA Consultant, BONO Master
**Subject:** PWS Consultant agent architecture review before implementation
**Status:** Completed — findings incorporated into implementation

---

## Consensus (All Agents Agree)

1. **The 3-phase architecture (Intro → Diagnostic → Consulting) is correct.** No agent argues against the fundamental flow.
2. **Problem type taxonomy (Un-Defined, Ill-Defined, Well-Defined, Wicked) is validated** — matches `problem_classifier.py` and PWS methodology.
3. **An interpretive bridge between DiagnosisResult and ExpertPanel is mandatory.** Larry must explain what the classification means for THIS specific user, using their own words.
4. **Existing tools must be composed, not duplicated.** `hybrid_retrieve()` should call `graphrag_lite.py`. `search_pws_materials()` should call `gemini_rag.py`. `execute_cypher_queries()` should use existing Neo4j pattern with parameterized queries.
5. **The expert panel needs a synthesis step.** A "Synthesize" button applying Minto Pyramid (Governing Thought + Key Arguments + Evidence) is required.
6. **Diagnostic progress must be persisted to session state** after each answer via `cl.user_session.set()`.
7. **The "reclassify" escape hatch is needed.** Users must be able to challenge the diagnosis.

## Disagreements

| Issue | Position A | Position B |
|-------|-----------|-----------|
| Diagnostic depth | Larry + Ackoff: More conversational, adaptive, LangExtract-informed | BONO: Efficient/quick to get to expert panel faster |
| Expert role count | BONO: Add Opportunity Strategist + Reframing Expert (7 experts) | QA: Keep to 5 with better differentiation |
| Neo4j batching vs concurrent | Stack Architect: Batch into single Cypher query | Larry: Separate queries for pedagogical traceability |

## Key Findings by Agent

### Larry (Pedagogy)
- Diagnostic is too passive — 5 MCQ is a quiz, not a consultation
- Phase transition from Diagnostic to Consulting is abrupt — needs Socratic bridge
- LangExtract signals should enrich diagnosis alongside MCQ answers
- Each question should have a conversational preamble from Larry

### Red Team
- **F1:** Neo4j circuit breaker has no state persistence between `text_to_cypher_queries()` and `execute_cypher_queries()`
- **F2:** Expert panel generation may not complete before user finishes 5-question diagnostic (race condition)
- **F3:** Diagnostic progress not persisted — browser refresh loses all answers
- **F4:** Text-to-Cypher must use parameterized queries to prevent injection
- **F5:** FileSearch async race condition — may return after LLM already responded

### Ackoff (DIKW)
- D layer (raw data): Solid — instant_extract + MCQ answers
- I layer (information): Acceptable but thin — MCQ alone is sparse; no Camera Test
- K layer (knowledge): Solid if pipeline composes existing tools properly
- U layer (understanding): **Underspecified** — expert panel provides perspectives but lacks causal integration
- W layer (wisdom): **Missing** — no explicit "So what should you do?" synthesis step

### Stack Architect
- Registration must follow CLAUDE.md TIER 1-4 checklist
- Pipeline introduces hybrid pattern (action-callback diagnostic + conversational consulting) — new complexity
- Consultant phase state must be managed in `cl.user_session`
- `on_message` handler should delegate to `process_consultant_turn()` only when `consultant_phase == "consulting"`
- Pipeline functions overlap with graphrag_lite.py — compose, don't duplicate

### QA Consultant
- Test: double-click debounce on diagnostic options
- Test: browser refresh mid-diagnostic
- Test: bot switch mid-diagnostic
- Test: expert panel gap if >3 seconds
- Test: all 4 problem type classifications produce correct frameworks
- Mobile: 2-column expert grid at 375px

### BONO Master
- Domain Insider and End-User Advocate can collapse into same perspective — differentiate supply-side vs demand-side
- Skeptical Analyst too negative without Yellow Hat equivalent — add Opportunity Strategist
- Problem-type-specific expert mapping: Undefined→Futurist, Ill-Defined→Researcher, Well-Defined→Validator, Wicked→Systems Thinker
- Expert construction needs grounding in real Neo4j domain data

## Prioritized Action Items

### P0 (Done)
1. System prompt with Larry's voice, diagnostic questions, per-type consulting guidance
2. `diagnostic_answer` callback with per-answer session persistence
3. Wire `build_expert_panel()` to compose graphrag_lite.py and gemini_rag.py
4. Pre-built Cypher templates with parameterized queries

### P1 (In Progress — see Implementation Plan swarm report)
5. Interpretive bridge generation
6. Reclassify escape hatch button
7. Opportunity Strategist expert role
8. Batch/parallelize expert panel Neo4j queries

### P2 (Future)
9. "Synthesize" button with Minto Pyramid
10. Adaptive diagnostic questions from LangExtract signals
11. Camera Test prompts during diagnostic
12. Mobile responsiveness testing

### P3 (Post-Release)
13. DIKW progress indicator
14. Expert-to-expert debate feature
15. Analytics: which experts consulted most, which types most common
