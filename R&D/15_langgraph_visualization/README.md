# LangGraph Callback Handler & Visualization

## What Is This?

Chainlit `cl.Step` integration for visualizing LangGraph multi-agent workflows. Users see each agent's execution as a nested step in the UI, providing transparency into the multi-agent collaboration.

## Status: **DONE** (2026-01-29)

## Why Implement This?

### Problems Solved

1. **Black Box Execution**: Multi-agent workflows ran without user visibility
2. **No Progress Indication**: Users didn't know which agents were running
3. **Debugging Difficulty**: Hard to see where workflows failed

### Benefits

- Real-time visibility into agent execution
- Nested steps show workflow progression
- Input/output captured for each agent
- Generic wrapper works with any LangGraph

## Implementation

### New Functions

Location: `agents/multi_agent_graph.py`

#### `run_multi_agent_with_steps()`

Wraps multi-agent workflow with Chainlit step visualization:

```python
async def run_multi_agent_with_steps(
    query: str,
    agents: List[str],
    mode: Literal["sequential", "parallel"] = "sequential"
) -> dict:
    """
    Run multi-agent workflow with Chainlit cl.Step visualization.

    Each agent's execution is displayed as a nested step in the UI.
    """
```

**Output Structure:**
```python
{
    "agent_responses": {"larry": "...", "redteam": "..."},
    "synthesis": "Combined analysis...",
    "mode": "sequential",
    "step_logs": [
        {"agent": "larry", "name": "Larry", "response_length": 450},
        {"agent": "redteam", "name": "Red Team", "response_length": 380}
    ]
}
```

#### `visualize_langgraph_execution()`

Generic wrapper for any compiled LangGraph:

```python
async def visualize_langgraph_execution(
    graph,                    # Compiled LangGraph
    initial_state: dict,      # Starting state
    step_name: str = "LangGraph Workflow"
) -> dict:
    """
    Execute a compiled LangGraph with Chainlit step visualization.
    Shows each node as it executes.
    """
```

### Step Visualization Structure

```
📋 Multi-Agent Analysis
├── 🤖 Larry
│   └── Input: "User's query..."
│   └── Output: "Larry's response..."
├── 🤖 Red Team
│   └── Input: "Building on previous insights..."
│   └── Output: "Red Team's challenges..."
├── 🤖 Ackoff
│   └── Output: "DIKW validation..."
└── 🔮 Synthesis
    └── Output: "Combined analysis..."
```

### Parallel Execution Visualization

```
📋 Multi-Agent Analysis
├── ⚡ Parallel Execution
│   └── Input: "Running 3 agents simultaneously"
│   └── Output: "Completed: Larry, Red Team, Ackoff"
└── 🔮 Synthesis
    └── Output: "Combined analysis..."
```

## Usage Examples

### Basic Multi-Agent with Steps

```python
from agents import run_multi_agent_with_steps

# Sequential execution with visualization
result = await run_multi_agent_with_steps(
    query="Should I pivot to AI?",
    agents=["larry", "scurve", "redteam"],
    mode="sequential"
)

# Access results
synthesis = result["synthesis"]
larry_response = result["agent_responses"]["larry"]
```

### Parallel Execution

```python
result = await run_multi_agent_with_steps(
    query="Analyze healthcare trends",
    agents=["tta", "jtbd", "scurve"],
    mode="parallel"
)
```

### Generic LangGraph Visualization

```python
from agents import visualize_langgraph_execution, LANGGRAPH_AVAILABLE

if LANGGRAPH_AVAILABLE:
    from langgraph.graph import StateGraph, END

    # Create your graph
    graph = StateGraph(MyState)
    graph.add_node("step1", step1_func)
    graph.add_node("step2", step2_func)
    graph.add_edge("step1", "step2")
    graph.add_edge("step2", END)

    compiled = graph.compile()

    # Execute with visualization
    result = await visualize_langgraph_execution(
        graph=compiled,
        initial_state={"query": "...", "data": {}},
        step_name="My Custom Workflow"
    )
```

## Module Exports

Updated `agents/__init__.py`:

```python
from .multi_agent_graph import (
    # Core workflow functions
    run_multi_agent_workflow,
    run_multi_agent_with_steps,  # Chainlit-visualized version
    visualize_langgraph_execution,  # Generic LangGraph visualizer

    # Convenience workflows
    quick_analysis,
    comprehensive_analysis,
    stress_test,

    # Agent registries
    AGENTS,
    BACKGROUND_AGENTS,

    # Check for LangGraph availability
    LANGGRAPH_AVAILABLE,
)
```

## Existing Multi-Agent Integration

The `run_multi_agent_with_type()` function in `mindrian_chat.py` already uses `cl.Step` for visualization. The new functions provide:

1. **More granular steps**: Each agent gets its own nested step
2. **Generic wrapper**: Works with any LangGraph, not just our workflows
3. **Better logging**: Captures step_logs for analytics

## Architecture

```
User clicks "Multi-Agent Analysis"
           ↓
run_multi_agent_with_type()
           ↓
┌──────────────────────────────────────┐
│ cl.Step("Multi-Agent: {type}")       │
│ ├── cl.Step("Running Pipeline")      │
│ │   └── workflow["func"](context)    │
│ ├── cl.Step("Background Results")    │
│ └── cl.Step("Expert Perspectives")   │
└──────────────────────────────────────┘
           ↓
Display combined results
```

## Graceful Degradation

If Chainlit is not available (e.g., running in tests):

```python
try:
    import chainlit as cl
    HAS_CHAINLIT = True
except ImportError:
    HAS_CHAINLIT = False

if HAS_CHAINLIT:
    # Use cl.Step visualization
else:
    # Fall back to basic execution
```

## Files Modified

| File | Changes |
|------|---------|
| `agents/multi_agent_graph.py` | Added `run_multi_agent_with_steps()`, `visualize_langgraph_execution()` |
| `agents/__init__.py` | Added exports for new functions |

## Testing

1. **Sequential Workflow**: Run multi-agent with sequential mode, verify steps nest correctly
2. **Parallel Workflow**: Run with parallel mode, verify parallel step shows
3. **Synthesis Step**: Verify synthesis step appears after agents complete
4. **Error Handling**: Test with invalid agent ID, verify graceful failure

## Future Enhancements

- [ ] Real-time streaming of agent responses in steps
- [ ] Clickable steps to expand/collapse
- [ ] Step timing metrics
- [ ] Graph visualization (mermaid diagram of workflow)
- [ ] Step replay for debugging

---

*Implemented: 2026-01-29*
*Commit: f8f3909*
