# Mindrian Chat Refactoring Analysis

## Current State: Monolithic Architecture

**File:** `mindrian_chat.py`
**Lines:** 10,339
**Functions:** 137
**Action Callbacks:** 70+

### Problem: Single File Handles Everything

```
mindrian_chat.py (10,339 lines)
├── Configuration & Constants (~800 lines)
│   ├── BOTS dict
│   ├── WORKSHOP_PHASES
│   ├── STARTERS
│   └── AGENT_TRIGGERS
│
├── Chainlit Lifecycle Handlers (~500 lines)
│   ├── @cl.on_chat_start
│   ├── @cl.on_chat_resume
│   ├── @cl.on_message (1,262 lines!) ← MAIN BOTTLENECK
│   ├── @cl.on_stop
│   └── @cl.on_audio_*
│
├── Action Callbacks (~4,000 lines)
│   ├── Agent switching (switch_to_*)
│   ├── Research actions (deep_research, arxiv_search, etc.)
│   ├── Phase navigation (jump_to_phase, acknowledge_phase)
│   ├── Grading workflows (grade_student_work, discuss_grade)
│   ├── Media actions (watch_video, listen_audiobook)
│   └── UI interactions (map_ideas, export_summary)
│
├── Helper Functions (~2,000 lines)
│   ├── show_thinking_panel()
│   ├── create_workshop_roadmap()
│   ├── suggest_agents_from_context()
│   └── get_core_action_buttons()
│
└── Business Logic (scattered throughout)
    ├── File processing
    ├── Grading logic
    ├── Research orchestration
    └── Multi-agent coordination
```

---

## Proposed Architecture: LangGraph-Based Modular System

### Layer 1: Chainlit UI Shell (Thin)
**File:** `mindrian_chat.py` → Reduced to ~2,000 lines

```python
# ONLY handles:
# - Chainlit lifecycle (@cl.on_*)
# - UI element creation
# - Session state management
# - Routing to LangGraph pipelines
```

### Layer 2: LangGraph Pipelines (Business Logic)
**Directory:** `intelligence/pipelines/`

```
intelligence/pipelines/
├── __init__.py
├── message_router.py      # NEW: Routes incoming messages
├── conversation.py        # NEW: Main conversation flow
├── file_processing.py     # DONE: File upload → extract → embed
├── grading.py             # EXISTS: Assessment pipeline
├── research.py            # NEW: Deep research orchestration
├── phase_management.py    # NEW: Workshop phase transitions
├── oracle_pipeline.py     # DONE: Prediction markets
├── minto_pyramid.py       # EXISTS: SCQA analysis
├── domain_discovery.py    # EXISTS: CV/research analysis
└── reverse_salient.py     # EXISTS: Cross-domain discovery
```

### Layer 3: Tools & Utilities
**Directory:** `tools/` and `utils/`

```
tools/
├── graphrag_lite.py       # Neo4j context enrichment
├── langextract.py         # Semantic extraction
├── tavily_search.py       # Web search
└── pws_brain.py           # FileSearch RAG

utils/
├── ui_helpers.py          # NEW: Button generation, roadmap creation
├── session_state.py       # NEW: Context preservation
├── action_handlers.py     # NEW: Callback implementations
└── media.py               # Video, audio, exports
```

---

## LangGraph Pipeline: Message Router

