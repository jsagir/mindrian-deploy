# Swarm Workflow Catalog

Pre-built workflow recipes for common multi-agent scenarios.

## Quick Reference

| Workflow | Agents | Time | Use Case |
|----------|--------|------|----------|
| Quick Pulse | 2 | ~10s | Fast check |
| Deep Research | Research + 3 | ~30s | Unknown domain |
| Stress Test | 1 + Red Team | ~20s | Challenge assumptions |
| Full Swarm | All + Research | ~60s | Major decisions |
| Regression Hunt | Commit + QA + QA-C | ~25s | Bug investigation |
| Architecture Review | Stack + Commit + R&D | ~30s | Technical decisions |

---

## 1. Quick Pulse

**Purpose:** Fast validation when you need a quick sanity check.

**Agents:** Router picks 2 most relevant

**Implementation:**
```python
from agents.multi_agent_graph import quick_analysis

result = await quick_analysis("Should I focus on B2B or B2C?")
```

**Maps to:** `quick_analysis()` in `agents/multi_agent_graph.py`

**Output format:**
```
## Quick Analysis

**TTA:** B2B has longer sales cycles but higher LTV. B2C is crowded.
**Larry:** Given your background in enterprise, B2B aligns better.

**Quick Take:** Start B2B, consider B2C expansion later.
```

---

## 2. Deep Research

**Purpose:** When entering an unknown domain, research first.

**Agents:** Research → 3 domain-relevant agents → Larry synthesis

**Implementation:**
```python
from agents.multi_agent_graph import research_and_explore

result = await research_and_explore("What's happening in synthetic biology startups?")
```

**Maps to:** `research_and_explore()` in `agents/multi_agent_graph.py`

**Flow:**
1. Research agent gathers current data (Tavily, web)
2. TTA analyzes trends from research
3. JTBD identifies customer needs
4. Larry synthesizes with grounded context

**Output format:**
```
## Research-Backed Analysis

### Current Landscape (Research)
- $12B market, 23% CAGR
- Key players: Ginkgo, Zymergen, Twist

### Trends (TTA)
- Shift from pharma to materials
- AI-driven design acceleration

### Customer Jobs (JTBD)
- Reduce R&D timelines
- Lower prototyping costs

### Synthesis (Larry)
Opportunity exists in AI-accelerated strain optimization...
```

---

## 3. Stress Test

**Purpose:** Challenge an idea before committing resources.

**Agents:** Proposing agent + Red Team debate

**Implementation:**
```python
from agents.multi_agent_graph import run_sequential_workflow

result = await run_sequential_workflow(
    query="Vertical farming will replace traditional agriculture",
    agents=["tta", "redteam", "tta"]  # Propose → Challenge → Defend
)
```

**Flow:**
1. TTA makes the case for the thesis
2. Red Team pokes holes and challenges
3. TTA responds to challenges

**Output format:**
```
## Stress Test Results

### Initial Thesis (TTA)
Vertical farming advantages: water efficiency, year-round, urban proximity...

### Challenges (Red Team)
- Energy costs make it 3x more expensive per calorie
- Only works for leafy greens, not staple crops
- Real estate in urban areas is the actual bottleneck

### Defense (TTA)
Valid concerns. Revised thesis: Vertical farming for high-value crops
in water-scarce or extreme climate regions, not broad replacement.

### Verdict
Thesis **MODIFIED** - narrower scope is defensible.
```

---

## 4. Full Swarm

**Purpose:** Comprehensive analysis for major decisions.

**Agents:** All agents + Research + Validation

**Implementation:**
```python
from agents.multi_agent_graph import full_analysis_with_research

result = await full_analysis_with_research(
    "Should I quit my job to pursue this startup idea?"
)
```

**Maps to:** `full_analysis_with_research()` in `agents/multi_agent_graph.py`

