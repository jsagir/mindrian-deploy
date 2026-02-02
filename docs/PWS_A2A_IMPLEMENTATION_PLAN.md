# PWS A2A Implementation Plan

## Comprehensive Architecture for Problems Worth Solving Methodology

Based on the complete PWS curriculum, this document maps all tools, processes, and frameworks to Mindrian's A2A multi-agent architecture.

> **IMPORTANT**: See `docs/A2A_PRACTICAL_ARCHITECTURE.md` for consolidated architectural decisions on implementation approach.

---

## Part 0: Key Architectural Decisions (Summary)

These decisions guide implementation:

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Classification** | Two-stage (Cynefin + PWS) inline in Python | Cynefin tells you *how uncertain*, PWS tells you *where in lifecycle*. No separate service until multiple clients need it. |
| **Context Separation** | Artifacts vs Frames | TTA speculation shouldn't become JTBD's "facts". Frames scoped to agent; artifacts persist. |
| **Red Team** | Cross-cutting middleware | Validates at ANY stage as checkpoint, not a final destination. |
| **Journey Mapping** | Cross-cutting view | Any agent can request journey context. |
| **MVP Scope** | 4 agents: TTA → JTBD → Red Team → Validation | Complete loop with minimal complexity. |
| **Existing Code** | Layer on top, don't rewrite | Bots work; add orchestration interface. |

### Phase Transition Graph

```
exploring → framing → defining → solving → validating → complete
              ↓         ↓                      ↓
           exploring  framing               stuck → framing
```

Explicit "stuck" state forces acknowledgment rather than infinite loops.

### Red Team as Middleware Pattern

```python
async def execute_with_validation(agent, input):
    result = await agent.execute(input)
    if should_validate(agent, input.phase):
        validation = await red_team_middleware.validate(result)
        if not validation.passed:
            return {...result, challenges: validation.challenges, needs_revision: True}
    return result
```

---

## Part 1: Architecture Overview

### The PWS Learning Journey as A2A Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        PWS METHODOLOGY PIPELINE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  FOUNDATIONS        TWO MODELS         EXPLORATION          VALIDATION      │
│  ───────────        ──────────         ───────────          ──────────      │
│                                                                              │
│  ┌──────────┐      ┌──────────┐       ┌──────────┐        ┌──────────┐     │
│  │ Problem  │      │ Problem  │       │Un-Defined│        │Portfolio │     │
│  │ vs       │  →   │ Types    │   →   │   or     │    →   │   of     │     │
│  │ Solution │      │ Model    │       │Ill-Defined│       │Opportun. │     │
│  └──────────┘      └──────────┘       └──────────┘        └──────────┘     │
│       │                 │                  │                    │           │
│       │            ┌──────────┐            │               ┌──────────┐     │
│       │            │Uncertain │            │               │Well-Def  │     │
│       │            │vs Risk   │            │               │Problem   │     │
│       │            │Model     │            │               └──────────┘     │
│       │            └──────────┘            │                    │           │
│       │                 │                  │               ┌──────────┐     │
│       └─────────────────┴──────────────────┘               │Solution  │     │
│                         │                                  │& Biz Case│     │
│                    ORCHESTRATION                           └──────────┘     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Part 2: Microservices Architecture

### Service Layer Design

```yaml
services:
  # === CORE SERVICES ===

  problem_classifier:
    description: "Classifies problems into Un-defined, Ill-defined, Well-defined"
    inputs:
      - user_description: string
      - domain_context: string
    outputs:
      - problem_type: enum[un-defined, ill-defined, well-defined]
      - confidence: float
      - recommended_tools: list[string]
      - uncertainty_risk_quadrant: enum[high-u-low-r, high-u-high-r, low-u-low-r, low-u-high-r]
    endpoint: /api/classify

  research_service:
    description: "Conducts primary and secondary research"
    tools:
      - tavily_search
      - google_trends (SerpAPI)
      - arxiv_search
      - patent_search
    inputs:
      - query: string
      - domain: string
      - research_type: enum[trends, validation, prior_art, market]
    outputs:
      - findings: list[dict]
      - sources: list[string]
      - summary: string
    endpoint: /api/research

  graphrag_service:
    description: "Neo4j + vector hybrid for relationship-aware context"
    capabilities:
      - framework_lookup
      - case_study_retrieval
      - concept_relationships
      - tool_recommendations
    endpoint: /api/graphrag

  pws_grading_service:
    description: "Scores opportunities against PWS criteria"
    criteria:
      - is_it_real: float  # Does this problem matter?
      - can_we_win: float  # Can we solve it?
      - is_it_worth_it: float  # Is there enough value?
    inputs:
      - opportunity: dict
      - validation_data: dict
    outputs:
      - score: float
      - grade: string
      - feedback: string
      - gaps: list[string]
    endpoint: /api/grade

  # === ANALYSIS SERVICES ===

  trend_analyzer:
    description: "Identifies and analyzes trends in a domain"
    inputs:
      - domain: string
      - timeframe: enum[short, medium, long]
    outputs:
      - trends: list[Trend]
      - macro_changes: list[MacroChange]
      - s_curve_positions: list[SCurveAnalysis]
    endpoint: /api/trends

  systems_mapper:
    description: "Creates nested hierarchy and systems maps"
    inputs:
      - focal_point: string
      - domain: string
      - levels_up: int
      - levels_down: int
    outputs:
      - hierarchy_map: dict
      - reverse_salients: list[string]
      - leverage_points: list[LeveragePoint]
      - systems_diagram: string  # Mermaid or DOT format
    endpoint: /api/systems

  scenario_builder:
    description: "Builds 2x2 scenario matrices"
    inputs:
      - domain: string
      - trends: list[string]
    outputs:
      - axes: list[Axis]
      - matrix: ScenarioMatrix
      - scenarios: list[Scenario]
    endpoint: /api/scenarios

  opportunity_validator:
    description: "Validates opportunities with standard questions"
    inputs:
      - opportunity: dict
      - validation_type: enum[reality, timing, competition, impact]
    outputs:
      - is_valid: bool
      - evidence: list[string]
      - gaps: list[string]
      - confidence: float
    endpoint: /api/validate

  # === VISUALIZATION SERVICES ===

  mind_map_generator:
    description: "Creates visual mind maps"
    inputs:
      - central_concept: string
      - branches: list[Branch]
    outputs:
      - mind_map: dict  # JSON structure
      - visualization: string  # Mermaid format
    endpoint: /api/mindmap

  process_mapper:
    description: "Maps user processes and journeys"
    inputs:
      - process_name: string
      - steps: list[ProcessStep]
    outputs:
      - process_map: dict
      - importance_satisfaction_matrix: dict
      - opportunity_gaps: list[Gap]
    endpoint: /api/process

  whitespace_mapper:
    description: "Creates whitespace market maps"
    inputs:
      - domain: string
      - axis_x: string
      - axis_y: string
      - players: list[dict]
    outputs:
      - whitespace_map: dict
      - opportunities: list[dict]
    endpoint: /api/whitespace
```

