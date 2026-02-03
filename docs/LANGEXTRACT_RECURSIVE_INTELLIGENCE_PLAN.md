# LangExtract Recursive Intelligence Implementation Plan

*Mindrian Swarm Team Analysis - February 2026*

---

## Executive Summary

The Mindrian swarm team analyzed three critical areas for implementing LangExtract as the engine for graph learning:

| Area | Current State | Gap Assessment |
|------|---------------|----------------|
| **LangExtract** | 60% infrastructure, 20% integration, 0% schema enforcement | Exists but unused in main chat flow |
| **Neo4j Integration** | Single-hop CO_OCCURS only, no chunk text retrieval | Missing KG²RAG bridge, entity resolution primitive |
| **Session Storage** | Conversations persist, A2A tables ready | No session.ended hook, no recursive pipeline |

**Critical Finding:** The code for nearly every required function exists, but **integration is missing**. LangExtract, opportunity bank, GraphRAG, and A2A orchestration are all built but disconnected.

---

## Architecture Vision

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        SESSION LIFECYCLE                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  REAL-TIME (During Session)                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐               │
│  │ Instant      │───►│ Background   │───►│ Phase        │               │
│  │ Extract      │    │ Intelligence │    │ Insights     │               │
│  │ (<5ms)       │    │ (async)      │    │ (UI)         │               │
│  └──────────────┘    └──────────────┘    └──────────────┘               │
│                                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  POST-SESSION (After Session Ends)                                       │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐               │
│  │ Session      │───►│ LangExtract  │───►│ Entity       │               │
│  │ Ended Hook   │    │ Schema       │    │ Resolution   │               │
│  │              │    │ Extraction   │    │ (Neo4j)      │               │
│  └──────────────┘    └──────────────┘    └──────────────┘               │
│         │                   │                   │                        │
│         ▼                   ▼                   ▼                        │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐               │
│  │ a2a_sessions │    │ session_     │    │ Neo4j        │               │
│  │ (Supabase)   │    │ insights     │    │ Graph        │               │
│  │              │    │ (staging)    │    │ Updates      │               │
│  └──────────────┘    └──────────────┘    └──────────────┘               │
│                             │                                            │
│                             ▼                                            │
│                      ┌──────────────┐                                    │
│                      │ Auto-Ingest  │◄── 3+ sessions, high confidence    │
│                      │ vs. Human    │◄── novel relationships             │
│                      │ Review       │                                    │
│                      └──────────────┘                                    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Tier 1: Foundation (Week 1-2)

### 1.1 Session Ended Hook

**Status:** ❌ MISSING - Critical gap

**Implementation:**

```python
# mindrian_chat.py - Add after @cl.on_stop

@cl.on_chat_end
async def on_chat_end():
    """Trigger recursive intelligence pipeline when session ends."""
    session_id = cl.user_session.get("id")
    user = cl.user_session.get("user")
    bot_id = cl.user_session.get("current_bot_id", "lawrence")

    # Get full history
    history = cl.user_session.get("history", [])
    if len(history) < 3:
        return  # Skip trivial sessions

    # Queue for background processing
    await queue_session_extraction(
        session_id=session_id,
        user_id=user.identifier if user else "anonymous",
        bot_id=bot_id,
        history=history,
        phases=cl.user_session.get("phases", []),
        current_phase=cl.user_session.get("current_phase", 0),
    )
```

**Files to modify:**
- `mindrian_chat.py` - Add `@cl.on_chat_end` handler
- `tools/langextract.py` - Add `queue_session_extraction()` function

### 1.2 Unified Extraction Schema (Pydantic)

**Status:** ❌ MISSING - Currently no schema enforcement

**New file:** `tools/extraction_schemas.py`

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime

class SourcePosition(BaseModel):
    start: int
    end: int
    turn: int

class ExtractedEntity(BaseModel):
    type: Literal["Framework", "Concept", "Problem", "Technique", "Person", "Tool"]
    name: str
    source: SourcePosition
    confidence: float = Field(ge=0.0, le=1.0)
    aliases: List[str] = []

