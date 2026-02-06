# Innovation Discovery Platform Patterns for Mindrian

**Created**: 2026-02-06
**Status**: Strategic Planning
**Priority**: High (Quick Wins) / Medium (Strategic)

## Overview

Analysis of how Innovation Discovery Platform (AGENTS.md) patterns can enhance Mindrian.

**Overall Alignment Score: 8.4/10**

## Quick Wins (Implemented)

- [x] LangGraph-style PWS state management (`utils/pws_state.py`)
- [x] Two-stage classification in on_message (`mindrian_chat.py` + `protocols/classifier.py`)
- [ ] Tier-weighted retrieval in graphrag_lite.py (Requires: tier metadata on documents)
- [ ] Red Team middleware in orchestrator.py (Requires: middleware pattern design)

## Key Patterns from AGENTS.md

### 1. Coordinator Agent Pattern
Routes queries to appropriate sub-agents based on intent classification.
- Mindrian has: `EntryPointRouter` + `run_router_workflow()`
- Gap: Explicit phase transition logging

### 2. Query Agent (Text-to-Cypher with Self-Correction)
3-iteration loop for Cypher generation with validation.
```python
for iteration in range(3):
    cypher = generate_cypher(query, iteration)
    results = execute_cypher(cypher)
    if validate_results(results, query):
        return results
    query = f"{query}\n\n[Previous attempt failed. Try different approach.]"
```
- Mindrian has: Pre-written Cypher with fallback
- Gap: Self-correction loop (adopt for Research Mode only)

### 3. Knowledge Graph Agent
Entity extraction with deduplication (cosine similarity > 0.85).
- Mindrian has: LazyGraphRAG, LangExtract
- Gap: Auto-populate Neo4j from sessions

### 4. Research Agent
Multi-query planning with citation extraction.
- Mindrian has: ResearchAgent with Tavily
- Gap: 3-query planning pattern

### 5. Data Pipeline Agent
Automated ETL with scheduling.
- Mindrian has: Manual upload scripts
- Gap: Large - requires new service

## Strategic Investments (3-6 Months)

1. **Self-Correcting Cypher** - 2 weeks, Research Mode only
2. **Data Pipeline Agent** - 1 month, requires scheduling
3. **Auto-populate Neo4j** - 3 weeks, leverage LangExtract
4. **Journey Mapping View** - 2 weeks, cross-cutting context

## Reference Documents

- `/R&D/10_agents_md_architecture/AGENTS_MD_FULL.md` - Full AGENTS.md content
- `/R&D/10_agents_md_architecture/MULTI_SKILL_REVIEW.md` - Detailed analysis
- `A2A_PRACTICAL_ARCHITECTURE.md` - Red Team middleware design
- `TRIPLE_MODE_ARCHITECTURE_SPEC.md` - Tier-weighted retrieval design

## Implementation Priority

| Week | Task | File |
|------|------|------|
| 1-2 | Tier-weighted retrieval | `tools/graphrag_lite.py` |
| 1-2 | Red Team middleware | `protocols/orchestrator.py` |
| 1-2 | Two-stage classification | `mindrian_chat.py` |
| 3-4 | Grounding prompts | `mindrian_chat.py` |
| 3-4 | Research 3-query planning | `agents/multi_agent_graph.py` |
