"""
Idea Canvas - Wave 3: Visual workspace for extracted ideas
Provides automatic extraction and structured storage of ideas from conversation.

Features:
- Two-stage extraction (instant regex + background LLM)
- Node types: problem, insight, assumption, decision, question
- Parent-child linking for idea hierarchy
- Persistence via Supabase storage
"""

import re
import os
import json
import uuid
import asyncio
from datetime import datetime
from typing import TypedDict, Optional, Literal, Dict, List, Any


# ═══════════════════════════════════════════════════════════════════════════════
# Type Definitions
# ═══════════════════════════════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════════════════════════════
# Pattern-Based Instant Extraction
# ═══════════════════════════════════════════════════════════════════════════════

IDEA_PATTERNS = {
    "problem": [
        r"\b(?:problem|issue|challenge|pain point|struggle|difficulty|obstacle)\b",
        r"\b(?:frustrated|stuck|blocked|can't|unable to)\b",
        r"what's (?:wrong|broken|not working)",
        r"\b(?:fails?|failing|broken|doesn't work)\b",
    ],
    "insight": [
        r"\b(?:realized?|discovered?|noticed|interesting(?:ly)?)\b",
        r"\b(?:aha|eureka|breakthrough|key insight)\b",
        r"(?:that explains|now I (?:see|understand))",
        r"\b(?:pattern|connection|link between)\b",
    ],
    "assumption": [
        r"\b(?:assume|assuming|assumption|presume|suppose)\b",
        r"\b(?:if|given that|based on the premise)\b",
        r"\b(?:we believe|I think|probably|likely|might be)\b",
        r"\b(?:expecting|expected|anticipate)\b",
    ],
    "decision": [
        r"\b(?:decided?|choosing|committed|going with)\b",
        r"\b(?:let's go with|moving forward with|our approach)\b",
        r"(?:the plan is|we will|action item)",
        r"\b(?:next step|implementation|execute|launch)\b",
    ],
    "question": [
        r"[^.!]*\?$",  # Sentences ending in ?
        r"\b(?:wondering|curious|unclear|not sure)\b",
        r"(?:what if|how might|could we)",
        r"\b(?:explore|investigate|research|look into)\b",
    ],
}


def instant_idea_signals(text: str) -> Dict[str, List[str]]:
    """
    Fast pattern matching to detect potential ideas.
    Returns dict of {node_type: [matched_snippets]}.

    Runtime: <5ms for typical messages
    """
    signals = {}
    for node_type, patterns in IDEA_PATTERNS.items():
        matches = []
        for pattern in patterns:
            # Find matches with context (50 chars before/after)
            found = re.findall(
                f".{{0,50}}{pattern}.{{0,50}}",
                text,
                re.IGNORECASE | re.DOTALL
            )
            matches.extend(found)
        if matches:
            # Deduplicate and limit
            unique_matches = list(set(m.strip() for m in matches))
            signals[node_type] = unique_matches[:3]
    return signals


def extract_questions(text: str) -> List[str]:
    """Extract question sentences from text."""
    # Split into sentences (rough)
    sentences = re.split(r'(?<=[.!?])\s+', text)
    questions = [s.strip() for s in sentences if s.strip().endswith('?')]
    return questions[:5]


