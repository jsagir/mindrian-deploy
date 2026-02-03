---
name: neo4j-schema-navigator
description: >
  Navigate the Mindrian Neo4j knowledge graph with full schema understanding.
  Use when querying Neo4j via MCP to avoid schema discovery overhead (schema is 2MB+).
  Triggers: Neo4j queries, graph operations, Cypher queries, knowledge graph exploration,
  finding nodes/relationships, querying frameworks, documents, entities, PWS methodologies.
  Provides pre-loaded schema so MCP does not need to fetch it.
version: 2.0.0
updated: 2026-02-03
---

# Neo4j Schema Navigator v2.0

Pre-loaded schema for the Mindrian PWS Knowledge Graph, eliminating MCP schema discovery overhead.

## Schema Overview (Feb 2026)

- **18,795+ nodes** across **350+ distinct labels**
- **Top labels**: LazyGraphConcept (8,425), __Entity__ (5,741), Chunk (1,167), Framework (761)
- Key domains: PWS Methodologies, Innovation Frameworks, Problems, Questions, Scenarios, Workshop Phases

## Quick Reference - Top 50 Node Types by Count

| Label | Count | Description |
|-------|-------|-------------|
| LazyGraphConcept | 8,425 | Core concepts from LazyGraph extraction |
| __Entity__ | 5,741 | Generic entities with embeddings |
| Chunk | 1,167 | Document chunks for RAG retrieval |
| Framework | 761 | PWS methodologies & innovation frameworks |
| base | 447 | Base graph nodes |
| StrategicResponse | 432 | Strategic analysis responses |
| DictionaryTerm | 313 | PWS terminology definitions |
| Document | 287 | Source documents |
| Problem | 221 | Problem definitions (PWS core) |
| ProcessStep | 197 | Workflow/process steps |
| Technique | 166 | Innovation techniques |
| Concept | 109 | Core concepts |
| Question | 74 | Beautiful questions, research questions |
| Book | 69 | Book references |
| Phase | 65 | Workshop phases |
| DevilsAdvocate | 65 | Red team challenges |
| Author | 65 | Document authors |
| Component | 61 | System components |
| Person | 56 | People entities |
| Domain | 52 | Domain categorizations |
| BeautifulQuestion | 43 | Beautiful Question methodology |
| InnovationTool | 40 | Innovation tools |
| Characteristic | 38 | Defining characteristics |
| Research | 38 | Research nodes |
| Agent | 37 | AI agents/bots |
| ResearchTool | 35 | Research tools |
| Stage | 33 | Process stages |
| Product | 30 | Products |
| Event | 30 | Events |
| LeveragePoint | 29 | System leverage points |
| CaseStudy | 23 | Real-world case studies |
| Opportunity | 20 | Innovation opportunities |
| Scenario | 17 | Scenario planning nodes |
| ReverseSalient | 17 | Reverse salient bottlenecks |
| Trend | 15 | Trends (TTA methodology) |
| Bot | 14 | Mindrian bot definitions |
| Job | 12 | Jobs To Be Done |
| Assumption | 12 | Assumptions to test |
| ThinkingHat | 6 | Six Thinking Hats |
| AbsurdScenario | 6 | TTA absurd scenarios |

## PWS Workshop Node Types

### TTA (Trending to the Absurd)
- `Trend` (15) - Current trends to extrapolate
- `AbsurdScenario` (6) - Extreme future scenarios
- `Opportunity` (20) - Problems worth solving found via TTA

### JTBD (Jobs To Be Done)
- `Job` (12) - Main job definitions
- `FunctionalJob` (5) - Functional jobs
- `EmotionalJob` (4) - Emotional jobs
- `SocialJob` (4) - Social jobs
- `JobCategory` (6) - Job categorizations

### Six Thinking Hats
- `ThinkingHat` (6) - The six hats
- `Hat` (6) - Hat instances
- `ThinkingMode` (6) - Thinking modes

### Scenario Analysis
- `Scenario` (17) - Scenario definitions
- `ScenarioMatrix` (2) - 2x2 matrices
- `ScenarioPath` (3) - Scenario pathways

### Nested Hierarchies / Reverse Salients
- `ReverseSalient` (17) - Bottlenecks/lagging components
- `LeveragePoint` (29) - High-impact intervention points
- `Bottleneck` (13) - System bottlenecks

