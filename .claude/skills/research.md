---
description: Deep research pipeline expert - Claude plans, Tavily searches, Gemini synthesizes with reflection loops
---

# Research Pipeline

Expert on Mindrian's LangGraph deep research pipeline with hybrid LLM strategy.

Read the full skill guide: `skills/research-pipeline/SKILL.md`

## Quick Reference

- **Core file**: `intelligence/pipelines/research_pipeline.py`
- **Full pipeline**: `run_deep_research(query, history, bot_id, depth)`
- **Quick one-shot**: `quick_pipeline_research(query, max_results)`
- **Graph factory**: `create_research_pipeline(checkpointer)`

## Depth: basic (0 reflections) | standard (1) | deep (3)

## Architecture
```
PLAN (Claude) → SEARCH (Tavily) → EVALUATE (Python) → REFLECT (Claude) → SYNTHESIZE (Gemini)
```
