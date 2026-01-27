# Neo4j Graph Layers

The Mindrian knowledge graph has 5 distinct layers:

```
┌─────────────────────────────────────────────┐
│           STRUCTURAL LAYER                   │
│  Product, Event, Domain, Organization        │
│  ReverseSalient, InnovationOpportunity       │
│  BeautifulQuestion, Problem, StrategicResponse│
│  SIMILAR, PART_OF, LEADS_TO, ENABLES         │
├─────────────────────────────────────────────┤
│           MEANING LAYER                      │
│  __Entity__, Concept, Framework, Person      │
│  ProcessStep, DictionaryTerm, Technique      │
│  ProblemType, Book, CaseStudy, CynefinDomain │
│  HAS_ENTITY, INTRODUCES_TERM, AUTHORED_BY   │
├─────────────────────────────────────────────┤
│           LAZY GRAPHRAG LAYER                │
│  LazyGraphConcept (7,922 nodes)              │
│  CO_OCCURS (132K edges), MENTIONED_IN (12K)  │
│  39 Louvain communities                      │
│  Zero LLM cost — spaCy NLP only             │
├─────────────────────────────────────────────┤
│           EVIDENCE LAYER                     │
│  Chunk (1,167), DocumentChunk, FrameworkChunk│
│  NEXT_CHUNK, FIRST_CHUNK                     │
│  Raw source content — the ground truth       │
├─────────────────────────────────────────────┤
│           INFRASTRUCTURE LAYER               │
│  Agent (54), Document (105), File (22)       │
│  MCPTool (31, orphaned after cleanup)        │
│  System metadata — not used in retrieval     │
└─────────────────────────────────────────────┘
```

## Layer Rules

| Layer | Who writes | When queried |
|-------|-----------|--------------|
| Evidence | Upload scripts only | Chunk-level grounding |
| Meaning | LightRAG extraction + manual | Concept/framework lookup |
| LazyGraphRAG | `lazy_graphrag_index.py` only | Community context, co-occurrence |
| Structural | Manual + LightRAG | Cross-domain discovery, relationships |
| Infrastructure | Setup scripts | Never (metadata only) |

## Key Indexes

| Index Name | Covers | Used By |
|------------|--------|---------|
| `entity_fulltext` | __Entity__, Person, Concept, Framework, Product, Organization | `graphrag_lite.py` entity search |
| `framework_ecosystem_search` | Framework, Method, Tool, Technique | `graphrag_lite.py` framework lookup |
| `lazy_concept_search` | LazyGraphConcept.name | `graphrag_lite.py` concept lookup |
| `lazy_concept_community` | LazyGraphConcept.community_id | Community context queries |