### Knowns/Unknowns Matrix
- `KnownKnown` (6) - Known knowns
- `KnownUnknown` (8) - Known unknowns
- `UnknownKnown` (7) - Unknown knowns
- `UnknownUnknown` (8) - Unknown unknowns

### Ackoff's Pyramid (DIKW)
- `PyramidLevel` (5) - Data, Information, Knowledge, Wisdom

### Red Team / Devil's Advocate
- `DevilsAdvocate` (65) - Challenge perspectives
- `Orthodoxy` (15) - Orthodoxies to challenge
- `Assumption` (12) - Assumptions to test

## Common Node Properties

### All __Entity__ Nodes
```
id: String (unique identifier)
name: String (display name)
embedding: FloatArray (1536-dim vector for similarity search)
```

### Framework Nodes
```
name: String
framework_type: String
principles: StringArray
methods: StringArray
capabilities: StringArray
status: String
```

### Document/Chunk Nodes
```
Document: name, doc_type, status, source, has_chunks, framework_types
Chunk: text, position, chunkId, embedding
```

### Problem Nodes
```
name: String
description: String
problem_type: String
severity: String
domain: String
```

## Common Cypher Patterns

### Find Frameworks by Type
```cypher
MATCH (f:Framework)
WHERE f.name CONTAINS 'PWS' OR f.framework_type = 'innovation'
RETURN f.name, f.framework_type, f.principles
```

### Find Problems Worth Solving
```cypher
MATCH (p:Problem)
WHERE p.problem_type = 'worth_solving'
RETURN p.name, p.description, p.domain
ORDER BY p.name
```

### Find Workshop Phases
```cypher
MATCH (p:Phase)
RETURN p.name, p.workshop_type, p.order
ORDER BY p.workshop_type, p.order
```

### Find Related Entities by Name
```cypher
MATCH (n)-[r]-(m)
WHERE n.name CONTAINS 'keyword'
RETURN n, type(r), m LIMIT 50
```

### Find Documents with Chunks (for RAG)
```cypher
MATCH (d:Document)-[:HAS_CHUNK]->(c:Chunk)
WHERE d.has_chunks = true
RETURN d.name, count(c) as chunk_count
ORDER BY chunk_count DESC
```

### Vector Similarity Search
```cypher
MATCH (n:__Entity__)
WHERE n.embedding IS NOT NULL
WITH n, gds.similarity.cosine(n.embedding, $queryEmbedding) AS score
WHERE score > 0.7
RETURN n.name, score
ORDER BY score DESC
LIMIT 10
```

### Find Case Studies for a Framework
```cypher
MATCH (cs:CaseStudy)-[:APPLIED_FRAMEWORK]->(f:Framework)
WHERE f.name CONTAINS 'JTBD'
RETURN cs.name, cs.description, f.name
```

### Find Bot Definitions
```cypher
MATCH (b:Bot)
RETURN b.name, b.bot_id, b.description, b.has_phases
```

## Relationship Types

Common relationships in the graph:
- `HAS_CHUNK` - Document to Chunk
- `APPLIED_FRAMEWORK` - CaseStudy to Framework
- `RELATED_TO` - General relationship
- `PART_OF` - Hierarchical containment
- `LEADS_TO` - Sequential/causal
- `CHALLENGES` - Devil's Advocate challenges
- `ADDRESSES` - Solution addresses Problem
- `CONTAINS` - Container relationship

## Usage with Neo4j MCP

When using Neo4j MCP tools, reference this schema instead of calling schema discovery:

1. Check this file for relevant node types and their counts
2. Look up specific properties in the patterns above
3. Build Cypher queries with confidence about available properties
4. **Skip MCP schema fetch calls** - this skill provides the schema

## Reference Files

- `references/node-counts.md` - Full node label counts (350+ types)
- `references/relationships.md` - Relationship type reference
- `references/pws-nodes.md` - PWS-specific node details

## Property Type Reference

Common property types:
- `String` - Text values
- `Long` - Integer numbers
- `Double` - Decimal numbers
- `Boolean` - true/false
- `FloatArray` - Embedding vectors (1536-dim)
- `StringArray` - Lists of strings
- `DateTime` - Timestamps
- `Date` - Date only
