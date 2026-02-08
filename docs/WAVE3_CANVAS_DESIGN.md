# Wave 3: Idea Canvas - Design Specification

> **Status:** DESIGN ONLY - Not yet implemented
> **Author:** Claude Architecture Session
> **Date:** 2026-02-08
> **Related Files:**
> - `/home/jsagi/Mindrian/mindrian-deploy/mindrian_chat.py`
> - `/home/jsagi/Mindrian/mindrian-deploy/tools/langextract.py`
> - `/home/jsagi/Mindrian/mindrian-deploy/utils/diagrams.py`
> - `/home/jsagi/Mindrian/mindrian-deploy/public/elements/MermaidDiagram.jsx`

---

## 1. Overview

The Idea Canvas is a visual, real-time workspace that automatically extracts and displays structured ideas from conversation. Unlike static diagrams, it:

- **Auto-populates** from conversation in real-time
- **Supports spatial arrangement** with drag-and-drop
- **Enables curation** via star/prune actions
- **Tracks provenance** linking ideas back to source messages
- **Persists across sessions** via Supabase storage

### Design Philosophy

1. **Invisible extraction** - Ideas appear without user effort
2. **Non-intrusive display** - Canvas updates smoothly, never interrupts flow
3. **Actionable curation** - Star promising ideas, prune dead ends
4. **Branch-aware** - Ideas track which exploration branch they came from
5. **Export-ready** - Canvas can be exported as image or markdown

---

## 2. IdeaNode Data Structure

### TypedDict Definition

```python
# tools/idea_canvas.py

from typing import TypedDict, Optional, Literal, Dict, List
from datetime import datetime

class Position(TypedDict):
    x: float
    y: float

class IdeaNode(TypedDict):
    """A single extracted idea on the canvas."""
    node_id: str                    # UUID for this idea
    content: str                    # The idea text (1-3 sentences)
    node_type: Literal[
        "problem",      # Pain point or challenge identified
        "insight",      # Aha moment or realization
        "assumption",   # Stated or hidden assumption
        "decision",     # Choice or commitment made
        "question"      # Open question to explore
    ]
    branch_id: str                  # Which exploration branch (for multi-path sessions)
    message_index: int              # Which message generated this (0-indexed)
    message_id: Optional[str]       # Chainlit message ID for navigation
    parent_node_id: Optional[str]   # Hierarchy - which idea led to this one
    child_node_ids: List[str]       # Ideas that emerged from this one
    confidence: float               # 0.0-1.0, how confident the extraction is
    starred: bool                   # User marked as promising
    pruned: bool                    # User marked as dead end
    created_at: str                 # ISO timestamp
    source_role: Literal["user", "assistant"]  # Who generated the source message
    tags: List[str]                 # Optional user-added tags
    metadata: Dict                  # Extensible metadata (framework, phase, etc.)


class CanvasLayout(TypedDict):
    """Layout configuration for the canvas."""
    positions: Dict[str, Position]  # node_id -> x,y coordinates
    zoom: float                     # Current zoom level (0.5 - 2.0)
    pan_x: float                    # Horizontal pan offset
    pan_y: float                    # Vertical pan offset


class CanvasState(TypedDict):
    """Complete canvas state for a session."""
    session_id: str
    idea_nodes: Dict[str, IdeaNode]  # node_id -> IdeaNode
    layout: CanvasLayout
    view_mode: Literal["tree", "cluster", "timeline", "type"]
    filters: Dict[str, bool]         # {"problems": True, "starred": True, etc.}
    current_branch_id: str
    last_updated: str
```

### Node Type Colors & Icons

| Type | Color | Icon | Description |
|------|-------|------|-------------|
| `problem` | Red `#ef4444` | AlertTriangle | Pain point identified |
| `insight` | Yellow `#eab308` | Lightbulb | Realization or aha moment |
| `assumption` | Purple `#a855f7` | HelpCircle | Stated or hidden assumption |
| `decision` | Green `#22c55e` | CheckCircle | Commitment made |
| `question` | Blue `#3b82f6` | MessageCircle | Open question |

---

## 3. Extraction Logic Design

### Two-Stage Extraction (Following LangExtract Pattern)

#### Stage 1: Instant Extraction (<5ms, regex-based)

Runs synchronously on every message. Detects signals for each node type:

