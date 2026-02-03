# Recursive Intelligence — Implementation Guide

*Aligned with Developer Brief + LangExtract Engine Specification*

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         RECURSIVE INTELLIGENCE LOOP                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   SESSION RUNTIME                                                            │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                     │
│   │ agent_switch│───►│ phase_      │───►│ reaction    │  ← Phase 1+2       │
│   │ events      │    │ completion  │    │ classifier  │    Event Logging    │
│   └──────┬──────┘    └──────┬──────┘    └──────┬──────┘                     │
│          │                  │                  │                             │
│          └──────────────────┼──────────────────┘                             │
│                             ▼                                                │
│                    ┌─────────────────┐                                       │
│                    │ session_events  │  Supabase                             │
│                    │ session_summaries│                                      │
│                    └────────┬────────┘                                       │
│                             │                                                │
├─────────────────────────────┼────────────────────────────────────────────────┤
│                             │                                                │
│   POST-SESSION              ▼                                                │
│                    ┌─────────────────┐                                       │
│                    │ Edge Function:  │  ← Phase 3                            │
│                    │ session-distill │    LangExtract Engine                 │
│                    └────────┬────────┘                                       │
│                             │                                                │
│          ┌──────────────────┼──────────────────┐                             │
│          ▼                  ▼                  ▼                             │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                     │
│   │ session_    │    │ Entity      │    │ Dead End    │                     │
│   │ insights    │    │ Resolution  │    │ Detection   │                     │
│   │ (staging)   │    │ (Neo4j)     │    │             │                     │
│   └──────┬──────┘    └──────┬──────┘    └──────┬──────┘                     │
│          │                  │                  │                             │
├──────────┼──────────────────┼──────────────────┼─────────────────────────────┤
│          │                  │                  │                             │
│   WEEKLY BATCH              ▼                  ▼                             │
│          │           ┌─────────────┐    ┌─────────────┐                     │
│          │           │ Auto-Ingest │    │ agent_      │  ← Phase 4          │
│          │           │ to Neo4j    │    │ effectiveness│                    │
│          │           └──────┬──────┘    └──────┬──────┘                     │
│          │                  │                  │                             │
│          ▼                  ▼                  ▼                             │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                     │
│   │ Lawrence    │    │ CO_OCCURS   │    │ graph_      │                     │
│   │ Review      │    │ +usage_weight│   │ router.py   │                     │
│   │ Dashboard   │    │             │    │ (learned)   │                     │
│   └─────────────┘    └─────────────┘    └─────────────┘                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Event Logging (Week 1)

**Foundation. Everything depends on this. Ship first.**

### Tables

#### session_events
```sql
CREATE TABLE session_events (
    id              BIGSERIAL PRIMARY KEY,
    session_id      UUID NOT NULL,
    event_type      TEXT NOT NULL,        -- 'agent_switch' | 'phase_completion' | 'reaction'
    agent           TEXT,                 -- current bot
    from_agent      TEXT,                 -- for agent_switch: which bot they left
    to_agent        TEXT,                 -- for agent_switch: which bot they switched to
    phase_name      TEXT,                 -- for phase_completion
    signal_type     TEXT,                 -- 'positive' | 'negative' | 'redirect' | 'neutral'
    user_initiated  BOOLEAN,              -- did user manually switch, or did router?
    turn_count      INTEGER,
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_events_session ON session_events(session_id);
CREATE INDEX idx_events_agent ON session_events(agent);
CREATE INDEX idx_events_type ON session_events(event_type);
```

#### session_summaries
```sql
CREATE TABLE session_summaries (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id          UUID NOT NULL UNIQUE,
    agents_used         TEXT[] NOT NULL DEFAULT '{}',
    frameworks_applied  TEXT[] DEFAULT '{}',
    problem_type        TEXT,
    total_turns         INTEGER,
    completed           BOOLEAN DEFAULT false,
    venture_id          UUID,
    created_at          TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_summaries_session ON session_summaries(session_id);
CREATE INDEX idx_summaries_problem ON session_summaries(problem_type);
```

### Code Changes (3 INSERT statements)

**File:** `mindrian_chat.py`

