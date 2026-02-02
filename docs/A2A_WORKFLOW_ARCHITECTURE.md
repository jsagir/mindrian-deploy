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

## Problem Classification Taxonomy

### The PWS Framework

Problems exist on a spectrum from completely undefined to well-defined. The tools you use depend on where you are on this spectrum.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PROBLEM DEFINITION SPECTRUM                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   UN-DEFINED                    ILL-DEFINED                    WELL-DEFINED │
│   (What problem?)               (Which problem?)               (How to solve?)│
│                                                                              │
│   ┌───────────────┐            ┌───────────────┐             ┌────────────┐ │
│   │ • TTA         │            │ • Combining   │             │ • Solution │ │
│   │ • Scenario    │     →      │ • S-Curves    │      →      │   Design   │ │
│   │ • Nested Hier │            │ • JTBD        │             │ • Execution│ │
│   │ • Red Team    │            │ • Questions   │             │ • Grading  │ │
│   └───────────────┘            └───────────────┘             └────────────┘ │
│                                                                              │
│   Output: Opportunity          Output: Problem                Output: Action │
│   candidates                   statement                      plan           │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# PART 1: UN-DEFINED PROBLEMS

> Tools for when you don't yet know what problem to solve.

## 1. Trending to the Absurd (TTA)

### Agent: `tta`
### Role: Orchestrator / Workshop

### Why Use It
- To get past the problem of **presentism**
- To challenge current thinking
- To imagine alternative futures where people behave and think differently

### When to Use
- When faced with an un-defined problem
- You want to think like a science fiction writer
- You need to imagine alternative futures with different needs

### How to Use (A2A Workflow)

```yaml
workflow: tta_methodology
phase: domain_and_trends

steps:
  1_domain_selection:
    agent: TTA
    action: "Select a domain or question"
    output: domain_context

  2_trend_research:
    agent: RESEARCH  # Sub-agent delegation
    action: "Generate list of current real trends impacting the space"
    tools: [tavily_search, google_trends]
    output: trend_list

  3_trend_selection:
    agent: TTA
    action: "Choose one trend"
    output: selected_trend

  4_absurd_extrapolation:
    agent: TTA
    action: |
      Carry trend to absurd conclusion by asking:
      - What if everything were...?
      - What if everyone were to do...?
      - What if nobody were to do...?
    output: absurd_scenario

  5_future_description:
    agent: TTA
    action: |
      Describe the alternative future:
      - What is missing here?
      - What products, services, policies will be needed?
      - What could we do that we cannot do now?
      - What will we not be able to do that we can do now?
      - What will be needed to live in such a future?
      - What could help prevent/slow an unwanted future?
    output: future_needs

  6_opportunity_generation:
    agent: TTA
    action: "Generate short list of opportunities (poorly defined problems worth solving)"
    output: opportunity_list

  7_opportunity_validation:
    agent: RED_TEAM  # Handoff for challenge
    handoff_type: DELEGATE
    action: |
      Challenge each opportunity:
      - Is this opportunity real?
      - What would have to be true for us to work on this now?
      - Can this be easily addressed by existing products/services/policies?
    output: validated_opportunities
```

### What Is the Result
- A short list of opportunities (poorly defined problems worth solving)
- Still missing key elements, needs further refinement
- Validated against basic reality checks

---

## 2. Scenario Analysis

### Agent: `scenario`
### Role: Orchestrator / Workshop

### Why Use It
- To get past the problem of **presentism**
- To challenge current thinking
- To imagine alternative futures (not predictions, but possibilities)

### When to Use
- When faced with an un-defined problem
- You want to think like an analyst
- Goal is NOT prediction, but exploring equally possible futures

### How to Use (A2A Workflow)

```yaml
workflow: scenario_analysis
phase: matrix_building

steps:
  1_domain_selection:
    agent: SCENARIO
    action: "Select a domain or question"
    output: domain_context

  2_trend_research:
    agent: RESEARCH
    action: "Generate list of current real trends impacting the space"
    output: trend_list

  3_axis_creation:
    agent: SCENARIO
    action: |
      Use trends to create possible axes:
      - Each axis presents two alternatives
      - Examples: this/that, much/little, discrete/continuous, one/many
    output: possible_axes

  4_axis_selection:
    agent: SCENARIO
    action: "Select two axes for the 2x2 matrix"
    output: selected_axes

  5_category_definition:
    agent: SCENARIO
    action: |
      Determine categories within each box:
      - Situation, key players, degree of change, treatment phase
      - Categories depend on the domain selected
    output: category_definitions

  6_matrix_generation:
    agent: SCENARIO
    action: "Generate the 2x2 scenario analysis matrix"
    output: scenario_matrix

  7_analysis_option_1:
    # Option 1: All scenarios simultaneously
    agent: SCENARIO
    action: |
      Analyze across all scenarios:
      - What is missing across ALL scenarios?
      - What products/services/policies needed no matter what?
      - What must we do today no matter what the future?
    output: cross_scenario_needs

  7_analysis_option_2:
    # Option 2: Deep dive one scenario
    agent: SCENARIO
    action: |
      Deep dive into one scenario:
      - If unwanted: what could prevent or slow it?
      - If desired: what can we do today to bring it about?
      - What is missing here?
      - What products/services/policies needed?
      - What could we do that we cannot do now?
      - What will we not be able to do?
    output: scenario_deep_dive

  8_opportunity_generation:
    agent: SCENARIO
    action: "Generate short list of opportunities"
    output: opportunity_list

  9_validation:
    agent: RED_TEAM
    handoff_type: DELEGATE
    action: "Challenge each opportunity with standard validation questions"
    output: validated_opportunities
```

