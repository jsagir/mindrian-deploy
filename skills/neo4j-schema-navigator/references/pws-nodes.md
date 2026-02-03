# PWS Methodology Nodes Reference

Detailed reference for nodes related to PWS (Problems Worth Solving) methodologies.

## Workshop Bot Nodes

### Bot (14 nodes)
Defines Mindrian's AI workshop bots.
```cypher
MATCH (b:Bot) RETURN b.name, b.bot_id, b.description, b.has_phases
```

Properties:
- `bot_id`: String - unique identifier (lawrence, tta, jtbd, etc.)
- `name`: String - display name
- `description`: String - bot purpose
- `has_phases`: Boolean - whether bot has workshop phases
- `system_prompt`: String - bot's system prompt reference

### Agent (37 nodes)
AI agent definitions and configurations.

### FrameworkAgent (10 nodes)
Agents mapped to specific frameworks.

---

## Framework Nodes (761 total)

### Core Framework Types
- Innovation frameworks
- Analysis frameworks
- Problem-solving frameworks
- Workshop methodologies

```cypher
MATCH (f:Framework)
WHERE f.framework_type IN ['innovation', 'analysis', 'problem_solving']
RETURN f.name, f.framework_type, f.description
```

### Framework Properties
- `name`: String
- `framework_type`: String (innovation, analysis, workshop, etc.)
- `principles`: StringArray
- `methods`: StringArray
- `phases`: StringArray
- `capabilities`: StringArray

---

## TTA (Trending to the Absurd)

### Trend (15 nodes)
Current trends to extrapolate.
```cypher
MATCH (t:Trend) RETURN t.name, t.domain, t.velocity, t.direction
```

### AbsurdScenario (6 nodes)
Extreme future scenarios from trend extrapolation.
```cypher
MATCH (s:AbsurdScenario)
RETURN s.name, s.description, s.year, s.probability
```

### Related Patterns
```cypher
// Find problems discovered via TTA
MATCH (t:Trend)-[:LEADS_TO]->(s:AbsurdScenario)-[:REVEALS]->(p:Problem)
RETURN t.name, s.name, p.name
```

---

## JTBD (Jobs To Be Done)

### Job (12 nodes)
Main job definitions.
```cypher
MATCH (j:Job) RETURN j.name, j.job_type, j.context
```

### FunctionalJob (5 nodes)
What the user is trying to accomplish functionally.

### EmotionalJob (4 nodes)
How the user wants to feel.

### SocialJob (4 nodes)
How the user wants to be perceived.

### JobCategory (6 nodes)
Job categorizations.

### Related Patterns
```cypher
// Full job hierarchy
MATCH (j:Job)-[:HAS_FUNCTIONAL]->(fj:FunctionalJob),
      (j)-[:HAS_EMOTIONAL]->(ej:EmotionalJob),
      (j)-[:HAS_SOCIAL]->(sj:SocialJob)
RETURN j.name, fj.name, ej.name, sj.name
```

---

## Scenario Analysis

### Scenario (17 nodes)
Future scenario definitions.
```cypher
MATCH (s:Scenario)
RETURN s.name, s.quadrant, s.probability, s.impact
```

### ScenarioMatrix (2 nodes)
2x2 uncertainty matrices.

### ScenarioPath (3 nodes)
Pathways between scenarios.

### Related Patterns
```cypher
// Find scenario matrix with all quadrants
MATCH (m:ScenarioMatrix)-[:CONTAINS]->(s:Scenario)
RETURN m.name, m.axis_x, m.axis_y, collect(s.name) as scenarios
```

---

## Six Thinking Hats

### ThinkingHat (6 nodes)
The six hats: White, Red, Black, Yellow, Green, Blue.

### Hat (6 nodes)
Hat instances.

### ThinkingMode (6 nodes)
Associated thinking modes.

### HatSequence (6 nodes)
Recommended sequences for different situations.

---

## Nested Hierarchies / Reverse Salients

### ReverseSalient (17 nodes)
Bottlenecks and lagging components in systems.
```cypher
MATCH (rs:ReverseSalient)
RETURN rs.name, rs.system, rs.level, rs.constraint_type
```

