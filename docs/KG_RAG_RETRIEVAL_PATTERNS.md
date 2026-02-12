# Retrieval Patterns for KG-RAG

## Pattern 1: Vector-First with Graph Expansion

The most common hybrid retrieval pattern. Start with vector similarity, then expand using graph structure.

### Flow
```
1. Embed user question
2. Run vector similarity search on graph node embeddings
3. For top-K results, execute expansion query
4. Merge and deduplicate expanded context
5. Pass to LLM with source attribution
```

### Neo4j Implementation
```cypher
CALL db.index.vector.queryNodes('chunk_embeddings', $topK, $queryEmbedding)
YIELD node AS hit, score

MATCH (hit)<-[:CONTAINS]-(parent)
OPTIONAL MATCH (parent)-[:CONTAINS]->(sibling)
OPTIONAL MATCH (hit)-[:REFERENCES]->(ref)
WITH hit, score, parent,
     collect(DISTINCT sibling) AS siblings,
     collect(DISTINCT ref) AS references

RETURN hit.text AS primary_text,
       score AS similarity_score,
       parent.title AS parent_context,
       [s IN siblings | s.text] AS sibling_texts,
       [r IN references | r.text] AS reference_texts
ORDER BY score DESC
```

---

## Pattern 2: Text-to-Cypher (Structured Query Generation)

For analytical questions (aggregations, counts, filters). LLM generates Cypher from natural language.

---

## Pattern 3: Agent-Based Multi-Strategy Retrieval

Agent selects best retrieval strategy per question: semantic search vs structured query vs hybrid.

---

## Pattern 4: Definition-Aware Retrieval

Handles the "definition problem" in legal/contract/PWS documents. Extracts defined terms from retrieved text and resolves them via graph lookup.

---

## Pattern 5: Proximity-Based Expansion

Generic N-hop expansion from vector search hits using `apoc.path.subgraphNodes`.

---

## Context Engineering Principles

1. **Context Window as Programmable Memory** - Curate the most relevant graph context dynamically
2. **Layered Context Assembly** - Priority-based layers with budget enforcement
3. **Dynamic Context Selection** - Different depth for different query intents
4. **Session-Aware Deduplication** - Don't repeat context already discussed
5. **Invisible Methodology Injection** - Domain frameworks injected naturally

### Anti-Patterns

| Anti-Pattern | Better Approach |
|-------------|-----------------|
| Dump everything into context | Budget-aware layered assembly |
| Same retrieval for all queries | Dynamic strategy selection |
| Announcing retrieval sources | Invisible integration |
| Ignoring conversation history | Session-aware deduplication |
| Static chunk sizes | Graph-aware chunking |

## Common Pitfalls

1. **Over-expansion:** Too many hops dilutes context quality. Start with 1-2 hops.
2. **Missing deduplication:** Graph expansion can return same content via different paths.
3. **Ignoring relationship types:** Not all relationships are equally relevant.
4. **No access control:** Graph expansion can leak across permission boundaries.
5. **Embedding everything:** Not all node properties need vectorization. Be selective.
6. **Skipping validation:** Always validate LLM-generated Cypher before execution.