class ExtractedRelationship(BaseModel):
    from_entity: str
    to_entity: str
    type: Literal[
        "COMPLEMENTS", "CONTRADICTS", "PRECEDES", "REPLACED_BY",
        "REFRAMES_TO", "REVEALS", "FAILED_ON", "CO_OCCURS"
    ]
    context: str
    source: SourcePosition
    confidence: float = Field(ge=0.0, le=1.0)

class SessionExtraction(BaseModel):
    session_id: str
    user_id: str
    bot_id: str
    extracted_at: datetime
    entities: List[ExtractedEntity]
    relationships: List[ExtractedRelationship]
    dead_ends: List[dict] = []
    quality_metrics: dict = {}
```

### 1.3 Connect LangExtract to Main Chat

**Status:** 🟡 Code exists but unused

**Changes needed in `mindrian_chat.py`:**

```python
# At top of file, add import
from tools.langextract import instant_extract, background_extract_pws

# In @cl.on_message handler, after response is sent:
async def on_message(message: cl.Message):
    # ... existing response generation ...

    # After response sent, trigger background extraction
    history = cl.user_session.get("history", [])
    if len(history) % 5 == 0:  # Every 5 turns
        asyncio.create_task(
            background_intelligence(
                history=history,
                session_id=session_id,
                bot_id=bot_id
            )
        )
```

---

## Tier 2: Entity Resolution (Week 2-3)

### 2.1 Fuzzy Entity Matching

**Status:** ❌ MISSING - Currently exact match + hardcoded aliases only

**New file:** `tools/entity_resolver.py`

```python
from rapidfuzz import fuzz
from typing import Optional, Dict, List

ENTITY_ALIASES = {
    "jobs to be done": ["jtbd", "jobs-to-be-done", "job to be done"],
    "ackoff systems thinking": ["ackoff", "systems thinking", "ackoff's approach"],
    # ... 60+ aliases from current FRAMEWORK_ALIASES
}

async def resolve_entity(
    name: str,
    entity_type: str,
    neo4j_driver,
    threshold: float = 0.85
) -> Optional[Dict]:
    """
    Resolve entity name to canonical Neo4j node.

    Resolution order:
    1. Exact match (case-insensitive)
    2. Alias match
    3. Fuzzy match (Levenshtein > threshold)
    4. Embedding similarity (if enabled)
    """
    normalized = name.lower().strip()

    # 1. Exact match
    result = await query_neo4j_exact(neo4j_driver, normalized, entity_type)
    if result:
        return {"match": result, "method": "exact", "confidence": 1.0}

    # 2. Alias match
    for canonical, aliases in ENTITY_ALIASES.items():
        if normalized in aliases:
            result = await query_neo4j_exact(neo4j_driver, canonical, entity_type)
            if result:
                return {"match": result, "method": "alias", "confidence": 0.95}

    # 3. Fuzzy match
    candidates = await query_neo4j_candidates(neo4j_driver, entity_type, limit=50)
    best_match = None
    best_score = 0
    for candidate in candidates:
        score = fuzz.ratio(normalized, candidate["name"].lower()) / 100
        if score > best_score and score >= threshold:
            best_score = score
            best_match = candidate

    if best_match:
        return {"match": best_match, "method": "fuzzy", "confidence": best_score}

    # 4. Not found - flag for review
    return None
```

### 2.2 Neo4j Entity Resolution Index

**Cypher setup:**

```cypher
-- Create fulltext index for entity names
CREATE FULLTEXT INDEX entity_name_fulltext IF NOT EXISTS
FOR (n:Framework|Concept|Problem|Technique|Tool|Person)
ON EACH [n.name]
OPTIONS {
  indexConfig: {
    `fulltext.analyzer`: 'english',
    `fulltext.eventually_consistent`: true
  }
};