### What Is the Result
- 2x2 scenario matrix with 4 possible futures
- Either cross-scenario insights OR deep dive on one scenario
- List of opportunities (poorly defined problems worth solving)

---

## 3. Nested Hierarchies

### Agent: `nested_hierarchies`
### Role: Workshop / Sub-Agent

### Why Use It
- To get past the problem of **presentism**
- To challenge current thinking by examining **system impacts**
- To explore relationships among changing trends
- To understand how change impacts existing systems

### When to Use
- When faced with an un-defined problem
- You want to think like an analyst about broader impacts
- Goal is to explore how change impacts the system(s) it's part of

### How to Use (A2A Workflow)

```yaml
workflow: nested_hierarchies_analysis
phase: system_mapping

steps:
  1_domain_selection:
    agent: NESTED_HIERARCHIES
    action: "Select a domain or question"
    output: domain_context

  2_trend_research:
    agent: RESEARCH
    action: "Generate list of current trends impacting the space"
    output: trend_list

  3_trend_selection:
    agent: NESTED_HIERARCHIES
    action: |
      Choose one trend:
      - What is changing and how fast?
      - Try carrying this trend to its absurd conclusion
    output: selected_trend

  4_element_identification:
    agent: NESTED_HIERARCHIES
    action: "Identify key elements (human and material) and sub-systems in that domain"
    output: system_elements

  5_hierarchy_mapping:
    agent: NESTED_HIERARCHIES
    action: |
      Place elements and domain within larger nested hierarchy:
      - Note: Trend could be part of different systems
      - Hierarchy could be structured in different ways
      - Create at least 5 levels up and down
    output: hierarchy_map

  6_systems_map:
    agent: NESTED_HIERARCHIES
    action: "Prepare a systems map showing the hierarchies"
    output: systems_map

  7_impact_analysis:
    agent: NESTED_HIERARCHIES
    action: |
      Analyze hierarchy impacts:
      - How will the trend impact the rest of the hierarchy?
      - Where are the reverse salients?
      - What leverage points exist?
    output: impact_analysis

  8_opportunity_identification:
    agent: NESTED_HIERARCHIES
    action: |
      Identify innovation opportunities:
      - How can we make elements more efficient/effective/productive?
      - How can we improve interactions among elements?
      - How can we improve overall system performance?
      - How can we re-imagine the purpose/meaning of the entire system?
    output: opportunity_list

  9_validation:
    agent: RED_TEAM
    handoff_type: DELEGATE
    action: "Challenge each opportunity with standard validation questions"
    output: validated_opportunities
```

### What Is the Result
- Systems map showing nested hierarchies
- Identification of reverse salients (constraints)
- Identification of leverage points
- List of opportunities at different levels of the hierarchy

---

## 4. Red Teaming (Cross-Cutting Middleware)

### Agent: `redteam`
### Role: **CROSS-CUTTING MIDDLEWARE** / Workshop / Sub-Agent / Validator

> **CRITICAL**: Red Team is NOT just a destination stage - it's a **checkpoint** that applies to ANY stage. See `docs/A2A_PRACTICAL_ARCHITECTURE.md` for middleware implementation.

### Why Use It
- A tool AND a way to check if opportunities are "real"
- To get past the problem of **presentism**
- To challenge current thinking about what could destroy or replace current offerings
- To explore how to take advantage of trends
- **As automatic validation at phase transitions** (middleware pattern)

### When to Use
- **AUTOMATICALLY**: At every phase transition (exploring→framing, framing→defining, etc.)
- **AUTOMATICALLY**: After any agent generates opportunities or claims
- **AUTOMATICALLY**: When confidence scores are below threshold
- As a standalone tool for assumption challenging
- As validation step after ANY other tool generates opportunities
- When you need to stress-test ideas

### Middleware Pattern

```python
# Red Team runs as middleware, not just as a destination
async def execute_with_validation(agent, input):
    result = await agent.execute(input)

    # Red Team validates at transitions and on key outputs
    if should_validate(agent, input.phase):
        validation = await red_team_middleware.validate({
            "claim": result.primary_output,
            "evidence": result.artifacts,
            "stage": input.phase
        })
        if not validation.passed:
            return {**result, challenges: validation.challenges, needs_revision: True}

    return result
```

### How to Use (A2A Workflow)

