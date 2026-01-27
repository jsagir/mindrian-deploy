# Neo4j Graph Writer Skill

**Purpose:** Safely add nodes, relationships, and structured knowledge to the Mindrian Neo4j knowledge graph.

---

## Pre-Flight: WHAT → WHY → HOW

Before writing ANYTHING to Neo4j, answer these three questions:

### 1. WHAT are you adding?

| Question | Must Answer |
|----------|-------------|
| Node or Relationship? | Node / Relationship / Both |
| What label(s)? | Must use an EXISTING label from the schema (see below) |
| What properties? | Every node needs `name` + label-specific props |
| How many items? | Estimate count before batch writing |

### 2. WHY does this belong in the graph?

| Question | Must Answer |
|----------|-------------|
| What query will use this? | Name the retrieval path |
| Does it duplicate existing data? | Run a CHECK query first |
| Which layer does it belong to? | evidence / meaning / structural / lazy_graphrag |
| Will Larry's enrichment benefit? | If no, don't add it |

### 3. HOW will you add it safely?

| Question | Must Answer |
|----------|-------------|
| Using MERGE (not CREATE)? | Always MERGE to avoid duplicates |
| Batch size? | Max 200 per UNWIND |
| Rollback plan? | Know how to DELETE what you added |
| Verification query? | Write the check query before the write query |

---

## Schema Governance Rules

### Allowed Labels (use ONLY these)

**Evidence Layer:**
- `Chunk` — raw content chunks (id, chunk_id, content, source)
- `DocumentChunk` — document-specific chunks (content, source, chunk_index)
- `FrameworkChunk` — framework-specific chunks (content, framework)

**Meaning Layer:**
- `__Entity__` — LightRAG extracted entities (name, entity_type, description)
- `Concept` — abstract concepts (name, description)
- `Framework` — named frameworks/methodologies (name, description, source)
- `Person` — people (name, role)
- `ProcessStep` — ordered steps (name, order)
- `DictionaryTerm` — definitions (name, definition)
- `ProblemType` — problem categories (name)
- `Technique` — methods/techniques (name)
- `Book` — books/publications (name, author)
- `CaseStudy` — real-world examples (name, description)
- `CynefinDomain` — ONLY 5 exist: Clear, Chaotic, Complex, Complicated, Disorder

**Structural Layer:**
- `Product` — products/services (name)
- `Event` — events (name)
- `Organization` — companies/orgs (name)
- `Domain` — knowledge domains (name)
- `InnovationOpportunity` — innovation opportunities (name)
- `BeautifulQuestion` — powerful questions (name)
- `ReverseSalient` — bottlenecks/gaps (name)
- `Problem` — specific problems (name)
- `StrategicResponse` — strategic responses (name)
- `DiagnosticElement` — diagnostic elements (name)
- `StrategicComponent` — strategic components (name)

**LazyGraphRAG Layer:**
- `LazyGraphConcept` — NLP-extracted concepts (name, community_id, degree, chunk_count)

**Infrastructure Layer:**
- `Agent` — system agents (name, role)
- `Document` — documents (name, type)

### DO NOT create new labels unless:
- The count will exceed 200 nodes
- No existing label fits
- You document the decision

### Allowed Relationship Types (top 20 by count)

| Type | Pattern | Count |
|------|---------|-------|
| CO_OCCURS | LazyGraphConcept ↔ LazyGraphConcept | 132,016 |
| MENTIONED_IN | LazyGraphConcept → Chunk | 12,564 |
| HAS_ENTITY | Chunk → Entity | 7,772 |
| SIMILAR | Entity ↔ Entity | 2,366 |
| IMPLEMENTED_AS | Concept → Product/Process | 2,052 |
| HAS | generic containment | 1,485 |
| PART_OF | Component → Parent | 1,471 |
| NEXT_CHUNK | Chunk → Chunk | 1,159 |
| INTRODUCES_TERM | Chunk → DictionaryTerm | 998 |
| ENABLES | Tool → Capability | 366 |
| LEADS_TO | Step → Step / Cause → Effect | 309 |
| ADDRESSES_PROBLEM_TYPE | Framework → ProblemType | 292 |
| ALTERNATIVE_TO | Framework ↔ Framework | 220 |
| SUPPORTS | Tool → Framework | 156 |
| COMPLEMENTS | Framework ↔ Framework | 148 |
| AUTHORED_BY | Book/CreativeWork → Person | 132 |
| INTRODUCES_FRAMEWORK | Chunk → Framework | 125 |

### DO NOT create new relationship types unless:
- Count will exceed 200 edges
- No existing type fits
- You document the decision

---

## Templates

### Add a single node