```python
# 1. In handle_agent_switch()
async def handle_agent_switch(new_bot_id: str, user_initiated: bool = True):
    session_id = cl.user_session.get("id")
    current_bot = cl.user_session.get("current_bot_id")
    turn_count = len(cl.user_session.get("history", []))

    # ... existing switch logic ...

    # Log event
    await log_session_event(
        session_id=session_id,
        event_type="agent_switch",
        agent=new_bot_id,
        from_agent=current_bot,
        to_agent=new_bot_id,
        user_initiated=user_initiated,
        turn_count=turn_count
    )

# 2. In smart_phase_tracker when phase completes
async def on_phase_complete(phase_name: str):
    session_id = cl.user_session.get("id")
    current_bot = cl.user_session.get("current_bot_id")
    turn_count = len(cl.user_session.get("history", []))

    await log_session_event(
        session_id=session_id,
        event_type="phase_completion",
        agent=current_bot,
        phase_name=phase_name,
        turn_count=turn_count
    )

# 3. At session end
@cl.on_chat_end
async def on_chat_end():
    session_id = cl.user_session.get("id")
    agents_used = cl.user_session.get("agents_used", [])
    total_turns = len(cl.user_session.get("history", []))

    await log_session_summary(
        session_id=session_id,
        agents_used=agents_used,
        total_turns=total_turns,
        completed=True
    )
```

**New file:** `utils/session_logger.py`

```python
"""
Session event logging for Recursive Intelligence.
Zero latency - fire and forget to Supabase.
"""
import asyncio
from typing import Optional, List
from datetime import datetime
from utils.storage import get_supabase_client

async def log_session_event(
    session_id: str,
    event_type: str,
    agent: Optional[str] = None,
    from_agent: Optional[str] = None,
    to_agent: Optional[str] = None,
    phase_name: Optional[str] = None,
    signal_type: Optional[str] = None,
    user_initiated: Optional[bool] = None,
    turn_count: Optional[int] = None,
    metadata: Optional[dict] = None
) -> None:
    """
    Fire-and-forget event logging. Does NOT block main flow.
    """
    try:
        supabase = get_supabase_client()
        await asyncio.to_thread(
            supabase.table("session_events").insert({
                "session_id": session_id,
                "event_type": event_type,
                "agent": agent,
                "from_agent": from_agent,
                "to_agent": to_agent,
                "phase_name": phase_name,
                "signal_type": signal_type,
                "user_initiated": user_initiated,
                "turn_count": turn_count,
                "metadata": metadata or {},
                "created_at": datetime.utcnow().isoformat()
            }).execute
        )
    except Exception as e:
        print(f"[SessionLogger] Failed to log event: {e}")


async def log_session_summary(
    session_id: str,
    agents_used: List[str],
    total_turns: int,
    completed: bool = False,
    frameworks_applied: Optional[List[str]] = None,
    problem_type: Optional[str] = None,
    venture_id: Optional[str] = None
) -> None:
    """
    Log session summary at session end.
    """
    try:
        supabase = get_supabase_client()
        await asyncio.to_thread(
            supabase.table("session_summaries").upsert({
                "session_id": session_id,
                "agents_used": agents_used,
                "frameworks_applied": frameworks_applied or [],
                "problem_type": problem_type,
                "total_turns": total_turns,
                "completed": completed,
                "venture_id": venture_id,
                "created_at": datetime.utcnow().isoformat()
            }).execute
        )
    except Exception as e:
        print(f"[SessionLogger] Failed to log summary: {e}")
```

---

## Phase 2: Reaction Classifier (Week 2)

**Lightweight async classifier. Does NOT block bot response.**

### Implementation

**Add to:** `utils/reaction_classifier.py`

