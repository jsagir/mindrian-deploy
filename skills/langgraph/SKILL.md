---
name: langgraph
description: "Expert in LangGraph - the production-grade framework for building stateful, multi-actor AI applications. Covers graph construction, state management, cycles and branches, persistence with checkpointers, human-in-the-loop patterns, and the ReAct agent pattern. Used in production at LinkedIn, Uber, and 400+ companies. This is LangChain's recommended approach for building agents. Use when: langgraph, langchain agent, stateful agent, agent graph, react agent."
source: vibeship-spawner-skills (Apache 2.0)
---

# LangGraph

**Role**: LangGraph Agent Architect

You are an expert in building production-grade AI agents with LangGraph. You
understand that agents need explicit structure - graphs make the flow visible
and debuggable. You design state carefully, use reducers appropriately, and
always consider persistence for production. You know when cycles are needed
and how to prevent infinite loops.

## Capabilities

- Graph construction (StateGraph)
- State management and reducers
- Node and edge definitions
- Conditional routing
- Checkpointers and persistence
- Human-in-the-loop patterns
- Tool integration
- Streaming and async execution

## Requirements

- Python 3.9+
- langgraph package
- LLM API access (OpenAI, Anthropic, etc.)
- Understanding of graph concepts

## Patterns

### Basic Agent Graph

Simple ReAct-style agent with tools

**When to use**: Single agent with tool calling

```python
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool

# 1. Define State
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    # add_messages reducer appends, doesn't overwrite

# 2. Define Tools
@tool
def search(query: str) -> str:
    """Search the web for information."""
    # Implementation here
    return f"Results for: {query}"

@tool
def calculator(expression: str) -> str:
    """Evaluate a math expression."""
    return str(eval(expression))

tools = [search, calculator]

# 3. Create LLM with tools
llm = ChatOpenAI(model="gpt-4o").bind_tools(tools)

# 4. Define Nodes
def agent(state: AgentState) -> dict:
    """The agent node - calls LLM."""
    response = llm.invoke(state["messages"])
    return {"messages": [response]}

# Tool node handles tool execution
tool_node = ToolNode(tools)

# 5. Define Routing
def should_continue(state: AgentState) -> str:
    """Route based on whether tools were called."""
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return END

# 6. Build Graph
graph = StateGraph(AgentState)

# Add nodes
graph.add_node("agent", agent)
graph.add_node("tools", tool_node)

# Add edges
graph.add_edge(START, "agent")
graph.add_conditional_edges("agent", should_continue, ["tools", END])
graph.add_edge("tools", "agent")  # Loop back

# Compile
app = graph.compile()

# 7. Run
result = app.invoke({
    "messages": [("user", "What is 25 * 4?")]
})
```

### State with Reducers

Complex state management with custom reducers

**When to use**: Multiple agents updating shared state

```python
from typing import Annotated, TypedDict
from operator import add
from langgraph.graph import StateGraph

# Custom reducer for merging dictionaries
def merge_dicts(left: dict, right: dict) -> dict:
    return {**left, **right}

# State with multiple reducers
class ResearchState(TypedDict):
    # Messages append (don't overwrite)
    messages: Annotated[list, add_messages]

    # Research findings merge
    findings: Annotated[dict, merge_dicts]

    # Sources accumulate
    sources: Annotated[list[str], add]

    # Current step (overwrites - no reducer)
    current_step: str

    # Error count (custom reducer)
    errors: Annotated[int, lambda a, b: a + b]

# Nodes return partial state updates
def researcher(state: ResearchState) -> dict:
    # Only return fields being updated
    return {
        "findings": {"topic_a": "New finding"},
        "sources": ["source1.com"],
        "current_step": "researching"
    }

def writer(state: ResearchState) -> dict:
    # Access accumulated state
    all_findings = state["findings"]
    all_sources = state["sources"]

    return {
        "messages": [("assistant", f"Report based on {len(all_sources)} sources")],
        "current_step": "writing"
    }

# Build graph
graph = StateGraph(ResearchState)
graph.add_node("researcher", researcher)
graph.add_node("writer", writer)
# ... add edges
```

### Conditional Branching

Route to different paths based on state

**When to use**: Multiple possible workflows

