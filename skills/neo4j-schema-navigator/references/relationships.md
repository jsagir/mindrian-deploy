# Relationship Types Reference

The graph contains **1,800+ relationship types**. Below are the most commonly used ones, categorized.

## Document/Content Relationships

| Relationship | Usage |
|-------------|-------|
| `HAS_CHUNK` | Document → Chunk |
| `FIRST_CHUNK` | Document → first Chunk |
| `NEXT_CHUNK` | Chunk → next Chunk |
| `CONTAINS` | Container → content |
| `CONTAINS_SECTION` | Document → Section |
| `PART_OF` | Element → Container |
| `AUTHORED_BY` | Document → Author |
| `PUBLISHED_IN` | Document → Publication |
| `REFERENCES` | Document → Reference |
| `CITED_BY` | Source → citing Document |

## Framework/Methodology Relationships

| Relationship | Usage |
|-------------|-------|
| `APPLIED_FRAMEWORK` | CaseStudy → Framework |
| `USES_FRAMEWORK` | Analysis → Framework |
| `IMPLEMENTS_FRAMEWORK` | Tool → Framework |
| `BASED_ON` | Derived → Source framework |
| `EXTENDS` | Child → Parent framework |
| `COMPLEMENTS` | Framework ↔ Framework |
| `HAS_PHASE` | Framework → Phase |
| `HAS_STEP` | Process → ProcessStep |
| `FOLLOWS` | Step → next Step |
| `PRECEDES` | Step → next Step |

## PWS/Innovation Relationships

| Relationship | Usage |
|-------------|-------|
| `ADDRESSES` | Solution → Problem |
| `IDENTIFIES` | Analysis → Opportunity |
| `LEADS_TO` | Cause → Effect |
| `REVEALS` | Analysis → Insight |
| `CHALLENGES` | DevilsAdvocate → Assumption |
| `ENABLES` | Technology → Innovation |
| `SOLVES` | Solution → Problem |
| `DISCOVERS` | Method → Pattern |

## Knowledge/Entity Relationships

| Relationship | Usage |
|-------------|-------|
| `RELATED_TO` | General association |
| `SIMILAR_TO` | Similarity |
| `ASSOCIATED_WITH` | Loose association |
| `BELONGS_TO` | Element → Category |
| `CATEGORIZES` | Category → Element |
| `DEFINES` | Definition → Term |
| `EXPLAINS` | Explanation → Concept |
| `EXAMPLE_OF` | Example → Concept |

## Analysis/Assessment Relationships

| Relationship | Usage |
|-------------|-------|
| `ANALYZES` | Analysis → Subject |
| `ASSESSES` | Assessment → Target |
| `EVALUATES` | Evaluation → Subject |
| `PRODUCES` | Process → Result |
| `GENERATES` | Generator → Output |
| `HAS_SCORE` | Assessment → Score |
| `HAS_FINDING` | Analysis → Finding |

## Workflow/Process Relationships

| Relationship | Usage |
|-------------|-------|
| `TRIGGERS` | Event → Action |
| `FOLLOWS_JOURNEY` | Step → JourneyPath |
| `TRANSITIONS_TO` | Phase → next Phase |
| `REQUIRES` | Step → Prerequisite |
| `DEPENDS_ON` | Element → Dependency |
| `BLOCKS` | Blocker → Blocked |
| `ENABLES` | Enabler → Enabled |

## Hierarchy/Structure Relationships

| Relationship | Usage |
|-------------|-------|
| `HAS_COMPONENT` | System → Component |
| `HAS_SUBCOMPONENT` | Component → SubComponent |
| `IS_PART_OF` | Part → Whole |
| `CONTAINS_ELEMENT` | Container → Element |
| `HAS_LEVEL` | Pyramid → Level |
| `HAS_LAYER` | Stack → Layer |

## JTBD-Specific Relationships

| Relationship | Usage |
|-------------|-------|
| `HAS_FUNCTIONAL` | Job → FunctionalJob |
| `HAS_EMOTIONAL` | Job → EmotionalJob |
| `HAS_SOCIAL` | Job → SocialJob |
| `REVEALS_JOB_IN` | Context → Job |

## TTA-Specific Relationships

| Relationship | Usage |
|-------------|-------|
| `TRENDS_TO` | Trend → Future state |
| `LEADS_TO` | Trend → AbsurdScenario |
| `REVEALS` | AbsurdScenario → Problem |

## Scenario Analysis Relationships

| Relationship | Usage |
|-------------|-------|
| `FORM_AXES_OF` | Uncertainties → ScenarioMatrix |
| `GENERATES_SCENARIOS` | Matrix → Scenarios |
| `HAS_SCENARIO` | Matrix → Scenario |

## Red Team Relationships

| Relationship | Usage |
|-------------|-------|
| `CHALLENGES` | DevilsAdvocate → Assumption |
| `QUESTIONS` | Challenge → Orthodoxy |
| `DISPROVES` | Evidence → Assumption |

## Common Query Patterns

### Find all relationships from a node
```cypher
MATCH (n {name: 'NodeName'})-[r]-(m)
RETURN type(r), m.name
```

### Find specific relationship paths
```cypher
MATCH path = (a:Framework)-[:HAS_PHASE*]->(p:Phase)
WHERE a.name CONTAINS 'TTA'
RETURN path
```

### Find relationship counts by type
```cypher
MATCH ()-[r]->()
RETURN type(r) as relType, count(*) as count
ORDER BY count DESC
LIMIT 50
```