---

## Part 3: Agent Architecture

### Agent Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ORCHESTRATOR LAYER                                 │
│                                                                              │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐                 │
│  │   LAWRENCE     │  │     TTA        │  │   SCENARIO     │                 │
│  │   (Default)    │  │  (Un-Defined)  │  │   (Futures)    │                 │
│  │                │  │                │  │                │                 │
│  │ Routes users   │  │ Orchestrates   │  │ Orchestrates   │                 │
│  │ to appropriate │  │ trend-based    │  │ scenario-based │                 │
│  │ methodology    │  │ exploration    │  │ exploration    │                 │
│  └───────┬────────┘  └───────┬────────┘  └───────┬────────┘                 │
│          │                   │                   │                          │
│          └───────────────────┼───────────────────┘                          │
│                              │                                              │
└──────────────────────────────┼──────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           WORKSHOP LAYER                                     │
│                                                                              │
│  UN-DEFINED TOOLS:          ILL-DEFINED TOOLS:          WELL-DEFINED TOOLS: │
│  ┌─────────┐ ┌─────────┐   ┌─────────┐ ┌─────────┐    ┌─────────┐          │
│  │ NESTED  │ │ RED     │   │  JTBD   │ │ S-CURVE │    │ PROBLEM │          │
│  │ HIER.   │ │ TEAM    │   │         │ │         │    │ DEFINER │          │
│  └─────────┘ └─────────┘   └─────────┘ └─────────┘    └─────────┘          │
│                                                                              │
│  ┌─────────┐               ┌─────────┐ ┌─────────┐    ┌─────────┐          │
│  │ WICKED  │               │ BEAUTI- │ │  BONO   │    │ SOLUTION│          │
│  │ PROBLEM │               │ FUL Q   │ │ (HATS)  │    │ DESIGNER│          │
│  └─────────┘               └─────────┘ └─────────┘    └─────────┘          │
│                                                                              │
│                            ┌─────────┐ ┌─────────┐    ┌─────────┐          │
│                            │ DOMAIN  │ │ KNOWNS  │    │ BIZ CASE│          │
│                            │ EXPLORER│ │ MATRIX  │    │ BUILDER │          │
│                            └─────────┘ └─────────┘    └─────────┘          │
└─────────────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SUB-AGENT LAYER                                    │
│                                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  TREND      │  │  PROCESS    │  │  FOUR       │  │  PRIOR ART  │        │
│  │  RESEARCHER │  │  MAPPER     │  │  ACTIONS    │  │  SEARCHER   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  ISSUE TREE │  │  ROOT CAUSE │  │  MULLINS    │  │  VALIDATION │        │
│  │  BUILDER    │  │  ANALYZER   │  │  SCORER     │  │  AGENT      │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SERVICE LAYER                                      │
│                                                                              │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐│
│  │ GRAPHRAG  │  │ RESEARCH  │  │ GRADING   │  │ SYSTEMS   │  │ VISUALIZE ││
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘  └───────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Part 4: Tool-to-Agent-to-Service Mapping

### Complete Tool Catalog with Implementation