# ═══════════════════════════════════════════════════════════════════════════════
# LLM-Based Background Extraction
# ═══════════════════════════════════════════════════════════════════════════════

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

    Args:
        message_content: The message text to extract from
        message_role: "user" or "assistant"
        message_index: Position in conversation (0-indexed)
        message_id: Chainlit message ID
        branch_id: Current exploration branch
        conversation_context: Recent conversation for context

    Returns:
        List of extracted IdeaNode objects
    """
    try:
        from google import genai
        from google.genai import types

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            # Fallback to pattern-based extraction
            return _pattern_based_extraction(
                message_content, message_role, message_index, message_id, branch_id
            )

        client = genai.Client(api_key=api_key)

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

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=extraction_prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=1000
            )
        )

        # Parse JSON response
        text = response.text.strip()
        # Handle potential markdown code blocks
        if text.startswith("```"):
            text = re.sub(r'^```(?:json)?\n?', '', text)
            text = re.sub(r'\n?```$', '', text)

        ideas_data = json.loads(text)
        nodes = []

        for idea in ideas_data:
            node = {
                "node_id": str(uuid.uuid4()),
                "content": idea.get("content", "")[:500],
                "node_type": idea.get("node_type", "insight"),
                "branch_id": branch_id,
                "message_index": message_index,
                "message_id": message_id,
                "parent_node_id": None,
                "child_node_ids": [],
                "confidence": float(idea.get("confidence", 0.7)),
                "starred": False,
                "pruned": False,
                "created_at": datetime.utcnow().isoformat(),
                "source_role": message_role,
                "tags": [],
                "metadata": {
                    "parent_hint": idea.get("parent_hint", "")
                }
            }
            nodes.append(node)

        return nodes

    except Exception as e:
        print(f"LLM idea extraction error: {e}")
        # Fallback to pattern-based
        return _pattern_based_extraction(
            message_content, message_role, message_index, message_id, branch_id
        )


def _pattern_based_extraction(
    message_content: str,
    message_role: str,
    message_index: int,
    message_id: str,
    branch_id: str
) -> List[IdeaNode]:
    """
    Fallback pattern-based extraction when LLM unavailable.
    Uses regex patterns to find potential ideas.
    """
    nodes = []
    signals = instant_idea_signals(message_content)

    for node_type, snippets in signals.items():
        for i, snippet in enumerate(snippets[:2]):  # Max 2 per type
            node = {
                "node_id": str(uuid.uuid4()),
                "content": snippet.strip()[:200],
                "node_type": node_type,
                "branch_id": branch_id,
                "message_index": message_index,
                "message_id": message_id,
                "parent_node_id": None,
                "child_node_ids": [],
                "confidence": 0.5,  # Lower confidence for pattern-based
                "starred": False,
                "pruned": False,
                "created_at": datetime.utcnow().isoformat(),
                "source_role": message_role,
                "tags": [],
                "metadata": {"extraction_method": "pattern"}
            }
            nodes.append(node)

    return nodes


def link_idea_parents(
    new_nodes: List[IdeaNode],
    existing_nodes: Dict[str, IdeaNode],
    parent_hints: List[str]
) -> None:
    """
    Use keyword similarity to link new ideas to parent ideas.
    Modifies nodes in place.
    """
    if not existing_nodes:
        return

    for i, node in enumerate(new_nodes):
        hint = ""
        if i < len(parent_hints) and parent_hints[i]:
            hint = parent_hints[i].lower()
        elif node.get("metadata", {}).get("parent_hint"):
            hint = node["metadata"]["parent_hint"].lower()

        if not hint:
            continue

        best_match = None
        best_score = 0.0

        for existing_id, existing_node in existing_nodes.items():
            if existing_node.get("pruned"):
                continue
            # Simple word overlap score
            hint_words = set(hint.split())
            content_words = set(existing_node["content"].lower().split())
            if not hint_words:
                continue
            overlap = len(hint_words & content_words) / len(hint_words)

            if overlap > best_score and overlap > 0.3:
                best_score = overlap
                best_match = existing_id

        if best_match:
            node["parent_node_id"] = best_match
            if "child_node_ids" not in existing_nodes[best_match]:
                existing_nodes[best_match]["child_node_ids"] = []
            existing_nodes[best_match]["child_node_ids"].append(node["node_id"])


# ═══════════════════════════════════════════════════════════════════════════════
# Canvas State Management
# ═══════════════════════════════════════════════════════════════════════════════

def init_canvas_state(session_id: str, branch_id: str = "main") -> CanvasState:
    """Initialize canvas state for a new session."""
    return {
        "session_id": session_id,
        "idea_nodes": {},
        "layout": {
            "positions": {},
            "zoom": 1.0,
            "pan_x": 0,
            "pan_y": 0
        },
        "view_mode": "tree",
        "filters": {
            "problem": True,
            "insight": True,
            "assumption": True,
            "decision": True,
            "question": True,
            "starred_only": False,
            "hide_pruned": True
        },
        "current_branch_id": branch_id,
        "last_updated": datetime.utcnow().isoformat()
    }


CANVAS_FOLDER = "canvas_states"


async def save_canvas_state(state: CanvasState) -> bool:
    """Persist canvas state to Supabase."""
    try:
        from utils.context_persistence import get_supabase_client, SUPABASE_BUCKET

        client = get_supabase_client()
        if not client:
            return False

        json_content = json.dumps(state, indent=2, default=str)
        storage_path = f"{CANVAS_FOLDER}/{state['session_id']}.json"

        try:
            client.storage.from_(SUPABASE_BUCKET).upload(
                path=storage_path,
                file=json_content.encode('utf-8'),
                file_options={"content-type": "application/json"}
            )
        except Exception as upload_err:
            if "duplicate" in str(upload_err).lower() or "already exists" in str(upload_err).lower():
                client.storage.from_(SUPABASE_BUCKET).update(
                    path=storage_path,
                    file=json_content.encode('utf-8'),
                    file_options={"content-type": "application/json"}
                )
            else:
                raise

        return True
    except Exception as e:
        print(f"Canvas save error: {e}")
        return False


async def load_canvas_state(session_id: str) -> Optional[CanvasState]:
    """Load canvas state from Supabase."""
    try:
        from utils.context_persistence import get_supabase_client, SUPABASE_BUCKET

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


# ═══════════════════════════════════════════════════════════════════════════════
# Layout Algorithms
# ═══════════════════════════════════════════════════════════════════════════════

def auto_layout(
    nodes: List[IdeaNode],
    view_mode: str,
    canvas_width: int = 800,
    canvas_height: int = 600
) -> Dict[str, Position]:
    """
    Calculate positions for all nodes based on view mode.
    """
    if view_mode == "tree":
        return tree_layout(nodes, canvas_width, canvas_height)
    elif view_mode == "cluster":
        return cluster_layout(nodes, canvas_width, canvas_height)
    elif view_mode == "timeline":
        return timeline_layout(nodes, canvas_width, canvas_height)
    elif view_mode == "type":
        return type_column_layout(nodes, canvas_width, canvas_height)
    else:
        return tree_layout(nodes, canvas_width, canvas_height)


def tree_layout(
    nodes: List[IdeaNode],
    canvas_width: int,
    canvas_height: int
) -> Dict[str, Position]:
    """Hierarchical tree layout based on parent-child relationships."""
    positions = {}
    if not nodes:
        return positions

    # Find root nodes (no parent)
    roots = [n for n in nodes if not n.get("parent_node_id")]
    if not roots:
        # No roots - treat all as roots
        roots = nodes

    def get_children(node_id: str) -> List[IdeaNode]:
        return [n for n in nodes if n.get("parent_node_id") == node_id]

    def layout_subtree(node: IdeaNode, x: float, y: float, width: float, depth: int = 0):
        positions[node["node_id"]] = {"x": x, "y": y}

        children = get_children(node["node_id"])
        if not children:
            return

        child_width = width / max(len(children), 1)
        for i, child in enumerate(children):
            child_x = x - width/2 + child_width/2 + i * child_width
            child_y = y + 100
            layout_subtree(child, child_x, child_y, child_width, depth + 1)

    root_width = canvas_width / max(len(roots), 1)
    for i, root in enumerate(roots):
        x = root_width / 2 + i * root_width
        layout_subtree(root, x, 50, root_width)

    return positions


def cluster_layout(
    nodes: List[IdeaNode],
    canvas_width: int,
    canvas_height: int
) -> Dict[str, Position]:
    """Cluster nodes by type in a circular arrangement."""
    positions = {}
    if not nodes:
        return positions

    types = ["problem", "insight", "assumption", "decision", "question"]
    center_x = canvas_width / 2
    center_y = canvas_height / 2
    radius = min(canvas_width, canvas_height) * 0.35

    import math

    for t, type_name in enumerate(types):
        angle = (t / len(types)) * 2 * math.pi - math.pi / 2
        cluster_x = center_x + radius * math.cos(angle)
        cluster_y = center_y + radius * math.sin(angle)

        type_nodes = [n for n in nodes if n.get("node_type") == type_name]
        for j, node in enumerate(type_nodes):
            offset = 35
            row = j // 3
            col = j % 3
            positions[node["node_id"]] = {
                "x": cluster_x + (col - 1) * offset,
                "y": cluster_y + row * offset
            }

    return positions


def timeline_layout(
    nodes: List[IdeaNode],
    canvas_width: int,
    canvas_height: int
) -> Dict[str, Position]:
    """Layout nodes left-to-right by message_index."""
    positions = {}
    if not nodes:
        return positions

    sorted_nodes = sorted(nodes, key=lambda n: n.get("message_index", 0))
    padding = 50
    usable_width = canvas_width - padding * 2
    max_index = max((n.get("message_index", 0) for n in nodes), default=1) or 1

    index_counts = {}
    for node in sorted_nodes:
        idx = node.get("message_index", 0)
        count = index_counts.get(idx, 0)
        index_counts[idx] = count + 1

        x = padding + (idx / max_index) * usable_width
        y = canvas_height / 2 + count * 80

        positions[node["node_id"]] = {"x": x, "y": y}

    return positions


def type_column_layout(
    nodes: List[IdeaNode],
    canvas_width: int,
    canvas_height: int
) -> Dict[str, Position]:
    """Layout nodes in columns by type."""
    positions = {}
    if not nodes:
        return positions

    types = ["problem", "insight", "assumption", "decision", "question"]
    col_width = canvas_width / len(types)

    for t, type_name in enumerate(types):
        col_x = col_width / 2 + t * col_width
        type_nodes = [n for n in nodes if n.get("node_type") == type_name]

        for j, node in enumerate(type_nodes):
            positions[node["node_id"]] = {
                "x": col_x,
                "y": 60 + j * 70
            }

    return positions


# ═══════════════════════════════════════════════════════════════════════════════
# Canvas Export
# ═══════════════════════════════════════════════════════════════════════════════

def export_canvas_to_markdown(canvas_state: CanvasState) -> str:
    """Export canvas state to markdown format."""
    lines = ["# Idea Canvas Export", ""]
    lines.append(f"*Exported: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}*")
    lines.append("")

    # Group by type
    types = ["problem", "insight", "assumption", "decision", "question"]
    type_names = {
        "problem": "🔴 Problems",
        "insight": "💡 Insights",
        "assumption": "🟣 Assumptions",
        "decision": "✅ Decisions",
        "question": "❓ Questions"
    }

    for type_name in types:
        type_nodes = [
            n for n in canvas_state["idea_nodes"].values()
            if n.get("node_type") == type_name and not n.get("pruned")
        ]
        if type_nodes:
            lines.append(f"## {type_names.get(type_name, type_name)}")
            lines.append("")
            for node in type_nodes:
                starred = "⭐ " if node.get("starred") else ""
                lines.append(f"- {starred}{node['content']}")
            lines.append("")

    # Starred ideas section
    starred = [
        n for n in canvas_state["idea_nodes"].values()
        if n.get("starred") and not n.get("pruned")
    ]
    if starred:
        lines.append("## ⭐ Starred Ideas")
        lines.append("")
        for node in starred:
            lines.append(f"- **{node['node_type']}**: {node['content']}")
        lines.append("")

    return "\n".join(lines)
