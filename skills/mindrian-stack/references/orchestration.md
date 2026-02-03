# Tool Orchestration Reference

## Table of Contents
1. [Orchestration Principles](#orchestration-principles)
2. [Decision Matrix](#decision-matrix)
3. [Workflow Patterns](#workflow-patterns)
4. [Failure Handling](#failure-handling)
5. [Performance Optimization](#performance-optimization)

---

## Orchestration Principles

Claude AI acts as the **orchestrator**, deciding WHEN and HOW to use each component.

### Core Principle
> Each component handles what it does best. Claude routes intelligently between them.

### Component Responsibilities

| Component | Best For | Avoid For |
|-----------|----------|-----------|
| **Neo4j** | Relationships, traversal, frameworks | Simple lookups, full-text search |
| **Supabase** | Vector search, persistence, transactions | Graph queries, reasoning |
| **Claude** | Reasoning, synthesis, decisions | Data storage, search |
| **Memory** | User context, continuity | Transient data |
| **Edge** | Real-time, async, orchestration | Heavy computation |

---

## Decision Matrix

### Query Type → Component Selection

| Query Characteristic | Primary Component | Secondary |
|---------------------|-------------------|-----------|
| "How does X relate to Y?" | Neo4j | Claude |
| "Find similar to X" | Supabase (vector) | Neo4j |
| "What should I do about X?" | Claude | Neo4j + Supabase |
| "Remember that I prefer X" | Memory | Supabase |
| "Apply framework X to Y" | Neo4j → Claude | Supabase |
| "Search for X in documents" | Supabase | Neo4j |

### Complexity-Based Routing

```
Simple Query (single-hop)
├── Keyword match → Supabase full-text
├── Semantic match → Supabase vector
└── Direct lookup → Supabase SQL

Complex Query (multi-hop)
├── Relationship discovery → Neo4j
├── Framework matching → Neo4j → Claude
└── Multi-source synthesis → All components

Reasoning Query
├── Analysis needed → Claude primary
├── With context → Memory + Claude
└── With knowledge → Supabase/Neo4j → Claude
```

---

## Workflow Patterns

### Pattern 1: RAG with Graph Enhancement (Lazy Graph RAG)

```
User Query
    │
    ▼
┌─────────────────┐
│ Generate        │
│ Embedding       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Supabase        │  Vector similarity search
│ Vector Search   │  Returns: candidate chunks
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Neo4j Graph     │  Expand with relationships
│ Expansion       │  Returns: related concepts
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Claude          │  Synthesize and respond
│ Synthesis       │  
└─────────────────┘
```

### Pattern 2: Framework Application

```
Problem Statement
    │
    ▼
┌─────────────────┐
│ Cynefin         │  Classify complexity
│ Classification  │  (Neo4j query)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Framework       │  Find applicable frameworks
│ Matching        │  (Neo4j: APPLIES_TO)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Framework       │  Get framework details
│ Retrieval       │  (Supabase + Neo4j)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Claude          │  Apply framework to problem
│ Application     │  Generate structured response
└─────────────────┘
```

### Pattern 3: Personalized Response

```
User Query
    │
    ├───────────────────┐
    ▼                   ▼
┌─────────────┐   ┌─────────────┐
│ Memory      │   │ Knowledge   │
│ Retrieval   │   │ Retrieval   │
└──────┬──────┘   └──────┬──────┘
       │                 │
       └────────┬────────┘
                │
                ▼
        ┌───────────────┐
        │ Context       │
        │ Assembly      │
        └───────┬───────┘
                │
                ▼
        ┌───────────────┐
        │ Claude        │  Personalized response
        │ Generation    │  based on user prefs
        └───────────────┘
```

### Pattern 4: Intelligent Workflow Execution

```
Task Request
    │
    ▼
┌─────────────────┐
│ Claude          │  Analyze task, plan steps
│ Planning        │  
└────────┬────────┘
         │
         ▼
    ┌────┴────┐
    │ For each │
    │   step   │
    └────┬────┘
         │
         ▼
┌─────────────────┐
│ Tool Selection  │  Choose appropriate tool
│ (Claude)        │  
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Tool Execution  │  Execute via Edge Function
│ (Edge)          │  
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Result          │  Evaluate, adapt if needed
│ Evaluation      │  
└────────┬────────┘
         │
         ▼
    Next step or complete
```

---

## Failure Handling

### Graceful Degradation

| Component Failed | Fallback Strategy |
|-----------------|-------------------|
| Neo4j down | Vector-only search (Supabase) |
| Supabase down | In-memory cache + Claude reasoning |
| Memory unavailable | Fresh context, no personalization |
| Edge timeout | Synchronous fallback |
| Claude overloaded | Queue + retry |

### Fallback Implementation

```typescript
async function resilientQuery(query: string) {
  try {
    // Primary: Full pipeline
    return await fullPipeline(query)
  } catch (error) {
    if (error.source === 'neo4j') {
      // Fallback: Vector-only
      console.warn('Neo4j unavailable, using vector-only')
      return await vectorOnlyPipeline(query)
    }
    if (error.source === 'supabase') {
      // Fallback: Claude reasoning only
      console.warn('Supabase unavailable, using Claude only')
      return await claudeOnlyPipeline(query)
    }
    throw error
  }
}
```

---

## Performance Optimization

### Parallel vs Sequential

```typescript
// GOOD: Parallel independent operations
async function optimizedPipeline(query: string, userId: string) {
  // These don't depend on each other
  const [embedding, userContext, sessionContext] = await Promise.all([
    generateEmbedding(query),
    getUserPreferences(userId),
    getSessionSummary(userId)
  ])
  
  // These depend on embedding
  const [vectorResults, graphResults] = await Promise.all([
    vectorSearch(embedding),
    graphSearch(query)  // Can run in parallel with vector
  ])
  
  // This depends on all above
  return await generateResponse({
    query, embedding, userContext, sessionContext,
    vectorResults, graphResults
  })
}
```

### Caching Strategy

| Data Type | Cache TTL | Cache Location |
|-----------|-----------|----------------|
| User preferences | 5 minutes | Edge memory |
| Framework definitions | 1 hour | Edge memory |
| Vector search results | 30 seconds | Request-scoped |
| Graph traversal | 1 minute | Edge memory |
| Embeddings | 24 hours | Supabase |

### Query Optimization

```typescript
// Batch multiple lookups
const results = await Promise.all(
  ids.map(id => lookup(id))  // Bad: N queries
)

// Better: Single batch query
const results = await batchLookup(ids)  // Good: 1 query
```

---

## Best Practices

1. **Route intelligently** - Match query type to component strength
2. **Parallelize aggressively** - Independent operations should be parallel
3. **Fail gracefully** - Always have a fallback path
4. **Cache strategically** - Cache stable data, not volatile
5. **Monitor latency** - Track component response times
6. **Batch when possible** - Reduce round trips