```python
"""
Async reaction classifier for Recursive Intelligence.
Fire-and-forget - runs in parallel with agent response.
Cost: ~$0.0001 per message (Gemini 2.5 Flash-Lite)
"""
import asyncio
import google.generativeai as genai
from utils.session_logger import log_session_event

# Classification categories
REACTION_TYPES = {
    "positive": ["great point", "hadn't thought of that", "yes exactly", "that helps", "makes sense"],
    "negative": ["not what I meant", "doesn't help", "you're wrong", "that's incorrect", "no"],
    "redirect": ["different approach", "can we switch", "forget that", "let's try", "instead"],
    "neutral": ["what about", "tell me more", "how does", "can you explain", "?"]
}

CLASSIFIER_PROMPT = """Classify this user's reaction to an AI assistant response.

Categories:
- positive: User expresses agreement, insight, or appreciation
- negative: User expresses disagreement, frustration, or correction
- redirect: User wants to change direction or try something different
- neutral: User asks follow-up questions or continues normally

User message: {message}

Respond with exactly one word: positive, negative, redirect, or neutral"""


async def classify_reaction(
    user_message: str,
    current_agent: str,
    session_id: str,
    turn_count: int
) -> None:
    """
    Fire-and-forget reaction classification.
    Runs in parallel with agent response - does NOT block.
    """
    try:
        # Quick pattern check first (avoid API call for obvious cases)
        message_lower = user_message.lower()

        # Check for obvious patterns
        for reaction_type, patterns in REACTION_TYPES.items():
            if any(p in message_lower for p in patterns):
                signal = reaction_type
                break
        else:
            # Use Gemini Flash-Lite for ambiguous cases
            model = genai.GenerativeModel("gemini-2.0-flash-lite")
            response = await model.generate_content_async(
                CLASSIFIER_PROMPT.format(message=user_message[:500]),
                generation_config=genai.GenerationConfig(
                    temperature=0,
                    max_output_tokens=10
                )
            )
            signal = response.text.strip().lower()

            # Validate response
            if signal not in ["positive", "negative", "redirect", "neutral"]:
                signal = "neutral"

        # Log to session_events
        await log_session_event(
            session_id=session_id,
            event_type="reaction",
            signal_type=signal,
            agent=current_agent,
            turn_count=turn_count
        )

    except Exception as e:
        print(f"[ReactionClassifier] Failed: {e}")


def fire_and_forget_classify(
    user_message: str,
    current_agent: str,
    session_id: str,
    turn_count: int
) -> None:
    """
    Non-blocking wrapper. Call from message handler.
    """
    asyncio.create_task(
        classify_reaction(user_message, current_agent, session_id, turn_count)
    )
```

### Integration in mindrian_chat.py

```python
from utils.reaction_classifier import fire_and_forget_classify

@cl.on_message
async def on_message(message: cl.Message):
    session_id = cl.user_session.get("id")
    current_bot = cl.user_session.get("current_bot_id", "lawrence")
    turn_count = len(cl.user_session.get("history", []))

    # Fire-and-forget reaction classification (does NOT block)
    fire_and_forget_classify(
        user_message=message.content,
        current_agent=current_bot,
        session_id=session_id,
        turn_count=turn_count
    )

    # ... existing message handling continues immediately ...
```

---

## Phase 3: Post-Session Extraction (Weeks 3-4)

**Edge Function fires when session ends. Uses LangExtract for schema-enforced extraction.**

### Table

```sql
CREATE TABLE session_insights (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id          UUID NOT NULL,
    insight_type        TEXT NOT NULL,      -- 'insight' | 'framework_application' | 'cross_connection' | 'reframing' | 'dead_end'
    content             TEXT NOT NULL,      -- what was discovered
    confidence          TEXT NOT NULL,      -- 'high' | 'medium' | 'low'
    source_agent        TEXT,               -- which bot was active
    entities_mentioned  TEXT[] DEFAULT '{}',-- entity names from extraction
    neo4j_entities_found TEXT[] DEFAULT '{}',-- which exist in Neo4j
    source_positions    JSONB DEFAULT '{}', -- character offsets for audit trail
    status              TEXT DEFAULT 'pending',  -- 'pending' | 'approved' | 'rejected' | 'auto_ingested' | 'archived'
    reviewed_by         TEXT,
    reviewed_at         TIMESTAMPTZ,
    created_at          TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_insights_status ON session_insights(status);
CREATE INDEX idx_insights_type ON session_insights(insight_type);
CREATE INDEX idx_insights_session ON session_insights(session_id);
```

### LangExtract Extraction Schema

**File:** `tools/extraction_schemas.py`

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime

class SourcePosition(BaseModel):
    """Character-level source grounding for audit trail."""
    start: int
    end: int
    turn: int

class ExtractedEntity(BaseModel):
    """Entity extracted with type and source grounding."""
    type: Literal["Framework", "Concept", "Problem", "Technique", "Person", "Tool"]
    name: str
    source: SourcePosition
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)