```python
# tools/idea_canvas.py

IDEA_PATTERNS = {
    "problem": [
        r"\b(?:problem|issue|challenge|pain point|struggle|difficulty|obstacle)\b",
        r"\b(?:frustrated|stuck|blocked|can't|unable to)\b",
        r"what's (?:wrong|broken|not working)",
    ],
    "insight": [
        r"\b(?:realized?|discovered?|noticed|interesting(?:ly)?)\b",
        r"\b(?:aha|eureka|breakthrough|key insight)\b",
        r"(?:that explains|now I (?:see|understand))",
    ],
    "assumption": [
        r"\b(?:assume|assuming|assumption|presume|suppose)\b",
        r"\b(?:if|given that|based on the premise)\b",
        r"\b(?:we believe|I think|probably|likely)\b",
    ],
    "decision": [
        r"\b(?:decided?|choosing|committed|going with)\b",
        r"\b(?:let's go with|moving forward with|our approach)\b",
        r"(?:the plan is|we will|action item)",
    ],
    "question": [
        r"[^.!]*\?$",  # Sentences ending in ?
        r"\b(?:wondering|curious|unclear|not sure)\b",
        r"(?:what if|how might|could we)",
    ],
}

def instant_idea_signals(text: str) -> Dict[str, List[str]]:
    """
    Fast pattern matching to detect potential ideas.
    Returns dict of {node_type: [matched_snippets]}.
    """
    signals = {}
    for node_type, patterns in IDEA_PATTERNS.items():
        matches = []
        for pattern in patterns:
            found = re.findall(f".{{0,50}}{pattern}.{{0,50}}", text, re.IGNORECASE)
            matches.extend(found)
        if matches:
            signals[node_type] = matches[:3]  # Max 3 samples per type
    return signals
```

#### Stage 2: Background Extraction (LLM-based, async)

Runs after response is sent, uses Gemini Flash for structured extraction:

```python
async def background_extract_ideas(
    message_content: str,
    message_role: str,
    message_index: int,
    message_id: str,
    branch_id: str,
    conversation_context: str = ""
) -> List[IdeaNode]:
    """
    Deep LLM extraction of ideas from a message.
    Runs in background - does NOT block user response.
    """
    extraction_prompt = f"""Analyze this message and extract discrete ideas.

MESSAGE ({message_role}):
{message_content[:3000]}

CONVERSATION CONTEXT:
{conversation_context[:1000]}

For each distinct idea, classify it:
- problem: A pain point, challenge, or obstacle identified
- insight: A realization, aha moment, or new understanding
- assumption: An explicit or implicit assumption being made
- decision: A choice, commitment, or action decided upon
- question: An open question that needs exploration

Return JSON array:
[
  {{
    "content": "The idea in 1-2 sentences",
    "node_type": "problem|insight|assumption|decision|question",
    "confidence": 0.0-1.0,
    "parent_hint": "Brief description of related prior idea if any"
  }}
]

Extract 0-5 ideas per message. Only extract genuinely distinct ideas.
Return ONLY valid JSON array, no explanation."""

    # Use Gemini Flash for speed
    response = await gemini_client.generate_content(
        model="gemini-2.0-flash",
        contents=extraction_prompt,
        config={"temperature": 0.1, "max_output_tokens": 1000}
    )

    # Parse and create IdeaNodes
    ideas_data = json.loads(response.text)
    nodes = []
    for idea in ideas_data:
        node = IdeaNode(
            node_id=str(uuid.uuid4()),
            content=idea["content"],
            node_type=idea["node_type"],
            branch_id=branch_id,
            message_index=message_index,
            message_id=message_id,
            parent_node_id=None,  # Resolved later via parent_hint
            child_node_ids=[],
            confidence=idea["confidence"],
            starred=False,
            pruned=False,
            created_at=datetime.utcnow().isoformat(),
            source_role=message_role,
            tags=[],
            metadata={}
        )
        nodes.append(node)

    return nodes
```

### Parent-Child Linking

After extraction, attempt to link new ideas to existing ones:

```python
def link_idea_parents(
    new_nodes: List[IdeaNode],
    existing_nodes: Dict[str, IdeaNode],
    parent_hints: List[str]
) -> None:
    """
    Use embedding similarity to link new ideas to parent ideas.
    Modifies nodes in place.
    """
    if not existing_nodes:
        return

    # Use simple keyword overlap for MVP
    # Could upgrade to embedding similarity later
    for i, node in enumerate(new_nodes):
        if i < len(parent_hints) and parent_hints[i]:
            hint = parent_hints[i].lower()
            best_match = None
            best_score = 0.0

            for existing_id, existing_node in existing_nodes.items():
                if existing_node["pruned"]:
                    continue
                # Simple word overlap score
                hint_words = set(hint.split())
                content_words = set(existing_node["content"].lower().split())
                overlap = len(hint_words & content_words) / max(len(hint_words), 1)

                if overlap > best_score and overlap > 0.3:
                    best_score = overlap
                    best_match = existing_id

            if best_match:
                node["parent_node_id"] = best_match
                existing_nodes[best_match]["child_node_ids"].append(node["node_id"])
```