```python
# intelligence/pipelines/message_router.py

class MessageState(TypedDict):
    user_message: str
    session_id: str
    bot_id: str
    has_attachments: bool
    attachment_types: List[str]

    # Routing decision
    route: Literal[
        "feedback",      # User providing feedback
        "image_gen",     # Image generation request
        "file_process",  # File upload handling
        "grading",       # Grading bot assessment
        "research",      # Deep research trigger
        "conversation",  # Normal conversation
    ]

    # Context
    history: List[Dict]
    neo4j_context: str
    filesearch_context: str

    # Output
    response: str
    actions: List[Dict]
    elements: List[Any]

def create_message_router() -> StateGraph:
    workflow = StateGraph(MessageState)

    # Nodes
    workflow.add_node("classify", classify_message_intent)
    workflow.add_node("enrich_context", gather_rag_context)
    workflow.add_node("route_feedback", handle_feedback_flow)
    workflow.add_node("route_image", handle_image_generation)
    workflow.add_node("route_files", handle_file_upload)
    workflow.add_node("route_grading", handle_grading_assessment)
    workflow.add_node("route_research", handle_research_request)
    workflow.add_node("route_conversation", handle_normal_conversation)
    workflow.add_node("format_response", prepare_chainlit_response)

    # Entry
    workflow.set_entry_point("classify")

    # Routing
    workflow.add_conditional_edges(
        "classify",
        route_by_intent,
        {
            "feedback": "route_feedback",
            "image_gen": "route_image",
            "file_process": "route_files",
            "grading": "route_grading",
            "research": "route_research",
            "conversation": "enrich_context",
        }
    )

    workflow.add_edge("enrich_context", "route_conversation")

    # All routes lead to format_response
    for route in ["route_feedback", "route_image", "route_files",
                  "route_grading", "route_research", "route_conversation"]:
        workflow.add_edge(route, "format_response")

    workflow.add_edge("format_response", END)

    return workflow.compile()
```

---

## LangGraph Pipeline: Conversation Flow

```python
# intelligence/pipelines/conversation.py

class ConversationState(TypedDict):
    user_message: str
    session_id: str
    bot_id: str
    bot_config: Dict

    # Context enrichment
    history: List[Dict]
    neo4j_hints: List[str]
    filesearch_chunks: List[str]
    web_context: Optional[str]

    # Thinking
    thinking_steps: List[Dict]
    reasoning_visible: bool

    # Phase management (workshop bots)
    current_phase: int
    phase_status: Dict
    should_advance_phase: bool
    phase_insight: Optional[Dict]

    # Response generation
    system_prompt: str
    model_config: Dict
    raw_response: str

    # Post-processing
    suggested_agents: List[str]
    actions_to_show: List[Dict]
    elements_to_attach: List[Any]

    # Learning (Recursive Intelligence)
    session_signals: Dict
    extraction_results: Dict

def create_conversation_pipeline() -> StateGraph:
    workflow = StateGraph(ConversationState)

    # Nodes
    workflow.add_node("load_context", load_session_context)
    workflow.add_node("enrich_neo4j", query_neo4j_lazygraph)
    workflow.add_node("enrich_filesearch", query_filesearch)
    workflow.add_node("capture_thinking", generate_thinking_steps)
    workflow.add_node("generate_response", call_gemini_streaming)
    workflow.add_node("check_phase", analyze_phase_progress)
    workflow.add_node("suggest_agents", find_relevant_agents)
    workflow.add_node("extract_signals", run_langextract)
    workflow.add_node("prepare_output", format_for_chainlit)

    # Flow
    workflow.set_entry_point("load_context")

    # Parallel enrichment
    workflow.add_edge("load_context", "enrich_neo4j")
    workflow.add_edge("load_context", "enrich_filesearch")

    # After enrichment, thinking
    workflow.add_edge("enrich_neo4j", "capture_thinking")
    workflow.add_edge("enrich_filesearch", "capture_thinking")

    # Generate response
    workflow.add_edge("capture_thinking", "generate_response")

    # Post-processing (parallel)
    workflow.add_edge("generate_response", "check_phase")
    workflow.add_edge("generate_response", "suggest_agents")
    workflow.add_edge("generate_response", "extract_signals")

    # Prepare output
    workflow.add_edge("check_phase", "prepare_output")
    workflow.add_edge("suggest_agents", "prepare_output")
    workflow.add_edge("extract_signals", "prepare_output")

    workflow.add_edge("prepare_output", END)

    return workflow.compile()
```

---

## Refactored mindrian_chat.py (Target: ~2,000 lines)