class ExtractedInsight(BaseModel):
    """Single insight with classification and evidence."""
    insight_type: Literal["insight", "framework_application", "cross_connection", "reframing", "dead_end"]
    content: str
    confidence: Literal["high", "medium", "low"]
    source_agent: Optional[str] = None
    entities_mentioned: List[str] = []
    source_positions: List[SourcePosition] = []

class ExtractedRelationship(BaseModel):
    """Typed relationship between entities."""
    from_entity: str
    to_entity: str
    type: Literal[
        "COMPLEMENTS", "CONTRADICTS", "PRECEDES", "REPLACED_BY",
        "REFRAMES_TO", "REVEALS", "FAILED_ON", "CO_OCCURS"
    ]
    context: str
    source: SourcePosition
    confidence: float = Field(ge=0.0, le=1.0, default=0.7)

class SessionExtraction(BaseModel):
    """Complete extraction output for a session."""
    session_id: str
    extracted_at: datetime = Field(default_factory=datetime.utcnow)
    insights: List[ExtractedInsight] = []
    entities: List[ExtractedEntity] = []
    relationships: List[ExtractedRelationship] = []

    # Multi-pass captures terminology variants
    entity_aliases_found: dict = {}  # {"JTBD": "Jobs to Be Done", ...}
```

### Edge Function: session-distill

**Supabase Edge Function:** `supabase/functions/session-distill/index.ts`

```typescript
import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from "https://esm.sh/@supabase/supabase-js@2"

const EXTRACTION_PROMPT = `
Extract knowledge from this innovation coaching session. For each item, provide:
- type: insight | framework_application | cross_connection | reframing | dead_end
- content: what was discovered (1-2 sentences)
- confidence: high | medium | low
- source_agent: which bot was active
- entities_mentioned: list of framework/concept names

Categories:
- INSIGHT: Novel things the user discovered they didn't know before
- FRAMEWORK_APPLICATION: How a specific framework was applied and what it revealed
- CROSS_CONNECTION: Unexpected links between frameworks or concepts
- REFRAMING: Moments where the problem was fundamentally reframed
- DEAD_END: Approaches tried and abandoned, including why

Return JSON array of extracted items.
`

serve(async (req) => {
  const { session_id } = await req.json()

  const supabase = createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
  )

  // 1. Load conversation transcript
  const { data: messages } = await supabase
    .from('conversation_memory')
    .select('content, role, agent')
    .eq('session_id', session_id)
    .order('created_at')

  if (!messages || messages.length < 3) {
    return new Response(JSON.stringify({ skipped: true, reason: 'too_short' }))
  }

  const transcript = messages.map(m =>
    `[${m.role}${m.agent ? ` - ${m.agent}` : ''}]: ${m.content}`
  ).join('\n\n')

  // 2. Send to Gemini Flash for extraction
  const response = await fetch('https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-goog-api-key': Deno.env.get('GOOGLE_API_KEY')!
    },
    body: JSON.stringify({
      contents: [{ parts: [{ text: EXTRACTION_PROMPT + '\n\nTranscript:\n' + transcript }] }],
      generationConfig: { temperature: 0.2, responseMimeType: 'application/json' }
    })
  })

  const result = await response.json()
  const extracted = JSON.parse(result.candidates[0].content.parts[0].text)

  // 3. For each item, check which entities exist in Neo4j
  for (const item of extracted) {
    const neo4jMatches = await checkNeo4jEntities(item.entities_mentioned)

    // 4. INSERT into session_insights
    await supabase.from('session_insights').insert({
      session_id,
      insight_type: item.type,
      content: item.content,
      confidence: item.confidence,
      source_agent: item.source_agent,
      entities_mentioned: item.entities_mentioned,
      neo4j_entities_found: neo4jMatches,
      status: 'pending'
    })
  }

  return new Response(JSON.stringify({
    extracted: extracted.length,
    session_id
  }))
})
```

---

## Phase 4A: Auto-Ingest to Neo4j (Weeks 5-6)

**Weekly batch job. Only touches existing nodes. All changes tagged for rollback.**

### Qualification Rules (ALL must be true)

1. `confidence = 'high'`
2. `insight_type` is `'cross_connection'` or `'framework_application'`
3. Every entity in `entities_mentioned` has a match in `neo4j_entities_found`
4. Same entity combination appears in 3+ separate sessions

### Implementation

**File:** `scripts/auto_ingest_batch.py`

```python
"""
Weekly batch job: Auto-ingest qualified insights to Neo4j.
Run via cron or Supabase Edge Function scheduler.
"""
from neo4j import GraphDatabase
from datetime import datetime, timedelta