```yaml
workflow: red_teaming
phase: assumption_challenge

steps:
  1_domain_selection:
    agent: RED_TEAM
    action: "Select a domain or question"
    output: domain_context

  2_status_quo_mapping:
    agent: RED_TEAM
    action: "Identify key products/services/policies that maintain status quo"
    output: status_quo_elements

  3_assumption_extraction:
    agent: RED_TEAM
    action: "Identify assumptions that support them, and which can be challenged"
    output: assumption_list

  4_trend_research:
    agent: RESEARCH
    action: "Generate list of current trends impacting the space"
    output: trend_list

  5_challenge_questions:
    agent: RED_TEAM
    action: |
      Challenge with probing questions:
      - What makes the problem (opportunity) real and worthy of solving?
      - What could make this problem unimportant?
      - Why has it not been solved to date?
      - What will be needed to make X work in the future?
      - What will be needed to get rid of X in the future?
      - What could completely replace X?
      - What if we could...?
      - What would surprise you?
    output: challenge_responses

  6_synthesis:
    agent: RED_TEAM
    action: |
      Synthesize findings:
      - What current assumptions can be challenged?
      - What new capabilities are needed?
      - What new products/services/policies needed to change status quo?
      - What existing systems will be disrupted?
    output: red_team_synthesis
```

### What Is the Result
- List of challengeable assumptions
- New capabilities needed
- New products/services/policies needed
- Systems that will be disrupted

---

## Cross-Cutting: Journey Mapping View

> **IMPORTANT**: Journey Mapping is NOT just a tool - it's a **cross-cutting view** that ANY agent can request.

### Why It's Cross-Cutting
Every agent benefits from understanding where the user has been in their exploration. Journey Mapping provides context about:
- Touchpoints in the conversation
- Emotional arc (frustration, clarity, excitement)
- Friction points encountered
- Decisions made

### Implementation Pattern

```python
class JourneyMapView:
    """Cross-cutting view that any agent can request."""

    def get_current_journey(self, context: ContextManager) -> JourneyMap:
        """Returns user's journey through the system so far."""
        return JourneyMap(
            touchpoints=self._extract_touchpoints(context),
            emotional_arc=self._analyze_emotional_state(context),
            friction_points=self._identify_friction(context),
            decision_points=self._mark_decisions(context),
            current_phase=context.current_phase,
            time_in_phase=context.time_in_current_phase
        )
```

### When Agents Request Journey Context
- **TTA**: Before generating opportunities, check what domains user has already explored
- **JTBD**: Before asking about jobs, see what the user has already validated
- **Red Team**: When challenging, reference previous decisions to avoid redundant questions
- **Any Agent**: When user seems frustrated (detected via emotional arc)

---

# PART 2: ILL-DEFINED PROBLEMS

> Tools for when you have identified an opportunity but need to refine it.

## 5. Combining Ideas

### Agent: `bono` (Six Thinking Hats / Creative)
### Role: Workshop / Sub-Agent

### Why Use It
- To generate surprising, unusual, and non-obvious ideas
- To create intersectional innovations from original combinations

### How to Use (A2A Workflow)

```yaml
workflow: combining_ideas
phase: intersection_creation

steps:
  1_starting_point:
    agent: BONO
    action: "Start with something of importance to user"
    output: focal_subject

  2_idea_generation:
    agent: BONO
    action: "Generate list of unrelated ideas, products, or services"
    output: unrelated_ideas

  3_combination:
    agent: BONO
    action: "Combine unrelated ideas with original subject"
    output: combinations

  4_alternative_perspectives:
    agent: BONO
    action: "Identify: Who from an unrelated field could give different perspective?"
    output: perspective_sources

  5_synthesis:
    agent: BONO
    action: |
      Identify surprising, unusual, non-obvious, fascinating ideas
      from the combinations (intersectional ideas)
    output: intersectional_ideas

  6_validation:
    agent: RED_TEAM
    handoff_type: DELEGATE
    action: "Challenge each opportunity with standard validation questions"
    output: validated_opportunities
```

### What Is the Result
- Intersectional ideas from combining unrelated elements
- List of opportunities for further exploration

---

## 6. Harnessing Trends

### Primary Agent: `scurve`
### Supporting Agents: `research`, `tta`
### Role: Workshop / Sub-Agent

### 6a. S-Curves

#### Why Use It
- To find opportunities at technological and market limits
- To identify potential replacement technologies

#### How to Use

```yaml
workflow: s_curve_analysis
phase: limit_identification

steps:
  1_limit_identification:
    agent: SCURVE
    action: "Identify where a technology is reaching its physical or market limit"
    output: technology_at_limit

  2_replacement_analysis:
    agent: SCURVE
    action: |
      Determine:
      - What features would a new technology need to replace the existing one?
      - What could be simpler than the current solution?
    output: replacement_requirements

  3_validation:
    agent: RED_TEAM
    handoff_type: DELEGATE
    action: "Challenge each opportunity"
    output: validated_opportunities
```

