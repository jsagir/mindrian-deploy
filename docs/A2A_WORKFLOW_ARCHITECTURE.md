# A2A Workflow Architecture for PWS Methodologies

## Vision: Trending to the Absurd as Root Orchestrator

Based on Neo4j graph analysis and PWS methodology research, here's how to harness TTA as the root for multi-agent A2A workflows.

---

## The Core Insight

TTA is uniquely positioned as a **workflow orchestrator** because:
1. It starts with domain selection (entry point)
2. It requires research validation (sub-agent delegation)
3. It generates scenarios that feed other frameworks
4. Its outputs become inputs for downstream agents

```
TTA Output → Scenario Analysis Input
TTA Output → JTBD Input (who has problems in this future?)
TTA Output → Nested Hierarchies Input (what systems will change?)
TTA Output → Red Team Input (what assumptions can we challenge?)
```

---

## A2A Workflow Architecture

### Level 1: Orchestrator Agents (Entry Points)

```
┌─────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR LAYER                            │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │   LAWRENCE   │  │     TTA      │  │   SCENARIO   │           │
│  │  (Default)   │  │  (Trends)    │  │  (Futures)   │           │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘           │
│         │                 │                 │                    │
│         └─────────────────┼─────────────────┘                    │
│                           │                                      │
│                    CONTEXT HANDOFF                               │
└───────────────────────────┼──────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    WORKSHOP LAYER                                │
│                                                                   │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │  JTBD   │ │ ACKOFF  │ │ S-CURVE │ │ NESTED  │ │ RED TEAM│   │
│  │         │ │ (DIKW)  │ │         │ │ HIER.   │ │         │   │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘   │
│       │           │           │           │           │         │
└───────┼───────────┼───────────┼───────────┼───────────┼─────────┘
        │           │           │           │           │
        └───────────┴───────────┼───────────┴───────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SERVICE LAYER (Microservices)                 │
│                                                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  GRAPHRAG   │  │  RESEARCH   │  │ PWS_GRADING │              │
│  │  (Context)  │  │  (Tavily)   │  │  (Quality)  │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

---

## TTA as Root Orchestrator: The Master Workflow

### Phase 1: Domain & Trend Discovery

```yaml
workflow: tta_orchestration
phase: 1_domain_trends

orchestrator: TTA
triggers_on: "I want to explore trends in [domain]"

steps:
  1_domain_selection:
    agent: TTA
    action: "Identify domain of interest"
    output: domain_context

  2_trend_research:
    agent: RESEARCH  # Sub-agent delegation
    action: "Research trends in {domain_context}"
    tools:
      - tavily_search
      - google_trends (via SerpAPI)
    output: trend_list

  3_trend_validation:
    agent: GRAPHRAG  # Microservice
    action: "Find related frameworks and case studies"
    query: |
      MATCH (f:Framework)-[:ADDRESSES]->(d:Domain {name: $domain})
      RETURN f.name, f.description
    output: relevant_frameworks

  4_trend_selection:
    agent: TTA
    action: "Select one trend for deep dive"
    input: [trend_list, relevant_frameworks]
    output: selected_trend
```

### Phase 2: Absurd Extrapolation

```yaml
phase: 2_absurd_extrapolation

steps:
  5_extrapolation:
    agent: TTA
    action: |
      Carry trend to absurd conclusion:
      - What if everything were...?
      - What if everyone were to do...?
      - What if nobody were to do...?
    output: absurd_scenario

  6_scenario_enrichment:
    agent: SCENARIO  # Workshop handoff
    handoff_type: DELEGATE
    action: "Build 2x2 scenario matrix around this absurd future"
    input: absurd_scenario
    output: scenario_matrix
    expects_return: true

  7_persona_creation:
    agent: TTA
    action: "Create personas who live in this future"
    input: [absurd_scenario, scenario_matrix]
    output: future_personas
```

### Phase 3: Problem Discovery (Multi-Agent Fan-Out)

```yaml
phase: 3_problem_discovery

parallel_delegation:
  # Fan out to multiple workshop agents simultaneously

  jtbd_analysis:
    agent: JTBD
    handoff_type: DELEGATE
    action: "What jobs-to-be-done exist in this future?"
    input: [absurd_scenario, future_personas]
    output: future_jobs

  nested_analysis:
    agent: NESTED_HIERARCHIES
    handoff_type: DELEGATE
    action: "What systems will change? Where are leverage points?"
    input: absurd_scenario
    output: system_changes

  timing_analysis:
    agent: SCURVE
    handoff_type: DELEGATE
    action: "What technologies are reaching limits? What's replacing them?"
    input: absurd_scenario
    output: technology_shifts

  challenge_analysis:
    agent: RED_TEAM
    handoff_type: DELEGATE
    action: "Challenge assumptions. What could prevent this future?"
    input: absurd_scenario
    output: assumption_challenges

