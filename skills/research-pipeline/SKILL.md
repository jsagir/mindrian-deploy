# Research Pipeline Skill

**Role:** Deep Research Pipeline Expert for Mindrian

You are the expert on Mindrian's LangGraph-based deep research pipeline. This pipeline uses a hybrid LLM strategy: **Claude plans**, **Tavily searches**, **Gemini synthesizes** — with reflection loops for iterative deepening.

## Architecture

```
START → PLAN (Claude) → SEARCH (Tavily) → EVALUATE (Python) → REFLECT (Claude) → SYNTHESIZE (Gemini) → END
                                ↑                                      │
                                └──── needs_more (max 3 loops) ────────┘
```

## Pipeline Tiers

| Tier | Function | Use Case |
|------|----------|----------|
| `run_deep_research()` | Full pipeline with reflection + checkpointing | Main research button in chat |
| `quick_pipeline_research()` | One-shot, no reflection | Drop-in for other pipelines (Minto, Reverse Salient, etc.) |
| `create_research_pipeline()` | Graph factory | Custom wiring |

## Depth Settings

| User Setting | Pipeline Depth | Queries | Tavily Depth | Max Reflections |
|-------------|---------------|---------|--------------|-----------------|
| basic | `basic` | 2-3 | basic | 0 (no reflection) |
| advanced | `standard` | 3-5 | advanced | 1 |
| deep | `deep` | 5-8 | advanced | 3 |

## Key Files

| File | Purpose |
|------|---------|
| `intelligence/pipelines/research_pipeline.py` | Core pipeline implementation (StateGraph, 6 nodes, 3-tier API) |
| `intelligence/pipelines/__init__.py` | Exports: DeepResearchState, create_research_pipeline, run_deep_research, quick_pipeline_research |
| `mindrian_chat.py` (~line 10790) | `_research_sources_first()` calls `run_deep_research()` |
| `tools/tavily_search.py` | Underlying search layer (batch_search, search_web) |
| `tools/research_orchestrator.py` | evaluate_sources(), _get_pws_context() reused |
| `utils/llm_router.py` | get_claude_client(), get_gemini_client(), cost_tracker |

## State Schema (DeepResearchState)

```python
class DeepResearchState(TypedDict):
    original_query: str          # User's EXACT words (never truncated)
    research_question: str       # Cleaned version for display
    conversation_history: list   # Full chat history
    bot_id: str                  # Current bot
    depth: str                   # quick/standard/deep
    planned_queries: list        # Claude's search plan [{query, purpose, priority}]
    search_results: list         # Tavily results accumulated across iterations
    evaluated_sources: list      # Scored/filtered sources
    evidence_gaps: list          # What's still missing
    synthesis: str               # Final report markdown
    pws_context: str             # GraphRAG enrichment
    iteration: int               # Current loop count (max 3)
    cost_summary: dict           # API cost tracking
    error: str                   # Error state
    findings: list               # Structured findings
    sources_display: list        # Formatted sources for UI
```

## Query Fidelity

The plan node includes a fidelity anchor:
```
USER'S EXACT WORDS: "{original_query}"
CRITICAL: Every search query MUST include at least one key phrase from the user's words.
Do NOT substitute with synonyms.
```

This prevents semantic drift (e.g., "project-based curricula" becoming "Project 2025").

## LightRAG Integration

After synthesis, research insights are stored in LightRAG (fire-and-forget):
- **RESEARCH_INSIGHT** entities (key findings)
- **DOMAIN** / **SUBDOMAIN** entities
- **SOURCE** entities (authoritative references)
- **EVIDENCE_GAP** entities (areas needing more research)
- Relations: BELONGS_TO, SOURCED_FROM, HAS_GAP, RELATED_INSIGHT

## Cost Budget

| Depth | Claude Calls | Tavily Calls | Gemini Calls | Est. Total |
|-------|-------------|-------------|-------------|------------|
| basic | 1 (plan) | 2-3 basic | 1 (synth) | ~$0.01 |
| standard | 2 (plan+reflect) | 3-5 advanced | 1 (synth) | ~$0.04 |
| deep | 2-4 (plan+reflects) | 5-15 advanced | 1 (synth) | ~$0.06-0.10 |

## Callers

| File | How It Uses Pipeline |
|------|---------------------|
| `mindrian_chat.py` | `_research_sources_first()` → `run_deep_research()` |
| `intelligence/pipelines/minto_pyramid.py` | Category searches → `quick_pipeline_research()` |
| `intelligence/pipelines/reverse_salient.py` | Domain search → `quick_pipeline_research()` |
| `intelligence/agents/research_agent.py` | Fallback → `quick_pipeline_research()` |
| `agents/multi_agent_graph.py` | ResearchAgent.run() → `quick_pipeline_research()` |

## Troubleshooting

1. **Semantic drift in queries**: Check plan_node prompt — fidelity anchor must include user's exact words
2. **Too many reflection loops**: Check depth setting — basic should have 0, standard 1, deep 3
3. **Claude unavailable**: Plan node falls back to Gemini for query generation
4. **Pipeline failure**: mindrian_chat falls back to raw search_web()
5. **LightRAG storage fails**: Fire-and-forget — doesn't block research response

## Usage Examples

```python
# Full deep research (from chat)
from intelligence.pipelines.research_pipeline import run_deep_research

result = await run_deep_research(
    query="How can AI transform project-based curricula in engineering education?",
    conversation_history=history,
    bot_id="lawrence",
    depth="standard",
)
print(result["synthesis"])

# Quick research (from other pipelines)
from intelligence.pipelines.research_pipeline import quick_pipeline_research

result = await quick_pipeline_research(
    query="vertical farming market size 2025",
    max_results=5,
)
print(result["sources"])
```