### 6b. Dominant Designs

#### Why Use It
- To find opportunities where dominant designs are falling apart
- Political, economic, social, technological designs being challenged

#### How to Use

```yaml
workflow: dominant_design_analysis
phase: design_disruption

steps:
  1_design_identification:
    agent: SCURVE
    action: |
      Identify where a dominant design is starting to fall apart:
      - Political designs being seriously challenged
      - Economic designs under pressure
      - Social designs shifting
      - Technological designs becoming obsolete
    output: challenged_designs

  2_new_design_exploration:
    agent: SCURVE
    action: "Explore: How might a new dominant design look?"
    output: new_design_possibilities

  3_trend_research:
    agent: RESEARCH
    action: "Research current trends that could lead to new dominant design"
    output: enabling_trends

  4_validation:
    agent: RED_TEAM
    handoff_type: DELEGATE
    action: "Challenge each opportunity"
    output: validated_opportunities
```

### 6c. Macro-Changes (PEST Analysis)

#### Why Use It
- To take advantage of Political, Economic, Social, Technological changes
- Every change destroys current paradigms - take advantage of destruction

#### How to Use

```yaml
workflow: macro_change_analysis
phase: pest_mapping

steps:
  1_domain_selection:
    agent: SCURVE
    action: "Choose a domain and macro-trend of interest"
    output: domain_and_trend

  2_destruction_analysis:
    agent: SCURVE
    action: "Identify what is being destroyed by this change"
    output: destruction_list

  3_consequence_mapping:
    agent: SCURVE
    action: "Map consequences of the trend/change"
    output: consequence_map

  4_pest_diagram:
    agent: SCURVE
    action: |
      Construct PEST systems diagram:
      - What is changing within each category (P/E/S/T)?
      - What is being destroyed?
      - What dominant designs are breaking down?
      - Where is the top of an S-Curve being reached?
      - Where are the discontinuities?
      - What are first, second, third order consequences?
    output: pest_analysis

  5_opportunity_synthesis:
    agent: SCURVE
    action: |
      Identify opportunities:
      - What are the next big problems worth solving?
      - Where are opportunities to build on/replace what's being destroyed?
    output: opportunity_list

  6_validation:
    agent: RED_TEAM
    handoff_type: DELEGATE
    action: "Challenge each opportunity"
    output: validated_opportunities
```

---

## 7. The User Experience

### Primary Agent: `jtbd`
### Role: Workshop / Sub-Agent

### 7a. User Process Mapping

#### Why Use It
- To find opportunities where user experience is unsatisfying

#### How to Use

```yaml
workflow: user_process_mapping
phase: satisfaction_analysis

steps:
  1_process_identification:
    agent: JTBD
    action: "Identify and map relevant user experience to desired detail level"
    output: process_map

  2_step_evaluation:
    agent: JTBD
    action: |
      Map every step against two criteria:
      - How important the step is to the total process
      - How well satisfied the step is by current products/services/policies
    output: satisfaction_matrix

  3_gap_identification:
    agent: JTBD
    action: "Identify high-importance, low-satisfaction gaps"
    output: opportunity_gaps

  4_validation:
    agent: RED_TEAM
    handoff_type: DELEGATE
    action: "Challenge each opportunity"
    output: validated_opportunities
```

### 7b. Jobs to Be Done (JTBD)

#### Why Use It
- To find opportunities where user experience is unsatisfying
- To find opportunities where user isn't making desired progress

#### How to Use

```yaml
workflow: jobs_to_be_done
phase: job_discovery

steps:
  1_job_identification:
    agent: JTBD
    action: |
      Identify what people are trying to accomplish:
      - What progress they are looking to make
      - What specific outcomes they are looking for
    output: job_list

  2_barrier_identification:
    agent: JTBD
    action: "Identify what is preventing them from doing the job they want"
    output: barrier_list

  3_process_mapping:
    agent: JTBD
    action: "Use process maps to visualize the journey"
    output: process_map

  4_job_statement:
    agent: JTBD
    action: |
      Prepare job statement with:
      - Subject (stakeholder: nurse, clinician, hospital)
      - Action verb (prepare, collect, insert)
      - Desired outcome (reduce patient discomfort)
      - Vector of measurement (minimize time, maximize output)
      - (sometimes) context (caused by..., in order to...)
    output: job_statement

  5_validation:
    agent: RED_TEAM
    handoff_type: DELEGATE
    action: "Challenge each opportunity"
    output: validated_opportunities
```

---

## 8. Challenging Orthodoxies

### Primary Agent: `beautiful_question`
### Supporting Agents: `bono`, `red_team`
### Role: Workshop

### 8a. Asking Questions (Why → What If → How)

#### Why Use It
- To find opportunities by challenging key assumptions
- To find opportunities where long-held paradigms are under pressure

#### How to Use

