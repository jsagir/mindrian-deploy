# Neo4j Knowledge Graph Reference

## Table of Contents
1. [Core Concepts](#core-concepts)
2. [Node Types](#node-types)
3. [Relationship Types](#relationship-types)
4. [Query Patterns](#query-patterns)
5. [Lazy Graph RAG](#lazy-graph-rag)
6. [Cynefin Integration](#cynefin-integration)

---

## Core Concepts

Neo4j stores **semantic relationships** and **contextual connections** that enable multi-hop traversal for non-obvious insights.

**Primary Functions:**
- Entity resolution via canonical IDs
- Framework-to-problem matching
- Dependency graph traversal
- Prerequisite chain discovery

---

## Node Types

| Node Label | Purpose | Key Properties |
|------------|---------|----------------|
| `Concept` | Knowledge entities | `id`, `name`, `description`, `embedding` |
| `Framework` | Problem-solving frameworks | `id`, `name`, `domain`, `complexity` |
| `ProcessStep` | Workflow steps | `id`, `order`, `action`, `dependencies` |
| `Problem` | User problems/queries | `id`, `description`, `cynefin_domain` |
| `User` | User profiles | `id`, `preferences`, `expertise_level` |
| `Session` | Conversation sessions | `id`, `start_time`, `context_summary` |

---

## Relationship Types

| Relationship | From → To | Purpose |
|--------------|-----------|---------|
| `APPLIES_TO` | Framework → Problem | Framework applicability |
| `REQUIRES` | Concept → Concept | Prerequisites |
| `CONTAINS` | Framework → ProcessStep | Framework composition |
| `RELATED_TO` | Concept → Concept | Semantic similarity |
| `FOLLOWS` | ProcessStep → ProcessStep | Sequence ordering |
| `CLASSIFIED_AS` | Problem → CynefinDomain | Complexity classification |

---

## Query Patterns

### Find Related Concepts (2-hop)
```cypher
MATCH (c:Concept {name: $concept_name})-[:RELATED_TO*1..2]-(related)
RETURN related.name, related.description
ORDER BY related.relevance_score DESC
LIMIT 10
```

### Find Applicable Frameworks
```cypher
MATCH (p:Problem)-[:CLASSIFIED_AS]->(d:CynefinDomain)
MATCH (f:Framework)-[:APPLIES_TO]->(d)
WHERE p.id = $problem_id
RETURN f.name, f.description, f.steps
```

### Get Prerequisite Chain
```cypher
MATCH path = (start:Concept {name: $concept})-[:REQUIRES*]->(prereq)
RETURN nodes(path) as prerequisite_chain
ORDER BY length(path) DESC
```

### Workflow Step Ordering
```cypher
MATCH (f:Framework {name: $framework})-[:CONTAINS]->(step:ProcessStep)
OPTIONAL MATCH (step)-[:FOLLOWS]->(next:ProcessStep)
RETURN step.order, step.action, next.action as next_step
ORDER BY step.order
```

### Entity Resolution
```cypher
MATCH (c:Concept)
WHERE c.name =~ $fuzzy_pattern OR c.aliases CONTAINS $search_term
RETURN c.id as canonical_id, c.name, c.aliases
```

---

## Lazy Graph RAG

Combines vector similarity with graph traversal for richer retrieval:

**Process:**
1. Vector search finds initial candidates (Supabase)
2. Graph expansion discovers related concepts (Neo4j)
3. Relationship weighting prioritizes results
4. Claude synthesizes combined context

**Query Pattern:**
```cypher
// After vector search returns candidate IDs
UNWIND $candidate_ids AS cid
MATCH (c:Concept {id: cid})-[r]-(related)
WHERE type(r) IN ['RELATED_TO', 'REQUIRES', 'APPLIES_TO']
RETURN c, r, related
```

---

## Cynefin Integration

Map problems to complexity domains for appropriate response strategies:

| Domain | Characteristics | Response Strategy |
|--------|-----------------|-------------------|
| **Clear** | Obvious cause-effect | Apply best practice |
| **Complicated** | Expert analysis needed | Analyze then respond |
| **Complex** | Emergent patterns | Probe-sense-respond |
| **Chaotic** | No clear patterns | Act-sense-respond |
| **Confused** | Domain unclear | Gather more information |

**Classification Query:**
```cypher
MATCH (p:Problem {id: $problem_id})
MATCH (p)-[:CLASSIFIED_AS]->(d:CynefinDomain)
RETURN d.name as domain, d.response_strategy
```

---

## Best Practices

1. **Always use canonical IDs** - Prevent duplicate knowledge nodes
2. **Limit traversal depth** - Use `*1..3` not unbounded `*`
3. **Index frequently queried properties** - `name`, `id`, `embedding`
4. **Batch relationship creation** - Use `UNWIND` for bulk operations
5. **Validate before insert** - Check for existing nodes with `MERGE`
