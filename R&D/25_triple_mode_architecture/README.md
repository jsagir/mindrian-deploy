# R&D 25: Triple-Mode Architecture & Agent Registry

> **Status:** Phase 1-2 Complete | Phase 3-4 In Progress
> **Priority:** P0 (Core Architecture)
> **Started:** 2026-02-02
> **Last Updated:** 2026-02-02

---

## Executive Summary

The Triple-Mode Architecture transforms Mindrian from a simple bot-switcher into an **intelligent entry-point router** that:

1. **Auto-detects** user intent from their first message using LangExtract
2. **Routes** to the appropriate entry point (brainstorming, document review, build venture)
3. **Tracks exploration depth** semantically (not by turn count)
4. **Grounds users** at the right moment based on content signals
5. **Enables all agents** to share full Mindrian intelligence via Agent Registry

---

## Table of Contents

1. [What We Built](#what-we-built)
2. [Architecture Overview](#architecture-overview)
3. [File Reference](#file-reference)
4. [What Still Needs Building](#what-still-needs-building)
5. [Implementation Guides](#implementation-guides)
6. [Testing Checklist](#testing-checklist)
7. [Known Issues & Warnings](#known-issues--warnings)
8. [Research Brief Archive](#research-brief-archive)

---

## What We Built

### Phase 1: Bug Fixes (COMPLETE)

| Task | Status | Files Changed |
|------|--------|---------------|
| Fix JSX to use global `callAction` (not `window.Chainlit`) | ✅ | 5 JSX files |
| Consolidate 7 callbacks to 3 | ✅ | triple_mode.py |
| Fix element display modes | ✅ | ExplorationProgress.jsx |
| Add TRIPLE_MODE_ENABLED flag | ✅ | triple_mode.py |

**JSX Files Fixed:**
- `public/elements/EntryPointSelector.jsx` - Uses `callAction` global
- `public/elements/ModeToggle.jsx` - Uses `mode_or_stage` callback
- `public/elements/GroundingPrompt.jsx` - Uses `grounding_response` callback
- `public/elements/VentureStageSelector.jsx` - Uses `mode_or_stage` callback
- `public/elements/ExplorationProgress.jsx` - Uses `display="side"` for sidebar

**Consolidated Callbacks:**
```python
# OLD (7 callbacks):
# select_brainstorming, select_document_review, select_build_venture,
# toggle_sandbox, toggle_workshop, grounding_acknowledge, grounding_skip

# NEW (3 callbacks):
@cl.action_callback("select_entry_point")   # payload: {entry_point: str}
@cl.action_callback("mode_or_stage")        # payload: {mode: str} OR {stage: str}
@cl.action_callback("grounding_response")   # payload: {action: str, reason: str}
```

### Phase 2: LangExtract Integration (COMPLETE)

| Task | Status | Files Changed |
|------|--------|---------------|
| Auto-detect entry point from first message | ✅ | triple_mode.py |
| Replace turn-based grounding with semantic | ✅ | triple_mode.py |
| Topic extraction from signals | ✅ | triple_mode.py |
| Depth calculation from content | ✅ | triple_mode.py |
| Grounding score calculation | ✅ | triple_mode.py |

**Key Functions:**
```python
# Auto-detection
detection = await auto_detect_entry_point(message, has_attachment)
# Returns: {entry_point, confidence, mode, signals, should_show_selector}

# Semantic grounding check
reason = check_semantic_grounding(signals)
# Returns: "pattern_check" | "synthesis" | "bank_prompt" | "problem_validation" | None

# Progress tracking
signals = await extract_and_update_progress(message)
# Updates: topics_explored, exploration_depth, grounding_score, sidebar element
```

### Phase 3: Agent Registry (COMPLETE)

| Task | Status | Files Changed |
|------|--------|---------------|
| Create Agent Registry system | ✅ | protocols/agent_registry.py |
| Define roles (Orchestrator, Workshop, SubAgent, Service) | ✅ | AgentRole enum |
| Define capabilities (GraphRAG, LangExtract, etc.) | ✅ | AgentCapability enum |
| Register all existing agents | ✅ | 12 agents registered |
| Create helper for new agents | ✅ | create_agent_with_defaults() |
| Export from protocols package | ✅ | protocols/__init__.py |

**Registered Agents:**
```
lawrence, larry_playground, tta, jtbd, ackoff, scurve,
redteam, pws_grading, research, scenario, beautiful_question, knowns
```

**Default Capabilities (all agents get these):**
```python
[AgentCapability.GRAPHRAG, AgentCapability.LANGEXTRACT,
 AgentCapability.CONTEXT_STORE, AgentCapability.FILE_SEARCH]
```

---

## Architecture Overview

### Triple-Mode Entry Points

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER'S FIRST MESSAGE                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │   auto_detect_entry_point()   │
              │   (LangExtract signals)       │
              └───────────────────────────────┘
                              │
           ┌──────────────────┼──────────────────┐
           ▼                  ▼                  ▼
   ┌───────────────┐  ┌───────────────┐  ┌───────────────┐
   │  BRAINSTORMING │  │ DOCUMENT_REVIEW│  │ BUILD_VENTURE │
   │  - Exploration │  │ - Analysis     │  │ - Execution   │
   │  - Sandbox mode│  │ - Workshop mode│  │ - Stage-based │
   │  - Topic track │  │ - Red teaming  │  │ - Tools focus │
   └───────────────┘  └───────────────┘  └───────────────┘
           │                  │                  │
           ▼                  ▼                  ▼
   ┌───────────────┐  ┌───────────────┐  ┌───────────────┐
   │  Exploration   │  │  Workshop     │  │  Stage        │
   │  Progress      │  │  Roadmap      │  │  Selector     │
   │  (sidebar)     │  │  (sidebar)    │  │  (selector)   │
   └───────────────┘  └───────────────┘  └───────────────┘
```

### Agent Registry Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       AGENT REGISTRY                             │
├─────────────────────────────────────────────────────────────────┤
│  ORCHESTRATORS          │  WORKSHOPS           │  SERVICES       │
│  ├── lawrence           │  ├── tta             │  ├── graphrag   │
│  └── larry_playground   │  ├── jtbd            │  ├── research   │
│                         │  ├── ackoff          │  └── pws_grading│
│                         │  ├── scurve          │                 │
│                         │  └── redteam         │                 │
├─────────────────────────────────────────────────────────────────┤
│  CAPABILITIES (shared by all):                                   │
│  • GRAPHRAG - Neo4j + vector hybrid retrieval                   │
│  • LANGEXTRACT - Zero-latency structured extraction             │
│  • CONTEXT_STORE - Cross-bot memory preservation                │
│  • FILE_SEARCH - Semantic document retrieval                    │
├─────────────────────────────────────────────────────────────────┤
│  ROUTING RULES:                                                  │
│  • Orchestrators can call any agent                             │
│  • Workshops can call services                                  │
│  • Services return data, no conversation                        │
│  • Sub-agents called by orchestrators only                      │
└─────────────────────────────────────────────────────────────────┘
```

### Semantic Grounding Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    AFTER EACH AI RESPONSE                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │  extract_and_update_progress() │
              │  - Extract topics              │
              │  - Calculate depth             │
              │  - Update grounding score      │
              │  - Update sidebar element      │
              └───────────────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │  check_semantic_grounding()    │
              │  (content signal analysis)     │
              └───────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
   ┌─────────┐          ┌─────────┐          ┌─────────┐
   │ pattern │          │synthesis│          │  bank   │
   │ _check  │          │         │          │ _prompt │
   └─────────┘          └─────────┘          └─────────┘
   3+ problems          assumptions +         solutions +
   no causation         causation            forward-looking
        │                     │                     │
        └─────────────────────┴─────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │   show_grounding_prompt()      │
              │   (GroundingPrompt.jsx)        │
              └───────────────────────────────┘
```

---

## File Reference

### Core Protocol Files

| File | Purpose | Lines |
|------|---------|-------|
| `protocols/triple_mode.py` | Entry point detection, semantic grounding, progress tracking | ~750 |
| `protocols/agent_registry.py` | Agent registration, capabilities, routing rules | ~780 |
| `protocols/entry_point_router.py` | Regex fallback detection, welcome messages | ~200 |
| `protocols/__init__.py` | Package exports | ~80 |

### JSX Components

| File | Purpose | Display |
|------|---------|---------|
| `public/elements/EntryPointSelector.jsx` | Entry point selection cards | inline |
| `public/elements/ModeToggle.jsx` | Sandbox/Workshop toggle | inline |
| `public/elements/GroundingPrompt.jsx` | Grounding intervention UI | inline |
| `public/elements/VentureStageSelector.jsx` | Build venture stage picker | inline |
| `public/elements/ExplorationProgress.jsx` | Exploration depth tracker | **side** |

### Supporting Files

| File | Purpose |
|------|---------|
| `tools/langextract.py` | Zero-latency extraction (instant_extract, get_extraction_hint) |
| `tools/graph_router.py` | Graph-based agent scoring (graph_score_agents) |
| `mindrian_chat.py` | Main app - needs callback integration |

---

## What Still Needs Building

### Priority 0 (Critical)

#### P0-1: Session Persistence
**Why:** Session state resets on page refresh, losing entry_point, mode, topics_explored.

**What to build:**
```python
# In on_chat_start - restore from database
async def restore_triple_mode_state(thread_id: str):
    """Restore triple-mode state from Chainlit's thread metadata."""
    thread = await cl.Thread.get(thread_id)
    if thread and thread.metadata:
        cl.user_session.set("entry_point", thread.metadata.get("entry_point"))
        cl.user_session.set("mode", thread.metadata.get("mode"))
        cl.user_session.set("topics_explored", thread.metadata.get("topics_explored", []))
        # etc.

# After state changes - persist to database
async def persist_triple_mode_state():
    """Save triple-mode state to thread metadata."""
    thread_id = cl.user_session.get("thread_id")
    if thread_id:
        await cl.Thread.update(thread_id, metadata={
            "entry_point": cl.user_session.get("entry_point"),
            "mode": cl.user_session.get("mode"),
            "topics_explored": cl.user_session.get("topics_explored"),
            # etc.
        })
```

**Files to modify:** `protocols/triple_mode.py`, `mindrian_chat.py`

#### P0-2: mindrian_chat.py Integration
**Why:** The callbacks and integration code haven't been added to the main app yet.

**What to add:**
```python
# At top of mindrian_chat.py
from protocols.triple_mode import (
    init_triple_mode_session,
    auto_detect_entry_point,
    extract_and_update_progress,
    check_semantic_grounding,
    handle_entry_point_selection,
    handle_mode_or_stage,
    handle_grounding_response,
    show_entry_point_selector,
    show_exploration_progress_sidebar,
    show_grounding_prompt,
    TRIPLE_MODE_ENABLED,
)

# Add callbacks
@cl.action_callback("select_entry_point")
async def on_select_entry_point(action: cl.Action):
    entry_point = action.payload.get("entry_point")
    await handle_entry_point_selection(entry_point)

@cl.action_callback("mode_or_stage")
async def on_mode_or_stage(action: cl.Action):
    await handle_mode_or_stage(action.payload)

@cl.action_callback("grounding_response")
async def on_grounding_response(action: cl.Action):
    await handle_grounding_response(action.payload)

# In on_chat_start (at end)
if TRIPLE_MODE_ENABLED:
    init_triple_mode_session()

# In on_message (before processing)
if TRIPLE_MODE_ENABLED:
    entry_point = cl.user_session.get("entry_point")
    if entry_point is None:
        has_attachment = bool(message.elements)
        detection = await auto_detect_entry_point(message.content, has_attachment)
        if detection["should_show_selector"]:
            await show_entry_point_selector()
            return
        else:
            await handle_entry_point_selection(detection["entry_point"])

# In on_message (after AI response)
if TRIPLE_MODE_ENABLED and entry_point == "brainstorming":
    signals = await extract_and_update_progress(message.content)
    grounding_reason = check_semantic_grounding(signals)
    if grounding_reason:
        await show_grounding_prompt(grounding_reason)
```

### Priority 1 (Important)

#### P1-1: Opportunity Bank Storage
**Why:** Users can "bank" opportunities but they're not persisted anywhere.

**What to build:**
```python
# New file: tools/opportunity_bank.py

@dataclass
class Opportunity:
    id: str
    user_id: str
    thread_id: str
    title: str
    description: str
    topics: List[str]
    signals: Dict[str, Any]
    created_at: datetime
    entry_point: str
    depth_when_banked: str

async def bank_opportunity(
    title: str,
    description: str,
    topics: List[str],
    signals: Dict
) -> Opportunity:
    """Save opportunity to Supabase."""
    opp = Opportunity(
        id=str(uuid4()),
        user_id=cl.user_session.get("user_id"),
        thread_id=cl.user_session.get("thread_id"),
        title=title,
        description=description,
        topics=topics,
        signals=signals,
        created_at=datetime.utcnow(),
        entry_point=cl.user_session.get("entry_point"),
        depth_when_banked=cl.user_session.get("exploration_depth"),
    )
    # Save to Supabase
    await supabase.table("opportunities").insert(opp.__dict__).execute()
    return opp

async def get_user_opportunities(user_id: str) -> List[Opportunity]:
    """Retrieve user's banked opportunities."""
    result = await supabase.table("opportunities").select("*").eq("user_id", user_id).execute()
    return [Opportunity(**row) for row in result.data]
```

**Files to create:** `tools/opportunity_bank.py`
**Files to modify:** `protocols/triple_mode.py` (handle_grounding_response bank action)

#### P1-2: DocumentUpload.jsx Component
**Why:** Document review entry point needs a dedicated upload UI.

**What to build:**
```jsx
// public/elements/DocumentUpload.jsx
export default function DocumentUpload() {
    const { disabled = false, acceptedTypes = [".pdf", ".docx", ".txt"] } = props || {};

    const handleUpload = (file) => {
        if (typeof callAction === 'function') {
            callAction({
                name: "document_uploaded",
                payload: {
                    filename: file.name,
                    type: file.type,
                    size: file.size
                }
            });
        }
    };

    // Drag-and-drop zone with file type filtering
    // Progress indicator
    // Preview for PDFs
}
```

#### P1-3: Graph Router Integration
**Why:** Agent suggestions should use Neo4j relationships, not just keywords.

**What to build:**
```python
# In mindrian_chat.py or protocols/triple_mode.py

from tools.graph_router import graph_score_agents

async def suggest_agent_for_context(message: str, entry_point: str) -> Optional[str]:
    """Use graph router to suggest best agent for current context."""
    # Get current conversation context
    history = cl.user_session.get("message_history", [])
    topics = cl.user_session.get("topics_explored", [])

    # Score agents using graph relationships
    scores = await graph_score_agents(
        query=message,
        topics=topics,
        entry_point=entry_point,
        current_agent=cl.user_session.get("bot_id")
    )

    # Return top suggestion if confidence > 0.7
    if scores and scores[0]["confidence"] > 0.7:
        return scores[0]["agent_id"]
    return None
```

### Priority 2 (Nice to Have)

#### P2-1: VentureProgress Sidebar
**Why:** Build Venture needs its own progress tracker (different from exploration).

**What to build:**
```jsx
// public/elements/VentureProgress.jsx
export default function VentureProgress() {
    const {
        currentStage = "pre_opportunity",
        stagesCompleted = [],
        toolsUsed = [],
        documentsCreated = [],
        validationScore = 0
    } = props || {};

    // Stage progress visualization
    // Tools checklist (BMC, JTBD, etc.)
    // Document inventory
    // Investment readiness score
}
```

#### P2-2: Claim Validation Pipeline
**Why:** Document review needs automated claim extraction and validation.

**What to build:**
```python
# tools/claim_validator.py

async def extract_claims(document_text: str) -> List[Claim]:
    """Extract factual claims from document."""
    # Use LangExtract for statistics, assumptions
    # Use LLM for implicit claims
    pass

async def validate_claim(claim: Claim) -> ValidationResult:
    """Validate a claim against knowledge base and web."""
    # Check against Neo4j facts
    # Check against File Search
    # Optionally check web (Tavily)
    pass

async def generate_validation_report(claims: List[Claim]) -> str:
    """Generate markdown report of validated claims."""
    pass
```

#### P2-3: Workshop Roadmap Sidebar
**Why:** Document review in workshop mode needs phase visualization.

**What to build:**
```jsx
// public/elements/WorkshopRoadmap.jsx (may already exist)
// Ensure it works with document_review entry point
// Add document-specific phases:
// 1. Document Analysis
// 2. Claim Extraction
// 3. Red Team Critique
// 4. Synthesis & Recommendations
```

### Priority 3 (Future)

#### P3-1: Multi-Agent Orchestration
**Why:** Complex queries should trigger multiple agents in sequence.

**Reference:** `agents/multi_agent_graph.py` already exists - integrate with Agent Registry.

#### P3-2: Agent Handoff Visualization
**Why:** Users should see when agents are collaborating.

**What to build:** Real-time handoff indicator showing agent-to-agent communication.

#### P3-3: Exploration Analytics Dashboard
**Why:** Track user exploration patterns across sessions.

**What to build:** Admin dashboard showing:
- Common exploration paths
- Average depth before banking
- Entry point distribution
- Agent utilization

---

## Implementation Guides

### Adding a New Agent with Full Mindrian Intelligence

```python
from protocols import create_agent_with_defaults, AgentRole

# This ensures the agent gets GraphRAG, LangExtract, ContextStore, FileSearch
new_agent = create_agent_with_defaults(
    id="my_new_agent",
    name="My New Agent",
    description="What this agent does",
    icon="🆕",
    roles=[AgentRole.WORKSHOP],  # or ORCHESTRATOR, SUB_AGENT, SERVICE
    entry_points=["brainstorming"],  # which entry points can access
    venture_stages=["opportunity_identified"],  # which stages can access
    can_call=["research", "graphrag"],  # agents this one can call
    called_by=["lawrence"],  # agents that can call this one
    # Additional capabilities beyond defaults:
    additional_capabilities=[AgentCapability.RESEARCH, AgentCapability.NEO4J],
    # Workshop phases if applicable:
    has_phases=True,
    phases=["Introduction", "Analysis", "Synthesis"],
)

# Don't forget to:
# 1. Create prompts/my_new_agent.py with system prompt
# 2. Add to BOTS dict in mindrian_chat.py
# 3. Add starters, chat profile, action callback
```

### Adding a New Entry Point

```python
# 1. Update entry_point_router.py
ENTRY_POINTS["my_entry_point"] = {
    "name": "My Entry Point",
    "description": "...",
    "welcome_message": "...",
    "default_mode": "sandbox",
    "keywords": ["keyword1", "keyword2"],
}

# 2. Update auto_detect_entry_point in triple_mode.py
# Add detection logic in _analyze_signals_for_entry_point()

# 3. Create JSX component if needed
# public/elements/MyEntryPointSelector.jsx

# 4. Update handle_entry_point_selection()
# Add any entry-point-specific initialization

# 5. Update get_entry_point_buttons()
# Add entry-point-specific action buttons
```

### Testing a Grounding Trigger

```python
# Test in Python REPL:
from protocols.triple_mode import check_semantic_grounding
from tools.langextract import instant_extract

# Simulate message that should trigger pattern_check
message = """
The problem is urban farming is expensive.
Another problem is vertical farming needs lots of energy.
A third problem is consumers don't trust indoor-grown produce.
"""
signals = instant_extract(message)
reason = check_semantic_grounding(signals)
print(f"Grounding reason: {reason}")  # Should be "pattern_check"
```

---

## Testing Checklist

### Phase 1: Bug Fixes
- [ ] EntryPointSelector calls `callAction` (not `window.Chainlit`)
- [ ] ModeToggle sends `mode_or_stage` callback with `{mode: "sandbox"}` or `{mode: "workshop"}`
- [ ] GroundingPrompt sends `grounding_response` callback
- [ ] VentureStageSelector sends `mode_or_stage` callback with `{stage: "..."}`
- [ ] ExplorationProgress displays in sidebar (not inline)

### Phase 2: LangExtract Integration
- [ ] First message with attachment → document_review (confidence > 0.9)
- [ ] First message "I want to explore trends in AI" → brainstorming (confidence > 0.7)
- [ ] First message with 100+ words + problem focus → document_review
- [ ] First message with short question → show selector (low confidence)
- [ ] 3+ problems without causation → pattern_check grounding
- [ ] Assumptions + causation + no problem statement → synthesis grounding
- [ ] Solutions + forward-looking + data → bank_prompt grounding

### Phase 3: Agent Registry
- [ ] All 12 agents registered
- [ ] `get_agents_by_role(AgentRole.ORCHESTRATOR)` returns Lawrence, Larry Playground
- [ ] `get_agents_for_entry_point("brainstorming")` returns exploration-capable agents
- [ ] `create_agent_with_defaults()` includes all 4 default capabilities
- [ ] `can_agent_call("lawrence", "tta")` returns True
- [ ] `can_agent_call("tta", "lawrence")` returns False (unless explicitly allowed)

### Integration Tests
- [ ] New chat → auto-detection works
- [ ] Entry point selection → welcome message + appropriate UI
- [ ] Mode toggle → mode changes and persists
- [ ] Bank opportunity → counter increments, sidebar updates
- [ ] Page refresh → state restored (once P0-1 implemented)

---

## Known Issues & Warnings

### Validation Warnings (Expected)
```
Agent Registry: lawrence.can_call references unknown agent: graphrag
Agent Registry: jtbd.can_call references unknown agent: graphrag
Agent Registry: jtbd.called_by references unknown agent: stage_router
Agent Registry: ackoff.can_call references unknown agent: graphrag
```

These warnings appear because some agents reference `graphrag` and `stage_router` which aren't registered yet. They'll be resolved when those service agents are implemented.

### JSX Component Caveats

1. **No TypeScript** - Chainlit custom elements must be `.jsx`, not `.tsx`
2. **Global props** - Use `const { prop } = props || {}` not function arguments
3. **Global APIs** - Check if API exists before calling: `if (typeof callAction === 'function')`
4. **No React import** - React is globally available, don't import it

### Session State Caveats

1. **No persistence yet** - State resets on page refresh (P0-1 needed)
2. **Thread metadata** - Use Chainlit's thread metadata for persistence, not custom DB
3. **Element references** - `progress_element` reference may become stale after refresh

---

## Research Brief Archive

### Original Requirements (from user)

**Triple-Mode Entry Points:**
1. **Brainstorming** - Exploration sandbox with opportunity banking
2. **Document Review** - Upload-triggered analysis with red teaming
3. **Build Venture** - Stage-based venture building with tool progression

**Mode Toggle:**
- Sandbox (free exploration) ↔ Workshop (guided phases)
- Should be available within brainstorming and document_review

**Semantic Grounding:**
- Replace turn-based grounding (broken - resets on refresh)
- Use LangExtract signals to detect when user needs grounding
- Content-aware, not count-based

**Agent Registry:**
- All new agents should have full Mindrian intelligence
- Agents can be orchestrators, workshops, sub-agents, or services
- Capabilities shared: GraphRAG, LangExtract, ContextStore, FileSearch

### Chainlit Expert Review Issues (Fixed)

| Issue | Problem | Fix |
|-------|---------|-----|
| TM-001 | `window.Chainlit` doesn't exist | Use global `callAction` |
| TM-002 | 7 callbacks too many | Consolidate to 3 |
| TM-003 | Turn-based grounding resets | Use semantic signals |
| TM-004 | Elements update wrong | Use `updateElement` API |
| TM-005 | Display mode wrong | Use `display="side"` for sidebar |
| TM-006 | Timing issues | Send elements with messages |

### LangExtract Signals Reference

```python
signals = instant_extract(text)
# Returns:
{
    "content_type": "exploratory" | "problem_focused" | "solution_focused" | "general",
    "counts": {
        "problems": int,
        "solutions": int,
        "assumptions": int,
        "causation": int,
        "questions": int,
        "trends": int,
    },
    "quality_signals": {
        "has_pws_elements": bool,
        "has_data": bool,
        "has_sources": bool,
        "has_uncertainty": bool,
        "is_forward_looking": bool,
    },
    "samples": {
        "problems": List[str],
        "trends": List[str],
        # etc.
    },
    "word_count": int,
}
```

---

## Quick Reference Commands

```bash
# Verify protocols load correctly
python3 -c "from protocols import AgentRole, TRIPLE_MODE_ENABLED, AGENT_REGISTRY; print(list(AGENT_REGISTRY.keys()))"

# Check LangExtract is working
python3 -c "from tools.langextract import instant_extract; print(instant_extract('What trends are disrupting healthcare?'))"

# Run health check
python3 scripts/health_check.py

# Start local dev server
chainlit run mindrian_chat.py --watch
```

---

## Neo4j Schema Requirements

### Core Schema (Should Already Exist)

| Node Type | Purpose | Expected Count |
|-----------|---------|----------------|
| `Concept` | Knowledge entities | ~8,000+ |
| `Community` | GraphRAG clusters | ~39 |
| `Framework` | PWS frameworks | 10-20+ |
| `CynefinDomain` | Complexity classification | 5 |
| `ProcessStep` | Framework workflow steps | Varies |

| Relationship | Purpose | Expected Count |
|--------------|---------|----------------|
| `CO_OCCURS` | Co-occurrence edges | ~123K |
| `RELATED_TO` | Semantic similarity | Varies |
| `CONTAINS` | Framework → Steps | Varies |
| `APPLIES_TO` | Framework → Domain | Varies |

### New Schema (Triple-Mode Required)

#### Bot Nodes (For Agent Routing)
```cypher
// Create Bot nodes matching Agent Registry
CREATE (b:Bot {
    id: 'lawrence',
    name: 'Lawrence',
    description: 'PWS thinking partner',
    role: 'orchestrator',
    icon: '🧠'
})
// ... for each registered agent
```

#### VentureStage Nodes (For Build Venture)
```cypher
CREATE (v:VentureStage {
    id: 'pre_opportunity',
    name: 'Pre-Opportunity',
    description: 'Still looking for problems to solve',
    order: 1
})
CREATE (v:VentureStage {
    id: 'opportunity_identified',
    name: 'Opportunity Identified',
    description: 'Found a problem, need to understand it deeply',
    order: 2
})
CREATE (v:VentureStage {
    id: 'well_defined_problem',
    name: 'Well-Defined Problem',
    description: 'Problem is clear, designing the business',
    order: 3
})
CREATE (v:VentureStage {
    id: 'ready_to_build',
    name: 'Ready to Build',
    description: 'Problem validated, solution designed',
    order: 4
})
```

#### Stage-Framework Relationships
```cypher
// Pre-Opportunity uses exploration frameworks
MATCH (v:VentureStage {id: 'pre_opportunity'})
MATCH (f:Framework) WHERE f.name IN ['Trending to the Absurd', 'Beautiful Question']
CREATE (v)-[:USES_FRAMEWORK {order: 1, priority: 'primary'}]->(f)

// Opportunity Identified uses validation frameworks
MATCH (v:VentureStage {id: 'opportunity_identified'})
MATCH (f:Framework) WHERE f.name IN ['Jobs to Be Done', 'Problem Validation']
CREATE (v)-[:USES_FRAMEWORK {order: 1, priority: 'primary'}]->(f)

// Well-Defined Problem uses business design frameworks
MATCH (v:VentureStage {id: 'well_defined_problem'})
MATCH (f:Framework) WHERE f.name IN ['Business Model Canvas', 'S-Curve Analysis', 'Ackoff DIKW']
CREATE (v)-[:USES_FRAMEWORK]->(f)

// Ready to Build uses execution frameworks
MATCH (v:VentureStage {id: 'ready_to_build'})
MATCH (f:Framework) WHERE f.name IN ['Red Teaming', 'Investment Readiness']
CREATE (v)-[:USES_FRAMEWORK]->(f)
```

#### Stage-Bot Relationships
```cypher
// Link stages to recommended bots
MATCH (v:VentureStage {id: 'pre_opportunity'})
MATCH (b:Bot) WHERE b.id IN ['lawrence', 'tta', 'beautiful_question']
CREATE (v)-[:RECOMMENDED_BOT {priority: 1}]->(b)

MATCH (v:VentureStage {id: 'opportunity_identified'})
MATCH (b:Bot) WHERE b.id IN ['jtbd', 'scenario']
CREATE (v)-[:RECOMMENDED_BOT]->(b)

MATCH (v:VentureStage {id: 'well_defined_problem'})
MATCH (b:Bot) WHERE b.id IN ['ackoff', 'scurve']
CREATE (v)-[:RECOMMENDED_BOT]->(b)

MATCH (v:VentureStage {id: 'ready_to_build'})
MATCH (b:Bot) WHERE b.id IN ['redteam', 'knowns']
CREATE (v)-[:RECOMMENDED_BOT]->(b)
```

#### EntryPoint Nodes (For Routing)
```cypher
CREATE (e:EntryPoint {
    id: 'brainstorming',
    name: 'Brainstorming',
    description: 'Free exploration of trends and opportunities',
    default_mode: 'sandbox'
})
CREATE (e:EntryPoint {
    id: 'document_review',
    name: 'Document Review',
    description: 'Analysis of uploaded documents',
    default_mode: 'workshop'
})
CREATE (e:EntryPoint {
    id: 'build_venture',
    name: 'Build Venture',
    description: 'Stage-based venture building',
    default_mode: 'sandbox'
})
```

#### Topic Nodes (For Exploration Tracking)
```cypher
// Topics are created dynamically from LangExtract
CREATE (t:Topic {
    name: 'AI education',
    first_seen: datetime(),
    exploration_count: 0
})
```

#### Insight Nodes (For Opportunity Bank)
```cypher
CREATE (i:Insight {
    id: 'uuid-here',
    content: 'User insight text',
    type: 'pattern|synthesis|opportunity',
    created_at: datetime(),
    grounding_reason: 'pattern_check'
})
```

### Migration Scripts

Run these in order to set up Triple-Mode schema:

```bash
# 1. Create Bot nodes
python scripts/neo4j_migrate_bots.py

# 2. Create VentureStage nodes
python scripts/neo4j_migrate_stages.py

# 3. Create EntryPoint nodes
python scripts/neo4j_migrate_entry_points.py

# 4. Link stages to frameworks and bots
python scripts/neo4j_migrate_stage_links.py
```

---

## New Agent Rules

### Rule 1: All Agents Get Default Capabilities

Every new agent MUST have these capabilities (enforced by `create_agent_with_defaults()`):

| Capability | Purpose | Required |
|------------|---------|----------|
| `GRAPHRAG` | Neo4j + vector hybrid retrieval | ✅ Always |
| `LANGEXTRACT` | Zero-latency signal extraction | ✅ Always |
| `CONTEXT_STORE` | Cross-bot memory | ✅ Always |
| `FILE_SEARCH` | Semantic document search | ✅ Always |

### Rule 2: Role Determines Routing

| Role | Can Call | Called By | Returns To User |
|------|----------|-----------|-----------------|
| `ORCHESTRATOR` | Anyone | Users only | Yes |
| `WORKSHOP` | Services, Sub-Agents | Orchestrators | Yes |
| `SUB_AGENT` | Services | Orchestrators, Workshops | Yes |
| `SERVICE` | None | Anyone | No (data only) |

### Rule 3: Entry Point Restrictions

| Entry Point | Allowed Roles | Example Agents |
|-------------|---------------|----------------|
| `brainstorming` | Orchestrator, Workshop | lawrence, tta, beautiful_question |
| `document_review` | Orchestrator, Workshop | lawrence, redteam, ackoff |
| `build_venture` | Orchestrator, Workshop | jtbd, scurve, knowns |

### Rule 4: Venture Stage Restrictions

| Stage | Primary Agents | Supporting Agents |
|-------|----------------|-------------------|
| `pre_opportunity` | lawrence, tta | beautiful_question, scenario |
| `opportunity_identified` | jtbd | scenario, research |
| `well_defined_problem` | ackoff, scurve | redteam |
| `ready_to_build` | redteam, knowns | pws_grading |

### Rule 5: Agent Registration Checklist

When creating a new agent, MUST complete:

```python
# 1. Register with Agent Registry
from protocols import create_agent_with_defaults, AgentRole, AgentCapability

new_agent = create_agent_with_defaults(
    id="my_agent",
    name="My Agent",
    description="...",
    icon="🆕",
    roles=[AgentRole.WORKSHOP],
    entry_points=["brainstorming"],
    venture_stages=["opportunity_identified"],
    can_call=["research", "graphrag"],
    called_by=["lawrence"],
)

# 2. Create system prompt
# prompts/my_agent.py

# 3. Add to BOTS dict
# mindrian_chat.py → BOTS["my_agent"] = {...}

# 4. Add chat profile
# mindrian_chat.py → chat_profiles()

# 5. Add starters (4 required)
# mindrian_chat.py → STARTERS["my_agent"]

# 6. Add switch callback
# mindrian_chat.py → @cl.action_callback("switch_to_my_agent")

# 7. Add to Neo4j
# CREATE (:Bot {id: 'my_agent', name: 'My Agent', ...})
```

### Rule 6: Neo4j Sync Required

Agent Registry and Neo4j MUST stay in sync:

```python
# After registering agent in code:
async def sync_agent_to_neo4j(agent: AgentConfig):
    """Sync agent config to Neo4j for graph routing."""
    cypher = """
    MERGE (b:Bot {id: $id})
    SET b.name = $name,
        b.description = $description,
        b.role = $role,
        b.icon = $icon,
        b.capabilities = $capabilities
    """
    await neo4j_session.run(cypher, {
        "id": agent.id,
        "name": agent.name,
        "description": agent.description,
        "role": agent.roles[0].value if agent.roles else "workshop",
        "icon": agent.icon,
        "capabilities": [c.value for c in agent.capabilities]
    })
```

---

## Changelog

### 2026-02-02
- Created `protocols/agent_registry.py` with full agent registration system
- Created `protocols/triple_mode.py` with LangExtract-powered detection
- Fixed 5 JSX components to use correct Chainlit APIs
- Consolidated 7 callbacks to 3
- Updated `protocols/__init__.py` with all exports
- Added `TRIPLE_MODE_ENABLED` environment variable support
- Created `scripts/neo4j_triple_mode_migration.py` for schema setup
- Created `R&D/25_triple_mode_architecture/neo4j_analysis.py` for schema verification
- Documented Neo4j schema requirements and new agent rules

---

## Next Steps (Prioritized)

### ✅ COMPLETED: mindrian_chat.py Integration
All integration is done:
- Imports at lines 27-44
- `init_triple_mode_session()` at line 2989
- 3 callbacks at lines 3972-4000
- Auto-detection at line 7217
- Semantic grounding at line 8085

### Immediate (Run When Neo4j Accessible)
```bash
# 1. Verify current Neo4j state
python R&D/25_triple_mode_architecture/neo4j_analysis.py

# 2. Run migration to create Triple-Mode schema
python scripts/neo4j_triple_mode_migration.py

# 3. Verify migration success
python R&D/25_triple_mode_architecture/neo4j_analysis.py
```

### ✅ COMPLETED: Session Persistence (P0-1)
State now persists across page refresh:
- `get_triple_mode_state()` - Get state for persistence
- `restore_triple_mode_state(metadata)` - Restore from thread metadata
- `persist_triple_mode_state()` - Save to thread metadata (called automatically)
- Updated `on_chat_resume` in mindrian_chat.py

### ✅ COMPLETED: Opportunity Bank (P1-1)
Already existed at `tools/opportunity_bank.py` with full implementation:
- Supabase table storage (primary)
- Neo4j graph storage
- FileSearch document export
- Extraction using Gemini
- Integrated with Triple-Mode `handle_grounding_response` bank action

---

## Quick Commands

```bash
# Verify protocols package
python3 -c "from protocols import AGENT_REGISTRY, TRIPLE_MODE_ENABLED; print(f'Agents: {len(AGENT_REGISTRY)}, TripleMode: {TRIPLE_MODE_ENABLED}')"

# Check LangExtract
python3 -c "from tools.langextract import instant_extract; print(instant_extract('What problems exist in healthcare?'))"

# Run health check
python3 scripts/health_check.py

# Start local server
chainlit run mindrian_chat.py --watch
```

---

## Files Created/Modified

| File | Status | Purpose |
|------|--------|---------|
| `protocols/agent_registry.py` | ✅ NEW | Agent registration system |
| `protocols/triple_mode.py` | ✅ NEW | Entry point detection, grounding |
| `protocols/__init__.py` | ✅ UPDATED | Package exports |
| `public/elements/EntryPointSelector.jsx` | ✅ FIXED | Uses callAction |
| `public/elements/ModeToggle.jsx` | ✅ FIXED | Uses mode_or_stage |
| `public/elements/GroundingPrompt.jsx` | ✅ FIXED | Uses grounding_response |
| `public/elements/VentureStageSelector.jsx` | ✅ FIXED | Uses mode_or_stage |
| `public/elements/ExplorationProgress.jsx` | ✅ FIXED | display="side" |
| `scripts/neo4j_triple_mode_migration.py` | ✅ NEW | Neo4j schema setup |
| `R&D/25_triple_mode_architecture/README.md` | ✅ NEW | This documentation |
| `R&D/25_triple_mode_architecture/neo4j_analysis.py` | ✅ NEW | Schema verification |
| `mindrian_chat.py` | ✅ COMPLETE | Fully integrated |

---

## Next Session Checklist

When returning to this work:

1. [ ] Run `python3 scripts/health_check.py`
2. [ ] Verify protocols load: `python3 -c "from protocols import AGENT_REGISTRY; print(len(AGENT_REGISTRY))"`
3. [ ] Run Neo4j migration when connected: `python scripts/neo4j_triple_mode_migration.py`
4. [x] ~~Integrate with mindrian_chat.py~~ ✅ DONE
5. [ ] Test entry point detection flow (run app locally)
6. [ ] Test semantic grounding triggers
7. [x] ~~Implement session persistence (P0-1)~~ ✅ DONE
8. [x] ~~Implement opportunity bank storage (P1-1)~~ ✅ DONE (already existed, integrated)
9. [ ] Run Neo4j migration when connected
10. [ ] Test full flow end-to-end
11. [ ] Update this README when completing items
