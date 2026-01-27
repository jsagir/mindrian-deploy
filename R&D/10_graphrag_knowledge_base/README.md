# GraphRAG Knowledge Base — Reference Hub

Everything needed to understand, maintain, and extend the Mindrian Neo4j knowledge graph.

---

## Contents

| File | Purpose |
|------|---------|
| `neo4j-graph-writer.skill.md` | Claude skill: WHAT/WHY/HOW protocol for adding to the graph |
| `neo4j_schema_post_cleanup.json` | Current graph schema with counts, layers, relationships |
| `GRAPH_LAYERS.md` | Visual guide to the 5 graph layers |
| `REVERSE_SALIENT_SPEC.md` | Spec for cross-intersectional innovation discovery (next phase) |

## Related Files (in main repo)

| File | Purpose |
|------|---------|
| `tools/graphrag_lite.py` | Runtime retrieval — bounded cache, circuit breaker, traceability |
| `tools/pws_brain.py` | Gemini File Search integration |
| `tools/neo4j_framework_discovery.py` | Neo4j query utilities |
| `scripts/lazy_graphrag_index.py` | LazyGraphRAG indexing pipeline (spaCy + Louvain) |
| `scripts/neo4j_schema_post_cleanup.json` | Canonical schema (source of truth) |
| `R&D/09_graphrag_lite/README.md` | GraphRAG Lite design philosophy and architecture |

## Quick Links

- **Schema JSON:** `scripts/neo4j_schema_post_cleanup.json`
- **Skill file:** `R&D/10_graphrag_knowledge_base/neo4j-graph-writer.skill.md`
- **Runtime code:** `tools/graphrag_lite.py`

## Graph Stats (2026-01-27)

- ~20,230 nodes across 5 layers
- ~166,250 edges
- 7,922 LazyGraphConcepts in 39 communities
- 233 ReverseSalient nodes (key for next phase)
- 56 InnovationOpportunity nodes
- 85 Domain nodes

## Next Phase: Reverse Salient Cross-Intersectional Discovery

See `REVERSE_SALIENT_SPEC.md` for the planned approach using:
- ReverseSalient nodes (233) as bottleneck/gap identifiers
- Domain nodes (85) for cross-domain bridging
- CO_OCCURS communities for concept clustering
- SIMILAR/ALTERNATIVE_TO/COMPLEMENTS for framework relationships