```yaml
# === FOUNDATION TOOLS ===

the_5_ws:
  primary_agent: lawrence
  sub_agents: []
  services: [graphrag]
  problem_type: all
  implementation:
    workflow:
      - Extract Who, What, When, Where, Why from user input
      - Use GraphRAG to find related frameworks
      - Structure findings into story format
    output: 5w_analysis

three_kinds_of_problems:
  primary_agent: problem_classifier
  sub_agents: []
  services: [problem_classifier]
  problem_type: all
  implementation:
    workflow:
      - Analyze problem description
      - Classify into un-defined/ill-defined/well-defined
      - Route to appropriate tool set
    output: problem_classification

# === UN-DEFINED PROBLEM TOOLS ===

trending_to_absurd:
  primary_agent: tta
  sub_agents:
    - trend_researcher
    - validation_agent
  services:
    - research_service
    - graphrag_service
  problem_type: un-defined
  implementation:
    phases:
      1_domain_selection:
        agent: tta
        action: "Help user select domain of interest"

      2_trend_identification:
        agent: trend_researcher
        service: research_service
        action: "Generate list of current real trends"

      3_trend_selection:
        agent: tta
        action: "Choose one trend for deep exploration"

      4_absurd_extrapolation:
        agent: tta
        questions:
          - "What if everything were...?"
          - "What if everyone were to do...?"
          - "What if nobody were to do...?"

      5_future_description:
        agent: tta
        questions:
          - "What is missing in this world?"
          - "What products/services/policies needed?"
          - "What could we do that we cannot do now?"
          - "What won't we be able to do?"
          - "What will be needed to live in such a future?"
          - "What could prevent/slow unwanted trends?"

      6_opportunity_generation:
        agent: tta
        output: opportunity_list

      7_validation:
        agent: red_team
        handoff_type: DELEGATE
        questions:
          - "Is this opportunity real?"
          - "What would have to be true to work on this now?"
          - "Can existing solutions address this?"

scenario_analysis:
  primary_agent: scenario
  sub_agents:
    - trend_researcher
    - scenario_builder
    - validation_agent
  services:
    - research_service
    - scenario_builder
    - graphrag_service
  problem_type: un-defined
  implementation:
    phases:
      1_domain_selection:
        agent: scenario
        action: "Help user select domain"

      2_trend_identification:
        agent: trend_researcher
        service: research_service

      3_axis_creation:
        agent: scenario
        service: scenario_builder
        action: |
          Create possible axes:
          - Each axis presents two alternatives
          - Examples: this/that, much/little, one/many

      4_axis_selection:
        agent: scenario
        action: "Select two axes for 2x2 matrix"

      5_category_definition:
        agent: scenario
        action: "Determine categories within each quadrant"

      6_matrix_generation:
        agent: scenario
        service: scenario_builder
        output: scenario_matrix

      7_analysis:
        options:
          extensive:
            action: |
              Look across all scenarios:
              - What's missing across ALL scenarios?
              - What's needed no matter what?
              - What must we do today regardless?
          intensive:
            action: |
              Deep dive one scenario:
              - If unwanted: what prevents/slows it?
              - If desired: what brings it about?
              - What's missing here?

      8_opportunity_generation:
        agent: scenario
        output: opportunity_list

      9_validation:
        agent: red_team
        handoff_type: DELEGATE

nested_hierarchies:
  primary_agent: nested_hierarchies
  sub_agents:
    - trend_researcher
    - systems_mapper
    - validation_agent
  services:
    - research_service
    - systems_mapper
    - graphrag_service
  problem_type: un-defined
  implementation:
    phases:
      1_domain_selection:
        agent: nested_hierarchies
        action: "Identify domain of interest"

      2_focal_point:
        agent: nested_hierarchies
        action: "Choose focal point within domain"

      3_trend_identification:
        agent: trend_researcher
        action: |
          Identify trends:
          - What is changing and how fast?
          - Try carrying trend to absurd conclusion

      4_element_identification:
        agent: nested_hierarchies
        action: "Identify key elements (human and material) and sub-systems"

      5_hierarchy_mapping:
        agent: nested_hierarchies
        service: systems_mapper
        action: |
          Create nested hierarchy:
          - Levels above focal point
          - Levels below focal point
          - Note: same trend could be part of different systems

      6_systems_map:
        agent: nested_hierarchies
        service: systems_mapper
        output: systems_diagram

      7_impact_analysis:
        agent: nested_hierarchies
        questions:
          - "How will trend impact rest of hierarchy?"
          - "Where are the reverse salients?"
          - "What leverage points exist?"

      8_opportunity_identification:
        agent: nested_hierarchies
        questions:
          - "How can we make elements more efficient/effective?"
          - "How can we improve interactions among elements?"
          - "How can we improve overall system performance?"
          - "How can we re-imagine the purpose/meaning of entire system?"

      9_validation:
        agent: red_team
        handoff_type: DELEGATE

red_teaming:
  primary_agent: red_team
  sub_agents:
    - trend_researcher
    - validation_agent
  services:
    - research_service
    - graphrag_service
  problem_type: both
  dual_purpose: true  # Tool AND validation step
  implementation:
    phases:
      1_domain_selection:
        agent: red_team
        action: "Select domain or question"

      2_status_quo_mapping:
        agent: red_team
        action: "Identify key products/services/policies maintaining status quo"

      3_assumption_extraction:
        agent: red_team
        action: "Identify supporting assumptions and which can be challenged"

      4_trend_research:
        agent: trend_researcher
        service: research_service

      5_challenge_questions:
        agent: red_team
        questions:
          - "What makes this opportunity real and worthy of solving?"
          - "What could make this problem unimportant?"
          - "Why has it not been solved to date?"
          - "What will be needed to make X work in the future?"
          - "What will be needed to get rid of X?"
          - "What could completely replace X?"
          - "What if we could...?"
          - "What would surprise you?"

      6_synthesis:
        agent: red_team
        outputs:
          - challenged_assumptions
          - new_capabilities_needed
          - new_products_services_policies
          - disrupted_systems

wicked_problems:
  primary_agent: nested_hierarchies
  sub_agents:
    - trend_researcher
    - systems_mapper
    - validation_agent
  services:
    - research_service
    - systems_mapper
  problem_type: un-defined
  implementation:
    phases:
      1_domain_selection:
        agent: nested_hierarchies

      2_domain_research:
        agent: trend_researcher
        action: "Research domain to understand factors involved"

      3_subsystem_identification:
        agent: nested_hierarchies
        action: "Identify relevant sub-systems"

      4_systems_mapping:
        agent: nested_hierarchies
        service: systems_mapper
        output: systems_map

      5_leverage_identification:
        agent: nested_hierarchies
        action: |
          Identify points of leverage using Meadows' hierarchy:
          - Parameters → Paradigms (weakest to strongest)
        tools_to_apply:
          - jobs_to_be_done
          - user_experiences
          - four_actions_framework
          - trending_to_absurd
          - red_teaming
          - white_space_mapping

      6_opportunity_synthesis:
        agent: nested_hierarchies

      7_validation:
        agent: red_team
        handoff_type: DELEGATE

# === ILL-DEFINED PROBLEM TOOLS ===

combining_ideas:
  primary_agent: bono
  sub_agents:
    - validation_agent
  services:
    - graphrag_service
  problem_type: ill-defined
  implementation:
    phases:
      1_starting_point:
        agent: bono
        action: "Start with something of importance"

      2_characteristic_listing:
        agent: bono
        action: "List out its characteristics"

      3_unrelated_ideas:
        agent: bono
        action: "List unrelated ideas/products/services with opposite characteristics"

      4_combination:
        agent: bono
        action: "Make combinations"

      5_synthesis:
        agent: bono
        action: "Identify surprising, unusual, non-obvious intersectional ideas"

      6_alternative:
        agent: bono
        action: "Who from unrelated field could give different perspective?"

      7_validation:
        agent: red_team
        handoff_type: DELEGATE

s_curves:
  primary_agent: scurve
  sub_agents:
    - trend_researcher
    - validation_agent
  services:
    - research_service
    - trend_analyzer
  problem_type: ill-defined
  implementation:
    phases:
      1_domain_selection:
        agent: scurve

      2_limit_identification:
        agent: scurve
        service: trend_analyzer
        action: "Identify technologies reaching physical or market limits"

      3_evidence_gathering:
        agent: trend_researcher
        action: "How do you know? Give examples and research."

      4_opportunity_synthesis:
        agent: scurve
        questions:
          - "What could replace existing technology at top of S-curve?"
          - "What's needed technologically/market-wise to replace?"
          - "Don't forget technology complex concept"

      5_validation:
        agent: red_team
        handoff_type: DELEGATE

dominant_designs:
  primary_agent: scurve
  sub_agents:
    - trend_researcher
    - validation_agent
  services:
    - research_service
    - trend_analyzer
  problem_type: ill-defined
  implementation:
    phases:
      1_domain_selection:
        agent: scurve

      2_design_identification:
        agent: scurve
        action: |
          Identify dominant designs falling apart:
          - Technological
          - Non-technological (political, economic, social)

      3_discontinuity_analysis:
        agent: scurve
        service: trend_analyzer
        questions:
          - "Is there a technology reaching its limit helping break apart this design?"

      4_evidence_gathering:
        agent: trend_researcher

      5_opportunity_synthesis:
        agent: scurve
        questions:
          - "What is being destroyed?"
          - "What are possibilities for new dominant design?"

      6_validation:
        agent: red_team
        handoff_type: DELEGATE

macro_changes:
  primary_agent: scurve
  sub_agents:
    - trend_researcher
    - systems_mapper
    - validation_agent
  services:
    - research_service
    - systems_mapper
  problem_type: ill-defined
  implementation:
    phases:
      1_domain_selection:
        agent: scurve
        action: "Choose domain of interest"

      2_macro_change_identification:
        agent: trend_researcher
        action: "What are important macro-changes in that domain?"

      3_change_selection:
        agent: scurve
        action: "Select one to explore"

      4_pest_analysis:
        agent: scurve
        service: systems_mapper
        action: |
          Construct PEST systems diagram:
          - Political
          - Economic
          - Social
          - Technological

      5_destruction_analysis:
        agent: scurve
        questions:
          - "What is changing within each PEST category?"
          - "What is being destroyed?"
          - "Where are discontinuities?"
          - "What are 1st, 2nd, 3rd order consequences?"

      6_opportunity_synthesis:
        agent: scurve
        questions:
          - "What are next big problems worth solving?"
          - "Where are opportunities to build on/replace what's destroyed?"

      7_validation:
        agent: red_team
        handoff_type: DELEGATE

user_process_mapping:
  primary_agent: jtbd
  sub_agents:
    - process_mapper
    - validation_agent
  services:
    - process_mapper
  problem_type: ill-defined
  implementation:
    phases:
      1_domain_selection:
        agent: jtbd
        action: "Choose domain you know well"

      2_process_identification:
        agent: jtbd
        action: "Identify important process or user experience"

      3_process_mapping:
        agent: process_mapper
        service: process_mapper
        action: "Create process map - choose relevant level of detail"

      4_step_rating:
        agent: jtbd
        service: process_mapper
        action: |
          Rate each step on two criteria:
          - Importance to total process
          - Satisfaction (how well it's addressed)

      5_gap_analysis:
        agent: jtbd
        action: "Focus on high importance / low satisfaction steps"

      6_barrier_identification:
        agent: jtbd
        action: "What is preventing these steps from being addressed well?"

      7_opportunity_synthesis:
        agent: jtbd

      8_validation:
        agent: red_team
        handoff_type: DELEGATE

jobs_to_be_done:
  primary_agent: jtbd
  sub_agents:
    - process_mapper
    - validation_agent
  services:
    - process_mapper
  problem_type: ill-defined
  implementation:
    phases:
      1_domain_selection:
        agent: jtbd
        action: "Choose domain you know well"

      2_job_identification:
        agent: jtbd
        questions:
          - "What are people trying to accomplish?"
          - "What progress are they looking to make?"
          - "What specific outcomes are they looking for?"

      3_barrier_identification:
        agent: jtbd
        action: "What is preventing them from doing the job they want?"

      4_process_decomposition:
        agent: process_mapper
        action: "Break job into components that can be improved (maximize or minimize)"

      5_job_statement:
        agent: jtbd
        template: |
          - Subject (stakeholder): e.g. nurse, clinician, hospital
          - Action verb: e.g. prepare, collect, insert
          - Desired outcome: e.g. reduce patient discomfort
          - Vector of measurement: e.g. minimize time, maximize output
          - Context (sometimes): e.g. caused by..., in order to...

      6_step_rating:
        agent: jtbd
        action: "Rate steps by importance and satisfaction"

      7_opportunity_synthesis:
        agent: jtbd

      8_validation:
        agent: red_team
        handoff_type: DELEGATE

beautiful_question:
  primary_agent: beautiful_question
  sub_agents:
    - process_mapper
    - validation_agent
  services:
    - process_mapper
  problem_type: ill-defined
  formula: "Q (questioning) + A (action) = I (innovation)"
  warning: "Q - A = P (philosophy)"
  implementation:
    phases:
      1_domain_selection:
        agent: beautiful_question

      2_why_phase:
        agent: beautiful_question
        action: "Person encounters less than ideal situation → asks WHY"

      3_what_if_phase:
        agent: beautiful_question
        action: "Person imagines improvements → asks WHAT IF possibilities"

      4_how_phase:
        agent: beautiful_question
        action: "Person tries to implement → figures out HOW"

      5_barrier_identification:
        agent: beautiful_question
        action: "Identify what prevents ideal"
        supporting_tools:
          - process_maps
          - job_statements

      6_opportunity_synthesis:
        agent: beautiful_question

      7_validation:
        agent: red_team
        handoff_type: DELEGATE

terms_of_competition:
  primary_agent: bono
  sub_agents:
    - four_actions_agent
    - jtbd
    - validation_agent
  services:
    - process_mapper
  problem_type: ill-defined
  implementation:
    phases:
      1_domain_selection:
        agent: bono

      2_current_state:
        agent: bono
        action: |
          Start with where you are:
          - Distinctive advantage of product/service
          - Current job(s) to be done
          - Current terms of competition:
            - Features and functionalities
            - Performance measures
            - Customer groups
            - Emotions and images
            - Positioning

      3_barrier_identification:
        agent: bono
        action: "What prevents ideal user experience?"
        supporting_tools:
          - process_maps
          - job_statements

      4_unconstrain:
        agent: bono
        questions:
          - "What received wisdom can be questioned?"
          - "What dominant designs can be challenged?"
          - "What corporate/societal assumptions can be challenged?"
          - "Regarding business models?"
          - "Regarding technologies?"
          - "Regarding user experiences?"

      5_four_actions:
        agent: four_actions_agent
        framework:
          - eliminate: "What factors can be eliminated?"
          - reduce: "What factors can be reduced well below standard?"
          - raise: "What factors can be raised well above standard?"
          - create: "What factors can be created that industry never offered?"

      6_new_jobs:
        agent: jtbd
        handoff_type: DELEGATE
        questions:
          - "What new jobs to be done using original terms differently?"
          - "Think in terms of pains and gains"
          - "Different trade-offs indicating different jobs?"
          - "Niche applications?"

      7_space_expansion:
        agent: bono
        action: |
          Expand space by:
          - Creating new ill-defined problems (How do I X without...)
          - Creating new un-defined problems (What is the future of...)
          - Finding high uncertainty / low risk opportunities

      8_validation:
        agent: red_team
        handoff_type: DELEGATE

white_space_mapping:
  primary_agent: bono
  sub_agents:
    - validation_agent
  services:
    - whitespace_mapper
  problem_type: ill-defined
  implementation:
    phases:
      1_domain_selection:
        agent: bono

      2_terms_identification:
        agent: bono
        action: "Identify relevant terms of competition"

      3_axis_selection:
        agent: bono
        action: "Choose two as axes (price is often good)"

      4_map_creation:
        agent: bono
        service: whitespace_mapper
        action: "Create map based on current products/services/companies"

      5_opportunity_identification:
        agent: bono
        questions:
          - "Where are the opportunities?"
          - "Where are the next big problems to solve?"

      6_validation:
        agent: red_team
        handoff_type: DELEGATE

innovation_of_meaning:
  primary_agent: bono
  sub_agents:
    - jtbd
    - four_actions_agent
    - validation_agent
  services:
    - trend_analyzer
  problem_type: ill-defined
  implementation:
    phases:
      1_domain_selection:
        agent: bono
        action: "Choose domain of particular interest"

      2_current_analysis:
        agent: bono
        action: |
          Identify:
          - Current terms of competition
          - Current job to be done

      3_meaning_exploration:
        agent: bono
        questions:
          - "Can you imagine a new job to be done?"
          - "A new way of perceiving the product/service?"
          - "Other jobs that could benefit from re-purposing?"
          - "Other emotional/social needs that could be filled?"
        with_or_without: "changing terms of competition"

      4_supporting_analysis:
        tools:
          - user_needs
          - technology_s_curves
          - dominant_designs
          - four_actions_framework

      5_opportunity_synthesis:
        agent: bono
        action: "Where are opportunities to create new meanings?"

      6_validation:
        agent: red_team
        handoff_type: DELEGATE

reverse_salients:
  primary_agent: nested_hierarchies
  sub_agents:
    - trend_researcher
    - systems_mapper
    - validation_agent
  services:
    - research_service
    - systems_mapper
  problem_type: ill-defined
  implementation:
    phases:
      1_domain_selection:
        agent: nested_hierarchies

      2_domain_research:
        agent: trend_researcher
        questions:
          - "What are key technologies and systems?"
          - "How is domain changing?"

      3_domain_mapping:
        agent: nested_hierarchies
        service: systems_mapper
        action: "Prepare domain map identifying reverse salient"

      4_salient_analysis:
        agent: nested_hierarchies
        questions:
          - "Why is this a reverse salient?"
          - "What measures of efficiency, effectiveness, reliability, profitability, useability are NOT being met?"

      5_opportunity_synthesis:
        agent: nested_hierarchies
        tools_to_apply:
          - intersectional_innovations
          - new_scientific_technological_trends
          - jobs_to_be_done
          - four_actions_framework
          - scenarios
          - systems_analysis

      6_validation:
        agent: red_team
        handoff_type: DELEGATE

life_cycles:
  primary_agent: jtbd
  sub_agents:
    - process_mapper
    - trend_researcher
    - validation_agent
  services:
    - process_mapper
    - research_service
  problem_type: ill-defined
  implementation:
    phases:
      1_domain_research:
        agent: trend_researcher

      2_lifecycle_mapping:
        agent: process_mapper
        service: process_mapper
        questions:
          - "Where are the inefficiencies?"
          - "What is sub-optimal?"
          - "How can this be measured?"
          - "What measures are NOT being met?"

      3_opportunity_synthesis:
        agent: jtbd
        tools_to_apply:
          - jobs_to_be_done
          - user_experiences
          - four_actions_framework
          - trending_to_absurd
          - red_teaming
          - changes_of_meaning
          - white_space_mapping

      4_validation:
        agent: red_team
        handoff_type: DELEGATE

leveraging_resources:
  primary_agent: jtbd
  sub_agents:
    - trend_researcher
    - validation_agent
  services:
    - research_service
  problem_type: ill-defined
  implementation:
    phases:
      1_company_research:
        agent: trend_researcher
        action: "Research company or industry"

      2_portfolio_mapping:
        agent: jtbd
        action: |
          Prepare product portfolio map based on:
          - Core technologies (product or process)
          - Core competencies

      3_extension_exploration:
        agent: jtbd
        questions:
          - "How can core technologies be extended/adapted into new market spaces?"
          - "What new product categories are possible?"

      4_opportunity_synthesis:
        agent: jtbd
        tools_to_apply:
          - jobs_to_be_done
          - user_experiences
          - four_actions_framework
          - trending_to_absurd
          - red_teaming
          - changes_of_meaning
          - white_space_mapping

      5_validation:
        agent: red_team
        handoff_type: DELEGATE

# === WELL-DEFINED PROBLEM TOOLS ===

well_defined_problem_creation:
  primary_agent: problem_definer
  sub_agents:
    - mind_map_generator
    - issue_tree_builder
    - root_cause_analyzer
    - validation_agent
  services:
    - research_service
    - mind_map_generator
  problem_type: well-defined
  implementation:
    phases:
      1_opportunity_selection:
        agent: problem_definer
        action: "What is the opportunity you want to address?"

      2_trend_research:
        agent: trend_researcher
        action: "What are relevant market trends making this exciting?"

      3_validation_research:
        agent: validation_agent
        methods:
          - primary_research
          - secondary_research

      4_mind_mapping:
        agent: mind_map_generator
        service: mind_map_generator
        action: "Organize data on Mind Map"

      5_5w_story:
        agent: problem_definer
        action: "Organize research around 5 W's to create basic story"

      6_root_cause_analysis:
        agent: root_cause_analyzer
        methods:
          - disaggregation
          - five_whys

      7_solution_criteria:
        agent: problem_definer
        action: |
          Determine what solution needs to deliver:
          - Pains relieved
          - Gains achieved

      8_iteration:
        agent: problem_definer
        action: "Validate and iterate until problem statement is 'right'"

      9_final_statement:
        agent: problem_definer
        template: |
          How can we help [WHO]
          do [WHAT]
          under these circumstances [CONTEXT]
          in order to accomplish [OUTCOME]?

prior_art_search:
  primary_agent: prior_art_searcher
  sub_agents: []
  services:
    - research_service
  problem_type: well-defined
  implementation:
    phases:
      1_problem_statement:
        agent: prior_art_searcher
        action: "What is the well-defined problem (as understood to date)?"

      2_prior_art_search:
        agent: prior_art_searcher
        service: research_service
        requirements:
          - minimum_sources: 3-5
          - focus: "science, not opportunity/market/competitors"
          - include:
            - "Introduction to problem from scientific/technological perspective"
            - "Standard tests most often used and accepted"
            - "Citations on the slide"

      3_synthesis:
        agent: prior_art_searcher
        questions:
          - "What have you learned from prior art?"
          - "How has this changed understanding of opportunity?"
          - "What constraints are you likely to face?"

solution_development:
  primary_agent: solution_designer
  sub_agents:
    - issue_tree_builder
    - root_cause_analyzer
  services:
    - mind_map_generator
  problem_type: well-defined
  implementation:
    phases:
      1_problem_disaggregation:
        agent: issue_tree_builder
        methods:
          - mind_map_first
          - mece_structure

      2_prioritization:
        agent: solution_designer
        method: "80/20 Rule to identify most important issues"

      3_root_cause_analysis:
        agent: root_cause_analyzer

      4_solution_strategy:
        agent: solution_designer
        strategies:
          - brute_force: "Try many approaches"
          - targeted_development: "Focus on specific solution"
          - wait_for_eureka: "Let insights emerge"

      5_workplan:
        agent: solution_designer
        action: "Build implementation workplan"

business_case:
  primary_agent: biz_case_builder
  sub_agents:
    - mullins_scorer
    - validation_agent
  services:
    - pws_grading_service
  problem_type: well-defined
  implementation:
    phases:
      1_opportunity_summary:
        agent: biz_case_builder
        action: "What is the opportunity?"

      2_background:
        agent: biz_case_builder
        include:
          - "Near and long-term trends"
          - "Literature search"
          - "Mind maps, process maps, issue trees"

      3_use_case:
        agent: biz_case_builder
        action: "Why is this worth addressing? Use the W's"
        questions:
          - "To whom is this important?"
          - "Why is it important?"

      4_problem_statement:
        agent: biz_case_builder
        template: "How can we help [WHO] do [WHAT] under [CONTEXT] to accomplish [OUTCOME]?"

      5_solution_vision:
        agent: biz_case_builder
        questions:
          - "What will solution look like?"
          - "What must it deliver?"
          - "Pains relieved / gains achieved"
          - "Root causes addressed"

      6_technical_plan:
        agent: solution_designer

      7_business_case:
        agent: mullins_scorer
        service: pws_grading_service
        framework: "Mullins Model"

      8_validation_summary:
        agent: validation_agent

      9_conclusion:
        agent: biz_case_builder
        questions:
          - "Problem: Is it real?"
          - "Solution: Can we win?"
          - "Business case: Is it worth it?"

# === PORTFOLIO & SYNTHESIS TOOLS ===

portfolio_of_opportunities:
  primary_agent: lawrence
  sub_agents:
    - validation_agent
  services:
    - pws_grading_service
  problem_type: synthesis
  implementation:
    phases:
      1_opportunity_selection:
        agent: lawrence
        action: "Select opportunities that deeply interest you"

      2_opportunity_description:
        agent: lawrence
        for_each_opportunity:
          - "Describe the opportunity"
          - "What is the domain?"
          - "What are macro trends? Show research."
          - "Where did it come from? Be explicit about tools used."
          - "Describe a specific use case"

      3_pws_validation:
        agent: lawrence
        service: pws_grading_service
        questions:
          - "Is it real? Does this problem matter to real people?"
          - "Can we win? Can we actually create a solution?"
          - "Is it worth it? Is there enough to be gained?"
          - "What validation do you have?"

      4_ranking:
        agent: lawrence
        action: "Rank opportunities in order of preference"

mind_map:
  primary_agent: mind_map_generator
  sub_agents: []
  services:
    - mind_map_generator
  problem_type: all
  implementation:
    phases:
      1_central_concept:
        agent: mind_map_generator
        action: "Define main concept or problem (short phrase/sentence + picture)"

      2_primary_branches:
        agent: mind_map_generator
        action: "Create primary branches in radial hierarchy structure"
        note: "Choosing 'right' primary branches is important for lower-level thinking"

      3_sub_branches:
        agent: mind_map_generator
        action: "Create sub-branches to desired level of granularity"

      4_connection:
        agent: mind_map_generator
        action: "Connect ideas and create a 'story'"
```

