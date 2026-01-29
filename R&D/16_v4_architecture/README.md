# Mindrian v4.0 Integration Analysis

**Date:** 2026-01-29
**Status:** Architecture Review Complete
**Fit Assessment:** 85-90% alignment with current codebase

---

## Executive Summary

The v4.0 Enhanced Specification has been validated against the current Mindrian codebase. **Most infrastructure already exists** - the primary work is exposing existing capabilities and adding orchestration layers.

| Category | Current State | v4.0 Ready |
|----------|---------------|------------|
| Neo4j GraphRAG | ✅ Full integration | Needs UI exposure |
| Cynefin Router | ✅ Backend working | Needs decision routing |
| Devil's Advocate | ✅ Red Team bot | Needs mode selector |
| Beautiful Questions | ✅ Full bot | Needs auto-trigger |
| LangExtract | ✅ Complete | Expand signals |
| Research Tools | ✅ 7 tools + orchestrator | Good foundation |
| Multi-Agent | ⚠️ Manual switching | Needs pipelines |

---

## Current Architecture (v3.1)

```
┌─────────────────────────────────────────────────────────────┐
│                    CHAINLIT UI (2.9+)                       │
│  13 Bots │ 52 Starters │ Phase Progress │ Action Buttons   │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────┐
│                 INTELLIGENCE LAYERS                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ LangExtract │  │ GraphRAG    │  │ Problem Classifier  │ │
│  │ (signals)   │  │ (frameworks)│  │ (problem types)     │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────┐
│                 RESEARCH ORCHESTRATOR                        │
│  Query Decomposition → Source Evaluation → Deep Extraction  │
│  → Gap Analysis → Synthesis (PWS framing)                   │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────┐
│              NEO4J KNOWLEDGE GRAPH                           │
│  761 Frameworks │ 8,425 Concepts │ 197 ProcessSteps         │
│  43 BeautifulQuestions │ 65 DevilsAdvocate │ 35 ResearchTools│
└─────────────────────────────────────────────────────────────┘
```

---

## v4.0 Enhancements Needed

### 1. Cynefin Cognitive Router

**Current:** Cynefin domain classification exists in `graph_orchestrator.py` but not exposed to UI or routing decisions.

**v4.0 Enhancement:**
```python
# Add to mindrian_chat.py after agent scoring

def boost_by_cynefin_domain(cynefin_domain: str, scores: dict) -> dict:
    """Boost agent scores based on Cynefin problem complexity."""
    boosts = {
        "simple": {"ackoff": 0.2, "validation": 0.15},
        "complicated": {"scurve": 0.2, "jtbd": 0.15, "investment": 0.1},
        "complex": {"tta": 0.25, "scenario": 0.2, "beautiful_question": 0.15},
        "chaotic": {"redteam": 0.25, "knowns": 0.2}
    }
    for agent, boost in boosts.get(cynefin_domain, {}).items():
        scores[agent] = scores.get(agent, 0) + boost
    return scores
```

**Files to modify:**
- `mindrian_chat.py` - Add Cynefin boost to `suggest_agents_from_context()`
- `tools/graph_orchestrator.py` - Expose domain in return value

**Effort:** 4 hours

---

### 2. Devil's Advocate Mode

**Current:** Red Team bot handles assumption challenging but is generalist.

**v4.0 Enhancement:** Add explicit Devil's Advocate mode to Red Team.

```python
# prompts/redteam.py - Add mode selector

DEVILS_ADVOCATE_MODE = """
## Devil's Advocate Mode (Active)

You are now in PURE OPPOSITION mode. Your role:
1. **Contradict** the user's main thesis with specific counter-arguments
2. **Find counter-evidence** for every claim
3. **Play strategic competitor** - what would a well-funded rival do?
4. **Escalate edge cases** - what happens when X fails?

Do NOT offer balanced views. Be the opposition.
"""

# In mindrian_chat.py - Add mode toggle
@cl.action_callback("devils_advocate_mode")
async def toggle_devils_advocate(action: cl.Action):
    bot = cl.user_session.get("bot")
    if bot["name"] == "Red Team":
        bot["devils_advocate_mode"] = not bot.get("devils_advocate_mode", False)
        # Update system prompt accordingly
```