```yaml
workflow: beautiful_question
phase: why_what_if_how

steps:
  1_domain_selection:
    agent: BEAUTIFUL_QUESTION
    action: "Choose a domain of interest"
    output: domain_context

  2_why_phase:
    agent: BEAUTIFUL_QUESTION
    action: |
      Person encounters situation less than ideal → asks WHY
      - Why is this situation this way?
      - Why hasn't this been solved?
      - Why do we accept this?
    output: why_insights

  3_what_if_phase:
    agent: BEAUTIFUL_QUESTION
    action: |
      Person begins to imagine improvements → asks WHAT IF
      - What if we could...?
      - What if this didn't exist?
      - What if we approached it differently?
    output: what_if_possibilities

  4_how_phase:
    agent: BEAUTIFUL_QUESTION
    action: |
      Person tries to implement → figures out HOW
      - How might we actually do this?
      - How would we start?
      - How would we know it's working?
    output: how_implementation

  5_barrier_identification:
    agent: BEAUTIFUL_QUESTION
    action: "Identify what prevents the ideal from being achieved"
    output: barriers

  6_validation:
    agent: RED_TEAM
    handoff_type: DELEGATE
    action: "Challenge each opportunity"
    output: validated_opportunities
```

### 8b. Changing the Terms of Competition (Four Actions Framework)

#### Why Use It
- To find opportunities by challenging key assumptions
- To re-imagine current products and services

#### How to Use

```yaml
workflow: terms_of_competition
phase: reframe_competition

steps:
  1_current_state:
    agent: BONO
    action: |
      Start with where you are:
      - What is the distinctive advantage of the product/service?
      - Identify current job(s) to be done
      - List current terms of competition:
        - Features and functionalities
        - Performance measures (customer evaluation criteria)
        - Customer groups
        - Emotions and images
        - Positioning
    output: current_state

  2_barrier_identification:
    agent: BONO
    action: "Identify what prevents ideal user experience"
    output: barriers

  3_unconstrain_space:
    agent: BONO
    action: |
      Un-constrain by changing/reversing terms of competition:
      - What received wisdom can be questioned?
      - What dominant designs can be challenged?
      - What corporate/societal assumptions can be challenged?
        - Regarding business models
        - Regarding technologies
        - Regarding user experiences
    output: unconstrained_space

  4_four_actions:
    agent: BONO
    action: |
      Apply Four Actions Framework:
      - What can we RAISE above industry standard?
      - What can we REDUCE below industry standard?
      - What can we ELIMINATE that industry takes for granted?
      - What can we CREATE that industry has never offered?
    output: four_actions_analysis

  5_new_jobs:
    agent: JTBD
    handoff_type: DELEGATE
    action: |
      Find new jobs to be done by utilizing original terms differently:
      - Think in terms of pains and gains
      - Are there different trade-offs indicating different jobs?
      - Are there niche applications?
    output: new_jobs

  6_space_expansion:
    agent: BONO
    action: |
      Expand the space:
      - Create new ill-defined problems (How do I X without...)
      - Create new un-defined problems (What is the future of...)
      - Identify high uncertainty/low risk opportunities
    output: expanded_opportunities

  7_validation:
    agent: RED_TEAM
    handoff_type: DELEGATE
    action: "Challenge each opportunity"
    output: validated_opportunities
```

### 8c. White Space Mapping

#### Why Use It
- To challenge key industry assumptions about products/services
- To find gaps in the market

#### How to Use

```yaml
workflow: white_space_mapping
phase: gap_identification

steps:
  1_domain_selection:
    agent: BONO
    action: "Choose a domain of interest"
    output: domain_context

  2_terms_identification:
    agent: BONO
    action: "Identify relevant terms of competition in that domain"
    output: competition_terms

  3_axis_selection:
    agent: BONO
    action: "Choose two terms as axes (price is often good)"
    output: axes

  4_map_creation:
    agent: BONO
    action: "Create whitespace map based on current products/services/companies"
    output: whitespace_map

  5_opportunity_identification:
    agent: BONO
    action: "Identify where the opportunities are - next big problems to solve"
    output: opportunity_list

  6_validation:
    agent: RED_TEAM
    handoff_type: DELEGATE
    action: "Challenge each opportunity"
    output: validated_opportunities
```

### 8d. Innovation of Meaning

#### Why Use It
- To find opportunities where user experience is unsatisfying or stale
- To re-imagine the purpose of products/services

#### How to Use

```yaml
workflow: innovation_of_meaning
phase: meaning_reimagination

steps:
  1_domain_selection:
    agent: BONO
    action: "Choose domain of particular interest"
    output: domain_context

  2_current_analysis:
    agent: BONO
    action: |
      Analyze current state:
      - Identify current terms of competition
      - Identify current job to be done
    output: current_state

  3_meaning_exploration:
    agent: BONO
    action: |
      Imagine new job to be done or new perception:
      - What other jobs could benefit from re-purposing this?
      - What other emotional/social needs could be filled?
      - With or without changing terms of competition
    output: new_meanings

  4_opportunity_creation:
    agent: BONO
    action: "Identify opportunities to create new meanings"
    output: opportunity_list

  5_validation:
    agent: RED_TEAM
    handoff_type: DELEGATE
    action: "Challenge each opportunity"
    output: validated_opportunities
```