---

## Part 5: Tool Combination Patterns (ComCo)

### Pre-Defined Workflows

```yaml
tool_combinations:

  foundational_exploration:
    tools: [the_5_ws, three_kinds_of_problems]
    purpose: "Initial exploration and problem classification"
    when_to_use: "Early stages to broadly understand problem"
    output: problem_classification_and_basic_story

  systemic_discovery:
    tools: [nested_hierarchies, causal_loop_diagram, leverage_points]
    purpose: "Understand system-level impact and intervention points"
    when_to_use: "Complex, multi-layered problems (environmental, organizational)"
    output: systems_map_with_leverage_points

  future_focused_scenario:
    tools: [scenario_analysis, trending_to_absurd, pest_analysis]
    purpose: "Map alternative futures and macro-environmental impacts"
    when_to_use: "Highly uncertain sectors (healthcare, urban planning)"
    output: scenario_matrix_with_opportunities

  problem_decomposition:
    tools: [issue_tree, root_cause_analysis, mece]
    purpose: "Break down problem into manageable parts"
    when_to_use: "Diagnosing operational, quality, or service issues"
    output: issue_tree_with_root_causes

  market_exploration:
    tools: [market_research, white_space_mapping, terms_of_competition]
    purpose: "Identify market opportunities and competitive dynamics"
    when_to_use: "Market entry, competitive positioning, unmet needs"
    output: whitespace_map_with_opportunities

  opportunity_identification:
    tools: [jobs_to_be_done, white_space_mapping, value_proposition]
    purpose: "Pinpoint customer needs and develop value offerings"
    when_to_use: "User-centered product/service design"
    output: job_statements_with_value_propositions

  strategic_growth:
    tools: [ansoff_matrix, kirzner_rule, four_actions_framework]
    purpose: "Formulate growth and value innovation strategies"
    when_to_use: "Established businesses seeking expansion/disruption"
    output: growth_strategy_with_four_actions

  innovation_validation:
    tools: [pws_value_proposition, mullins_model, business_case]
    purpose: "Assess feasibility, viability, strategic value"
    when_to_use: "Later stages to validate proposals"
    output: validated_business_case

  process_improvement:
    tools: [user_process_mapping, pareto_80_20, root_cause_analysis]
    purpose: "Streamline processes by focusing on high-impact areas"
    when_to_use: "Operations optimization, customer experience improvement"
    output: optimized_process_map

  portfolio_development:
    tools: [portfolio_of_opportunities, mind_map, leverage_points]
    purpose: "Build and prioritize innovation opportunities"
    when_to_use: "R&D settings, new venture exploration, resource allocation"
    output: prioritized_opportunity_portfolio
```