**Files to modify:**
- `prompts/redteam.py` - Add mode-specific prompts
- `mindrian_chat.py` - Add action callback for mode toggle

**Effort:** 3 hours

---

### 3. Beautiful Questions Auto-Trigger

**Current:** Beautiful Questions bot exists but requires manual selection.

**v4.0 Enhancement:** Auto-suggest based on conversation phase.

```python
# Add to suggest_agents_from_context() in mindrian_chat.py

def detect_beautiful_question_phase(extraction: dict, history: list) -> str:
    """Detect which Beautiful Question phase user needs."""

    # WHY phase: High certainty but no clear problem definition
    if extraction.get("certainty", 0) >= 2 and extraction.get("problems", 0) == 0:
        return "why"  # Need to clarify the problem

    # WHAT IF phase: Problem defined, exploring solutions
    if extraction.get("problems", 0) > 0 and extraction.get("solutions", 0) < 2:
        return "what_if"  # Need to brainstorm possibilities

    # HOW phase: Has solutions, needs implementation
    if extraction.get("solutions", 0) >= 2 and extraction.get("is_forward_looking", False):
        return "how"  # Need to test and validate

    return None

# Boost beautiful_question agent based on detected phase
phase = detect_beautiful_question_phase(extraction, history)
if phase:
    agent_scores["beautiful_question"] += 0.3
```

**Files to modify:**
- `mindrian_chat.py` - Add phase detection logic
- `tools/langextract.py` - Ensure signals support phase detection

**Effort:** 3 hours

---

### 4. Multi-Agent Pipelines

**Current:** Manual bot switching with context preservation.

**v4.0 Enhancement:** Automated multi-agent workflows.

```python
# New file: agents/pipelines.py

PRESET_PIPELINES = {
    "validate_startup_idea": {
        "name": "Startup Validation Pipeline",
        "description": "Comprehensive idea validation",
        "steps": [
            {"bot": "jtbd", "focus": "Understand customer jobs"},
            {"bot": "redteam", "focus": "Challenge assumptions"},
            {"bot": "ackoff", "focus": "Ground in evidence"},
            {"bot": "scenario", "focus": "Plan for futures"}
        ]
    },
    "trend_to_opportunity": {
        "name": "Trend Analysis Pipeline",
        "description": "Turn trends into opportunities",
        "steps": [
            {"bot": "tta", "focus": "Extrapolate trend"},
            {"bot": "scurve", "focus": "Analyze timing"},
            {"bot": "investment", "focus": "Evaluate opportunity"}
        ]
    },
    "problem_deep_dive": {
        "name": "Problem Clarification Pipeline",
        "description": "Deeply understand a problem",
        "steps": [
            {"bot": "beautiful_question", "focus": "WHY questions"},
            {"bot": "knowns", "focus": "Map uncertainties"},
            {"bot": "jtbd", "focus": "Customer perspective"}
        ]
    }
}

async def run_pipeline(pipeline_id: str, initial_context: str):
    """Execute a multi-agent pipeline with cl.Step visualization."""
    pipeline = PRESET_PIPELINES[pipeline_id]

    for step in pipeline["steps"]:
        async with cl.Step(name=f"🤖 {step['bot'].title()}") as agent_step:
            agent_step.input = step["focus"]
            # Run agent and collect output
            result = await run_agent_response(step["bot"], context)
            agent_step.output = result
            context = result  # Pass to next agent

    return synthesize_pipeline_results(results)
```

**Files to create:**
- `agents/pipelines.py` - Pipeline definitions and execution

**Files to modify:**
- `mindrian_chat.py` - Add pipeline action callbacks

**Effort:** 12 hours

---

### 5. Assumption Tracking Across Bots

