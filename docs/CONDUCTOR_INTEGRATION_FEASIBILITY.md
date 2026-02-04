# Conductor + LangGraph Memory Integration - Feasibility Analysis

**Date:** 2026-02-04
**Status:** ✅ FEASIBLE - Infrastructure Already Exists

---

## Executive Summary

The proposed Conductor-style memory management is **100% feasible** with Mindrian's current stack. In fact, **most of the infrastructure already exists** but isn't fully utilized.

---

## Current Stack Inventory

### ✅ Already Implemented

| Component | Location | Status |
|-----------|----------|--------|
| **LangGraph StateGraph** | `intelligence/pipelines/*.py` | Active in 7 pipelines |
| **AsyncPostgresSaver** | grading, domain_discovery, minto_pyramid, reverse_salient | Implemented but optional |
| **Neo4j** | `tools/neo4j_framework_discovery.py`, MCP server | Framework discovery, Cypher queries |
| **Supabase Storage** | `protocols/supabase_storage.py` | A2A sessions, artifacts, phases |
| **LangExtract** | `tools/langextract.py` | Extraction caching with Supabase |
| **FileSearch** | Gemini RAG via `google-genai` | PWS knowledge retrieval |
| **PostgreSQL** | `asyncpg`, `psycopg2-binary` | Chainlit data layer |

### 📦 Dependencies (in requirements.txt)

```
✅ supabase>=2.0.0              # Storage
✅ neo4j>=5.0.0                  # Graph database
✅ langextract>=0.1.0            # Structured extraction
✅ google-genai>=1.0.0           # FileSearch + Gemini
✅ asyncpg>=0.29.0               # Postgres async
✅ sqlalchemy[asyncio]>=2.0.0    # ORM
⚠️ langgraph (commented out)     # Need to uncomment or install separately
```

---

## Architecture Mapping

### Conductor Concepts → Mindrian Implementation

| Conductor Concept | Mindrian Equivalent | Implementation |
|-------------------|---------------------|----------------|
| `product.md` | BOTS config | Already in `mindrian_chat.py` |
| `tech-stack.md` | System prompts | `prompts/*.py` |
| `workflow.md` | Workshop phases | `WORKSHOP_PHASES` dict |
| `tracks/<id>/spec.md` | User problem definition | → Store in **Supabase** |
| `tracks/<id>/plan.md` | Phase checkpoints | → Store in **Neo4j** |
| `tracks/<id>/metadata.json` | Session state | → **PostgresSaver** checkpoints |

---

## Proposed Integration

### Memory Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                    MINDRIAN MEMORY STACK                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  LAYER 1: SHORT-TERM (Conversation)                             │
│  ├── LangGraph MemorySaver / PostgresSaver                      │
│  ├── Thread-scoped checkpoints                                  │
│  └── Per-session state                                          │
│                                                                  │
│  LAYER 2: MEDIUM-TERM (PWS Journey)                             │
│  ├── Supabase: a2a_sessions, a2a_artifacts                      │
│  ├── Neo4j: User journey graph                                  │
│  └── Phase progress, extracted insights                         │
│                                                                  │
│  LAYER 3: LONG-TERM (Knowledge)                                 │
│  ├── FileSearch: PWS methodology corpus                         │
│  ├── Neo4j: Framework relationships                             │
│  └── LangExtract cache: Reusable extractions                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: Enable Persistent Checkpointers (1 day)

**Already exists** - just needs activation:

```python
# intelligence/pipelines/minto_pyramid.py (line 39-44)
try:
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
```

**Change required:** Uncomment LangGraph in requirements.txt and ensure it's installed.

```python
# requirements.txt
langgraph>=0.2.0
langgraph-checkpoint-postgres>=0.1.0
```

### Phase 2: Create User Journey Tracker (2 days)

New module: `memory/user_journey.py`