---

## Part 6: A2A Handoff Protocols

### Standard Handoff Structure

```yaml
handoff_protocol:
  version: "a2a/v2"

  fields:
    from_agent: string
    to_agent: string
    handoff_type: enum[SWITCH, DELEGATE, CONSULT, RETURN]
    expects_return: bool
    priority: enum[low, normal, high, urgent]

    context:
      domain: string
      problem_type: enum[un-defined, ill-defined, well-defined]
      methodology_in_use: string
      current_phase: string
      previous_findings: dict

    task:
      action: string
      questions_to_answer: list[string]
      tools_to_apply: list[string]
      expected_output: dict

    entities:
      trends: list[Trend]
      opportunities: list[Opportunity]
      assumptions: list[Assumption]
      stakeholders: list[Stakeholder]

    validation_requirements:
      standard_questions: bool  # Always apply 3 validation questions
      red_team_challenge: bool
      pws_grading: bool

  example:
    handoff:
      protocol: "a2a/v2"
      from_agent: "tta"
      to_agent: "nested_hierarchies"
      handoff_type: "DELEGATE"
      expects_return: true
      priority: "normal"

      context:
        domain: "electric vehicles"
        problem_type: "un-defined"
        methodology_in_use: "Trending to the Absurd"
        current_phase: "5_future_description"
        previous_findings:
          trend: "battery technology reaching physical limits"
          absurd_scenario: "What if batteries became 100x more energy-dense?"

      task:
        action: "Map nested hierarchy of EV systems"
        questions_to_answer:
          - "Where does the battery constraint sit in the hierarchy?"
          - "What are the reverse salients?"
          - "What leverage points exist?"
        tools_to_apply:
          - "systems_mapping"
          - "reverse_salient_analysis"
        expected_output:
          system_levels: 5
          reverse_salients: list
          leverage_points: list

      validation_requirements:
        standard_questions: true
        red_team_challenge: true
        pws_grading: false  # Not ready for grading yet
```

