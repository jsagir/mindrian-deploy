# Schema Governance Reference

Complete schema for Mindrian's Neo4j knowledge graph. **Use ONLY these labels and relationships** unless creating 200+ new items.

## Table of Contents

1. [Allowed Labels by Layer](#allowed-labels-by-layer)
2. [Allowed Relationship Types](#allowed-relationship-types)
3. [Graph Stats Baseline](#graph-stats-baseline)
4. [Creating New Schema Elements](#creating-new-schema-elements)

---

## Allowed Labels by Layer

### Evidence Layer (raw content)

| Label | Required Properties | Optional Properties |
|-------|---------------------|---------------------|
| `Chunk` | `id`, `chunk_id`, `content` | `source`, `position` |
| `DocumentChunk` | `content`, `source` | `chunk_index`, `embedding` |
| `FrameworkChunk` | `content`, `framework` | `chunk_index` |

### Meaning Layer (extracted knowledge)

| Label | Required Properties | Optional Properties |
|-------|---------------------|---------------------|
| `__Entity__` | `name` | `entity_type`, `description`, `embedding` |
| `Concept` | `name` | `description`, `embedding` |
| `Framework` | `name` | `description`, `source`, `framework_type`, `principles` |
| `Person` | `name` | `role`, `organization` |
| `ProcessStep` | `name`, `order` | `description`, `parent_process` |
| `DictionaryTerm` | `name`, `definition` | `source`, `domain` |
| `ProblemType` | `name` | `description`, `domain` |
| `Technique` | `name` | `description`, `use_case` |
| `Book` | `name` | `author`, `year`, `isbn` |
| `CaseStudy` | `name`, `description` | `outcome`, `industry`, `year` |
| `CynefinDomain` | `name` | — (ONLY 5 exist: Clear, Chaotic, Complex, Complicated, Disorder) |

### Structural Layer (organizational)

| Label | Required Properties | Optional Properties |
|-------|---------------------|---------------------|
| `Product` | `name` | `description`, `company` |
| `Event` | `name` | `date`, `location`, `type` |
| `Organization` | `name` | `type`, `industry`, `location` |
| `Domain` | `name` | `description`, `parent_domain` |
| `InnovationOpportunity` | `name` | `description`, `potential`, `status` |
| `BeautifulQuestion` | `name` | `context`, `source`, `domain` |
| `ReverseSalient` | `name` | `description`, `domains`, `gap_type` |
| `Problem` | `name` | `description`, `severity`, `domain` |
| `StrategicResponse` | `name` | `description`, `problem_addressed` |
| `DiagnosticElement` | `name` | `description`, `category` |
| `StrategicComponent` | `name` | `description`, `strategy` |

### LazyGraphRAG Layer (NLP-extracted)

| Label | Required Properties | Optional Properties |
|-------|---------------------|---------------------|
| `LazyGraphConcept` | `name` | `community_id`, `degree`, `chunk_count` |

### Infrastructure Layer

| Label | Required Properties | Optional Properties |
|-------|---------------------|---------------------|
| `Agent` | `name` | `role`, `capabilities` |
| `Document` | `name` | `type`, `status`, `source`, `has_chunks` |

---

## Allowed Relationship Types

### Top 20 by Count (use these first)

| Type | Pattern | Count | Use For |
|------|---------|-------|---------|
| `CO_OCCURS` | LazyGraphConcept ↔ LazyGraphConcept | 132,016 | Concept co-occurrence |
| `MENTIONED_IN` | LazyGraphConcept → Chunk | 12,564 | Concept-to-source linking |
| `HAS_ENTITY` | Chunk → Entity | 7,772 | Chunk entity extraction |
| `SIMILAR` | Entity ↔ Entity | 2,366 | Semantic similarity |
| `IMPLEMENTED_AS` | Concept → Product/Process | 2,052 | Abstract → concrete |
| `HAS` | Parent → Child | 1,485 | Generic containment |
| `PART_OF` | Component → Parent | 1,471 | Membership/hierarchy |
| `NEXT_CHUNK` | Chunk → Chunk | 1,159 | Sequential ordering |
| `INTRODUCES_TERM` | Chunk → DictionaryTerm | 998 | Term definitions |
| `ENABLES` | Tool → Capability | 366 | Tool functionality |
| `LEADS_TO` | Cause → Effect | 309 | Causal chains |
| `ADDRESSES_PROBLEM_TYPE` | Framework → ProblemType | 292 | Framework applicability |
| `ALTERNATIVE_TO` | Framework ↔ Framework | 220 | Competing approaches |
| `SUPPORTS` | Tool → Framework | 156 | Tool-framework links |
| `COMPLEMENTS` | Framework ↔ Framework | 148 | Synergistic frameworks |
| `AUTHORED_BY` | Book → Person | 132 | Authorship |
| `INTRODUCES_FRAMEWORK` | Chunk → Framework | 125 | Framework source |

### Additional Semantic Relationships

| Type | Pattern | Use For |
|------|---------|---------|
| `APPLIES_TO` | Framework → Domain | Framework scope |
| `REQUIRES` | Step → Step | Process dependencies |
| `CONTRADICTS` | Concept ↔ Concept | Conflicting ideas |
| `EXEMPLIFIES` | CaseStudy → Concept | Case-concept links |
| `BELONGS_TO` | Entity → Organization | Organizational membership |
| `INFLUENCES` | Person → Framework | Intellectual contribution |
| `PRECEDES` | Event → Event | Temporal ordering |
| `SUPERSEDES` | New → Old | Version/replacement |

---

## Graph Stats Baseline

| Metric | Value |
|--------|-------|
| Total nodes | ~20,230 |
| Total edges | ~166,250 |
| LazyGraphConcepts | 7,922 |
| Communities | 39 |
| Label types | 700 (consolidation planned) |
| Relationship types | 1,610 (consolidation planned) |

---

## Creating New Schema Elements

### When to Create a New Label

Only create a new label when ALL of these are true:

1. **Volume threshold**: Will create 200+ nodes with this label
2. **No fit**: No existing label semantically fits
3. **Unique properties**: Needs properties no existing label has
4. **Documented**: Decision recorded with rationale

### When to Create a New Relationship Type

Only create a new relationship type when ALL of these are true:

1. **Volume threshold**: Will create 200+ edges of this type
2. **No fit**: No existing type captures the semantics
3. **Consistent direction**: Clear source → target semantics
4. **Documented**: Decision recorded with rationale

### Documentation Template for New Schema

```cypher
// NEW LABEL: MyNewLabel
// Rationale: [Why existing labels don't fit]
// Expected count: [200+ estimate]
// Properties: [List required and optional]
// Retrieval path: [How Larry will find these]

// NEW RELATIONSHIP: NEW_REL_TYPE
// Rationale: [Why existing types don't fit]
// Pattern: LabelA → LabelB
// Expected count: [200+ estimate]
// Semantics: [What the relationship means]
```