-- Query pattern for fuzzy search
CALL db.index.fulltext.queryNodes("entity_name_fulltext", $search_term)
YIELD node, score
WHERE score > 0.5
RETURN node.name, labels(node), score
ORDER BY score DESC
LIMIT 10
```

---

## Tier 3: KG²RAG Bridge (Week 3-4)

### 3.1 Chunk → Entity Links

**Status:** ❌ MISSING - MENTIONED_IN exists but not utilized for retrieval

**Enhancement to `tools/graphrag_lite.py`:**

```python
async def get_chunk_text_for_concept(
    concept_name: str,
    limit: int = 5
) -> List[Dict]:
    """
    Retrieve actual chunk text for a concept.
    KG²RAG pattern: Concept → MENTIONED_IN → Chunk → text from Supabase
    """
    driver = _get_neo4j()

    # Get chunk IDs from Neo4j
    with driver.session() as session:
        result = session.run("""
            MATCH (c:LazyGraphConcept {name: $name})-[r:MENTIONED_IN]->(ch:Chunk)
            RETURN ch.chunk_id as chunk_id, r.source_position as position
            ORDER BY r.frequency DESC
            LIMIT $limit
        """, name=concept_name, limit=limit)

        chunk_ids = [record["chunk_id"] for record in result]

    # Fetch text from Supabase
    texts = []
    for chunk_id in chunk_ids:
        response = supabase.table("knowledge_base").select("content").eq("id", chunk_id).single().execute()
        if response.data:
            texts.append({
                "chunk_id": chunk_id,
                "text": response.data["content"],
                "concept": concept_name
            })

    return texts
```

### 3.2 Multi-Hop Retrieval

**New function in `tools/graphrag_lite.py`:**

```python
async def multi_hop_retrieval(
    query: str,
    max_hops: int = 2,
    top_k: int = 10
) -> Dict:
    """
    KG²RAG: Query → Concepts → Related Concepts → Chunks

    Returns concepts AND their supporting chunk text.
    """
    driver = _get_neo4j()

    # Step 1: Find seed concepts matching query
    seed_concepts = await lazy_multi_concept_context(query, limit=5)

    # Step 2: Expand via CO_OCCURS (1-hop neighbors)
    expanded = set()
    for concept in seed_concepts:
        with driver.session() as session:
            result = session.run("""
                MATCH (c:LazyGraphConcept {name: $name})-[r:CO_OCCURS]-(neighbor)
                WHERE r.weight > 0.3
                RETURN neighbor.name as name, r.weight as weight
                ORDER BY r.weight DESC
                LIMIT 10
            """, name=concept["name"])

            for record in result:
                expanded.add(record["name"])

    # Step 3: Retrieve chunk text for top concepts
    all_concepts = seed_concepts + [{"name": n} for n in expanded]
    chunks = []
    for concept in all_concepts[:top_k]:
        concept_chunks = await get_chunk_text_for_concept(concept["name"], limit=2)
        chunks.extend(concept_chunks)

    return {
        "concepts": all_concepts[:top_k],
        "chunks": chunks,
        "query": query
    }
```

### 3.3 Relationship Metadata Schema

**Cypher migrations:**

```cypher
-- Add metadata to CO_OCCURS relationships
MATCH ()-[r:CO_OCCURS]-()
WHERE r.usage_weight IS NULL
SET r.usage_weight = r.weight,
    r.session_count = 0,
    r.discovery_type = null,
    r.last_context = null,
    r.added_by = "legacy";

-- New relationship update pattern (for session extractions)
MERGE (a:LazyGraphConcept {name: $from})-[r:CO_OCCURS]-(b:LazyGraphConcept {name: $to})
ON CREATE SET
    r.weight = $weight,
    r.usage_weight = $usage_weight,
    r.session_count = 1,
    r.discovery_type = $rel_type,
    r.last_context = $context,
    r.added_by = "langextract-recursive",
    r.created_at = datetime()
ON MATCH SET
    r.session_count = r.session_count + 1,
    r.usage_weight = r.usage_weight + 0.05,
    r.discovery_type = COALESCE($rel_type, r.discovery_type),
    r.last_context = $context,
    r.updated_at = datetime()
```

---

## Tier 4: Session Extraction Pipeline (Week 4-5)

### 4.1 Schema-Enforced LangExtract

**Enhancement to `tools/langextract.py`:**

```python
from tools.extraction_schemas import SessionExtraction, ExtractedEntity, ExtractedRelationship