### Fan-Out/Fan-In Patterns

```yaml
parallel_delegation_pattern:
  name: "Multi-Agent Problem Discovery"
  trigger: "After absurd scenario or opportunity is generated"

  fan_out:
    orchestrator: tta
    delegates_to:
      - agent: jtbd
        task: "What jobs-to-be-done exist?"

      - agent: nested_hierarchies
        task: "What systems will change?"

      - agent: scurve
        task: "What technologies reaching limits?"

      - agent: red_team
        task: "Challenge assumptions"

  fan_in:
    collector: tta
    synthesis_action: "Synthesize findings into opportunity map"
    inputs:
      - future_jobs
      - system_changes
      - technology_shifts
      - assumption_challenges
    output: opportunity_map

  post_synthesis:
    - agent: ackoff
      task: "Ground in DIKW pyramid"

    - agent: pws_grading
      task: "Score against PWS criteria"

sequential_validation_pattern:
  name: "Standard Validation Pipeline"
  trigger: "After ANY tool generates opportunities"

  sequence:
    1_reality_check:
      questions:
        - "Is this opportunity real?"
        - "What evidence supports this?"
        - "Who has this problem and how do you know?"

    2_timing_check:
      questions:
        - "What would have to be true to work on this now?"
        - "Is the timing right?"
        - "What signals would tell us to proceed?"

    3_competition_check:
      questions:
        - "Can existing solutions address this?"
        - "Who else is working on this?"
        - "What's our unfair advantage?"

    4_impact_check:
      questions:
        - "Is this worth solving?"
        - "What's the scale of impact?"
        - "Who benefits and how much?"

    5_red_team:
      agent: red_team
      handoff_type: DELEGATE
      optional: false  # Always run Red Team on opportunities
```