---

## 4. Canvas State Management

### Session State Schema

```python
# In mindrian_chat.py - session state additions

async def init_canvas_state(session_id: str) -> CanvasState:
    """Initialize canvas state for a new session."""
    return CanvasState(
        session_id=session_id,
        idea_nodes={},
        layout=CanvasLayout(
            positions={},
            zoom=1.0,
            pan_x=0,
            pan_y=0
        ),
        view_mode="tree",
        filters={
            "problem": True,
            "insight": True,
            "assumption": True,
            "decision": True,
            "question": True,
            "starred_only": False,
            "hide_pruned": True
        },
        current_branch_id="main",
        last_updated=datetime.utcnow().isoformat()
    )

# Attach to cl.user_session
@cl.on_chat_start
async def on_chat_start():
    # ... existing init code ...

    session_id = cl.user_session.get("session_id") or str(uuid.uuid4())
    canvas_state = await init_canvas_state(session_id)
    cl.user_session.set("canvas_state", canvas_state)
```

### State Persistence (Supabase)

```python
CANVAS_FOLDER = "canvas_states"

async def save_canvas_state(state: CanvasState) -> bool:
    """Persist canvas state to Supabase."""
    try:
        from utils.storage import get_supabase_client, SUPABASE_BUCKET

        client = get_supabase_client()
        if not client:
            return False

        json_content = json.dumps(state, indent=2, default=str)
        storage_path = f"{CANVAS_FOLDER}/{state['session_id']}.json"

        client.storage.from_(SUPABASE_BUCKET).upload(
            path=storage_path,
            file=json_content.encode('utf-8'),
            file_options={"content-type": "application/json", "upsert": "true"}
        )
        return True
    except Exception as e:
        print(f"Canvas save error: {e}")
        return False

async def load_canvas_state(session_id: str) -> Optional[CanvasState]:
    """Load canvas state from Supabase."""
    try:
        from utils.storage import get_supabase_client, SUPABASE_BUCKET

        client = get_supabase_client()
        if not client:
            return None

        storage_path = f"{CANVAS_FOLDER}/{session_id}.json"
        result = client.storage.from_(SUPABASE_BUCKET).download(storage_path)

        if result:
            return json.loads(result.decode('utf-8'))
        return None
    except Exception:
        return None
```

---

## 5. IdeaCanvas.jsx Component Specification

### Component Location

`/home/jsagi/Mindrian/mindrian-deploy/public/elements/IdeaCanvas.jsx`

### Props Interface

```javascript
/**
 * IdeaCanvas - Visual workspace for extracted ideas
 *
 * Props (injected globally by Chainlit):
 * - nodes: Array of IdeaNode objects
 * - layout: CanvasLayout object (positions, zoom, pan)
 * - viewMode: "tree" | "cluster" | "timeline" | "type"
 * - filters: Object with boolean flags for each node type
 * - currentBranchId: String identifying current exploration branch
 * - editable: Boolean to enable/disable interactions
 * - onNodeClick: Callback name for node selection
 * - title: Optional canvas title
 */
```

### Component Structure

```jsx
export default function IdeaCanvas() {
  const { updateElement, callAction, sendUserMessage } = window.Chainlit || {}

  const {
    nodes = [],
    layout = { positions: {}, zoom: 1, pan_x: 0, pan_y: 0 },
    viewMode = "tree",
    filters = {},
    currentBranchId = "main",
    editable = true,
    title = "Idea Canvas"
  } = props || {}

  // Local state
  const [selectedNode, setSelectedNode] = React.useState(null)
  const [hoveredNode, setHoveredNode] = React.useState(null)
  const [localPositions, setLocalPositions] = React.useState(layout.positions)
  const [isDragging, setIsDragging] = React.useState(false)
  const [dragNode, setDragNode] = React.useState(null)
  const [zoom, setZoom] = React.useState(layout.zoom)
  const [pan, setPan] = React.useState({ x: layout.pan_x, y: layout.pan_y })
  const [filterState, setFilterState] = React.useState(filters)

  // Canvas dimensions
  const canvasWidth = 800
  const canvasHeight = 600

  // Node colors
  const typeColors = {
    problem: { bg: '#fef2f2', border: '#ef4444', text: '#b91c1c' },
    insight: { bg: '#fefce8', border: '#eab308', text: '#a16207' },
    assumption: { bg: '#faf5ff', border: '#a855f7', text: '#7c3aed' },
    decision: { bg: '#f0fdf4', border: '#22c55e', text: '#15803d' },
    question: { bg: '#eff6ff', border: '#3b82f6', text: '#1d4ed8' }
  }

  // Filter visible nodes
  const visibleNodes = React.useMemo(() => {
    return nodes.filter(node => {
      if (filterState.hide_pruned && node.pruned) return false
      if (filterState.starred_only && !node.starred) return false
      if (!filterState[node.node_type]) return false
      return true
    })
  }, [nodes, filterState])

  // Auto-layout calculation
  const calculateLayout = React.useCallback(() => {
    // Implementation depends on viewMode
    // tree: hierarchical layout
    // cluster: force-directed by type
    // timeline: left-to-right by message_index
    // type: grouped columns by node_type
  }, [viewMode, visibleNodes])

  // ... Drag handlers, render logic ...
}
```