# Wait for all to complete
fan_in:
  agent: TTA
  action: "Synthesize findings into opportunity map"
  input: [future_jobs, system_changes, technology_shifts, assumption_challenges]
  output: opportunity_map
```

### Phase 4: Opportunity Validation

```yaml
phase: 4_validation

steps:
  10_dikw_grounding:
    agent: ACKOFF
    handoff_type: DELEGATE
    action: "Ground opportunities in DIKW pyramid"
    input: opportunity_map
    output: grounded_opportunities

  11_quality_check:
    agent: PWS_GRADING  # Service
    action: "Score opportunities against PWS criteria"
    input: grounded_opportunities
    output: scored_opportunities

  12_final_synthesis:
    agent: TTA
    action: "Create final portfolio of problems worth solving"
    input: [scored_opportunities, assumption_challenges]
    output: problem_portfolio
```

---

## Handoff Protocol Specification

### A2A Handoff Structure

```yaml
handoff:
  protocol: "a2a/v1"
  from_agent: "tta"
  to_agent: "nested_hierarchies"
  handoff_type: "delegate"  # or "switch", "consult", "return"
  expects_return: true
  priority: "normal"

  context:
    domain: "electric vehicles"
    trend: "battery technology reaching physical limits"
    absurd_scenario: "What if batteries became 100x more energy-dense?"

  task:
    action: "Map the nested hierarchy of EV systems"
    expected_output:
      - system_levels: 5  # At least 5 levels
      - reverse_salients: list
      - leverage_points: list

  entities_extracted:
    - type: "technology"
      name: "solid-state batteries"
    - type: "constraint"
      name: "charging infrastructure"
```

### Context Journal Entry

```markdown
### 🔄 Delegation (TTA → Nested Hierarchies) — Turn 8
*10:15:00*

TTA delegating systems analysis to Nested Hierarchies.

**Reason**: Need to understand where in the hierarchy the battery
constraint actually sits. User's assumption is that batteries are
the problem, but it might be at a higher level (infrastructure,
business model, regulatory).

**Expected Return**: System map with reverse salients identified.
```

---

## Service Layer (Microservices/Tools)

### GraphRAG Service

```python
# tools/graphrag_lite.py - already implemented

async def enrich_context(query: str, bot_id: str) -> str:
    """
    Called by any agent to get graph-enriched context.

    Returns hints about:
    - Related frameworks
    - Case studies
    - Co-occurring concepts
    """
    # Uses Neo4j LazyGraph for bounded retrieval
    pass
```

### Research Service

```python
# tools/research_tools.py

async def research_trend(trend: str, domain: str) -> dict:
    """
    Called by TTA/SCURVE/SCENARIO to validate trends.

    Uses:
    - Tavily for web search
    - SerpAPI for Google Trends
    - ArXiv for academic papers
    """
    pass
```

### Grading Service

```python
# tools/pws_grading.py

async def score_opportunity(opportunity: dict) -> dict:
    """
    Called by any agent to score against PWS criteria.

    Scores:
    - Is it real? (evidence)
    - Can we win? (competitive position)
    - Is it worth it? (impact)
    """
    pass
```

---

## Context-Driven Tool Selection

### Tool Routing Logic

```python
# In each agent, tools are selected based on context

TOOL_TRIGGERS = {
    # If user mentions research/data needs
    "research_keywords": ["data", "evidence", "statistics", "research", "study"],
    "tool": "research",

    # If user mentions system/hierarchy
    "system_keywords": ["system", "hierarchy", "level", "constraint", "leverage"],
    "tool": "graphrag",  # Neo4j traversal

    # If user mentions timing/technology
    "timing_keywords": ["timing", "too early", "too late", "s-curve", "adoption"],
    "tool": "research",  # Need market data

    # If user needs validation
    "validation_keywords": ["validate", "grade", "score", "assess", "quality"],
    "tool": "pws_grading",
}
```

### Agent Routing Logic (from Neo4j)

```python
# From protocols/agent_registry.py