EXTRACTION_PROMPT = """
Extract frameworks, concepts, techniques, and relationships discovered during this
innovation coaching session. Use ONLY these entity types:
- Framework: Named methodologies (JTBD, TTA, Six Thinking Hats, etc.)
- Concept: Abstract ideas discussed (system boundaries, job context, etc.)
- Problem: Specific problems identified
- Technique: Methods or approaches used
- Person: Named individuals mentioned
- Tool: Specific tools referenced

Use ONLY these relationship types:
- COMPLEMENTS: Two frameworks enhance each other
- CONTRADICTS: Frameworks give conflicting guidance
- PRECEDES: One framework works best before another
- REPLACED_BY: One framework replaced another mid-session
- REFRAMES_TO: A concept is reframed as another
- REVEALS: A technique reveals a specific insight
- FAILED_ON: A framework consistently fails for a problem type
- CO_OCCURS: General co-occurrence (default)

For each entity and relationship, provide source positions (character offsets in text).
"""

async def extract_session_structured(
    transcript: str,
    session_id: str,
    user_id: str,
    bot_id: str
) -> SessionExtraction:
    """
    Schema-enforced extraction with source grounding.
    Returns Pydantic-validated SessionExtraction.
    """
    model = genai.GenerativeModel("gemini-2.5-flash")

    response = await model.generate_content_async(
        EXTRACTION_PROMPT + "\n\nTranscript:\n" + transcript,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema=SessionExtraction.model_json_schema()
        )
    )

    # Validate with Pydantic
    extraction = SessionExtraction.model_validate_json(response.text)
    extraction.session_id = session_id
    extraction.user_id = user_id
    extraction.bot_id = bot_id
    extraction.extracted_at = datetime.utcnow()

    return extraction
```

### 4.2 Session Insights Staging Table

**Supabase migration:**

```sql
CREATE TABLE session_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id TEXT NOT NULL,
    user_id TEXT,
    bot_id TEXT,
    extracted_at TIMESTAMPTZ DEFAULT NOW(),

    -- Entities (JSON array)
    entities JSONB NOT NULL DEFAULT '[]',

    -- Relationships (JSON array)
    relationships JSONB NOT NULL DEFAULT '[]',

    -- Resolution status
    entities_resolved INTEGER DEFAULT 0,
    entities_unresolved INTEGER DEFAULT 0,

    -- Review status
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'auto_ingested', 'human_reviewed', 'rejected')),
    reviewed_by TEXT,
    reviewed_at TIMESTAMPTZ,

    -- Quality metrics
    extraction_confidence FLOAT,
    entity_resolution_rate FLOAT,

    CONSTRAINT fk_session FOREIGN KEY (session_id) REFERENCES a2a_sessions(session_id)
);

CREATE INDEX idx_session_insights_status ON session_insights(status);
CREATE INDEX idx_session_insights_session ON session_insights(session_id);
```

### 4.3 Auto-Ingest vs Human Review Logic

**New file:** `tools/insight_ingestor.py`

```python
async def process_session_extraction(extraction: SessionExtraction) -> Dict:
    """
    Process extracted session data:
    1. Resolve entities against Neo4j
    2. Route to auto-ingest or human review
    3. Update Neo4j relationships
    """
    resolved = []
    unresolved = []

    # Entity resolution
    for entity in extraction.entities:
        match = await resolve_entity(
            name=entity.name,
            entity_type=entity.type,
            neo4j_driver=get_neo4j_driver()
        )
        if match:
            resolved.append({**entity.model_dump(), "neo4j_match": match})
        else:
            unresolved.append(entity.model_dump())

    # Determine routing
    resolution_rate = len(resolved) / len(extraction.entities) if extraction.entities else 1.0

    # Auto-ingest criteria:
    # - All entities resolved
    # - Session has 3+ prior sessions with similar patterns
    # - High confidence extraction
    can_auto_ingest = (
        resolution_rate == 1.0 and
        extraction.extraction_confidence >= 0.8 and
        await check_pattern_frequency(extraction.relationships) >= 3
    )

    if can_auto_ingest:
        await auto_ingest_to_neo4j(resolved, extraction.relationships)
        status = "auto_ingested"
    else:
        status = "pending"  # Human review required

    # Store in staging table
    await store_session_insight(
        extraction=extraction,
        resolved=resolved,
        unresolved=unresolved,
        status=status,
        resolution_rate=resolution_rate
    )

    return {
        "status": status,
        "resolved_count": len(resolved),
        "unresolved_count": len(unresolved),
        "resolution_rate": resolution_rate
    }