### Key Features

#### 1. Drag-and-Drop Repositioning

```jsx
const handleDragStart = (e, nodeId) => {
  if (!editable) return
  setIsDragging(true)
  setDragNode(nodeId)
  e.dataTransfer.effectAllowed = 'move'
}

const handleDrag = (e) => {
  if (!isDragging || !dragNode) return
  const rect = canvasRef.current.getBoundingClientRect()
  const x = (e.clientX - rect.left - pan.x) / zoom
  const y = (e.clientY - rect.top - pan.y) / zoom

  setLocalPositions(prev => ({
    ...prev,
    [dragNode]: { x, y }
  }))
}

const handleDragEnd = () => {
  setIsDragging(false)
  setDragNode(null)

  // Persist new positions
  if (callAction) {
    callAction({
      name: 'canvas_layout_updated',
      payload: { positions: localPositions }
    })
  }
}
```

#### 2. Click to View Source Message

```jsx
const handleNodeClick = (node) => {
  setSelectedNode(node)

  if (callAction) {
    callAction({
      name: 'canvas_node_selected',
      payload: {
        node_id: node.node_id,
        message_id: node.message_id,
        message_index: node.message_index
      }
    })
  }
}
```

#### 3. Star/Prune Actions

```jsx
const handleStar = (nodeId, e) => {
  e.stopPropagation()
  if (callAction) {
    callAction({
      name: 'star_idea',
      payload: { node_id: nodeId }
    })
  }
}

const handlePrune = (nodeId, e) => {
  e.stopPropagation()
  if (callAction) {
    callAction({
      name: 'prune_idea',
      payload: { node_id: nodeId }
    })
  }
}
```

#### 4. Filter Controls

```jsx
const FilterBar = () => (
  <div style={filterBarStyle}>
    {Object.entries(typeColors).map(([type, colors]) => (
      <button
        key={type}
        onClick={() => toggleFilter(type)}
        style={{
          ...filterButtonStyle,
          backgroundColor: filterState[type] ? colors.bg : '#f5f5f5',
          borderColor: filterState[type] ? colors.border : '#e0e0e0',
          opacity: filterState[type] ? 1 : 0.5
        }}
      >
        {getTypeIcon(type)} {type}
      </button>
    ))}
    <button
      onClick={() => setFilterState(prev => ({ ...prev, starred_only: !prev.starred_only }))}
      style={filterButtonStyle}
    >
      {filterState.starred_only ? 'All' : 'Starred'}
    </button>
  </div>
)
```

#### 5. View Mode Toggle

```jsx
const ViewModeSelector = () => (
  <div style={viewModeSelectorStyle}>
    {['tree', 'cluster', 'timeline', 'type'].map(mode => (
      <button
        key={mode}
        onClick={() => setViewMode(mode)}
        style={{
          ...viewModeButtonStyle,
          backgroundColor: viewMode === mode ? '#e0e7ff' : 'transparent'
        }}
      >
        {getViewModeIcon(mode)} {mode}
      </button>
    ))}
  </div>
)
```

### Layout Algorithms

#### Tree Layout (Default)

```javascript
function treeLayout(nodes, canvasWidth, canvasHeight) {
  // Find root nodes (no parent_node_id)
  const roots = nodes.filter(n => !n.parent_node_id)
  const positions = {}

  const layoutSubtree = (node, x, y, width, depth = 0) => {
    positions[node.node_id] = { x, y }

    const children = nodes.filter(n => n.parent_node_id === node.node_id)
    if (children.length === 0) return

    const childWidth = width / children.length
    children.forEach((child, i) => {
      const childX = x - width/2 + childWidth/2 + i * childWidth
      const childY = y + 100
      layoutSubtree(child, childX, childY, childWidth, depth + 1)
    })
  }

  const rootWidth = canvasWidth / roots.length
  roots.forEach((root, i) => {
    const x = rootWidth / 2 + i * rootWidth
    layoutSubtree(root, x, 50, rootWidth)
  })

  return positions
}
```

#### Cluster Layout (by Type)

