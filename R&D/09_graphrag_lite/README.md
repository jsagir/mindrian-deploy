# GraphRAG Lite - Lightweight Knowledge Graph Retrieval

**Status:** Implemented
**Location:** `tools/graphrag_lite.py`
**Integration:** `mindrian_chat.py` (auto-enabled when Neo4j is configured)

---

## Overview

GraphRAG Lite combines **Gemini File Search** (vector/semantic) with **Neo4j** (graph/structural) for conversational AI that understands relationships between concepts.

### Design Philosophy

**For conversational coaching (Larry's style), less is more.**

| Heavy RAG | GraphRAG Lite |
|-----------|---------------|
| Always retrieves | Retrieves conditionally |
| Returns paragraphs | Returns hints |
| Dumps frameworks | Suggests connections |
| Makes Larry verbose | Keeps Larry conversational |

**Graph's real value:** Understanding relationships between concepts so Larry can ask better questions - not delivering lectures.

---

## Architecture

```
USER QUERY
    |
    v
[Should Retrieve?] --> NO --> Regular response
    |
    YES
    v
[Get Retrieval Type]
    |
    +-- "concept" --> get_concept_connections() --> Related concepts
    |
    +-- "framework" --> get_related_frameworks() --> Framework suggestions
    |
    +-- "problem" --> get_problem_context() --> Problem type + approaches
    |
    v
[Light Context Hint]
    |
    v
[Add to user message as invisible context]
    |
    v
Larry uses hint to ask better questions
```

---

## When GraphRAG Retrieves

### Explicit Knowledge Requests (Always)
- "What is JTBD?"
- "Explain the S-curve"
- "Tell me about Minto Pyramid"
- "Walk me through validation"

### Framework/Methodology Mentions (After 2+ turns)
- "Which framework should I use?"
- "Is there a tool for this?"
- "What approach works here?"

### Problem Situations
- "I'm struggling with customer interviews"
- "The problem is we don't know our market"

### Action Requests
- "What should I do next?"
- "Give me homework"

---

## What GraphRAG Does NOT Do

- First response to vague problems (Larry asks questions first)
- Simple conversational exchanges ("Thanks!", "That makes sense")
- When user hasn't asked about methodology yet

---

## Neo4j Indexes Used

| Index | Labels | Purpose |
|-------|--------|---------|
| `framework_ecosystem_search` | Framework, Method, Tool, Technique | Framework lookups |
| `entity_fulltext` | __Entity__, Person, Organization, Concept, Framework, Product | Broad entity search |

---

## Key Functions

### `enrich_for_larry(user_message, turn_count) -> Optional[str]`

Main entry point. Returns context hint or None.

```python
from tools.graphrag_lite import enrich_for_larry

hint = enrich_for_larry("What is JTBD?", turn_count=2)
# Returns: "Jobs to Be Done connects to: Milkshake Example, Customer Interviews, Progress"
```

### `should_retrieve(message, turn_count) -> bool`

Decides if retrieval would help this turn.

### `get_concept_connections(concept) -> Dict`

Gets a concept and its immediate graph neighbors.

```python
{
    "name": "Jobs to Be Done",
    "type": "Framework",
    "description": "Framework for understanding...",
    "connections": [
        {"relation": "HAS_COMPONENT", "name": "Milkshake Example", "type": "Concept"},
        {"relation": "REQUIRES", "name": "Customer Interviews", "type": "Tool"}
    ]
}
```

### `get_related_frameworks(topic, limit=3) -> List[Dict]`

Finds frameworks related to a topic.

### `get_problem_context(description) -> Dict`

Given a problem description, finds relevant problem types and approaches.

---

## Environment Variables

```bash
# Required for GraphRAG
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password
```

If Neo4j is not configured, GraphRAG gracefully disables itself.

---

## Integration in mindrian_chat.py

```python
# Auto-imported at top
try:
    from tools.graphrag_lite import enrich_for_larry
    GRAPHRAG_ENABLED = True
except ImportError:
    GRAPHRAG_ENABLED = False

# In @cl.on_message handler
if GRAPHRAG_ENABLED:
    hint = enrich_for_larry(message.content, turn_count)
    if hint:
        full_user_message += f"\n\n[GraphRAG context: {hint}]"
```

---

## Example Flow

**Turn 1:**
```
User: "I'm working on a healthcare startup"
GraphRAG: (no retrieval - first turn, vague problem)
Larry: "Interesting. But you've given me a solution. What's the problem?"
```

**Turn 3:**
```
User: "What framework should I use to understand customers?"
GraphRAG: Retrieves → "Relevant frameworks: Jobs to Be Done, Customer Discovery"
Larry: "There's a framework called Jobs to Be Done - basically asking what progress someone is trying to make. Have you talked to any doctors yet?"
```

---

## Testing

```bash
# Test Neo4j connection
python -c "from tools.graphrag_lite import get_concept_connections; print(get_concept_connections('JTBD'))"

# Test framework search
python -c "from tools.graphrag_lite import get_related_frameworks; print(get_related_frameworks('customer validation'))"
```

---

## Future Enhancements

1. **Cohere Reranking** - Re-rank graph results by relevance
2. **Context Expansion** - 2-hop graph walks for deeper connections
3. **Hybrid Fusion** - Combine FileSearch + Graph scores
4. **Caching** - Cache frequent queries for faster response

---

## Files

| File | Purpose |
|------|---------|
| `tools/graphrag_lite.py` | Core implementation |
| `tools/pws_brain.py` | Gemini File Search (vector search) |
| `tools/neo4j_framework_discovery.py` | Neo4j utilities |

---

**Built for conversational AI that asks better questions.**
