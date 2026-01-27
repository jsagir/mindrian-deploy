# R&D 11: Gemini Deep Research Integration

## Status: Experimental

## What Is This?

Integration of Google's Gemini Deep Research agent (Interactions API) into Mindrian.
Unlike the existing Tavily-based "Research" button (seconds, surface-level), this
launches an autonomous AI agent that spends 5-20 minutes browsing 30-50+ sources
and returns a comprehensive research report.

## Architecture

```
User clicks "Deep Research"
    |
    v
[Expectation Setting] -- Immediate message: "5-15 min, you can keep chatting"
    |
    v
[Graph Intelligence]  -- LazyGraphRAG (concepts, communities, cross-domain)
    |                    + Graph Orchestrator (ProblemType -> Cynefin -> Framework -> Technique)
    v
[Query Composition]   -- Enriched research query with graph-derived framing
    |
    v
[Gemini Deep Research] -- Interactions API, background=True, polling every 15s
    |                     Live progress updates via cl.Step + cl.Message
    v
[Report Storage]       -- Supabase: deep-research/{date}/{slug}.md + .json
    |
    v
[Result Display]       -- Summary in chat + download action + injected into history
```

## Key Design Decisions

### LazyGraphRAG in the Loop
The research query isn't the raw user input. It's enriched with:
- **Concept co-occurrence** from LazyGraphRAG (what concepts cluster together)
- **Cross-domain signals** (when concepts span multiple communities)
- **ProblemType classification** (Undefined, Ill-Defined, Well-Defined, Wicked)
- **Cynefin domain** (Clear, Complicated, Complex, Chaotic)
- **Framework names** from ADDRESSES_PROBLEM_TYPE relationships
- **Technique names** from USES_TECHNIQUE relationships
- **Bot-specific framing** (TTA focuses on trends, Red Team on weaknesses, etc.)

This means Gemini Deep Research gets a research brief, not a vague question.

### UX for Long-Running Tasks
- Immediate expectation-setting message (before anything runs)
- cl.Step nested visualization (Graph Intelligence -> Query -> Research -> Storage)
- Live polling updates every 15s with elapsed time
- "You can keep chatting" — research doesn't block the conversation
- Result posted with summary + download action when done

### Storage
- **Supabase Storage**: `deep-research/{date}/{topic-slug}.md` (full report with YAML frontmatter)
- **Supabase Storage**: `deep-research/{date}/{topic-slug}.json` (metadata + trace for analytics)
- **Conversation History**: Summary injected so the active bot can reference findings

### Two Research Tiers
| Feature | Quick Research (Tavily) | Deep Research (Gemini) |
|---------|------------------------|----------------------|
| Button | "Research" | "Deep Research" |
| Time | 5-30 seconds | 5-20 minutes |
| Sources | 5-10 per query | 30-50+ autonomous |
| Depth | Surface results + snippets | Full synthesis + citations |
| Cost | ~$0.01 | ~$2-5 |
| Graph enrichment | No | Yes (LazyGraphRAG + orchestrator) |
| Output | In-chat results | Report + Supabase file |

## Files

| File | Role |
|------|------|
| `tools/deep_research.py` | Core: query composition, Gemini API, polling, storage |
| `tools/graph_orchestrator.py` | ProblemType -> Framework -> MCPTool pipeline discovery |
| `tools/tool_dispatcher.py` | MCPTool node -> Python callable registry |
| `mindrian_chat.py` | `@cl.action_callback("gemini_deep_research")` handler |

## API Reference

```python
from tools.deep_research import run_deep_research

result = await run_deep_research(
    topic="How to scale an artisanal food business",
    conversation_context="User: We make tahini...",
    bot_id="larry",
    on_progress=async_callback,
)

# result = {
#     "status": "completed",
#     "report": "...(full markdown report)...",
#     "report_url": "https://supabase.../deep-research/2026-01-27/scale-artisanal-food.md",
#     "summary": "...(first 500 chars)...",
#     "trace": {
#         "lazy_concepts": ["Innovation", "Market Analysis"],
#         "problem_type": "Undefined Problem",
#         "cynefin_domain": "Complex",
#         "frameworks": ["Scenario Planning", "TTA"],
#         "techniques": ["Pattern Detection", "Market Research"],
#     },
#     "elapsed_sec": 420,
# }
```

## Gemini Interactions API

- Agent: `deep-research-pro-preview-12-2025`
- Mode: `background=True` (long-running)
- Polling: every 15s, max 80 polls (20 min timeout)
- Docs: https://ai.google.dev/gemini-api/docs/deep-research

## Limitations

- Deep Research agent cannot use custom tools (no MCP/function calling)
- Cannot provide structured output format
- Costs $2-5 per run
- Takes 5-20 minutes (not suitable for quick questions)
- Requires `google-genai` SDK with Interactions API support

## Future Work

- Stream real-time updates from the Deep Research agent (streaming API)
- Write extracted frameworks/sources back to Neo4j as nodes
- A/B test: graph-enriched queries vs raw user queries for research quality
- Budget controls: limit runs per session or require confirmation for expensive queries