```python
"""
User Journey Tracker - Conductor-style persistent memory.
Combines: Neo4j (graph), Supabase (artifacts), Postgres (checkpoints)
"""

from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class UserJourney:
    """A user's PWS journey - like a Conductor "track"."""
    user_id: str
    problem_spec: str           # Their problem definition
    current_phase: str          # TTA, JTBD, Validation, etc.
    completed_phases: list
    key_insights: list          # Extracted via LangExtract
    assumptions_tested: list    # From Red Team sessions
    created_at: datetime
    last_active: datetime

class JourneyStore:
    """
    Persistent storage for user journeys.
    Uses: Neo4j (relationships) + Supabase (artifacts) + Postgres (state)
    """

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.neo4j = get_neo4j_driver()
        self.supabase = get_supabase_client()
        self.postgres_url = os.getenv("DATABASE_URL")

    async def create_journey(self, problem: str) -> UserJourney:
        """Create new PWS journey for user."""
        journey = UserJourney(
            user_id=self.user_id,
            problem_spec=problem,
            current_phase="discovery",
            completed_phases=[],
            key_insights=[],
            assumptions_tested=[],
            created_at=datetime.now(),
            last_active=datetime.now()
        )

        # Store in Neo4j as a node
        await self._create_neo4j_journey_node(journey)

        # Store artifacts in Supabase
        await self._save_spec_to_supabase(journey)

        return journey

    async def update_phase(self, new_phase: str, insights: list = None):
        """Update journey progress - called after each significant step."""
        # Update Neo4j journey node
        # Add insights to Supabase
        # Create checkpoint in Postgres
        pass

    async def get_journey_context(self) -> str:
        """Get journey context for agent prompts."""
        # Query Neo4j for journey + related frameworks
        # Retrieve key artifacts from Supabase
        # Format as context injection
        pass
```

### Phase 3: Integrate with LangGraph Pipelines (1 day)

Modify existing pipelines to use journey context:

```python
# intelligence/pipelines/minto_pyramid.py

async def run_minto_pipeline(
    query: str,
    user_id: str = None,
    session_id: str = None,
    use_journey_context: bool = True
):
    """Run Minto Pyramid with journey-aware context."""

    # Get user's journey context if available
    journey_context = ""
    if user_id and use_journey_context:
        from memory.user_journey import JourneyStore
        store = JourneyStore(user_id)
        journey_context = await store.get_journey_context()

    # Get checkpointer (already implemented!)
    checkpointer = await get_postgres_checkpointer()
    if checkpointer is None:
        checkpointer = MemorySaver()

    # Create pipeline with checkpointer
    pipeline = create_minto_pipeline(checkpointer)

    # Thread ID includes user for cross-session persistence
    thread_id = f"minto_{user_id}_{session_id}" if user_id else session_id

    # Run with journey context injected
    result = await pipeline.ainvoke(
        {
            "query": query,
            "context": journey_context,  # <-- Journey context injected!
        },
        config={
            "configurable": {"thread_id": thread_id}
        }
    )

    # Update journey with new insights
    if user_id:
        insights = extract_insights_from_result(result)
        await store.update_phase(result.get("phase"), insights)

    return result
```

### Phase 4: Add Conductor Commands (Optional, 2 days)

Create Chainlit action buttons that mirror Conductor's workflow:

```python
# Action buttons for journey management

@cl.action_callback("journey_status")
async def on_journey_status(action: cl.Action):
    """Show user's PWS journey progress - like /conductor:status"""
    user_id = cl.user_session.get("user_id")
    store = JourneyStore(user_id)
    journey = await store.get_journey()

    # Display progress
    await cl.Message(content=format_journey_status(journey)).send()

@cl.action_callback("journey_revert")
async def on_journey_revert(action: cl.Action):
    """Revert to previous phase - like /conductor:revert"""
    phase_id = action.payload.get("phase_id")
    # Load checkpoint from Postgres
    # Restore state
    pass
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERACTION                             │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      CHAINLIT MESSAGE HANDLER                        │
│  1. Get user_id from session                                        │
│  2. Load journey context from JourneyStore                          │
│  3. Inject context into agent prompt                                │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
           ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
           │   Neo4j     │  │  Supabase   │  │  Postgres   │
           │ (Journey    │  │ (Artifacts, │  │ (Checkpoints│
           │  Graph)     │  │  Extracts)  │  │  State)     │
           └─────────────┘  └─────────────┘  └─────────────┘
                    │               │               │
                    └───────────────┼───────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      LANGGRAPH PIPELINE                              │
│  - Minto Pyramid, BONO, Domain Discovery, etc.                      │
│  - Checkpointer saves state at each node                            │
│  - Can resume from any checkpoint                                   │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      POST-PIPELINE HOOKS                             │
│  1. Extract insights via LangExtract                                │
│  2. Store in Neo4j as journey edges                                 │
│  3. Update Supabase artifacts                                       │
│  4. Cache extractions for future sessions                           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Neo4j Schema for User Journeys

```cypher
// User Journey Graph Schema

