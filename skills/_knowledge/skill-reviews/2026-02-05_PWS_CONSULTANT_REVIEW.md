# Skill Review: PWS Consultant

**Date:** 2026-02-05
**Reviewer:** Claude Code (Opus 4.5)
**Skill:** pws-consultant
**Status:** Implemented — registered in agent_registry, all files created

---

## Implementation Summary

### Files Created
| File | Lines | Purpose |
|------|-------|---------|
| `prompts/pws_consultant.py` | 593 | System prompt, PROBLEM_TYPES, DIAGNOSTIC_QUESTIONS, scoring, expert builder |
| `tools/pws_consultant_pipeline.py` | ~400 | Hybrid retrieval: instant_analyze → text_to_cypher → Neo4j → cypher_to_text → FileSearch |
| `public/elements/DiagnosticFlow.jsx` | 99 | MCQ diagnostic UI with progress bar |
| `public/elements/DiagnosisResult.jsx` | 128 | Problem type classification reveal |
| `public/elements/ExpertPanel.jsx` | 117 | Domain expert panel with consult buttons |
| `skills/pws-consultant/SKILL.md` | 143 | Full skill documentation |
| `.claude/skills/pws-consultant.md` | 37 | Claude Code shortcut |

### Files Modified
| File | Changes |
|------|---------|
| `prompts/__init__.py` | Added 8 PWS Consultant imports/exports |
| `mindrian_chat.py` | BOTS entry, WORKSHOP_PHASES, chat_profile, STARTERS (4), AGENT_TRIGGERS (12 keywords), 3 action callbacks |
| `protocols/agent_registry.py` | Registered pws_consultant: 8 capabilities, 10 frameworks, 14 keywords |

## Verification Results

- Agent registry: 17 total agents, PWS Consultant = workshop + sub_agent
- Diagnostic scoring: ill_defined 82% confidence, wicked 83% confidence (correct)
- Pipeline: graceful degradation when Neo4j unavailable
- All prompt exports working from __init__.py
- JSX components: proper default exports, props handling, callAction integration

## Architecture

### Unique Pattern
Unlike other bots (free-form chat), PWS Consultant follows structured 3-phase flow:
1. **Intro** — User describes challenge, background pipelines begin
2. **Diagnostic** — 5 MCQ questions classify problem type
3. **Consulting** — Framework-guided conversation with domain expert panel

### Hybrid Retrieval Pipeline
```
User Message → instant_analyze (<5ms) → text_to_cypher (templates) → Neo4j (3s breaker)
     ↓                                        ↓
  get_hint()                          cypher_to_text()
     ↓                                        ↓
     └──────────── merged context ────────────→ Gemini system prompt
                        ↑
                   FileSearch (async)
```

### Expert Panel (BONO Pipeline)
5 domain-grounded experts built in background:
1. Domain Insider — supply-side industry knowledge
2. End-User Advocate — demand-side, JTBD
3. Skeptical Analyst — Red Team, Camera Test
4. Cross-Domain Innovator — adjacent industries, S-curve
5. Type-specific expert — Futurist / Problem Sharpener / Validation Expert / Systems Thinker

## Known Gaps (from swarm review)

### P0 (Blocking)
- `pws_challenge_description` session var read but never set — intro capture missing
- No structured intro phase (ChallengeIntro component needed)

### P1 (Important)
- PROBLEM_TYPES missing: cynefin_domain, innovation_tools, workshop_phase, techniques
- No WORKSHOPS data (8 curriculum workshops)
- No SELECTION_CRITERIA data
- No interpretive bridge message between diagnosis and consulting
- No reclassify escape hatch
- No Opportunity Strategist (Yellow Hat) in expert panel

### P2 (Polish)
- No WorkshopTimeline component
- No Synthesize button (Minto Pyramid)
- No ConsultantBadge on messages
- Neo4j queries not batched/parallel

### P3 (Future)
- Adaptive diagnostic questions from LangExtract signals
- DIKW progress indicator
- Expert-to-expert debate
- Analytics tracking

## Comparison with Reference JSX Prototype

The standalone React reference had richer data (15 innovation tools per type, Cynefin mapping, 8 workshops) but lacked: expert panel, retrieval pipeline, agent integration, session persistence, dynamic tool offering.

See: `swarm-reports/2026-02-05_PWS_CONSULTANT_IMPLEMENTATION_PLAN.md` for full gap analysis and implementation plan.
