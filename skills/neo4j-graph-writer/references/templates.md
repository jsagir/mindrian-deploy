# Cypher Templates Reference

Complete templates for all common Neo4j write operations in Mindrian.

## Table of Contents

1. [Single Node Operations](#single-node-operations)
2. [Relationship Operations](#relationship-operations)
3. [Batch Operations](#batch-operations)
4. [PWS-Specific Templates](#pws-specific-templates)
5. [Rollback Templates](#rollback-templates)
6. [Verification Queries](#verification-queries)
7. [Health Check Queries](#health-check-queries)

---

## Single Node Operations

### Add a Framework

```cypher
// 1. CHECK
MATCH (n:Framework {name: "My Framework"}) RETURN n;

// 2. WRITE
MERGE (n:Framework {name: "My Framework"})
SET n.description = "What it does",
    n.source = "Where it came from",
    n.framework_type = "innovation",
    n.added_by = "claude-skill",
    n.added_date = date()
RETURN n;

// 3. VERIFY
MATCH (n:Framework {name: "My Framework"})
RETURN n.name, n.description, n.framework_type, labels(n);
```

### Add a Concept

```cypher
MERGE (n:Concept {name: "My Concept"})
SET n.description = "What this concept represents",
    n.added_by = "claude-skill",
    n.added_date = date()
RETURN n;
```

### Add a Person

```cypher
MERGE (n:Person {name: "Jane Doe"})
SET n.role = "Innovation Consultant",
    n.organization = "ACME Corp",
    n.added_by = "claude-skill",
    n.added_date = date()
RETURN n;
```

### Add a CaseStudy

```cypher
MERGE (n:CaseStudy {name: "Target Canada Failure"})
SET n.description = "Retail expansion failure due to data quality issues",
    n.outcome = "$7B loss",
    n.industry = "Retail",
    n.year = 2015,
    n.added_by = "claude-skill",
    n.added_date = date()
RETURN n;
```

### Add a BeautifulQuestion

```cypher
MERGE (n:BeautifulQuestion {name: "What if failure was impossible?"})
SET n.context = "Innovation brainstorming",
    n.source = "PWS Workshop",
    n.domain = "Strategic Thinking",
    n.added_by = "claude-skill",
    n.added_date = date()
RETURN n;
```

---

## Relationship Operations

### Link Framework to ProblemType

```cypher
MATCH (a:Framework {name: "JTBD"})
MATCH (b:ProblemType {name: "Customer Understanding"})
MERGE (a)-[r:ADDRESSES_PROBLEM_TYPE]->(b)
SET r.added_by = "claude-skill",
    r.added_date = date()
RETURN type(r), a.name, b.name;
```

### Link Concept to Cynefin Domain

```cypher
// Cynefin domains are FIXED — never create new ones
// Valid: Clear, Chaotic, Complex, Complicated, Disorder
MATCH (concept:Concept {name: "My Concept"})
MATCH (domain:CynefinDomain {name: "Complex"})
MERGE (concept)-[r:PART_OF]->(domain)
SET r.added_by = "claude-skill",
    r.added_date = date()
RETURN concept.name, domain.name;
```

### Link Framework to Framework (Alternative)

```cypher
MATCH (a:Framework {name: "Design Thinking"})
MATCH (b:Framework {name: "Lean Startup"})
MERGE (a)-[r:ALTERNATIVE_TO]->(b)
SET r.context = "Product development methodologies",
    r.added_by = "claude-skill",
    r.added_date = date()
RETURN a.name, type(r), b.name;
```

### Link Framework to Framework (Complement)

```cypher
MATCH (a:Framework {name: "JTBD"})
MATCH (b:Framework {name: "Design Thinking"})
MERGE (a)-[r:COMPLEMENTS]->(b)
SET r.context = "Customer-centric innovation",
    r.added_by = "claude-skill",
    r.added_date = date()
RETURN a.name, type(r), b.name;
```

### Link CaseStudy to Concept

```cypher
MATCH (cs:CaseStudy {name: "Target Canada Failure"})
MATCH (c:Concept {name: "Data Quality"})
MERGE (cs)-[r:EXEMPLIFIES]->(c)
SET r.added_by = "claude-skill",
    r.added_date = date()
RETURN cs.name, type(r), c.name;
```

### Link Book to Person (Author)

```cypher
MATCH (b:Book {name: "The Innovator's Dilemma"})
MATCH (p:Person {name: "Clayton Christensen"})
MERGE (b)-[r:AUTHORED_BY]->(p)
SET r.added_by = "claude-skill",
    r.added_date = date()
RETURN b.name, type(r), p.name;
```

---

## Batch Operations

### Batch Add Concepts (max 200)

```cypher
UNWIND $nodes AS node
MERGE (n:Concept {name: node.name})
SET n.description = node.description,
    n.added_by = "claude-skill",
    n.added_date = date()
RETURN count(n) AS created;
```

**Parameter format:**
```json
{
  "nodes": [
    {"name": "Concept A", "description": "Description A"},
    {"name": "Concept B", "description": "Description B"}
  ]
}
```

### Batch Add Relationships

```cypher
UNWIND $edges AS edge
MATCH (a {name: edge.source})
MATCH (b {name: edge.target})
MERGE (a)-[r:PART_OF]->(b)
SET r.added_by = "claude-skill",
    r.added_date = date()
RETURN count(r) AS created;
```

**Parameter format:**
```json
{
  "edges": [
    {"source": "Concept A", "target": "Domain X"},
    {"source": "Concept B", "target": "Domain Y"}
  ]
}
```

---

## PWS-Specific Templates

### Add a ReverseSalient with Cross-Domain Links

```cypher
MERGE (rs:ReverseSalient {name: "Data Privacy in Healthcare AI"})
SET rs.description = "Gap between AI capability and regulatory compliance",
    rs.gap_type = "regulatory",
    rs.added_by = "claude-skill",
    rs.added_date = date()

WITH rs
MATCH (d1:Domain {name: "Healthcare"})
MATCH (d2:Domain {name: "Artificial Intelligence"})
MERGE (rs)-[:PART_OF]->(d1)
MERGE (rs)-[:PART_OF]->(d2)

RETURN rs.name, collect(d1.name) + collect(d2.name) AS domains;
```

### Add an InnovationOpportunity

```cypher
MERGE (io:InnovationOpportunity {name: "AI-Powered DIKW Validation"})
SET io.description = "Automated validation of understanding before action",
    io.potential = "High",
    io.status = "Exploring",
    io.added_by = "claude-skill",
    io.added_date = date()

WITH io
MATCH (f:Framework {name: "Ackoff Pyramid"})
MERGE (io)-[:APPLIES_TO]->(f)

RETURN io.name, io.status;
```

### Add ProcessSteps in Order

```cypher
UNWIND range(0, size($steps)-1) AS i
MERGE (s:ProcessStep {name: $steps[i].name})
SET s.order = i + 1,
    s.description = $steps[i].description,
    s.parent_process = $process_name,
    s.added_by = "claude-skill",
    s.added_date = date()
RETURN count(s) AS created;
```

### Link ProcessSteps Sequentially

```cypher
MATCH (s:ProcessStep)
WHERE s.parent_process = $process_name
WITH s ORDER BY s.order
WITH collect(s) AS steps
UNWIND range(0, size(steps)-2) AS i
WITH steps[i] AS current, steps[i+1] AS next
MERGE (current)-[r:LEADS_TO]->(next)
SET r.added_by = "claude-skill"
RETURN count(r) AS links_created;
```

---

## Rollback Templates

### Delete All Nodes Added Today by Claude

```cypher
MATCH (n) 
WHERE n.added_by = "claude-skill" AND n.added_date = date()
DETACH DELETE n
RETURN count(n) AS deleted;
```

### Delete Specific Node

```cypher
MATCH (n:Label {name: "Node Name"})
DETACH DELETE n;
```

### Delete Specific Relationship

```cypher
MATCH (a {name: "Source"})-[r:REL_TYPE]->(b {name: "Target"})
DELETE r;
```

### Delete Relationships Only (Keep Nodes)

```cypher
MATCH ()-[r]->()
WHERE r.added_by = "claude-skill" AND r.added_date = date()
DELETE r
RETURN count(r) AS deleted;
```

---

## Verification Queries

### Check for Duplicates Before Adding

```cypher
// Exact match
MATCH (n) WHERE n.name = "My Node Name"
RETURN labels(n), n.name, n.description;

// Fuzzy match (fulltext index)
CALL db.index.fulltext.queryNodes("entity_fulltext", "my search term")
YIELD node, score
WHERE score > 0.5
RETURN labels(node), node.name, score
LIMIT 10;
```

### Verify Node Was Created

```cypher
MATCH (n)
WHERE n.added_by = "claude-skill" AND n.added_date = date()
RETURN labels(n)[0] AS label, n.name, n.description
ORDER BY n.name;
```

### Verify Relationship Was Created

```cypher
MATCH (a)-[r]->(b)
WHERE r.added_by = "claude-skill" AND r.added_date = date()
RETURN a.name, type(r), b.name
ORDER BY type(r);
```

---

## Health Check Queries

### Find Orphan Nodes (no relationships)

```cypher
MATCH (n)
WHERE NOT (n)--()
AND NOT n:MCPTool  // Known orphans
RETURN labels(n)[0] AS label, count(n) AS orphans
ORDER BY orphans DESC
LIMIT 20;
```

### Find Self-Loops

```cypher
MATCH (n)-[r]->(n)
RETURN labels(n)[0] AS label, type(r) AS rel, count(r) AS loops
ORDER BY loops DESC;
```

### Count Nodes by Label

```cypher
MATCH (n)
RETURN labels(n)[0] AS label, count(n) AS count
ORDER BY count DESC
LIMIT 30;
```

### Count Relationships by Type

```cypher
MATCH ()-[r]->()
RETURN type(r) AS type, count(r) AS count
ORDER BY count DESC
LIMIT 30;
```

### Check Index Coverage

```cypher
SHOW INDEXES
YIELD name, labelsOrTypes, properties, type
RETURN name, labelsOrTypes, properties, type
ORDER BY name;
```