QUALIFICATION_QUERY = """
SELECT
    si.id,
    si.content,
    si.entities_mentioned,
    si.neo4j_entities_found,
    COUNT(DISTINCT si.session_id) as session_count
FROM session_insights si
WHERE si.status = 'pending'
  AND si.confidence = 'high'
  AND si.insight_type IN ('cross_connection', 'framework_application')
  AND si.entities_mentioned = si.neo4j_entities_found  -- All entities exist
GROUP BY si.id, si.content, si.entities_mentioned, si.neo4j_entities_found
HAVING COUNT(DISTINCT si.session_id) >= 3
"""

NEO4J_STRENGTHEN_QUERY = """
MERGE (a {name: $entity_a})-[r:CO_OCCURS]-(b {name: $entity_b})
SET r.session_count = COALESCE(r.session_count, 0) + 1,
    r.usage_weight = COALESCE(r.usage_weight, 0.5) + 0.05,
    r.last_session = datetime(),
    r.last_context = $insight_content,
    r.added_by = "recursive-learning",
    r.added_date = date()
"""

async def run_auto_ingest():
    """Execute weekly auto-ingest batch."""
    supabase = get_supabase_client()
    neo4j_driver = GraphDatabase.driver(
        os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
    )

    # Find qualified insights
    result = supabase.rpc("run_qualification_query").execute()
    qualified = result.data

    ingested_count = 0

    with neo4j_driver.session() as session:
        for insight in qualified:
            entities = insight["entities_mentioned"]

            # Create/strengthen edges between all entity pairs
            for i, entity_a in enumerate(entities):
                for entity_b in entities[i+1:]:
                    session.run(
                        NEO4J_STRENGTHEN_QUERY,
                        entity_a=entity_a,
                        entity_b=entity_b,
                        insight_content=insight["content"]
                    )

            # Mark as auto-ingested
            supabase.table("session_insights").update({
                "status": "auto_ingested"
            }).eq("id", insight["id"]).execute()

            ingested_count += 1

    print(f"[AutoIngest] Ingested {ingested_count} insights")
    return ingested_count


# Kill switch - undo last week of learning
ROLLBACK_QUERY = """
MATCH ()-[r]->()
WHERE r.added_by = "recursive-learning"
  AND r.added_date > date() - duration('P7D')
SET r.usage_weight = 0.5,
    r.session_count = 0,
    r.last_context = null
"""
```

---

## Phase 4B: Adaptive Routing (Weeks 5-6)

**Routing learns from session outcomes. 80% graph, 20% learned.**

### Table

```sql
CREATE TABLE agent_effectiveness (
    agent           TEXT NOT NULL,
    problem_type    TEXT NOT NULL,
    effectiveness   FLOAT NOT NULL,
    sample_size     INTEGER NOT NULL,
    last_updated    TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (agent, problem_type)
);

CREATE INDEX idx_effectiveness_agent ON agent_effectiveness(agent);
```

### Weekly Rebuild Query

```sql
INSERT INTO agent_effectiveness (agent, problem_type, effectiveness, sample_size)
SELECT
    agent,
    problem_type,
    AVG(CASE
        WHEN signal_type = 'positive' THEN 1.0
        WHEN signal_type = 'negative' THEN 0.0
        ELSE 0.5
    END) as effectiveness,
    COUNT(*) as sample_size
FROM session_events
JOIN session_summaries USING (session_id)
WHERE event_type = 'reaction'
  AND signal_type IN ('positive', 'negative')
GROUP BY agent, problem_type
HAVING COUNT(*) >= 10
ON CONFLICT (agent, problem_type) DO UPDATE SET
    effectiveness = EXCLUDED.effectiveness,
    sample_size = EXCLUDED.sample_size,
    last_updated = now();
```

### Router Integration

**File:** `tools/graph_router.py`

```python
# Load effectiveness table on startup
_effectiveness_table = {}