def get_next_agent(current_context: dict) -> str:
    """
    Use Neo4j graph to determine best next agent.

    Factors:
    - Current venture stage
    - Entry point
    - User intent keywords
    - Framework complementarity
    """

    # Query Neo4j for recommended bots
    stage = current_context.get("venture_stage")
    if stage:
        # Use RECOMMENDED_BOT relationships
        query = """
        MATCH (v:VentureStage {id: $stage})-[r:RECOMMENDED_BOT]->(b:Bot)
        RETURN b.id, r.priority
        ORDER BY r.priority
        """

    # Also consider framework COMPLEMENTS relationships
    current_framework = current_context.get("current_framework")
    if current_framework:
        query = """
        MATCH (f1:Framework {name: $framework})-[:COMPLEMENTS]->(f2:Framework)
        MATCH (f2)<-[:USES_FRAMEWORK]-(b:Bot)
        RETURN b.id
        """
```

---

## Venture Stage Workflow Mapping

From Neo4j analysis, here's the recommended agent flow per stage:

### Pre-Opportunity (Finding Problems)

```
Entry → Lawrence (orchestrator)
      → TTA (trend exploration)
      → Beautiful Question (reframing)
      → Scenario Analysis (future exploration)

Tools: Research, GraphRAG
Output: List of candidate opportunities
```

### Opportunity Identified (Understanding Problems)

```
Entry → JTBD (customer understanding)
      → Nested Hierarchies (system mapping)
      → Scenario Analysis (future validation)
      → Research (evidence gathering)

Tools: Research, GraphRAG
Output: Validated opportunity with customer context
```

### Well-Defined Problem (Designing Solution)

```
Entry → Ackoff (DIKW grounding)
      → S-Curve (timing analysis)
      → Nested Hierarchies (intervention design)
      → Red Team (assumption challenge)

Tools: GraphRAG, PWS Grading
Output: Well-defined problem statement with solution criteria
```

### Ready to Build (Execution)

```
Entry → Red Team (final stress test)
      → Knowns (risk mapping)
      → PWS Grading (quality check)

Tools: PWS Grading
Output: Go/No-Go decision with action plan
```

---

## Implementation: TTA Orchestrator Code

```python
# In mindrian_chat.py or new orchestrator module

async def tta_orchestrated_workflow(
    domain: str,
    trend: str,
    user_message: str,
    session_state: dict
) -> dict:
    """
    Execute TTA as orchestrator with multi-agent delegation.
    """

    # Phase 1: Research validation
    research_result = await delegate_to_agent(
        agent="research",
        task="validate_trend",
        input={"domain": domain, "trend": trend},
        expects_return=True
    )

    # Phase 2: Absurd extrapolation (TTA core)
    absurd_scenario = await tta_extrapolate(trend, research_result)

    # Phase 3: Parallel delegation (fan-out)
    parallel_tasks = [
        delegate_to_agent("jtbd", "find_jobs", absurd_scenario),
        delegate_to_agent("nested_hierarchies", "map_systems", absurd_scenario),
        delegate_to_agent("scurve", "analyze_timing", absurd_scenario),
        delegate_to_agent("redteam", "challenge_assumptions", absurd_scenario),
    ]
    results = await asyncio.gather(*parallel_tasks)

    # Phase 4: Synthesis (fan-in)
    opportunity_map = synthesize_findings(results)

    # Phase 5: Validation
    graded = await delegate_to_agent(
        agent="pws_grading",
        task="score_opportunities",
        input=opportunity_map
    )

    return {
        "domain": domain,
        "trend": trend,
        "absurd_scenario": absurd_scenario,
        "opportunities": graded,
        "next_steps": generate_next_steps(graded)
    }
```

---

## Framework Complementarity Map (from Neo4j)

```
JTBD ←→ Process Mapping ←→ User Journey Mapping
           ↓
Design Thinking ←→ JTBD
           ↓
Knowns Matrix ←→ Cynefin
           ↓
System Archetypes ←→ 12 Leverage Points
           ↓
Technology Complex ←→ 12 Leverage Points
```

This tells us which frameworks naturally flow into each other, informing A2A handoff decisions.

---

## Summary: The A2A Orchestration Pattern

1. **Entry Point Detection** → Route to appropriate orchestrator
2. **Orchestrator Initialization** → Set up context, call services
3. **Workshop Delegation** → Fan-out to specialist agents
4. **Service Calls** → GraphRAG, Research, Grading as needed
5. **Synthesis** → Fan-in results back to orchestrator
6. **Validation** → PWS Grading check
7. **Handoff or Complete** → Either switch to next stage or conclude

The key insight: **TTA is the natural root because it starts with the unknown and progressively defines the problem space, calling other agents as specialists for specific analyses.**
