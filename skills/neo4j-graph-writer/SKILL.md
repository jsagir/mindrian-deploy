---
name: Mindrian-Team-Neo4j-Writer
description: >
  Mindrian-Team-Neo4j-Writer - Safely write nodes, relationships, and structured knowledge
  to the Mindrian Neo4j knowledge graph. Use when asked to: add a framework/concept/entity
  to the graph, create relationships between nodes, store PWS insights, add ReverseSalients
  or BeautifulQuestions, link concepts to Cynefin domains, enrich Larry's knowledge base,
  batch import structured data to Neo4j, or update the Mindrian knowledge graph.
  Enforces WHAT/WHY/HOW pre-flight checks, schema governance, and 512MB memory safety.
  Repository: https://github.com/jsagir/mindrian-deploy
---

# Mindrian-Team-Neo4j-Writer

Mindrian-Team-Neo4j-Writer writes safely to Mindrian's Neo4j knowledge graph (~20K nodes, ~166K edges).

## Pre-Flight Checklist (MANDATORY)

Before ANY write operation, answer these three questions:

### 1. WHAT are you adding?

| Question | Answer Required |
|----------|-----------------|
| Node or Relationship? | Node / Relationship / Both |
| Which label(s)? | Must use EXISTING label (see `references/schema.md`) |
| Which properties? | Every node needs `name` + label-specific props |
| How many items? | Estimate count for batching |

### 2. WHY does it belong in the graph?

| Question | Answer Required |
|----------|-----------------|
| What query will retrieve this? | Name the retrieval path |
| Does it duplicate existing data? | Run CHECK query first |
| Which layer? | evidence / meaning / structural / lazy_graphrag |
| Will Larry benefit? | If no, don't add it |

### 3. HOW will you add it safely?

| Question | Answer Required |
|----------|-----------------|
| Using MERGE (not CREATE)? | Always MERGE |
| Batch size ≤200? | Max 200 per UNWIND |
| Rollback plan ready? | Know your DELETE query |
| Verification query written? | CHECK → WRITE → VERIFY |

## Quick Reference

### Write Pattern (always follow this order)

```cypher
// 1. CHECK - does it exist?
MATCH (n:Label {name: "Name"}) RETURN n;

// 2. WRITE - with MERGE and tracking
MERGE (n:Label {name: "Name"})
SET n.description = "...",
    n.added_by = "claude-skill",
    n.added_date = date()
RETURN n;

// 3. VERIFY - confirm success
MATCH (n:Label {name: "Name"}) RETURN n.name, labels(n);
```

### Add Relationship

```cypher
MATCH (a:Label1 {name: "Source"})
MATCH (b:Label2 {name: "Target"})
MERGE (a)-[r:RELATIONSHIP_TYPE]->(b)
SET r.added_by = "claude-skill", r.added_date = date()
RETURN type(r), a.name, b.name;
```

### Batch Write (max 200)

```cypher
UNWIND $nodes AS node
MERGE (n:Label {name: node.name})
SET n.description = node.description,
    n.added_by = "claude-skill",
    n.added_date = date()
RETURN count(n) AS created;
```

### Rollback

```cypher
// Delete today's additions
MATCH (n) WHERE n.added_by = "claude-skill" AND n.added_date = date()
DETACH DELETE n;
```

## Memory Safety (512MB Render)

- **LIMIT all queries** — never `MATCH (n) RETURN n` without filters
- **Max 1000 nodes** per result set
- **Batch at 200** per UNWIND
- **Use indexes** — fulltext search over label scan

## Verification After Writes

Test that Larry can retrieve your data:

```python
from tools.graphrag_lite import enrich_for_larry
hint = enrich_for_larry("your test query", turn_count=3)
print(hint)  # Should include your new data
```

Larry's retrieval paths:
1. Fulltext search on `LazyGraphConcept.name`
2. `CO_OCCURS` neighbors in same community
3. `entity_fulltext` index for `__Entity__`, `Framework`, `Concept`
4. `framework_ecosystem_search` index

## Reference Files

- **`references/schema.md`** — Allowed labels, relationships, and their properties
- **`references/templates.md`** — Complete Cypher templates for all common operations

Consult these before creating new labels or relationship types.

## Key Constraints

| Constraint | Value |
|------------|-------|
| Max batch size | 200 nodes/edges |
| Max result set | 1,000 nodes |
| New label threshold | 200+ nodes required |
| New relationship threshold | 200+ edges required |
| Always use | MERGE (never CREATE) |
| Always tag | `added_by`, `added_date` |