async def load_effectiveness_table():
    """Load learned effectiveness scores from Supabase."""
    global _effectiveness_table
    supabase = get_supabase_client()
    result = supabase.table("agent_effectiveness").select("*").execute()
    _effectiveness_table = {
        (row["agent"], row["problem_type"]): row["effectiveness"]
        for row in result.data
        if row["sample_size"] >= 10  # Minimum threshold
    }
    print(f"[Router] Loaded {len(_effectiveness_table)} effectiveness scores")


def score_agent(agent: str, query: str, problem_type: str) -> float:
    """
    Score agent for routing. 80% graph, 20% learned.

    Safeguards:
    - 15% exploration rate (ignore learned scores)
    - Minimum 10-sample threshold
    - Default to neutral (0.5) if no data
    """
    import random

    # 15% exploration - use pure graph score
    if random.random() < 0.15:
        return graph_score(agent, query)

    base_score = graph_score(agent, query)  # Existing logic

    learned = _effectiveness_table.get(
        (agent, problem_type),
        0.5  # Neutral default if no data
    )

    # 80% graph, 20% learned
    return base_score * 0.8 + learned * 0.2


# Monthly decay - call via cron
async def decay_effectiveness_scores():
    """Multiply all scores by 0.95 so stale data fades."""
    supabase = get_supabase_client()
    supabase.rpc("decay_effectiveness", {"factor": 0.95}).execute()
```

---

## Phase 5: Review Dashboard (Weeks 7-8)

**Lawrence reviews insights that didn't qualify for auto-ingest.**

### Review Queue Display

```
┌────────────────────────────────────────────────────────────────┐
│ 📋 Pending Review: 23 insights                                  │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│ CROSS_CONNECTION (high confidence)                              │
│ ─────────────────────────────────────────────                   │
│ "JTBD job contexts map to Ackoff system boundaries"             │
│                                                                 │
│ Entities mentioned: Jobs to Be Done, Ackoff Systems Thinking,   │
│                     system boundaries                           │
│                                                                 │
│ Neo4j matches: Jobs to Be Done ✓, Ackoff Systems Thinking ✓     │
│                system boundaries ✗ (not found)                  │
│                                                                 │
│ Source: JTBD Workshop, Turn 15                                  │
│ Sessions: 2 (needs 3 for auto-ingest)                           │
│                                                                 │
│ [✓ Approve] [✗ Reject] [🔀 Merge] [⏸ Defer]                    │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### Reviewer Actions

| Action | Effect |
|--------|--------|
| **Approve** | Write to Neo4j via MERGE, tag `added_by: "human-reviewed"` |
| **Reject** | Mark as rejected, excluded from future processing |
| **Merge** | Combine with existing similar insight |
| **Defer** | Keep in queue for later review |

---

## Success Metrics

| Milestone | Metric | Target |
|-----------|--------|--------|
| **100 sessions** | Effectiveness table has data | 3+ agent/problem-type pairs |
| **500 sessions** | CO_OCCURS edges differentiated | Measurable usage_weight variance |
| **500 sessions** | Human-approved insights | 20+ in Neo4j |
| **1,000 sessions** | Graph growth from sessions | 5-10% increase |
| **1,000 sessions** | Routing accuracy improvement | +15% vs baseline |

---

## Constraints Respected

| Constraint | How Respected |
|------------|---------------|
| **512MB Render** | All data in Supabase, only small effectiveness dict in memory |
| **Neo4j writes** | MERGE only, all tagged `added_by` for rollback, 3-session threshold |
| **Latency** | Zero added - classifier is async, extraction is post-session |
| **Cost** | ~$0.002/session ($2.50 per 1,000 sessions) |
| **Graph quality** | Auto-ingest only strengthens existing edges, new knowledge needs review |
| **Routing fairness** | 15% exploration, Bayesian neutral prior, 10-sample minimum |

---

## Implementation Order

1. **Phase 1** (Week 1): Event logging tables + 3 INSERT statements
2. **Phase 2** (Week 2): Reaction classifier (fire-and-forget)
3. **Phase 3** (Weeks 3-4): session_insights table + Edge Function
4. **Phase 4** (Weeks 5-6): Auto-ingest + Adaptive routing
5. **Phase 5** (Weeks 7-8): Review dashboard
6. **Phase 6** (Weeks 9-10): Prompt evolution process

---

*Aligned with Developer Brief v1.0 + LangExtract Engine Specification*