```python
# mindrian_chat.py - Thin Chainlit Shell

import chainlit as cl
from intelligence.pipelines import (
    create_message_router,
    create_conversation_pipeline,
    process_files,
)
from utils.ui_helpers import (
    create_action_buttons,
    create_workshop_roadmap,
    show_thinking_panel,
)
from utils.session_state import (
    get_context_key,
    preserve_context,
    restore_context,
)

# Initialize pipelines once
MESSAGE_ROUTER = create_message_router()
CONVERSATION_PIPELINE = create_conversation_pipeline()


@cl.on_message
async def main(message: cl.Message):
    """Thin handler - routes to LangGraph pipelines."""

    # Build initial state
    state = {
        "user_message": message.content,
        "session_id": cl.user_session.get("id"),
        "bot_id": cl.user_session.get("chat_profile", "lawrence"),
        "has_attachments": bool(message.elements),
        "attachment_types": [type(e).__name__ for e in (message.elements or [])],
        "history": cl.user_session.get("history", []),
    }

    # Run router pipeline
    result = await MESSAGE_ROUTER.ainvoke(state)

    # Handle response
    msg = cl.Message(content="")
    await msg.send()

    # Stream if conversation, otherwise direct output
    if result["route"] == "conversation":
        for token in result.get("stream_tokens", []):
            await msg.stream_token(token)
    else:
        msg.content = result["response"]

    # Add elements and actions
    if result.get("elements"):
        msg.elements = result["elements"]
    if result.get("actions"):
        msg.actions = result["actions"]

    await msg.update()

    # Update session state
    cl.user_session.set("history", result.get("updated_history", []))


@cl.action_callback("switch_to_*")
async def on_switch_agent(action: cl.Action):
    """Generic agent switch handler."""
    target_bot = action.name.replace("switch_to_", "")
    await handle_agent_switch(target_bot)


# ... other thin handlers
```

---

## Migration Roadmap

### Phase 1: Extract Message Router (Week 1)
- [ ] Create `intelligence/pipelines/message_router.py`
- [ ] Move intent classification logic
- [ ] Move routing conditions
- [ ] Test with existing code

### Phase 2: Extract Conversation Pipeline (Week 2)
- [ ] Create `intelligence/pipelines/conversation.py`
- [ ] Move context enrichment (Neo4j, FileSearch)
- [ ] Move thinking capture
- [ ] Move response generation
- [ ] Move post-processing

### Phase 3: Extract UI Helpers (Week 3)
- [ ] Create `utils/ui_helpers.py`
- [ ] Move button generation
- [ ] Move roadmap creation
- [ ] Move element creation

### Phase 4: Extract Action Handlers (Week 4)
- [ ] Create `utils/action_handlers.py`
- [ ] Group related callbacks
- [ ] Create generic handler patterns

### Phase 5: Thin Shell Integration (Week 5)
- [ ] Refactor `mindrian_chat.py` to use pipelines
- [ ] Test all workflows
- [ ] Performance optimization

---

## Benefits

| Aspect | Current | After Refactoring |
|--------|---------|-------------------|
| **Lines of Code** | 10,339 in one file | ~2,000 shell + modular pipelines |
| **Testing** | Hard to unit test | Each pipeline testable in isolation |
| **Debugging** | Trace through 10K lines | LangGraph step visualization |
| **Parallelism** | Manual async | LangGraph automatic parallelization |
| **State Management** | cl.user_session sprawl | TypedDict state per pipeline |
| **Retry Logic** | Manual try/catch | LangGraph conditional edges |
| **Extensibility** | Edit monolith | Add new nodes to pipeline |

---

## Quick Wins (Can Do Now)

1. **File Processing** ✅ DONE - `file_processing.py` pipeline created

2. **Research Orchestration** - Extract deep_research, arxiv_search, etc. into a LangGraph pipeline

3. **Grading Flow** - Already has `grading.py`, need to wire it to replace inline code

4. **Phase Management** - Extract phase tracking logic into dedicated pipeline

---

## Questions to Resolve

1. **Streaming**: How to stream LangGraph responses through Chainlit?
   - Option A: Yield from pipeline nodes
   - Option B: Callback-based streaming
   - Option C: Buffer and stream after pipeline completes

2. **Session State**: Keep in cl.user_session or move to pipeline state?
   - Recommendation: Pipeline state for logic, cl.user_session for UI-only data

3. **Action Callbacks**: Keep in main file or distribute?
   - Recommendation: Generic handlers in main, logic in pipelines