```javascript
function clusterLayout(nodes, canvasWidth, canvasHeight) {
  const types = ['problem', 'insight', 'assumption', 'decision', 'question']
  const positions = {}

  // Position type clusters in a circle
  const centerX = canvasWidth / 2
  const centerY = canvasHeight / 2
  const radius = Math.min(canvasWidth, canvasHeight) * 0.35

  types.forEach((type, i) => {
    const angle = (i / types.length) * 2 * Math.PI - Math.PI / 2
    const clusterX = centerX + radius * Math.cos(angle)
    const clusterY = centerY + radius * Math.sin(angle)

    const typeNodes = nodes.filter(n => n.node_type === type)
    typeNodes.forEach((node, j) => {
      // Spread nodes within cluster
      const offset = 30
      const row = Math.floor(j / 3)
      const col = j % 3
      positions[node.node_id] = {
        x: clusterX + (col - 1) * offset,
        y: clusterY + row * offset
      }
    })
  })

  return positions
}
```

#### Timeline Layout

```javascript
function timelineLayout(nodes, canvasWidth, canvasHeight) {
  const positions = {}
  const sortedNodes = [...nodes].sort((a, b) => a.message_index - b.message_index)

  const padding = 50
  const usableWidth = canvasWidth - padding * 2
  const maxIndex = Math.max(...nodes.map(n => n.message_index), 1)

  sortedNodes.forEach((node, i) => {
    const x = padding + (node.message_index / maxIndex) * usableWidth
    // Stack vertically if same message_index
    const sameIndexCount = sortedNodes.filter(
      n => n.message_index === node.message_index &&
           sortedNodes.indexOf(n) < i
    ).length
    const y = canvasHeight / 2 + sameIndexCount * 80

    positions[node.node_id] = { x, y }
  })

  return positions
}
```

---

## 6. Integration with Conversation Flow

### Message Handler Integration

```python
# In mindrian_chat.py - @cl.on_message handler

@cl.on_message
async def on_message(message: cl.Message):
    # ... existing message handling ...

    # Get canvas state
    canvas_state = cl.user_session.get("canvas_state")
    message_index = len(history)

    # Stage 1: Instant signals (for UI hints, not extraction)
    signals = instant_idea_signals(message.content)

    # ... generate AI response ...

    # Stage 2: Background extraction (after response sent)
    asyncio.create_task(
        extract_and_update_canvas(
            user_message=message.content,
            ai_response=response_content,
            message_index=message_index,
            user_message_id=message.id,
            ai_message_id=ai_message.id,
            canvas_state=canvas_state
        )
    )
```

### Background Extraction Task

```python
async def extract_and_update_canvas(
    user_message: str,
    ai_response: str,
    message_index: int,
    user_message_id: str,
    ai_message_id: str,
    canvas_state: CanvasState
) -> None:
    """
    Background task to extract ideas and update canvas.
    Runs after response is sent - does not block user.
    """
    try:
        branch_id = canvas_state.get("current_branch_id", "main")

        # Build conversation context from recent nodes
        recent_nodes = sorted(
            canvas_state["idea_nodes"].values(),
            key=lambda n: n["message_index"],
            reverse=True
        )[:10]
        context = "\n".join(n["content"] for n in recent_nodes)

        # Extract from user message
        user_ideas = await background_extract_ideas(
            message_content=user_message,
            message_role="user",
            message_index=message_index,
            message_id=user_message_id,
            branch_id=branch_id,
            conversation_context=context
        )

        # Extract from AI response
        ai_ideas = await background_extract_ideas(
            message_content=ai_response,
            message_role="assistant",
            message_index=message_index,
            message_id=ai_message_id,
            branch_id=branch_id,
            conversation_context=context
        )

        # Add new nodes to canvas state
        all_new_ideas = user_ideas + ai_ideas
        for idea in all_new_ideas:
            canvas_state["idea_nodes"][idea["node_id"]] = idea

        # Link parents
        parent_hints = [idea.get("metadata", {}).get("parent_hint", "") for idea in all_new_ideas]
        link_idea_parents(all_new_ideas, canvas_state["idea_nodes"], parent_hints)

        # Calculate new layout
        canvas_state["layout"]["positions"] = auto_layout(
            list(canvas_state["idea_nodes"].values()),
            canvas_state["view_mode"]
        )

        canvas_state["last_updated"] = datetime.utcnow().isoformat()

        # Update session state
        cl.user_session.set("canvas_state", canvas_state)

        # Persist to Supabase
        await save_canvas_state(canvas_state)

        # Emit canvas update event (for real-time UI update)
        await emit_canvas_update(canvas_state)

    except Exception as e:
        print(f"Canvas extraction error (non-fatal): {e}")
```

### Real-Time UI Updates

