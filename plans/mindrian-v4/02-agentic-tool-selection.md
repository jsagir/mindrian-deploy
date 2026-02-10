---
description: Give Lawrence intelligent tool selection - autonomously pick the right tool for each user need
---

# Step 2: Agentic Tool Selection

## Goal
Make Lawrence (and all bots) intelligently select tools based on user intent, instead of relying on keyword matching and hardcoded action buttons. The AI should reason about WHICH tool to use, not just IF to use a tool.

## Current State
- Tools are triggered by action buttons (user clicks "Research", "Minto Pyramid", etc.)
- Some tools triggered by keyword matching in `AGENT_TRIGGERS`
- No autonomous tool selection — bot never decides "I should research this" on its own
- Multi-agent analysis requires explicit user request

## What to Build

### 1. Intent-to-Tool Router (`intelligence/tool_router.py`)
- Lightweight classifier that runs after each user message
- Analyzes: user intent, conversation context, current phase, available tools
- Returns: suggested_tool (or None), confidence, reasoning
- Uses Gemini Flash (cheap, fast) with a structured output schema
- Tool categories:
  - `research` → Deep research pipeline
  - `validate` → Camera Test / assumption validation
  - `analyze` → Multi-agent analysis (TTA, Minto, S-Curve)
  - `visualize` → Mermaid diagram, quadrant chart, BMC
  - `knowledge` → Neo4j query, GraphRAG lookup
  - `none` → Just respond conversationally

### 2. Auto-Tool Invocation in Chat
- After intent classification, if confidence > 0.8, auto-invoke the tool
- Show a brief "thinking" step: "I'm going to research this for you..."
- If confidence 0.5-0.8, suggest the tool as an action button instead
- If confidence < 0.5, just respond normally

### 3. Tool Chain Planning
- For complex queries, the router can suggest a CHAIN of tools
- Example: "Research X, then validate the key assumption, then visualize the findings"
- Execute sequentially, feeding output of each into the next

## Files to Create/Modify

| Action | File | Changes |
|--------|------|---------|
| CREATE | `intelligence/tool_router.py` | Intent classifier + tool chain planner |
| MODIFY | `mindrian_chat.py` | Add tool_router call in on_message before response |
| MODIFY | `intelligence/pipelines/__init__.py` | Export tool_router |

## Acceptance Criteria
- [ ] Tool router classifies user intent with >80% accuracy on test queries
- [ ] High-confidence tools auto-invoked without user clicking buttons
- [ ] Medium-confidence tools suggested as action buttons
- [ ] Tool chains work for multi-step queries
- [ ] No performance regression (router adds <500ms latency)

## Validation
```bash
python3 -c "import ast; ast.parse(open('intelligence/tool_router.py').read())"
python3 -c "import ast; ast.parse(open('mindrian_chat.py').read())"
python3 scripts/health_check.py
```