```

---

## Tier 5: Dead End Detection (Week 5-6)

### 5.1 Abandonment Signal Extraction

**Enhancement to `tools/langextract.py`:**

```python
DEADEND_PROMPT = """
Identify moments where an approach or framework was abandoned during this session.
Look for:
- Direction changes ("let's try a different approach")
- Expressions of frustration ("this keeps circling back")
- Explicit redirection ("instead, let's look at...")
- Framework switching mid-analysis

For each dead end, identify:
- what_was_tried: Framework or approach that stalled
- replaced_by: What was used instead (if any)
- context: Why it seemed to fail
- turn: Which turn this occurred
"""

async def extract_dead_ends(transcript: str) -> List[Dict]:
    """
    Detect abandoned approaches for routing evolution.
    """
    model = genai.GenerativeModel("gemini-2.5-flash")

    response = await model.generate_content_async(
        DEADEND_PROMPT + "\n\nTranscript:\n" + transcript,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json"
        )
    )

    dead_ends = json.loads(response.text)

    # Create REPLACED_BY relationships
    for de in dead_ends:
        if de.get("replaced_by"):
            await update_effectiveness_table(
                framework=de["what_was_tried"],
                outcome="abandoned",
                replaced_by=de["replaced_by"],
                context=de["context"]
            )

    return dead_ends
```

### 5.2 Effectiveness Table

**Supabase table:**

```sql
CREATE TABLE framework_effectiveness (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    framework TEXT NOT NULL,
    problem_type TEXT,
    outcome TEXT CHECK (outcome IN ('successful', 'abandoned', 'partial')),
    replaced_by TEXT,
    context TEXT,
    session_id TEXT,
    user_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Aggregation helpers
    success_count INTEGER DEFAULT 0,
    abandon_count INTEGER DEFAULT 0,
    effectiveness_score FLOAT GENERATED ALWAYS AS (
        CASE WHEN success_count + abandon_count > 0
        THEN success_count::float / (success_count + abandon_count)
        ELSE 0.5 END
    ) STORED
);

CREATE INDEX idx_effectiveness_framework ON framework_effectiveness(framework);
CREATE INDEX idx_effectiveness_problem ON framework_effectiveness(problem_type);
```

---

## Tier 6: Chunk ETL Pipeline (Week 6-7)

### 6.1 One-Time Knowledge Base Processing

**New script:** `scripts/chunk_entity_etl.py`

```python
"""
One-time ETL: Process existing knowledge_base chunks to create MENTIONS relationships.
Estimated: ~10K chunks, ~$10 total, ~2-3 hours runtime.
"""

import asyncio
from supabase import create_client
from tools.langextract import extract_entities_from_chunk
from tools.entity_resolver import resolve_entity

BATCH_SIZE = 50

async def process_knowledge_base():
    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
    neo4j_driver = get_neo4j_driver()

    # Get total count
    count_response = supabase.table("knowledge_base").select("id", count="exact").execute()
    total = count_response.count
    print(f"Processing {total} chunks...")

    processed = 0
    offset = 0

    while offset < total:
        # Fetch batch
        response = supabase.table("knowledge_base") \
            .select("id, content") \
            .range(offset, offset + BATCH_SIZE - 1) \
            .execute()

        chunks = response.data

        for chunk in chunks:
            try:
                # Extract entities
                entities = await extract_entities_from_chunk(chunk["content"])

                # Create MENTIONS relationships
                for entity in entities:
                    match = await resolve_entity(
                        name=entity["name"],
                        entity_type=entity["type"],
                        neo4j_driver=neo4j_driver
                    )

                    if match:
                        await create_mentions_relationship(
                            chunk_id=chunk["id"],
                            entity_name=match["match"]["name"],
                            source_position=entity.get("source_position"),
                            neo4j_driver=neo4j_driver
                        )

                processed += 1
                if processed % 100 == 0:
                    print(f"Processed {processed}/{total} chunks")

            except Exception as e:
                print(f"Error processing chunk {chunk['id']}: {e}")

        offset += BATCH_SIZE
        await asyncio.sleep(0.5)  # Rate limiting

    print(f"ETL complete. Processed {processed} chunks.")

