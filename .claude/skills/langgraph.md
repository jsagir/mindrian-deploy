---
description: Expert in LangGraph - production-grade stateful multi-actor AI apps. Use for state graphs, reducers, cycles, checkpointers, human-in-the-loop.
---

# LangGraph

Read the full guide: `skills/langgraph/SKILL.md`

## Quick Start

```python
from langgraph.graph import StateGraph, START, END

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

graph = StateGraph(AgentState)
graph.add_node("agent", agent_node)
graph.add_node("tools", tool_node)
graph.add_edge(START, "agent")
graph.add_conditional_edges("agent", should_continue, ["tools", END])
graph.add_edge("tools", "agent")

app = graph.compile()
```

## Key Patterns

- **StateGraph**: Define nodes and edges
- **Reducers**: Control how state updates merge
- **Conditional edges**: Route based on state
- **Checkpointers**: Persistence for long-running workflows

$ARGUMENTS