---

## 9. Reverse Salients

### Agent: `nested_hierarchies` (with `scurve` support)
### Role: Workshop / Sub-Agent

### Why Use It
- To identify opportunity areas for concentrated innovation effort
- To ask WHY a domain is not advancing, then find opportunities

### How to Use

```yaml
workflow: reverse_salient_analysis
phase: constraint_identification

steps:
  1_domain_research:
    agent: NESTED_HIERARCHIES
    action: "Research the domain deeply"
    tools: [research, graphrag]
    output: domain_knowledge

  2_domain_mapping:
    agent: NESTED_HIERARCHIES
    action: "Prepare a domain map showing systems and subsystems"
    output: domain_map

  3_salient_identification:
    agent: NESTED_HIERARCHIES
    action: |
      Identify the reverse salient:
      - Why is this a reverse salient?
      - What measures of efficiency, effectiveness, reliability,
        profitability, useability are NOT being met?
    output: reverse_salient

  4_opportunity_synthesis:
    agent: NESTED_HIERARCHIES
    action: |
      Identify opportunities using multiple lenses:
      - Intersectional innovations
      - New scientific/technological trends
      - Jobs to be done
      - Four actions framework
      - Scenarios
      - Systems analysis
    output: opportunity_list

  5_validation:
    agent: RED_TEAM
    handoff_type: DELEGATE
    action: "Challenge each opportunity"
    output: validated_opportunities
```

---

## 10. Life Cycles

### Agent: `jtbd` (with `process_mapping` support)
### Role: Workshop / Sub-Agent

### Why Use It
- To identify opportunity areas for innovation in a domain
- To ask how a product/service life cycle could be more efficient

### How to Use

```yaml
workflow: life_cycle_analysis
phase: efficiency_mapping

steps:
  1_domain_research:
    agent: JTBD
    action: "Research the domain"
    tools: [research, graphrag]
    output: domain_knowledge

  2_lifecycle_mapping:
    agent: JTBD
    action: |
      Prepare life cycle map:
      - Where are the inefficiencies?
      - What is sub-optimal?
      - How can this be measured?
      - What measures are NOT being met?
    output: lifecycle_map

  3_opportunity_synthesis:
    agent: JTBD
    action: |
      Identify opportunities using multiple lenses:
      - Jobs to be done
      - User experiences
      - Four actions framework
      - Trending to the absurd
      - Red teaming
      - Changes of meaning
      - White space mapping
    output: opportunity_list

  4_validation:
    agent: RED_TEAM
    handoff_type: DELEGATE
    action: "Challenge each opportunity"
    output: validated_opportunities
```

---

## 11. Finding New Jobs by Leveraging Resources

### Agent: `jtbd` (with `research` support)
### Role: Workshop / Sub-Agent

### Why Use It
- To identify opportunity areas by leveraging existing capabilities
- To extend core technologies into new markets

### How to Use

```yaml
workflow: resource_leverage
phase: capability_extension

steps:
  1_company_research:
    agent: RESEARCH
    action: "Research company or industry"
    output: company_knowledge

  2_portfolio_mapping:
    agent: JTBD
    action: |
      Prepare product portfolio map:
      - Core technologies (product or process)
      - Existing capabilities
    output: portfolio_map

  3_extension_exploration:
    agent: JTBD
    action: |
      Explore how core technologies can be extended/adapted:
      - New market spaces
      - New product categories
    output: extension_possibilities

  4_opportunity_synthesis:
    agent: JTBD
    action: |
      Identify opportunities using multiple lenses:
      - Jobs to be done
      - User experiences
      - Four actions framework
      - Trending to the absurd
      - Red teaming
      - Changes of meaning
      - White space mapping
    output: opportunity_list

  5_validation:
    agent: RED_TEAM
    handoff_type: DELEGATE
    action: "Challenge each opportunity"
    output: validated_opportunities
```

---

## 12. Wicked Problems

### Agent: `nested_hierarchies` (with `ackoff` support)
### Role: Workshop / Orchestrator

### Why Use It
- To look for innovation opportunities in systems (wicked) problems
- To find leverage points in complex, interconnected systems

### How to Use