---

## Part 7: Implementation Roadmap

### Phase 1: Core Services (Foundation)

```yaml
phase_1:
  timeline: "Week 1-2"
  deliverables:
    - problem_classifier_service
    - research_service (enhance existing)
    - validation_service

  agents_to_add:
    - problem_definer
    - validation_agent
    - root_cause_analyzer
```

### Phase 2: Analysis Services

```yaml
phase_2:
  timeline: "Week 3-4"
  deliverables:
    - systems_mapper_service
    - scenario_builder_service
    - trend_analyzer_service

  agents_to_add:
    - systems_mapper
    - scenario_builder
    - trend_researcher
```

### Phase 3: Visualization Services

```yaml
phase_3:
  timeline: "Week 5-6"
  deliverables:
    - mind_map_generator_service
    - process_mapper_service
    - whitespace_mapper_service

  agents_to_add:
    - mind_map_generator
    - process_mapper
    - four_actions_agent
```

### Phase 4: Synthesis & Grading

```yaml
phase_4:
  timeline: "Week 7-8"
  deliverables:
    - portfolio_manager_service
    - mullins_scorer_service
    - business_case_builder_service

  agents_to_add:
    - portfolio_manager
    - mullins_scorer
    - biz_case_builder
```

### Phase 5: Tool Combinations & Workflows