### LeveragePoint (29 nodes)
High-impact intervention points.
```cypher
MATCH (lp:LeveragePoint)
RETURN lp.name, lp.level, lp.effectiveness, lp.description
```

### Bottleneck (13 nodes)
System bottlenecks.

### Related Patterns
```cypher
// Find leverage points that address reverse salients
MATCH (rs:ReverseSalient)<-[:ADDRESSES]-(lp:LeveragePoint)
RETURN rs.name, lp.name, lp.effectiveness
```

---

## Knowns/Unknowns Matrix

### KnownKnown (6 nodes)
Things we know we know.

### KnownUnknown (8 nodes)
Things we know we don't know (research questions).

### UnknownKnown (7 nodes)
Things we don't know we know (hidden expertise).

### UnknownUnknown (8 nodes)
Things we don't know we don't know (blind spots).

### Related Patterns
```cypher
// Full matrix view
MATCH (k)
WHERE k:KnownKnown OR k:KnownUnknown OR k:UnknownKnown OR k:UnknownUnknown
RETURN labels(k)[0] as quadrant, k.name, k.domain
```

---

## Ackoff's DIKW Pyramid

### PyramidLevel (5 nodes)
The five levels: Data, Information, Knowledge, Understanding, Wisdom.

### Related Patterns
```cypher
MATCH (pl:PyramidLevel)
RETURN pl.name, pl.level_order, pl.description, pl.examples
ORDER BY pl.level_order
```

---

## Red Team / Devil's Advocate

### DevilsAdvocate (65 nodes)
Challenge perspectives and contrarian views.
```cypher
MATCH (da:DevilsAdvocate)
RETURN da.challenge_type, da.assumption_targeted, da.counter_argument
```

### Orthodoxy (15 nodes)
Established beliefs to challenge.

### Assumption (12 nodes)
Assumptions to test and validate.

### Related Patterns
```cypher
// Find challenges to specific orthodoxies
MATCH (o:Orthodoxy)<-[:CHALLENGES]-(da:DevilsAdvocate)
RETURN o.name, da.counter_argument
```

---

## Beautiful Questions

### BeautifulQuestion (43 nodes)
Questions that reframe problems and open possibilities.
```cypher
MATCH (bq:BeautifulQuestion)
RETURN bq.question, bq.question_type, bq.domain, bq.insight
```

### Question (74 nodes)
General research and exploration questions.

### BreakthroughQuestion (10 nodes)
Questions that led to breakthroughs.

### SupportingQuestion (10 nodes)
Supporting research questions.

---

## Problem Nodes (221 total)

### Problem Properties
```cypher
MATCH (p:Problem)
RETURN p.name, p.problem_type, p.domain, p.severity, p.worth_solving
```

### WickedProblem (7 nodes)
Complex, ill-defined problems with no clear solution.

### ProblemWorthSolving (3 nodes)
Validated PWS opportunities.

### ProblemType (11 nodes)
Problem categorizations.

---

## Innovation Nodes

### Innovation (17 nodes)
Innovation instances.

### InnovationTool (40 nodes)
Tools for innovation.

### InnovationOpportunity (13 nodes)
Identified opportunities.

### InnovationPathway (13 nodes)
Paths to innovation.

### Breakthrough (5 nodes)
Breakthrough innovations.

---

## Case Studies (23 nodes)

Real-world examples of methodologies in action.
```cypher
MATCH (cs:CaseStudy)-[:APPLIED_FRAMEWORK]->(f:Framework)
RETURN cs.name, cs.company, cs.outcome, f.name as framework
```

---

## Phase/Workshop Nodes

### Phase (65 nodes)
Workshop phases across all methodologies.
```cypher
MATCH (p:Phase)
RETURN p.name, p.workshop_type, p.order, p.description
ORDER BY p.workshop_type, p.order
```

### PhaseAction (12 nodes)
Actions within phases.

### PhaseResult (5 nodes)
Phase outcomes.

### ProcessStep (197 nodes)
Detailed process steps.

### Stage (33 nodes)
Process stages.