```yaml
workflow: wicked_problem_analysis
phase: systems_leverage

steps:
  1_domain_selection:
    agent: NESTED_HIERARCHIES
    action: "Choose a domain of interest"
    output: domain_context

  2_domain_research:
    agent: RESEARCH
    action: "Research that domain to understand the factors involved"
    tools: [tavily, graphrag]
    output: domain_knowledge

  3_subsystem_identification:
    agent: NESTED_HIERARCHIES
    action: "Identify the relevant sub-systems"
    output: subsystems

  4_systems_mapping:
    agent: NESTED_HIERARCHIES
    action: "Draw a systems map"
    output: systems_map

  5_leverage_identification:
    agent: NESTED_HIERARCHIES
    action: |
      Identify points of leverage using Meadows' hierarchy:
      - Parameters (weakest)
      - Buffers
      - Stock-and-flow structures
      - Delays
      - Feedback loops
      - Information flows
      - Rules
      - Self-organization
      - Goals
      - Paradigms (strongest)
    output: leverage_points

  6_opportunity_synthesis:
    agent: NESTED_HIERARCHIES
    action: |
      Where are opportunities for innovation?
      - Products that address leverage points
      - Services that change system dynamics
      - Policies that shift paradigms
    output: opportunity_list

  7_validation:
    agent: RED_TEAM
    handoff_type: DELEGATE
    action: "Challenge each opportunity"
    output: validated_opportunities
```

---

# PART 3: A2A ARCHITECTURE

## Architecture Overview

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
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐               │
│  │ QUESTION│ │  BONO   │ │ PROBLEM │ │  KNOWN  │               │
│  │ (Why→)  │ │ (Hats)  │ │ CLASSIF │ │ UNKNOWNS│               │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘               │
│       │           │           │           │                     │
└───────┼───────────┼───────────┼───────────┼─────────────────────┘
        │           │           │           │
        └───────────┴───────────┼───────────┘
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

## Tool-to-Agent Mapping

| Tool/Methodology | Primary Agent | Supporting Agents | Problem Type |
|------------------|---------------|-------------------|--------------|
| Trending to Absurd | `tta` | research, redteam | Un-Defined |
| Scenario Analysis | `scenario` | research, redteam | Un-Defined |
| Nested Hierarchies | `nested_hierarchies` | research, ackoff | Un-Defined |
| Red Teaming | `redteam` | research | Both |
| Combining Ideas | `bono` | redteam | Ill-Defined |
| S-Curves | `scurve` | research, redteam | Ill-Defined |
| Dominant Designs | `scurve` | research, redteam | Ill-Defined |
| Macro-Changes | `scurve` | research, nested | Ill-Defined |
| User Process Map | `jtbd` | redteam | Ill-Defined |
| Jobs to Be Done | `jtbd` | process, redteam | Ill-Defined |
| Beautiful Question | `beautiful_question` | bono, redteam | Ill-Defined |
| Terms of Competition | `bono` | jtbd, redteam | Ill-Defined |
| White Space | `bono` | redteam | Ill-Defined |
| Innovation of Meaning | `bono` | jtbd, redteam | Ill-Defined |
| Reverse Salients | `nested_hierarchies` | scurve, redteam | Ill-Defined |
| Life Cycles | `jtbd` | process, redteam | Ill-Defined |
| Resource Leverage | `jtbd` | research, redteam | Ill-Defined |
| Wicked Problems | `nested_hierarchies` | ackoff, redteam | Both |

---

## Standard Validation Questions

Every opportunity generated by ANY tool must be challenged with these questions:

```yaml
validation_questions:
  reality_check:
    - "Is this opportunity real?"
    - "What evidence supports this opportunity?"
    - "Who has this problem and how do you know?"

  timing_check:
    - "What would have to be true for us to work on this opportunity now?"
    - "Is the timing right?"
    - "What signals would tell us to proceed?"

  competition_check:
    - "Can this opportunity be easily addressed by existing products, services, and policies?"
    - "Who else is working on this?"
    - "What's our unfair advantage?"

  impact_check:
    - "Is this worth solving?"
    - "What's the scale of impact?"
    - "Who benefits and how much?"
```

---

## TTA as Root Orchestrator: Complete Workflow

```yaml
workflow: tta_orchestration
name: "Full PWS Discovery Pipeline"

phase_1_domain_trends:
  orchestrator: TTA
  triggers_on: "I want to explore trends in [domain]"

  steps:
    1_domain_selection:
      agent: TTA
      action: "Identify domain of interest"
      output: domain_context

    2_trend_research:
      agent: RESEARCH
      action: "Research trends in {domain_context}"
      tools: [tavily_search, google_trends]
      output: trend_list

    3_trend_validation:
      agent: GRAPHRAG
      action: "Find related frameworks and case studies"
      output: relevant_frameworks

    4_trend_selection:
      agent: TTA
      action: "Select one trend for deep dive"
      input: [trend_list, relevant_frameworks]
      output: selected_trend

phase_2_absurd_extrapolation:
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
      agent: SCENARIO
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

phase_3_problem_discovery:
  parallel_delegation:
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

  fan_in:
    agent: TTA
    action: "Synthesize findings into opportunity map"
    input: [future_jobs, system_changes, technology_shifts, assumption_challenges]
    output: opportunity_map

phase_4_validation:
  steps:
    10_dikw_grounding:
      agent: ACKOFF
      handoff_type: DELEGATE
      action: "Ground opportunities in DIKW pyramid"
      input: opportunity_map
      output: grounded_opportunities

    11_quality_check:
      agent: PWS_GRADING
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
    problem_type: "un-defined"  # or "ill-defined"
    methodology_in_use: "Trending to the Absurd"

  task:
    action: "Map the nested hierarchy of EV systems"
    expected_output:
      - system_levels: 5
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

**Methodology**: Trending to the Absurd → Nested Hierarchies (systems impact)
**Problem Type**: Un-defined → exploring broader impact

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
# tools/graphrag_lite.py

async def enrich_context(query: str, bot_id: str) -> str:
    """
    Called by any agent to get graph-enriched context.

    Returns hints about:
    - Related frameworks and their methodologies
    - Case studies with relevant applications
    - Co-occurring concepts and tools
    - Recommended next agents based on context
    """
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
    - Is the timing right? (market readiness)
    """
    pass
```