```yaml
phase_5:
  timeline: "Week 9-10"
  deliverables:
    - tool_combination_orchestrator
    - workflow_templates
    - automated_validation_pipeline

  integration:
    - Connect all ComCo patterns
    - Implement fan-out/fan-in
    - Standard validation after every opportunity
```

---

## Part 8: Neo4j Schema Extensions

### New Node Types

```cypher
// Tool nodes
CREATE (:Tool {
  id: "trending_to_absurd",
  name: "Trending to the Absurd",
  problem_type: "un-defined",
  why_use: ["Get past presentism", "Challenge current thinking"],
  when_to_use: ["Un-defined problem", "Want to think like sci-fi writer"],
  primary_agent: "tta"
})

// ToolCombination nodes
CREATE (:ToolCombination {
  id: "systemic_discovery",
  name: "Systemic Discovery Combo",
  tools: ["nested_hierarchies", "causal_loop_diagram", "leverage_points"],
  purpose: "Understand system-level impact and intervention points"
})

// Workflow nodes
CREATE (:Workflow {
  id: "tta_full_pipeline",
  name: "TTA Full Discovery Pipeline",
  orchestrator: "tta",
  phases: 4
})

// New relationships
CREATE (t:Tool)-[:REQUIRES_SERVICE]->(s:Service)
CREATE (t:Tool)-[:DELEGATES_TO]->(a:Agent)
CREATE (t:Tool)-[:VALIDATES_WITH]->(v:ValidationStep)
CREATE (tc:ToolCombination)-[:INCLUDES]->(t:Tool)
CREATE (w:Workflow)-[:USES_TOOL]->(t:Tool)
CREATE (w:Workflow)-[:ORCHESTRATED_BY]->(a:Agent)
```

---

## Summary

This implementation plan transforms the complete PWS methodology into a comprehensive A2A multi-agent system with:

1. **12+ Microservices** handling specific analytical tasks
2. **20+ Agents** organized in Orchestrator → Workshop → Sub-Agent layers
3. **18 Complete Tool Implementations** with full Why/When/How/Result workflows
4. **10 Tool Combination Patterns** for common use cases
5. **Standard Validation Pipeline** ensuring all opportunities are challenged
6. **Fan-Out/Fan-In Orchestration** for parallel multi-agent analysis

The key insight remains: **TTA serves as the natural root orchestrator** because it starts with the unknown and progressively defines the problem space, calling other agents as specialists for specific analyses. Every tool follows the same structure: domain selection → research → analysis → opportunity generation → validation.