```python
async def emit_canvas_update(canvas_state: CanvasState) -> None:
    """
    Send canvas update to connected clients.
    Uses Chainlit's element update mechanism.
    """
    # Get the canvas element ID if displayed
    canvas_element_id = cl.user_session.get("canvas_element_id")

    if canvas_element_id:
        # Update existing element
        updated_element = cl.CustomElement(
            id=canvas_element_id,
            name="IdeaCanvas",
            props={
                "nodes": list(canvas_state["idea_nodes"].values()),
                "layout": canvas_state["layout"],
                "viewMode": canvas_state["view_mode"],
                "filters": canvas_state["filters"],
                "currentBranchId": canvas_state["current_branch_id"]
            },
            display="side"  # Sidebar display
        )
        await updated_element.update()
```

---

## 7. Canvas Actions

### Action Callbacks

```python
# In mindrian_chat.py

@cl.action_callback("star_idea")
async def on_star_idea(action: cl.Action):
    """Toggle star status on an idea."""
    node_id = action.payload.get("node_id")
    canvas_state = cl.user_session.get("canvas_state")

    if node_id in canvas_state["idea_nodes"]:
        node = canvas_state["idea_nodes"][node_id]
        node["starred"] = not node["starred"]

        cl.user_session.set("canvas_state", canvas_state)
        await save_canvas_state(canvas_state)
        await emit_canvas_update(canvas_state)

        status = "starred" if node["starred"] else "unstarred"
        await cl.Message(
            content=f"Idea {status}: {node['content'][:50]}...",
            author="system"
        ).send()


@cl.action_callback("prune_idea")
async def on_prune_idea(action: cl.Action):
    """Mark an idea as pruned (dead end)."""
    node_id = action.payload.get("node_id")
    canvas_state = cl.user_session.get("canvas_state")

    if node_id in canvas_state["idea_nodes"]:
        node = canvas_state["idea_nodes"][node_id]
        node["pruned"] = True

        # Also prune all children (cascade)
        def prune_children(nid):
            for child_id in canvas_state["idea_nodes"].get(nid, {}).get("child_node_ids", []):
                if child_id in canvas_state["idea_nodes"]:
                    canvas_state["idea_nodes"][child_id]["pruned"] = True
                    prune_children(child_id)

        prune_children(node_id)

        cl.user_session.set("canvas_state", canvas_state)
        await save_canvas_state(canvas_state)
        await emit_canvas_update(canvas_state)

        await cl.Message(
            content=f"Pruned: {node['content'][:50]}... (and {len(node.get('child_node_ids', []))} children)",
            author="system"
        ).send()


@cl.action_callback("canvas_layout_updated")
async def on_canvas_layout_updated(action: cl.Action):
    """Save new node positions from drag-and-drop."""
    positions = action.payload.get("positions", {})
    canvas_state = cl.user_session.get("canvas_state")

    canvas_state["layout"]["positions"] = positions
    canvas_state["last_updated"] = datetime.utcnow().isoformat()

    cl.user_session.set("canvas_state", canvas_state)
    await save_canvas_state(canvas_state)


@cl.action_callback("canvas_node_selected")
async def on_canvas_node_selected(action: cl.Action):
    """Handle node selection - scroll to source message."""
    node_id = action.payload.get("node_id")
    message_id = action.payload.get("message_id")

    # Could implement scroll-to-message if supported by Chainlit
    canvas_state = cl.user_session.get("canvas_state")
    node = canvas_state["idea_nodes"].get(node_id)

    if node:
        await cl.Message(
            content=f"**Source of this idea (message #{node['message_index'] + 1}):**\n\n> {node['content']}",
            author="system"
        ).send()


@cl.action_callback("rearrange_canvas")
async def on_rearrange_canvas(action: cl.Action):
    """Change canvas layout/view mode."""
    view_mode = action.payload.get("view_mode", "tree")
    canvas_state = cl.user_session.get("canvas_state")

    canvas_state["view_mode"] = view_mode
    canvas_state["layout"]["positions"] = auto_layout(
        list(canvas_state["idea_nodes"].values()),
        view_mode
    )

    cl.user_session.set("canvas_state", canvas_state)
    await emit_canvas_update(canvas_state)


@cl.action_callback("export_canvas")
async def on_export_canvas(action: cl.Action):
    """Export canvas as markdown."""
    format_type = action.payload.get("format", "markdown")
    canvas_state = cl.user_session.get("canvas_state")

    if format_type == "markdown":
        md = export_canvas_markdown(canvas_state)
        await cl.Message(content=f"```markdown\n{md}\n```").send()

        # Also create downloadable file
        elements = [
            cl.File(
                name="idea_canvas.md",
                content=md.encode(),
                display="inline"
            )
        ]
        await cl.Message(
            content="Download your Idea Canvas:",
            elements=elements
        ).send()


def export_canvas_markdown(canvas_state: CanvasState) -> str:
    """Export canvas to markdown format."""
    md = "# Idea Canvas Export\n\n"
    md += f"Generated: {datetime.utcnow().isoformat()}\n\n"

    # Group by type
    types = ["problem", "insight", "assumption", "decision", "question"]
    type_names = {
        "problem": "Problems",
        "insight": "Insights",
        "assumption": "Assumptions",
        "decision": "Decisions",
        "question": "Questions"
    }

    for node_type in types:
        nodes = [n for n in canvas_state["idea_nodes"].values()
                 if n["node_type"] == node_type and not n["pruned"]]

        if nodes:
            md += f"## {type_names[node_type]}\n\n"

            starred = [n for n in nodes if n["starred"]]
            unstarred = [n for n in nodes if not n["starred"]]

            if starred:
                md += "### Starred\n"
                for n in starred:
                    md += f"- **{n['content']}**\n"
                md += "\n"

            if unstarred:
                for n in unstarred:
                    md += f"- {n['content']}\n"
                md += "\n"

    return md
```