// User node
CREATE (u:User {
    id: "user_123",
    email: "user@example.com",
    created_at: datetime()
})

// Journey node (like a Conductor "track")
CREATE (j:Journey {
    id: "journey_abc",
    user_id: "user_123",
    problem_spec: "How can AI improve education accessibility?",
    status: "in_progress",
    current_phase: "tta",
    started_at: datetime()
})

// Phase completion nodes
CREATE (p:PhaseCompletion {
    journey_id: "journey_abc",
    phase: "domain_discovery",
    completed_at: datetime(),
    insights_count: 5
})

// Insight nodes (extracted via LangExtract)
CREATE (i:Insight {
    id: "insight_xyz",
    journey_id: "journey_abc",
    type: "assumption",
    content: "Users will pay for AI tutoring",
    confidence: 0.7,
    tested: false
})

// Relationships
CREATE (u)-[:HAS_JOURNEY]->(j)
CREATE (j)-[:COMPLETED_PHASE]->(p)
CREATE (j)-[:HAS_INSIGHT]->(i)
CREATE (i)-[:CHALLENGES]->(assumption:Assumption)
```

---

## Supabase Tables (Already Partially Exist)

```sql
-- a2a_sessions (already exists)
-- Add journey_id column
ALTER TABLE a2a_sessions ADD COLUMN journey_id TEXT;

-- journey_artifacts (new)
CREATE TABLE journey_artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    journey_id TEXT NOT NULL,
    type TEXT NOT NULL,  -- 'spec', 'insight', 'assumption', 'evidence'
    content JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- journey_checkpoints (for Conductor-style plan.md tracking)
CREATE TABLE journey_checkpoints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    journey_id TEXT NOT NULL,
    phase TEXT NOT NULL,
    step TEXT NOT NULL,
    status TEXT DEFAULT 'pending',  -- 'pending', 'in_progress', 'completed'
    completed_at TIMESTAMP
);
```

---

## Effort Estimate

| Phase | Description | Effort | Dependencies |
|-------|-------------|--------|--------------|
| 1 | Enable Postgres Checkpointers | 1 day | Install langgraph-checkpoint-postgres |
| 2 | User Journey Module | 2 days | Neo4j + Supabase schemas |
| 3 | Pipeline Integration | 1 day | Phase 1 & 2 complete |
| 4 | Conductor Commands (UI) | 2 days | Optional |

**Total: 4-6 days** (without optional UI)

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Neo4j connection issues | Already have fallback to default frameworks |
| Supabase rate limits | Batch writes, use caching |
| Postgres checkpoint size | Set retention policy (30 days) |
| Token consumption | Same as Conductor warning - monitor with `/stats` |

---

## Conclusion

**✅ 100% Feasible** - The infrastructure exists. We just need to:

1. **Uncomment/install** `langgraph-checkpoint-postgres`
2. **Create** `memory/user_journey.py` module
3. **Wire up** journey context injection in message handler
4. **Add** Neo4j/Supabase schema for journeys

The Conductor pattern maps perfectly to Mindrian's PWS workshop methodology:
- **Spec** = Problem Definition phase
- **Plan** = Workshop phases with checkpoints
- **Implement** = Research, validation, synthesis

---

*Generated: 2026-02-04*