---

## Venture Stage Workflow Mapping

### Pre-Opportunity (Finding Problems)

```
Entry → Lawrence (orchestrator)
      → TTA (trend exploration) — Un-Defined tools
      → Beautiful Question (reframing)
      → Scenario Analysis (future exploration)

Tools: Research, GraphRAG
Problem Type: Un-Defined
Output: List of candidate opportunities
```

### Opportunity Identified (Understanding Problems)

```
Entry → JTBD (customer understanding) — Ill-Defined tools
      → Nested Hierarchies (system mapping)
      → Scenario Analysis (future validation)
      → Research (evidence gathering)

Tools: Research, GraphRAG
Problem Type: Ill-Defined
Output: Validated opportunity with customer context
```

### Well-Defined Problem (Designing Solution)

```
Entry → Ackoff (DIKW grounding)
      → S-Curve (timing analysis)
      → Nested Hierarchies (intervention design)
      → Red Team (assumption challenge)

Tools: GraphRAG, PWS Grading
Problem Type: Well-Defined
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

## Implementation Code

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
    Uses PWS methodology tools based on problem definition stage.
    """

    # Determine problem type
    problem_type = session_state.get("problem_type", "un-defined")

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
    # Select agents based on problem type
    if problem_type == "un-defined":
        parallel_tasks = [
            delegate_to_agent("nested_hierarchies", "map_systems", absurd_scenario),
            delegate_to_agent("scenario", "build_matrix", absurd_scenario),
            delegate_to_agent("redteam", "challenge_assumptions", absurd_scenario),
        ]
    else:  # ill-defined
        parallel_tasks = [
            delegate_to_agent("jtbd", "find_jobs", absurd_scenario),
            delegate_to_agent("scurve", "analyze_timing", absurd_scenario),
            delegate_to_agent("redteam", "challenge_assumptions", absurd_scenario),
        ]

    results = await asyncio.gather(*parallel_tasks)

    # Phase 4: Synthesis (fan-in)
    opportunity_map = synthesize_findings(results)

    # Phase 5: Validation with standard questions
    validated = await validate_opportunities(
        opportunity_map,
        validation_questions=[
            "Is this opportunity real?",
            "What would have to be true for us to work on this now?",
            "Can this be easily addressed by existing solutions?",
        ]
    )

    # Phase 6: Grade
    graded = await delegate_to_agent(
        agent="pws_grading",
        task="score_opportunities",
        input=validated
    )

    return {
        "domain": domain,
        "trend": trend,
        "problem_type": problem_type,
        "absurd_scenario": absurd_scenario,
        "opportunities": graded,
        "next_steps": generate_next_steps(graded, problem_type)
    }
```

---

## Framework Complementarity Map

```
UN-DEFINED PROBLEM TOOLS:
TTA ←→ Scenario Analysis ←→ Nested Hierarchies
         ↓                      ↓
    Red Teaming ←──────────────┘

ILL-DEFINED PROBLEM TOOLS:
JTBD ←→ Process Mapping ←→ User Journey Mapping
           ↓
Design Thinking ←→ JTBD
           ↓
Knowns Matrix ←→ Cynefin
           ↓
System Archetypes ←→ 12 Leverage Points
           ↓
Technology Complex ←→ 12 Leverage Points

CROSS-CUTTING:
Red Team → Validates ALL tools
S-Curve → Informs timing for ALL opportunities
DIKW (Ackoff) → Grounds ALL findings
```

---

## Summary: The A2A Orchestration Pattern

1. **Problem Classification** → Un-Defined vs Ill-Defined
2. **Tool Selection** → Match tools to problem type
3. **Entry Point Detection** → Route to appropriate orchestrator
4. **Orchestrator Initialization** → Set up context, call services
5. **Workshop Delegation** → Fan-out to specialist agents with methodology
6. **Service Calls** → GraphRAG, Research, Grading as needed
7. **Standard Validation** → Challenge all opportunities with standard questions
8. **Synthesis** → Fan-in results back to orchestrator
9. **Grading** → PWS criteria scoring
10. **Handoff or Complete** → Either switch to next stage or conclude

**The key insight**: TTA is the natural root because it starts with the unknown and progressively defines the problem space, calling other agents as specialists for specific analyses. Each tool has a clear Why/When/How/Result structure that guides the A2A workflow.