async def create_mentions_relationship(chunk_id, entity_name, source_position, neo4j_driver):
    with neo4j_driver.session() as session:
        session.run("""
            MERGE (c:Chunk {chunk_id: $chunk_id})
            MERGE (e {name: $entity_name})
            MERGE (c)-[r:MENTIONS]->(e)
            SET r.source_position = $source_pos,
                r.added_by = "chunk-etl",
                r.created_at = datetime()
        """, chunk_id=chunk_id, entity_name=entity_name, source_pos=source_position)
```

---

## Implementation Timeline

| Week | Tier | Deliverables |
|------|------|-------------|
| 1-2 | Tier 1: Foundation | Session ended hook, Pydantic schemas, LangExtract integration |
| 2-3 | Tier 2: Entity Resolution | Fuzzy matching, Neo4j fulltext index, resolver module |
| 3-4 | Tier 3: KG²RAG Bridge | Chunk text retrieval, multi-hop queries, relationship metadata |
| 4-5 | Tier 4: Extraction Pipeline | Schema-enforced extraction, staging table, auto-ingest logic |
| 5-6 | Tier 5: Dead End Detection | Abandonment signals, effectiveness table, routing evolution |
| 6-7 | Tier 6: Chunk ETL | One-time knowledge base processing, incremental updates |

---

## Cost Estimates

| Operation | Per Unit | Volume | Monthly Cost |
|-----------|----------|--------|--------------|
| Session extraction | $0.001 | 1,000 sessions | $1.00 |
| Chunk ETL (one-time) | $0.001 | 10,000 chunks | $10.00 |
| Incremental chunks | $0.001 | 200/month | $0.20 |
| Entity resolution (Neo4j) | $0.00 | — | $0.00 |
| **Total monthly** | — | — | **~$1.20** |

---

## Success Metrics

| Metric | Baseline | Target |
|--------|----------|--------|
| Entity resolution rate | 0% (no extraction) | >90% |
| Auto-ingest rate | 0% | >70% |
| Session → Graph latency | N/A | <30 seconds |
| Chunk coverage (MENTIONS) | 0% | 100% |
| Relationship types discovered | 2 (CO_OCCURS, MENTIONED_IN) | 8+ |
| Dead end detection accuracy | N/A | >80% |

---

## Files to Create/Modify

### New Files
- `tools/extraction_schemas.py` - Pydantic schemas
- `tools/entity_resolver.py` - Fuzzy entity matching
- `tools/insight_ingestor.py` - Auto-ingest logic
- `scripts/chunk_entity_etl.py` - One-time ETL
- `migrations/session_insights.sql` - Staging table
- `migrations/framework_effectiveness.sql` - Dead end tracking

### Modify Existing
- `mindrian_chat.py` - Add `@cl.on_chat_end` hook
- `tools/langextract.py` - Schema-enforced extraction
- `tools/graphrag_lite.py` - Multi-hop retrieval, chunk text
- `protocols/supabase_storage.py` - New tables

---

## Dependencies

```txt
# Add to requirements.txt
rapidfuzz>=3.0.0  # Fuzzy string matching
pydantic>=2.0.0   # Schema validation (likely already present)
```

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| LLM extraction hallucinations | Schema enforcement + source grounding |
| Entity resolution errors | Human review for unresolved entities |
| Neo4j memory pressure | Batch processing, bounded queries |
| Supabase rate limits | Exponential backoff, batch writes |
| Cost overruns | Monitor extraction volume, cap at 2000/month |

---

## Next Steps

1. **Immediate:** Review this plan with Jonathan
2. **Week 1:** Implement Tier 1 (session hook + schemas)
3. **Week 2:** Test end-to-end with 10 sample sessions
4. **Week 3:** Scale to full integration

---

*Generated by Mindrian Swarm Team - February 2026*