**Flow:**
1. Research gathers market data
2. TTA analyzes timing and trends
3. JTBD identifies customer validation status
4. S-Curve assesses technology maturity
5. Ackoff validates decision grounding
6. Red Team challenges the thesis
7. Larry synthesizes all perspectives

**Output format:**
```
## Full Swarm Analysis

### Market Context (Research)
[Data and sources]

### Timing Assessment (TTA)
[Trend analysis]

### Customer Validation (JTBD)
[Job satisfaction evidence]

### Technology Readiness (S-Curve)
[Maturity assessment]

### Decision Grounding (Ackoff)
[DIKW validation]

### Challenges (Red Team)
[Key risks and objections]

### Synthesis (Larry)
[Unified recommendation with confidence level]

**Recommendation:** [GO / NO-GO / CONDITIONAL]
**Confidence:** 73%
**Key Condition:** [What would change this recommendation]
```

---

## 5. Regression Hunt (Skill-Based)

**Purpose:** Investigate when something broke in the codebase.

**Agents:** Commit Expert → QA Analyzer → QA Consultant

**Implementation:**
```python
# Via skill invocation
# /swarm --workflow regression-hunt "Login stopped working after last deploy"
```

**Flow:**
1. Commit Expert analyzes recent changes
2. QA Analyzer identifies test coverage gaps
3. QA Consultant recommends investigation path

**Output format:**
```
## Regression Hunt

### Recent Changes (Commit Expert)
- 3 commits since last known good: auth refactor, deps update, config change
- Most likely culprit: auth refactor (touched 12 files)

### Test Coverage (QA Analyzer)
- Auth module: 45% coverage
- Missing tests for: session timeout, OAuth refresh

### Investigation Path (QA Consultant)
1. Check OAuth token refresh logic in auth/oauth.py:145
2. Verify session cookie settings after config change
3. Add integration test for login → refresh → action flow

**Recommended Action:** Start with auth/oauth.py line 145
```

---

## 6. Architecture Review (Skill-Based)

**Purpose:** Evaluate technical decisions and stack choices.

**Agents:** Mindrian Stack → Commit Expert → R&D Consultant

**Implementation:**
```python
# Via skill invocation
# /swarm --workflow architecture-review "Should we migrate to microservices?"
```

**Flow:**
1. Mindrian Stack assesses current architecture
2. Commit Expert identifies pain points from history
3. R&D Consultant evaluates options

**Output format:**
```
## Architecture Review

### Current State (Mindrian Stack)
- Monolith with 47K LOC
- Deploy frequency: 2x/week
- Pain points: long build times, coupling

### Historical Context (Commit Expert)
- 60% of bugs in last quarter touched shared modules
- Average PR touches 8 files
- Most reverted: user service changes

### Options Analysis (R&D Consultant)
| Option | Effort | Risk | Payoff |
|--------|--------|------|--------|
| Stay monolith + modularize | Low | Low | Medium |
| Extract 2 critical services | Medium | Medium | High |
| Full microservices | High | High | Uncertain |

**Recommendation:** Extract auth and payments as services first.
Validate operational readiness before further decomposition.
```

---

## Creating Custom Workflows

```python
from agents.multi_agent_graph import run_custom_workflow

# Define your workflow
workflow = {
    "name": "Customer Discovery",
    "stages": [
        {"agents": ["research"], "mode": "sequential"},
        {"agents": ["jtbd", "larry"], "mode": "parallel"},
        {"agents": ["redteam"], "mode": "sequential"},
    ],
    "synthesis_style": "prioritized"
}

result = await run_custom_workflow("Validate our ICP hypothesis", workflow)
```

## Workflow Selection Heuristics

```
IF query contains "should I" or "good idea"
    → Stress Test

IF query mentions unknown industry/technology
    → Deep Research

IF query is about major decision (quit, invest, pivot)
    → Full Swarm

IF query is about code/bugs
    → Regression Hunt

IF query is about architecture/tech stack
    → Architecture Review

ELSE
    → Quick Pulse (let router pick)
```