**Current:** Assumptions extracted per-message but not tracked across bot switches.

**v4.0 Enhancement:** Cross-session assumption cache.

```python
# Add to context_store structure

context_store[context_key] = {
    "bot_id": str,
    "history": List[Message],
    # NEW: Cross-bot assumption tracking
    "assumptions": {
        "extracted": [
            {"text": "...", "source_bot": "lawrence", "timestamp": "..."},
            ...
        ],
        "challenged": [  # From Red Team/Devil's Advocate
            {"assumption": "...", "challenge": "...", "resolution": "..."},
            ...
        ],
        "validated": [  # From Ackoff/Validation
            {"assumption": "...", "evidence": "...", "confidence": 0.8},
            ...
        ]
    }
}
```

**Files to modify:**
- `mindrian_chat.py` - Update context_store structure
- `tools/langextract.py` - Extract assumptions to cache

**Effort:** 8 hours

---

## Implementation Roadmap

### Phase 1: Quick Wins (Week 1) - 12 hours

| Task | File | Hours | Impact |
|------|------|-------|--------|
| Expose Cynefin domain in UI | `mindrian_chat.py` | 2 | Users see problem classification |
| Cynefin-aware bot boosting | `mindrian_chat.py` | 4 | Better agent suggestions |
| Devil's Advocate mode toggle | `prompts/redteam.py` | 3 | Focused challenge sessions |
| Beautiful Questions auto-trigger | `mindrian_chat.py` | 3 | Timely interventions |

### Phase 2: Intelligence (Week 2-3) - 20 hours

| Task | File | Hours | Impact |
|------|------|-------|--------|
| Assumption tracking cache | `mindrian_chat.py` | 8 | Cross-bot context |
| Problem type on chat start | `mindrian_chat.py` | 4 | Route to right bot |
| Research button ranking | `mindrian_chat.py` | 4 | Most relevant first |
| Simple multi-agent pipeline | `agents/pipelines.py` | 4 | 3-step workflows |

### Phase 3: Advanced (Week 4) - 20 hours

| Task | File | Hours | Impact |
|------|------|-------|--------|
| Full LangGraph orchestration | `agents/` | 12 | Visual reasoning |
| Adaptive phase progression | `mindrian_chat.py` | 4 | Optimize transitions |
| Reverse salient queries | `tools/graphrag_lite.py` | 4 | Find bottlenecks |

---

## Neo4j Assets Available

| Asset | Count | v4.0 Usage |
|-------|-------|------------|
| Framework | 761 | Route to specialists |
| LazyGraphConcept | 8,425 | LangExtract validation |
| ProcessStep | 197 | Define workflows |
| BeautifulQuestion | 43 | Cynefin classification |
| DevilsAdvocate | 65 | Challenge patterns |
| ResearchTool | 35 | Tool discovery |
| CaseStudy | 21+ | Example grounding |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Cynefin misclassification | Medium | Low | Fallback to current routing |
| Pipeline timeout | Medium | Medium | Add step timeouts |
| Assumption tracking bloat | Low | Low | Bounded cache size |
| Over-aggressive auto-suggestions | Medium | Medium | Confidence thresholds |

---

## Success Metrics

| Metric | Current | v4.0 Target |
|--------|---------|-------------|
| Bot suggestion relevance | ~70% | 85%+ |
| Research result relevance | ~60% | 80%+ |
| Assumption identification | Manual | Automatic |
| Multi-bot workflow completion | 0 | 50+ per month |
| Cynefin-aware routing | 0% | 100% |

---

## Conclusion

**v4.0 is highly achievable** with the current codebase:

1. **85% of infrastructure exists** - GraphRAG, LangExtract, Beautiful Questions, Research Orchestrator
2. **Primary work is integration** - Connecting existing components
3. **No breaking changes needed** - Incremental enhancements
4. **Estimated total effort:** 50-60 development hours

**Recommended starting point:** Phase 1 Quick Wins (12 hours) delivers immediate value with minimal risk.