```python
from langgraph.graph import StateGraph, START, END

class RouterState(TypedDict):
    query: str
    query_type: str
    result: str

def classifier(state: RouterState) -> dict:
    """Classify the query type."""
    query = state["query"].lower()
    if "code" in query or "program" in query:
        return {"query_type": "coding"}
    elif "search" in query or "find" in query:
        return {"query_type": "search"}
    else:
        return {"query_type": "chat"}

def coding_agent(state: RouterState) -> dict:
    return {"result": "Here's your code..."}

def search_agent(state: RouterState) -> dict:
    return {"result": "Search results..."}

def chat_agent(state: RouterState) -> dict:
    return {"result": "Let me help..."}

# Routing function
def route_query(state: RouterState) -> str:
    """Route to appropriate agent."""
    query_type = state["query_type"]
    return query_type  # Returns node name

# Build graph
graph = StateGraph(RouterState)

graph.add_node("classifier", classifier)
graph.add_node("coding", coding_agent)
graph.add_node("search", search_agent)
graph.add_node("chat", chat_agent)

graph.add_edge(START, "classifier")

# Conditional edges from classifier
graph.add_conditional_edges(
    "classifier",
    route_query,
    {
        "coding": "coding",
        "search": "search",
        "chat": "chat"
    }
)

# All agents lead to END
graph.add_edge("coding", END)
graph.add_edge("search", END)
graph.add_edge("chat", END)

app = graph.compile()
```

## Anti-Patterns

### ❌ Infinite Loop Without Exit

**Why bad**: Agent loops forever.
Burns tokens and costs.
Eventually errors out.

**Instead**: Always have exit conditions:
- Max iterations counter in state
- Clear END conditions in routing
- Timeout at application level

def should_continue(state):
    if state["iterations"] > 10:
        return END
    if state["task_complete"]:
        return END
    return "agent"

### ❌ Stateless Nodes

**Why bad**: Loses LangGraph's benefits.
State not persisted.
Can't resume conversations.

**Instead**: Always use state for data flow.
Return state updates from nodes.
Use reducers for accumulation.
Let LangGraph manage state.

### ❌ Giant Monolithic State

**Why bad**: Hard to reason about.
Unnecessary data in context.
Serialization overhead.

**Instead**: Use input/output schemas for clean interfaces.
Private state for internal data.
Clear separation of concerns.

## Limitations

- Python-only (TypeScript in early stages)
- Learning curve for graph concepts
- State management complexity
- Debugging can be challenging

## Related Skills

Works well with: `crewai`, `autonomous-agents`, `langfuse`, `structured-output`

---

## Mindrian LangGraph Pipelines

Mindrian uses LangGraph for complex multi-step workflows in `intelligence/pipelines/`.

### Available Pipelines

| Pipeline | Purpose | File |
|----------|---------|------|
| **File Processing** | Upload → Detect → Extract → Chunk → Embed | `file_processing.py` |
| **Oracle** | Prediction markets: Formulate → Research → Predict → Resolve | `oracle_pipeline.py` |
| **Minto Pyramid** | SCQA analysis with deep research | `minto_pyramid.py` |
| **Grading** | Multi-phase assessment with Neo4j evidence | `grading.py` |
| **Domain Discovery** | CV analysis for research domains | `domain_discovery.py` |
| **Reverse Salient** | Cross-domain discovery (10 stages) | `reverse_salient.py` |

### File Processing Pipeline Example

```python
from intelligence.pipelines import process_files, process_single_file

# Process multiple files with Neo4j embedding
result = await process_files(
    files=[
        {"path": "/path/to/doc.pdf", "name": "doc.pdf"},
        {"path": "/path/to/notes.docx", "name": "notes.docx"},
    ],
    embed_to_neo4j=True,
    max_chunk_size=1000,
    chunk_overlap=200,
)

# Result contains:
# - files: List of FileState with extracted content
# - total_chunks: Number of chunks created
# - total_chars: Total characters extracted
# - completed_files / failed_files counts
```

### Pipeline Flow (File Processing)

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  DETECT  │ ──> │ EXTRACT  │ ──> │  CHUNK   │ ──> │  EMBED   │
│ File Type│     │ Content  │     │ Semantic │     │ LazyGraph│
└──────────┘     └──────────┘     └──────────┘     └──────────┘
     │                │                │                │
 PDF/DOCX/        PyPDF2/DocAI/    Recursive       Neo4j nodes +
 Image detect     OCR routing      splitter        LangExtract
                  + auto-retry                     relationships
```

### Oracle Pipeline Example

```python
from intelligence.pipelines import run_oracle_formulation, run_oracle_resolution

# Phase 1-2: Market formulation + research brief
result = await run_oracle_formulation(
    user_input="Will AI tutoring reach 100 users in 90 days?",
    session_id="session_123"
)

# Result contains structured market, research brief, HSI surprises

# Phase 4-5: Resolution + retrospective
resolution_result = await run_oracle_resolution(
    market_id="market_abc",
    market=result["market"],
    predictions=[...],
    resolution={"outcome": "yes", "actual_value": 0.85},
    session_id="session_123"
)
```

### Importing Pipelines

```python
from intelligence import (
    # File Processing
    process_files,
    process_single_file,
    process_uploaded_files_langgraph,

    # Oracle
    run_oracle_formulation,
    run_oracle_resolution,

    # Minto
    run_minto_pipeline,

    # Grading
    run_grading_pipeline,

    # Domain Discovery
    run_domain_discovery,

    # Reverse Salient
    run_reverse_salient,
)
```
