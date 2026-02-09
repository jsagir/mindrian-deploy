---
name: Mindrian-Team-Stack-Architect
description: Mindrian-Team-Stack-Architect - Comprehensive guide for the Mindrian technology stack including Neo4j GraphRAG Lite, Supabase PostgreSQL, Google Gemini AI, Memory System, and Supabase Edge Functions. Provides architectural patterns, query templates, and orchestration workflows. Use when building, debugging, or extending the Mindrian platform.
---

# Mindrian-Team-Stack-Architect

Mindrian-Team-Stack-Architect provides essential knowledge for working with the Mindrian technology stack. It guides intelligent decisions about which component to use and how to use it correctly.

## Core Architecture Principle

> **Each component handles what it does best:**
> - **Neo4j + GraphRAG Lite** for **relationships and semantic context**
> - **Supabase PostgreSQL** for **persistence and vector search**
> - **Google Gemini** for **reasoning and synthesis**
> - **Memory System** for **continuity and personalization**
> - **Edge Functions** for **real-time execution**

## Component Overview

| Component | Primary Role | Key Implementation |
|---|---|---|
| 🔷 **Neo4j** | Relationships & Context | `tools/graphrag_lite.py`, `tools/graph_router.py` |
| 🔶 **Supabase** | Persistence & Vector Search | pgvector, `utils/data_layer.py` |
| 🟣 **Gemini AI** | Reasoning & Intelligence | `gemini-2.5-flash-preview`, `gemini-2.5-pro-preview` |
| 🔴 **Memory** | Continuity & Personalization | `utils/context_persistence.py`, `context_store` |
| 🟢 **Edge Functions** | Execution & Real-time | Supabase Edge Functions (Deno) |

## Quick Decision Guide

| If you need to... | Use This | Implementation File |
|---|---|---|
| Find related concepts | **Neo4j** | `tools/graphrag_lite.py` |
| Search by similarity | **Supabase pgvector** | `utils/data_layer.py` |
| Decide what to do | **Gemini** | Model calls in `mindrian_chat.py` |
| Remember preferences | **Memory System** | `utils/context_persistence.py` |
| Run async operations | **Edge Functions** | Supabase Edge Functions |
| Store structured data | **Supabase PostgreSQL** | `utils/data_layer.py` |
| Find frameworks | **Neo4j** | `tools/neo4j_framework_discovery.py` |
| Route to correct tool | **Graph Router** | `tools/graph_router.py` |

## GraphRAG Lite (Neo4j Integration)

The actual implementation uses **GraphRAG Lite** — a lightweight, memory-safe graph retrieval system.

### Key Characteristics
- **~8K concepts**, **39 communities**, **~123K co-occurrence edges**
- **Bounded cache**: Community map + PWS terms only (~2MB)
- **Circuit breaker**: Falls back gracefully if Neo4j is slow (3s timeout)
- **Memory safe**: Designed for 512MB Render instances

### Core Functions (from `tools/graphrag_lite.py`)

```python
from tools.graphrag_lite import enrich_for_larry, enrich_for_bot, should_retrieve
from tools.graph_router import graph_score_agents, classify_and_route, has_problem_language

# Check if retrieval is needed
if should_retrieve(user_message):
    context = enrich_for_larry(user_message)
    
# Route to appropriate agent
agent_scores = graph_score_agents(user_message)
best_agent = classify_and_route(user_message)
```

### When GraphRAG is Used
- Larry Playground (full tools)
- Bot switching decisions
- Framework discovery
- Concept relationship lookup

## Smart Phase Tracker

Uses **LangChain + Gemini** for intelligent phase detection (not turn counting).

### Key Functions (from `tools/smart_phase_tracker.py`)

```python
from tools.smart_phase_tracker import (
    analyze_workshop_state,
    format_progress_indicator,
    should_show_advance_prompt,
    get_smart_phase_message,
    extract_phase_context
)

# Analyze current workshop state
state = analyze_workshop_state(conversation_history, workshop_type)

# Check if should advance
if should_show_advance_prompt(state):
    prompt = get_smart_phase_message(state)
```

## Core Workflows

### Workflow 1: GraphRAG Lite Retrieval

```
User Query
    │
    ▼
┌─────────────────┐
│ should_retrieve │  Check if retrieval needed
└────────┬────────┘
         │ Yes
         ▼
┌─────────────────┐
│ LazyCache       │  Check bounded cache (~2MB)
│ (39 communities)│  
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Neo4j Query     │  On-demand CO_OCCURS fetch
│ (3s timeout)    │  Circuit breaker protection
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ enrich_for_*    │  Return hints, not lectures
└─────────────────┘
```

### Workflow 2: Agent Routing

```
User Message
    │
    ▼
┌─────────────────┐
│ has_problem_    │  Check for problem language
│ language()      │  
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ graph_score_    │  Score each agent's fit
│ agents()        │  
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ classify_and_   │  Route to best agent
│ route()         │  
└─────────────────┘
```

## Detailed Component Guides

For deep dives into each component, consult the reference files:

- **Neo4j**: `/home/jsagi/Mindrian/mindrian-deploy/skills/mindrian-stack/references/neo4j.md`
- **Supabase**: `/home/jsagi/Mindrian/mindrian-deploy/skills/mindrian-stack/references/supabase.md`
- **Memory**: `/home/jsagi/Mindrian/mindrian-deploy/skills/mindrian-stack/references/memory.md`
- **Edge Functions**: `/home/jsagi/Mindrian/mindrian-deploy/skills/mindrian-stack/references/edge-functions.md`
- **Orchestration**: `/home/jsagi/Mindrian/mindrian-deploy/skills/mindrian-stack/references/orchestration.md`

## Code Templates

Pre-built templates for common operations:

- **Cypher Queries**: `/home/jsagi/Mindrian/mindrian-deploy/skills/mindrian-stack/templates/cypher-queries.cypher`
- **SQL Queries**: `/home/jsagi/Mindrian/mindrian-deploy/skills/mindrian-stack/templates/sql-queries.sql`
- **Edge Function**: `/home/jsagi/Mindrian/mindrian-deploy/skills/mindrian-stack/templates/edge-function.ts`

## Failure & Degradation

| Component Down | Impact | Fallback |
|---|---|---|
| 🔴 **Gemini** | Critical | None — brain is gone |
| 🟠 **Neo4j** | High | `GRAPHRAG_ENABLED = False`, vector-only |
| 🟠 **Supabase** | High | Memory-only, no persistence |
| 🟡 **Smart Phase** | Medium | `SMART_PHASE_ENABLED = False`, turn counting |

## Environment Variables

```bash
GOOGLE_API_KEY          # Primary Gemini API key
GOOGLE_FILESEARCH_API_KEY  # FileSearch store key (optional)
TAVILY_API_KEY          # Web search
NEO4J_URI               # Neo4j connection
NEO4J_USER              # Neo4j auth
NEO4J_PASSWORD          # Neo4j auth
SUPABASE_URL            # Supabase project URL
SUPABASE_SERVICE_KEY    # Supabase service role key
SUPABASE_ANON_KEY       # Public key for frontend auth
SUPABASE_JWT_SECRET     # JWT validation
DATABASE_URL            # PostgreSQL connection
CHAINLIT_AUTH_SECRET    # Session signing
```

## Integration

This skill works with:
- `context-manager` - User session isolation, auth flow, persistence layers
- `commit-expert` - For recent code changes to the stack
- `qa-consultant` - For tracking stack-related issues
- `neo4j-schema-navigator` - Graph schema and queries
- `swarm-orchestrator` - Coordinates Architecture Review workflows