---

## 8. Display Options

### Sidebar Display (Persistent)

```python
async def show_canvas_sidebar():
    """Display canvas in persistent sidebar."""
    canvas_state = cl.user_session.get("canvas_state")

    element = cl.CustomElement(
        name="IdeaCanvas",
        props={
            "nodes": list(canvas_state["idea_nodes"].values()),
            "layout": canvas_state["layout"],
            "viewMode": canvas_state["view_mode"],
            "filters": canvas_state["filters"],
            "currentBranchId": canvas_state["current_branch_id"],
            "editable": True,
            "title": "Idea Canvas"
        },
        display="side"  # Sidebar display
    )

    await element.send()
    cl.user_session.set("canvas_element_id", element.id)
```

### Inline Display (On Demand)

```python
async def show_canvas_inline():
    """Display canvas inline in conversation."""
    canvas_state = cl.user_session.get("canvas_state")

    element = cl.CustomElement(
        name="IdeaCanvas",
        props={
            "nodes": list(canvas_state["idea_nodes"].values()),
            "layout": canvas_state["layout"],
            "viewMode": canvas_state["view_mode"],
            "filters": canvas_state["filters"],
            "editable": True
        },
        display="inline"
    )

    await cl.Message(
        content="Here's your current Idea Canvas:",
        elements=[element]
    ).send()
```

### Action Button

```python
# Add to actions in on_chat_start
cl.Action(
    name="show_canvas",
    payload={},
    label="Show Idea Canvas",
    icon="map",
    description="View extracted ideas from this conversation"
)

@cl.action_callback("show_canvas")
async def on_show_canvas(action: cl.Action):
    await show_canvas_inline()
```

---

## 9. Integration with Existing Components

### Relationship to MermaidDiagram.jsx

**Decision: Create new component, don't extend MermaidDiagram**

Reasons:
1. MermaidDiagram is for static, declarative diagrams
2. IdeaCanvas needs interactive features (drag, star, prune)
3. Different rendering approach (custom SVG/canvas vs Mermaid library)
4. Real-time updates require different state management

However, we CAN offer Mermaid export:

```python
def canvas_to_mermaid(canvas_state: CanvasState) -> str:
    """Convert canvas to Mermaid mindmap syntax."""
    nodes = canvas_state["idea_nodes"]
    starred = [n for n in nodes.values() if n["starred"]]

    lines = ["mindmap", "  root((Key Ideas))"]

    for node_type in ["problem", "insight", "assumption", "decision", "question"]:
        type_nodes = [n for n in starred if n["node_type"] == node_type]
        if type_nodes:
            lines.append(f"    {node_type.title()}s")
            for n in type_nodes[:5]:
                clean = n["content"][:40].replace("(", "[").replace(")", "]")
                lines.append(f"      {clean}")

    return "\n".join(lines)
```

### Relationship to ProblemCanvas.jsx

ProblemCanvas is a structured form with fixed sections. IdeaCanvas is freeform. They can complement each other:

```python
async def populate_problem_canvas_from_ideas():
    """Use starred ideas to pre-populate ProblemCanvas."""
    canvas_state = cl.user_session.get("canvas_state")
    starred = [n for n in canvas_state["idea_nodes"].values() if n["starred"]]

    sections = {}
    for node in starred:
        if node["node_type"] == "problem":
            sections.setdefault("problem", []).append(node["content"])
        elif node["node_type"] == "assumption":
            sections.setdefault("constraints", []).append(node["content"])
        # ... map other types ...

    # Combine into single strings
    problem_canvas_props = {
        "sections": {k: "\n\n".join(v) for k, v in sections.items()}
    }

    element = cl.CustomElement(
        name="ProblemCanvas",
        props=problem_canvas_props,
        display="inline"
    )
    await cl.Message(
        content="Based on your starred ideas, here's a draft Problem Canvas:",
        elements=[element]
    ).send()
```