```cypher
// 1. CHECK first
MATCH (n:Framework {name: "My Framework"}) RETURN n;

// 2. WRITE with MERGE
MERGE (n:Framework {name: "My Framework"})
SET n.description = "What it does",
    n.source = "Where it came from",
    n.added_by = "claude-skill",
    n.added_date = date()
RETURN n;

// 3. VERIFY
MATCH (n:Framework {name: "My Framework"})
RETURN n.name, n.description, labels(n);
```

### Add a relationship

```cypher
// 1. CHECK both endpoints exist
MATCH (a:Framework {name: "JTBD"}) RETURN a.name;
MATCH (b:ProblemType {name: "Customer Understanding"}) RETURN b.name;

// 2. WRITE with MERGE
MATCH (a:Framework {name: "JTBD"})
MATCH (b:ProblemType {name: "Customer Understanding"})
MERGE (a)-[r:ADDRESSES_PROBLEM_TYPE]->(b)
SET r.added_by = "claude-skill",
    r.added_date = date()
RETURN type(r), a.name, b.name;

// 3. VERIFY
MATCH (a:Framework {name: "JTBD"})-[r:ADDRESSES_PROBLEM_TYPE]->(b)
RETURN a.name, type(r), b.name;
```

### Batch add nodes

```cypher
// UNWIND batch (max 200 per batch)
UNWIND $nodes AS node
MERGE (n:Concept {name: node.name})
SET n.description = node.description,
    n.added_by = "claude-skill",
    n.added_date = date()
RETURN count(n) AS created;
```

### Link a concept to Cynefin domain

```cypher
// Cynefin domains are FIXED — never create new ones
MATCH (concept:Concept {name: "My Concept"})
MATCH (domain:CynefinDomain {name: "Complex"})
MERGE (concept)-[:PART_OF]->(domain)
RETURN concept.name, domain.name;
```

### Add a ReverseSalient with cross-domain links

```cypher
MERGE (rs:ReverseSalient {name: "Data Privacy in Healthcare AI"})
SET rs.description = "Gap between AI capability and regulatory compliance",
    rs.added_by = "claude-skill",
    rs.added_date = date()

WITH rs
MATCH (d1:Domain {name: "Healthcare"})
MATCH (d2:Domain {name: "Artificial Intelligence"})
MERGE (rs)-[:PART_OF]->(d1)
MERGE (rs)-[:PART_OF]->(d2)

RETURN rs.name;
```

---

## Rollback Templates

### Delete nodes you just added

```cypher
// By added_by tag
MATCH (n) WHERE n.added_by = "claude-skill" AND n.added_date = date()
DETACH DELETE n
RETURN count(n) AS deleted;
```

### Delete specific relationship

```cypher
MATCH (a {name: "Source"})-[r:REL_TYPE]->(b {name: "Target"})
DELETE r;
```

---

## Verification Queries

### Check for duplicates before adding

```cypher
// Exact match
MATCH (n) WHERE n.name = "My Node Name"
RETURN labels(n), n.name, n.description;

// Fuzzy match (fulltext)
CALL db.index.fulltext.queryNodes("entity_fulltext", "my search term")
YIELD node, score
WHERE score > 0.5
RETURN labels(node), node.name, score
LIMIT 10;
```

### Verify graph health after changes

```cypher
// Orphan check — nodes with zero relationships
MATCH (n)
WHERE NOT (n)--()
AND NOT n:MCPTool  // MCPTools are known orphans
RETURN labels(n)[0] AS label, count(n) AS orphans
ORDER BY orphans DESC;

// Self-loop check
MATCH (n)-[r]->(n)
RETURN labels(n)[0] AS label, type(r) AS rel, count(r) AS loops;
```

---

## Graph Stats (Post-Cleanup Baseline)

| Metric | Value |
|--------|-------|
| Total nodes | ~20,230 |
| Total edges | ~166,250 |
| LazyGraphConcepts | 7,922 |
| Communities | 39 |
| Label types | 700 (consolidation planned) |
| Relationship types | 1,610 (consolidation planned) |

---

## Memory Safety (512MB Render)

- Never load more than 1,000 nodes into a single result
- Use `LIMIT` on all exploratory queries
- Avoid `MATCH (n) RETURN n` without filters
- Batch writes at max 200 per UNWIND
- The `graphrag_lite.py` bounded cache keeps memory under 2MB

---

## Integration with graphrag_lite.py

After adding data, verify Larry can find it:

```python
from tools.graphrag_lite import enrich_for_larry
hint = enrich_for_larry("your test query", turn_count=3)
print(hint)
```

The retrieval paths that `graphrag_lite.py` uses:
1. **Concept lookup** — fulltext search on LazyGraphConcept.name
2. **Community context** — CO_OCCURS neighbors in same community
3. **Entity layer** — __Entity__, Framework, Concept via entity_fulltext index
4. **Framework suggestions** — framework_ecosystem_search index

If your new data should appear in retrieval, it must be reachable through one of these paths.