---

## 10. Implementation Checklist

### Phase 1: Core Data Layer (1-2 days)

- [ ] Create `/home/jsagi/Mindrian/mindrian-deploy/tools/idea_canvas.py`
  - [ ] Define `IdeaNode`, `CanvasLayout`, `CanvasState` TypedDicts
  - [ ] Implement `instant_idea_signals()` regex patterns
  - [ ] Implement `background_extract_ideas()` LLM extraction
  - [ ] Implement `link_idea_parents()` linking logic
  - [ ] Implement `save_canvas_state()` / `load_canvas_state()` persistence

### Phase 2: Session Integration (1 day)

- [ ] Add canvas state initialization to `@cl.on_chat_start`
- [ ] Add canvas state restoration to `@cl.on_chat_resume`
- [ ] Implement `extract_and_update_canvas()` background task
- [ ] Integrate extraction task into `@cl.on_message` handler

### Phase 3: React Component (2-3 days)

- [ ] Create `/home/jsagi/Mindrian/mindrian-deploy/public/elements/IdeaCanvas.jsx`
  - [ ] Basic node rendering with type colors
  - [ ] Drag-and-drop repositioning
  - [ ] Star/prune action buttons
  - [ ] Filter controls (by type, starred only, hide pruned)
  - [ ] View mode selector (tree, cluster, timeline, type)
  - [ ] Zoom and pan controls
  - [ ] Node selection and detail panel

### Phase 4: Layout Algorithms (1 day)

- [ ] Implement `treeLayout()` - hierarchical by parent/child
- [ ] Implement `clusterLayout()` - force-directed by type
- [ ] Implement `timelineLayout()` - left-to-right by message
- [ ] Implement `auto_layout()` dispatcher

### Phase 5: Action Handlers (1 day)

- [ ] Add `@cl.action_callback("star_idea")`
- [ ] Add `@cl.action_callback("prune_idea")`
- [ ] Add `@cl.action_callback("canvas_layout_updated")`
- [ ] Add `@cl.action_callback("canvas_node_selected")`
- [ ] Add `@cl.action_callback("rearrange_canvas")`
- [ ] Add `@cl.action_callback("export_canvas")`
- [ ] Add `@cl.action_callback("show_canvas")` button

### Phase 6: Export & Integration (1 day)

- [ ] Implement `export_canvas_markdown()`
- [ ] Implement `canvas_to_mermaid()` for diagram export
- [ ] Implement `populate_problem_canvas_from_ideas()`
- [ ] Add canvas export as downloadable file

### Phase 7: Testing & Polish (1-2 days)

- [ ] Test extraction accuracy with various conversation types
- [ ] Test real-time updates during conversation
- [ ] Test persistence across session resume
- [ ] Test all layout algorithms
- [ ] Accessibility testing (keyboard navigation)
- [ ] Mobile responsiveness

---

## 11. Future Enhancements (Post-MVP)

1. **Collaborative Canvas** - Multiple users editing same canvas
2. **Embedding-based Linking** - Use vector similarity for smarter parent-child links
3. **Canvas Templates** - Pre-defined layouts for specific frameworks (JTBD, TTA, etc.)
4. **AI Suggestions** - "You have 3 unvalidated assumptions - want to explore?"
5. **Branch Visualization** - Show different exploration paths visually
6. **Image Export** - PNG/SVG export via canvas-to-image
7. **Canvas Sharing** - Public link to view-only canvas

---

## 12. Appendix: Related Existing Patterns

### From LangExtract (tools/langextract.py)

The extraction pattern follows LangExtract's two-stage approach:
- `instant_extract()` - Fast regex, no API calls
- `background_extract_pws()` - LLM-based, async after response

### From Diagrams (utils/diagrams.py)

The diagram utilities show how to create Chainlit CustomElements:
- `create_mermaid_element()` - Creates cl.CustomElement with props
- Pattern for async element creation

### From QuadrantChart.jsx

The interactive component pattern to follow:
- Access `window.Chainlit` for APIs
- Use `callAction()` for backend communication
- Local state for UI interactions
- `props || {}` for global prop access

### From ProblemCanvas.jsx

The editable canvas pattern:
- Section-based structure with edit mode
- `updateElement()` for real-time updates
- `sendUserMessage()` for AI assistance requests
