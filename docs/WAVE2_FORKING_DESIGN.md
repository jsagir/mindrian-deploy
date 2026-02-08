# Wave 2: Conversation Forking Design Specification

**Status:** Design Phase (Do Not Implement Yet)
**Author:** Claude Opus 4.5
**Date:** 2026-02-08
**Dependencies:** Wave 1 (Session Persistence, Topic Exclusion, Quick Mode)

---

## Executive Summary

Conversation forking allows users to explore alternative directions from any point in their conversation without losing context. Think of it as "git branches" for thinking: branch off to explore "what if?" scenarios, compare different approaches, then optionally merge insights back.

**Use Cases:**
- Explore multiple solutions to a problem simultaneously
- Test different assumptions without backtracking
- Compare Red Team vs. optimistic analysis on the same premise
- "Save my place" while exploring a tangent

---

## 1. Data Model Design

### 1.1 Core TypedDict Definitions

Add to `utils/forking_types.py`:

```python
"""
Conversation Forking - Type Definitions
Wave 2 of Mindrian Session Management
"""

from typing import TypedDict, Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class BranchStatus(Enum):
    """Branch lifecycle status."""
    ACTIVE = "active"           # Currently being worked on
    PAUSED = "paused"           # User switched away, preserves state
    MERGED = "merged"           # Insights merged into parent
    ARCHIVED = "archived"       # Soft deleted, recoverable


class ConversationBranch(TypedDict):
    """
    A single branch in the conversation tree.

    Design notes:
    - branch_id is UUID for global uniqueness
    - parent_branch_id enables tree structure (None = root)
    - fork_point_message_index marks WHERE we branched
    - Messages from 0 to fork_point are SHARED with parent
    """
    branch_id: str                          # UUID
    parent_branch_id: Optional[str]         # None for root branch
    fork_point_message_index: int           # Index in parent's history where fork occurred
    title: str                              # User-facing name (auto-generated or custom)
    created_at: str                         # ISO 8601 timestamp
    status: str                             # BranchStatus value
    is_active: bool                         # Currently selected branch

    # Branch-specific state
    history: List[Dict[str, Any]]           # Messages AFTER fork point (branch-local)
    bot_id: str                             # Active bot in this branch
    phases: List[Dict[str, Any]]            # Workshop phases (if applicable)
    current_phase: int                      # Current phase index
    excluded_topics: List[str]              # Topic exclusions for this branch

    # Metadata
    message_count: int                      # Quick stat: total messages in this branch
    last_activity: str                      # ISO 8601 timestamp of last message
    merge_target: Optional[str]             # If merged, which branch received insights


class BranchTree(TypedDict):
    """
    Complete branch tree for a conversation.

    Stored in context persistence and user session.
    """
    root_branch_id: str                     # The original conversation
    branches: Dict[str, ConversationBranch] # branch_id -> ConversationBranch
    active_branch_id: str                   # Currently active branch
    fork_points: List[int]                  # Message indices where any fork exists

    # Tree metadata
    conversation_id: str                    # Links to main conversation
    created_at: str                         # When first branch was created
    last_modified: str                      # Any branch activity


class MergeResult(TypedDict):
    """Result of merging two branches."""
    success: bool
    source_branch_id: str
    target_branch_id: str
    insights_merged: List[str]              # Key insights extracted and merged
    conflicts: List[str]                    # Any conflicting conclusions
    merge_summary: str                      # LLM-generated summary
```

### 1.2 Branch Title Auto-Generation

```python
def generate_branch_title(
    fork_context: str,
    parent_title: str,
    branch_count: int
) -> str:
    """
    Generate a descriptive branch title based on context.

    Examples:
    - "Alternative: Red Team Analysis"
    - "What if: No budget constraints"
    - "Exploration #2"

    Args:
        fork_context: Last few messages before fork (for LLM analysis)
        parent_title: Parent branch title for context
        branch_count: Number of existing branches (for fallback naming)

    Returns:
        Human-readable branch title
    """
    # Quick pattern matching first (no API call)
    patterns = {
        r"what if|alternatively|suppose|imagine": "What if",
        r"devil's advocate|challenge|attack|red team": "Red Team",
        r"let me try|different approach|another way": "Alternative",
        r"explore|tangent|side note|unrelated": "Exploration",
    }

    for pattern, prefix in patterns.items():
        if re.search(pattern, fork_context.lower()):
            return f"{prefix}: {parent_title}"

    # Fallback to numbered branch
    return f"Branch #{branch_count + 1}"
```

---

## 2. Session State Extensions

### 2.1 New `cl.user_session` Keys

Add these keys to session initialization in `on_chat_start`:

```python
# === Wave 2: Forking State ===

# Branch tree structure
cl.user_session.set("branch_tree", None)  # BranchTree or None if no forks

# Current active branch
cl.user_session.set("active_branch_id", None)  # str or None

# Quick access to fork points for UI
cl.user_session.set("fork_points", [])  # List[int] - message indices with forks

# Branch-local history (messages after fork point)
cl.user_session.set("branch_history", [])  # List[Dict] - only this branch's messages

# Merge state (when merging branches)
cl.user_session.set("pending_merge", None)  # MergeResult or None

# UI state
cl.user_session.set("show_branch_selector", False)  # Toggle for BranchSelector visibility
cl.user_session.set("branch_comparison_mode", False)  # Side-by-side comparison
```

### 2.2 Session State Diagram

```
cl.user_session
├── history              # Full history (shared + branch-local combined)
├── branch_tree          # BranchTree structure
│   ├── root_branch_id
│   ├── branches: {id: ConversationBranch, ...}
│   ├── active_branch_id
│   └── fork_points: [3, 15, 22]
├── active_branch_id     # Current branch (duplicated for fast access)
├── branch_history       # Messages specific to active branch
├── fork_points          # Quick access for UI (duplicated)
├── pending_merge        # Active merge operation state
└── show_branch_selector # UI toggle
```

### 2.3 History Composition Logic

```python
def get_composed_history(user_session) -> List[Dict]:
    """
    Compose full history from shared + branch-local messages.

    If no branching: return history as-is
    If branched: return parent history up to fork + branch history
    """
    branch_tree = user_session.get("branch_tree")

    if not branch_tree:
        return user_session.get("history", [])

    active_branch_id = user_session.get("active_branch_id")
    if not active_branch_id:
        return user_session.get("history", [])

    branch = branch_tree["branches"].get(active_branch_id)
    if not branch:
        return user_session.get("history", [])

    # If root branch, just return history
    if not branch.get("parent_branch_id"):
        return user_session.get("history", [])

    # Compose: shared history (up to fork point) + branch-local history
    parent = branch_tree["branches"].get(branch["parent_branch_id"])
    if parent:
        fork_point = branch["fork_point_message_index"]
        shared_history = parent.get("history", [])[:fork_point]
        branch_history = branch.get("history", [])
        return shared_history + branch_history

    return user_session.get("history", [])
```

---

## 3. Action Callbacks

### 3.1 Fork Conversation

```python
@cl.action_callback("fork_conversation")
async def on_fork_conversation(action: cl.Action):
    """
    Create a new branch from the current conversation point.

    Triggered by:
    - "Fork Here" button on message hover
    - "Create Branch" in BranchSelector
    - Automatic fork suggestion after "what if" detection

    Payload:
    - fork_at_index: Optional[int] - message index to fork from (default: current)
    - title: Optional[str] - custom branch title
    - copy_excluded_topics: bool - inherit topic exclusions (default: True)
    """
    try:
        fork_at_index = action.payload.get("fork_at_index")
        custom_title = action.payload.get("title")
        copy_excluded = action.payload.get("copy_excluded_topics", True)

        # Get current state
        history = cl.user_session.get("history", [])
        bot_id = cl.user_session.get("bot_id", "lawrence")
        phases = cl.user_session.get("phases", [])
        current_phase = cl.user_session.get("current_phase", 0)
        excluded_topics = cl.user_session.get("excluded_topics", [])

        # Determine fork point
        if fork_at_index is None:
            fork_at_index = len(history)  # Fork from current position

        # Get or create branch tree
        branch_tree = cl.user_session.get("branch_tree")
        if not branch_tree:
            # First fork - create root branch from existing conversation
            root_branch_id = str(uuid.uuid4())
            branch_tree = {
                "root_branch_id": root_branch_id,
                "branches": {
                    root_branch_id: {
                        "branch_id": root_branch_id,
                        "parent_branch_id": None,
                        "fork_point_message_index": 0,
                        "title": "Main Conversation",
                        "created_at": datetime.utcnow().isoformat(),
                        "status": "paused",  # Switching to new branch
                        "is_active": False,
                        "history": history.copy(),
                        "bot_id": bot_id,
                        "phases": [p.copy() for p in phases],
                        "current_phase": current_phase,
                        "excluded_topics": excluded_topics.copy(),
                        "message_count": len(history),
                        "last_activity": datetime.utcnow().isoformat(),
                        "merge_target": None,
                    }
                },
                "active_branch_id": root_branch_id,
                "fork_points": [],
                "conversation_id": cl.user_session.get("conversation_id", str(uuid.uuid4())),
                "created_at": datetime.utcnow().isoformat(),
                "last_modified": datetime.utcnow().isoformat(),
            }
            parent_branch_id = root_branch_id
        else:
            parent_branch_id = branch_tree["active_branch_id"]

        # Generate branch title
        context = "\n".join([
            m.get("content", "")[:200]
            for m in history[max(0, fork_at_index-3):fork_at_index]
        ])
        parent_title = branch_tree["branches"][parent_branch_id]["title"]
        title = custom_title or generate_branch_title(
            context,
            parent_title,
            len(branch_tree["branches"])
        )

        # Create new branch
        new_branch_id = str(uuid.uuid4())
        new_branch = {
            "branch_id": new_branch_id,
            "parent_branch_id": parent_branch_id,
            "fork_point_message_index": fork_at_index,
            "title": title,
            "created_at": datetime.utcnow().isoformat(),
            "status": "active",
            "is_active": True,
            "history": [],  # New branch starts empty (inherits shared history)
            "bot_id": bot_id,
            "phases": [p.copy() for p in phases],
            "current_phase": current_phase,
            "excluded_topics": excluded_topics.copy() if copy_excluded else [],
            "message_count": 0,
            "last_activity": datetime.utcnow().isoformat(),
            "merge_target": None,
        }

        # Update parent branch
        branch_tree["branches"][parent_branch_id]["status"] = "paused"
        branch_tree["branches"][parent_branch_id]["is_active"] = False

        # Add new branch
        branch_tree["branches"][new_branch_id] = new_branch
        branch_tree["active_branch_id"] = new_branch_id
        branch_tree["fork_points"].append(fork_at_index)
        branch_tree["fork_points"] = sorted(set(branch_tree["fork_points"]))
        branch_tree["last_modified"] = datetime.utcnow().isoformat()

        # Update session state
        cl.user_session.set("branch_tree", branch_tree)
        cl.user_session.set("active_branch_id", new_branch_id)
        cl.user_session.set("fork_points", branch_tree["fork_points"])
        cl.user_session.set("branch_history", [])

        # Persist to storage
        await save_branch_state(cl.user_session)

        # Show confirmation with branch selector
        await show_branch_created_message(new_branch, parent_title, fork_at_index)

    except Exception as e:
        print(f"Fork error: {e}")
        await cl.Message(content=f"Unable to create branch: {str(e)[:100]}").send()
```

### 3.2 Switch Branch

```python
@cl.action_callback("switch_branch")
async def on_switch_branch(action: cl.Action):
    """
    Switch to a different branch.

    Payload:
    - branch_id: str - target branch ID
    - confirm_unsaved: bool - skip confirmation if True
    """
    try:
        target_branch_id = action.payload.get("branch_id")
        confirm_unsaved = action.payload.get("confirm_unsaved", False)

        branch_tree = cl.user_session.get("branch_tree")
        if not branch_tree:
            await cl.Message(content="No branches exist yet.").send()
            return

        target_branch = branch_tree["branches"].get(target_branch_id)
        if not target_branch:
            await cl.Message(content="Branch not found.").send()
            return

        current_branch_id = branch_tree["active_branch_id"]
        if current_branch_id == target_branch_id:
            await cl.Message(content=f"Already on branch: {target_branch['title']}").send()
            return

        # Save current branch state before switching
        current_branch = branch_tree["branches"].get(current_branch_id)
        if current_branch:
            current_branch["history"] = cl.user_session.get("branch_history", [])
            current_branch["status"] = "paused"
            current_branch["is_active"] = False
            current_branch["last_activity"] = datetime.utcnow().isoformat()
            current_branch["bot_id"] = cl.user_session.get("bot_id")
            current_branch["phases"] = cl.user_session.get("phases", [])
            current_branch["current_phase"] = cl.user_session.get("current_phase", 0)

        # Activate target branch
        target_branch["status"] = "active"
        target_branch["is_active"] = True
        branch_tree["active_branch_id"] = target_branch_id
        branch_tree["last_modified"] = datetime.utcnow().isoformat()

        # Restore target branch state to session
        cl.user_session.set("branch_tree", branch_tree)
        cl.user_session.set("active_branch_id", target_branch_id)
        cl.user_session.set("branch_history", target_branch.get("history", []))
        cl.user_session.set("bot_id", target_branch.get("bot_id", "lawrence"))
        cl.user_session.set("phases", target_branch.get("phases", []))
        cl.user_session.set("current_phase", target_branch.get("current_phase", 0))
        cl.user_session.set("excluded_topics", target_branch.get("excluded_topics", []))

        # Compose full history for LLM context
        composed_history = get_composed_history(cl.user_session)
        cl.user_session.set("history", composed_history)

        # Persist
        await save_branch_state(cl.user_session)

        # Show branch switch message
        await show_branch_switched_message(target_branch, current_branch)

    except Exception as e:
        print(f"Switch branch error: {e}")
        await cl.Message(content=f"Unable to switch branch: {str(e)[:100]}").send()
```

### 3.3 Merge Branches

```python
@cl.action_callback("merge_branches")
async def on_merge_branches(action: cl.Action):
    """
    Merge insights from one branch into another.

    Uses LLM to:
    1. Extract key insights from source branch
    2. Identify conflicts with target branch
    3. Generate merged summary
    4. Optionally archive source branch

    Payload:
    - source_branch_id: str - branch to merge FROM
    - target_branch_id: str - branch to merge INTO
    - archive_source: bool - archive source after merge (default: True)
    - merge_mode: str - "insights" | "full" (default: "insights")
    """
    try:
        source_id = action.payload.get("source_branch_id")
        target_id = action.payload.get("target_branch_id")
        archive_source = action.payload.get("archive_source", True)
        merge_mode = action.payload.get("merge_mode", "insights")

        branch_tree = cl.user_session.get("branch_tree")
        if not branch_tree:
            await cl.Message(content="No branches to merge.").send()
            return

        source_branch = branch_tree["branches"].get(source_id)
        target_branch = branch_tree["branches"].get(target_id)

        if not source_branch or not target_branch:
            await cl.Message(content="Source or target branch not found.").send()
            return

        # Show merging status
        msg = cl.Message(content="Merging branches...")
        await msg.send()

        # Extract insights from source branch using LLM
        source_history = source_branch.get("history", [])
        target_history = target_branch.get("history", [])

        merge_result = await extract_and_merge_insights(
            source_history=source_history,
            target_history=target_history,
            source_title=source_branch["title"],
            target_title=target_branch["title"],
            merge_mode=merge_mode
        )

        if merge_result["success"]:
            # Add merge summary as system message to target
            merge_message = {
                "role": "system",
                "content": f"[Merged from '{source_branch['title']}']\n\n{merge_result['merge_summary']}"
            }
            target_branch["history"].append(merge_message)
            target_branch["message_count"] += 1
            target_branch["last_activity"] = datetime.utcnow().isoformat()

            # Update source branch status
            if archive_source:
                source_branch["status"] = "merged"
                source_branch["merge_target"] = target_id

            # Update tree
            branch_tree["last_modified"] = datetime.utcnow().isoformat()
            cl.user_session.set("branch_tree", branch_tree)

            # Persist
            await save_branch_state(cl.user_session)

            # Show result
            await msg.update()
            await cl.Message(
                content=f"""**Merge Complete**

Merged insights from *{source_branch['title']}* into *{target_branch['title']}*.

**Key Insights Merged:**
{chr(10).join('- ' + i for i in merge_result['insights_merged'][:5])}

{f"**Conflicts Noted:**{chr(10)}{chr(10).join('- ' + c for c in merge_result['conflicts'][:3])}" if merge_result['conflicts'] else ""}
""",
                actions=[
                    cl.Action(name="switch_branch", payload={"branch_id": target_id}, label=f"Go to {target_branch['title']}"),
                    cl.Action(name="show_branch_selector", payload={}, label="View All Branches"),
                ]
            ).send()
        else:
            await msg.update()
            await cl.Message(content=f"Merge failed: {merge_result.get('error', 'Unknown error')}").send()

    except Exception as e:
        print(f"Merge error: {e}")
        await cl.Message(content=f"Unable to merge branches: {str(e)[:100]}").send()
```

### 3.4 Delete Branch

```python
@cl.action_callback("delete_branch")
async def on_delete_branch(action: cl.Action):
    """
    Delete (archive) a branch.

    Payload:
    - branch_id: str - branch to delete
    - permanent: bool - true = delete forever, false = archive (default)
    """
    try:
        branch_id = action.payload.get("branch_id")
        permanent = action.payload.get("permanent", False)

        branch_tree = cl.user_session.get("branch_tree")
        if not branch_tree:
            await cl.Message(content="No branches exist.").send()
            return

        # Cannot delete root branch
        if branch_id == branch_tree["root_branch_id"]:
            await cl.Message(content="Cannot delete the main conversation branch.").send()
            return

        # Cannot delete currently active branch
        if branch_id == branch_tree["active_branch_id"]:
            await cl.Message(
                content="Cannot delete the active branch. Switch to another branch first.",
                actions=[cl.Action(name="show_branch_selector", payload={}, label="Switch Branch")]
            ).send()
            return

        branch = branch_tree["branches"].get(branch_id)
        if not branch:
            await cl.Message(content="Branch not found.").send()
            return

        # Check for child branches
        children = [b for b in branch_tree["branches"].values() if b.get("parent_branch_id") == branch_id]
        if children:
            await cl.Message(
                content=f"Cannot delete branch with {len(children)} child branch(es). Delete children first.",
            ).send()
            return

        if permanent:
            # Hard delete
            del branch_tree["branches"][branch_id]
            # Remove from fork_points if this was the only branch at that point
            # (complex logic - simplified here)
        else:
            # Soft delete (archive)
            branch["status"] = "archived"
            branch["is_active"] = False

        branch_tree["last_modified"] = datetime.utcnow().isoformat()
        cl.user_session.set("branch_tree", branch_tree)

        await save_branch_state(cl.user_session)

        action_word = "deleted" if permanent else "archived"
        await cl.Message(
            content=f"Branch '{branch['title']}' has been {action_word}.",
            actions=[cl.Action(name="show_branch_selector", payload={}, label="View Branches")]
        ).send()

    except Exception as e:
        print(f"Delete branch error: {e}")
        await cl.Message(content=f"Unable to delete branch: {str(e)[:100]}").send()
```

### 3.5 Show Branch Selector

```python
@cl.action_callback("show_branch_selector")
async def on_show_branch_selector(action: cl.Action):
    """Toggle visibility of the BranchSelector custom element."""
    branch_tree = cl.user_session.get("branch_tree")

    if not branch_tree or len(branch_tree["branches"]) <= 1:
        await cl.Message(content="No branches to display. Use 'Fork Here' to create a branch.").send()
        return

    # Create BranchSelector element
    selector = cl.CustomElement(
        name="BranchSelector",
        props={
            "branches": list(branch_tree["branches"].values()),
            "activeBranchId": branch_tree["active_branch_id"],
            "rootBranchId": branch_tree["root_branch_id"],
            "forkPoints": branch_tree["fork_points"],
        },
        display="inline"
    )

    await cl.Message(content="", elements=[selector]).send()
```

---

## 4. UI Component Specification

### 4.1 BranchSelector.jsx

**Location:** `/public/elements/BranchSelector.jsx`

**Props:**
```typescript
interface BranchSelectorProps {
  branches: ConversationBranch[];        // All branches
  activeBranchId: string;                // Currently active
  rootBranchId: string;                  // Root branch ID
  forkPoints: number[];                  // Message indices with forks
  showTree?: boolean;                    // Show tree structure (default: true)
  compact?: boolean;                     // Minimal mode for sidebar
}
```

**Behavior:**
1. Display branches in tree structure (indentation shows parent-child)
2. Highlight active branch
3. Show status indicators (active, paused, merged, archived)
4. Click to switch branches (calls `switch_branch`)
5. Actions menu per branch: Rename, Merge, Delete
6. "New Branch" button at bottom

**Visual Design:**
```
+------------------------------------------+
|  Branches                            [+] |
+------------------------------------------+
|  [*] Main Conversation          12 msgs  |
|      [+] What if: No constraints   5 msgs |
|      [+] Red Team Analysis         8 msgs |
|          [ ] Deep Dive              3 msgs |
|  Legend: [*]=active [+]=paused [ ]=merged|
+------------------------------------------+
```

**Implementation Skeleton:**
```jsx
export default function BranchSelector() {
    const { callAction } = window.Chainlit || {};

    const {
        branches = [],
        activeBranchId = null,
        rootBranchId = null,
        forkPoints = [],
        showTree = true,
        compact = false,
    } = props || {};

    // Build tree structure from flat list
    const buildTree = (branches, parentId = null) => {
        return branches
            .filter(b => b.parent_branch_id === parentId)
            .map(branch => ({
                ...branch,
                children: buildTree(branches, branch.branch_id)
            }));
    };

    const tree = buildTree(branches, null);

    const handleSwitch = (branchId) => {
        if (callAction) {
            callAction({ name: 'switch_branch', payload: { branch_id: branchId } });
        }
    };

    const handleMerge = (sourceId, targetId) => {
        if (callAction) {
            callAction({
                name: 'merge_branches',
                payload: { source_branch_id: sourceId, target_branch_id: targetId }
            });
        }
    };

    const handleDelete = (branchId) => {
        if (callAction) {
            callAction({ name: 'delete_branch', payload: { branch_id: branchId } });
        }
    };

    const handleCreate = () => {
        if (callAction) {
            callAction({ name: 'fork_conversation', payload: {} });
        }
    };

    // Render tree recursively
    const renderBranch = (branch, depth = 0) => {
        const isActive = branch.branch_id === activeBranchId;
        const isRoot = branch.branch_id === rootBranchId;

        const statusIcons = {
            active: '*',
            paused: '+',
            merged: ' ',
            archived: 'x'
        };

        return (
            <div key={branch.branch_id}>
                <div
                    style={{
                        paddingLeft: `${depth * 20}px`,
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        padding: '8px',
                        backgroundColor: isActive ? '#e0e7ff' : 'transparent',
                        borderRadius: '4px',
                        cursor: 'pointer',
                    }}
                    onClick={() => handleSwitch(branch.branch_id)}
                >
                    <span style={{ fontFamily: 'monospace' }}>
                        [{statusIcons[branch.status] || '+'}]
                    </span>
                    <span style={{ flex: 1, fontWeight: isActive ? 600 : 400 }}>
                        {branch.title}
                    </span>
                    <span style={{ fontSize: '12px', color: '#6b7280' }}>
                        {branch.message_count} msgs
                    </span>
                </div>
                {branch.children?.map(child => renderBranch(child, depth + 1))}
            </div>
        );
    };

    return (
        <div style={{
            backgroundColor: '#ffffff',
            borderRadius: '8px',
            padding: '16px',
            boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
            maxWidth: '400px',
        }}>
            <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '12px',
            }}>
                <span style={{ fontWeight: 600 }}>Branches</span>
                <button
                    onClick={handleCreate}
                    style={{
                        padding: '4px 8px',
                        borderRadius: '4px',
                        border: '1px solid #d1d5db',
                        backgroundColor: '#ffffff',
                        cursor: 'pointer',
                    }}
                >
                    +
                </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                {tree.map(branch => renderBranch(branch, 0))}
            </div>

            <div style={{
                marginTop: '12px',
                fontSize: '11px',
                color: '#9ca3af',
                fontFamily: 'monospace',
            }}>
                [*]=active [+]=paused [ ]=merged
            </div>
        </div>
    );
}
```

### 4.2 Fork Point Indicator

**Integration with existing message display:**

Add a fork indicator that appears on messages where branches exist:

```jsx
// In message rendering (conceptual - actual implementation depends on Chainlit)
{forkPoints.includes(messageIndex) && (
    <div style={{
        position: 'absolute',
        right: '-20px',
        top: '50%',
        transform: 'translateY(-50%)',
    }}>
        <button
            onClick={() => callAction({ name: 'show_branch_selector', payload: {} })}
            title="Branches exist from this point"
            style={{
                width: '20px',
                height: '20px',
                borderRadius: '50%',
                backgroundColor: '#8b5cf6',
                color: 'white',
                fontSize: '12px',
                border: 'none',
                cursor: 'pointer',
            }}
        >
            {getBranchCountAtPoint(messageIndex)}
        </button>
    </div>
)}
```

---

## 5. Persistence Integration

### 5.1 Extend `save_cross_bot_context()`

Modify `/utils/context_persistence.py`:

```python
async def save_cross_bot_context(
    user_key: str,
    history: List[Dict],
    bot_id: str,
    bot_name: str,
    phases: Optional[List[Dict]] = None,
    current_phase: int = 0,
    conversation_id: Optional[str] = None,
    conversation_name: Optional[str] = None,
    # === Wave 2: Forking ===
    branch_tree: Optional[Dict] = None,
    active_branch_id: Optional[str] = None,
) -> bool:
    """
    Save context including branch tree structure.
    """
    last_checkpoint = datetime.utcnow().isoformat()

    context_data = {
        "user_key": user_key,
        "history": history[-100:],
        "last_bot_id": bot_id,
        "last_bot_name": bot_name,
        "timestamp": last_checkpoint,
        "message_count": len(history),
        "phases": phases or [],
        "current_phase": current_phase,
        "conversation_id": conversation_id,
        "conversation_name": conversation_name or "",
        "last_checkpoint": last_checkpoint,
        # === Wave 2 additions ===
        "branch_tree": branch_tree,  # Full BranchTree structure
        "active_branch_id": active_branch_id,
    }

    # ... rest of save logic unchanged ...
```

### 5.2 New `save_branch_state()` Helper

```python
async def save_branch_state(user_session) -> bool:
    """
    Convenience function to save current branch state.
    Called after any branch operation (fork, switch, merge, delete).
    """
    from utils.context_persistence import save_cross_bot_context

    context_key = get_context_key()

    return await save_cross_bot_context(
        user_key=context_key,
        history=user_session.get("history", []),
        bot_id=user_session.get("bot_id", "lawrence"),
        bot_name=BOTS.get(user_session.get("bot_id", "lawrence"), {}).get("name", "Lawrence"),
        phases=user_session.get("phases"),
        current_phase=user_session.get("current_phase", 0),
        conversation_id=user_session.get("conversation_id"),
        conversation_name=user_session.get("conversation_name"),
        branch_tree=user_session.get("branch_tree"),
        active_branch_id=user_session.get("active_branch_id"),
    )
```

### 5.3 Restore Branch State in `on_chat_start`

Add to `on_chat_start`:

```python
# === Wave 2: Restore Branch State ===
preserved_branch_tree = preserved_context.get("branch_tree")
preserved_active_branch_id = preserved_context.get("active_branch_id")

if preserved_branch_tree:
    cl.user_session.set("branch_tree", preserved_branch_tree)
    cl.user_session.set("active_branch_id", preserved_active_branch_id)
    cl.user_session.set("fork_points", preserved_branch_tree.get("fork_points", []))

    # If we have an active branch, restore its specific history
    if preserved_active_branch_id:
        active_branch = preserved_branch_tree["branches"].get(preserved_active_branch_id, {})
        cl.user_session.set("branch_history", active_branch.get("history", []))

    print(f"[FORKING] Restored branch tree with {len(preserved_branch_tree['branches'])} branches")
```

---

## 6. Implementation Checklist

### Phase 1: Core Infrastructure (Week 1)

| # | Task | File(s) | Status |
|---|------|---------|--------|
| 1 | Create `utils/forking_types.py` with TypedDict definitions | `utils/forking_types.py` | [ ] |
| 2 | Add branch state keys to `on_chat_start` | `mindrian_chat.py` | [ ] |
| 3 | Implement `get_composed_history()` utility | `utils/forking_utils.py` | [ ] |
| 4 | Extend `save_cross_bot_context()` with branch fields | `utils/context_persistence.py` | [ ] |
| 5 | Create `save_branch_state()` helper | `utils/forking_utils.py` | [ ] |
| 6 | Add branch restoration to `on_chat_start` | `mindrian_chat.py` | [ ] |

### Phase 2: Action Callbacks (Week 2)

| # | Task | File(s) | Status |
|---|------|---------|--------|
| 7 | Implement `fork_conversation` callback | `mindrian_chat.py` | [ ] |
| 8 | Implement `switch_branch` callback | `mindrian_chat.py` | [ ] |
| 9 | Implement `delete_branch` callback | `mindrian_chat.py` | [ ] |
| 10 | Implement `show_branch_selector` callback | `mindrian_chat.py` | [ ] |
| 11 | Implement `generate_branch_title()` utility | `utils/forking_utils.py` | [ ] |

### Phase 3: Merge Logic (Week 3)

| # | Task | File(s) | Status |
|---|------|---------|--------|
| 12 | Create `extract_and_merge_insights()` LLM function | `utils/forking_merge.py` | [ ] |
| 13 | Implement `merge_branches` callback | `mindrian_chat.py` | [ ] |
| 14 | Add merge conflict detection | `utils/forking_merge.py` | [ ] |

### Phase 4: UI Components (Week 4)

| # | Task | File(s) | Status |
|---|------|---------|--------|
| 15 | Create `BranchSelector.jsx` component | `public/elements/BranchSelector.jsx` | [ ] |
| 16 | Add "Fork Here" hover action to messages | `mindrian_chat.py` | [ ] |
| 17 | Add fork point indicators | TBD (depends on message rendering) | [ ] |
| 18 | Add branch count badge to UI | `public/elements/WorkshopRoadmap.jsx` | [ ] |

### Phase 5: Integration & Polish (Week 5)

| # | Task | File(s) | Status |
|---|------|---------|--------|
| 19 | Update `on_chat_resume` for branch state | `mindrian_chat.py` | [ ] |
| 20 | Add branch info to export/synthesize | `mindrian_chat.py` | [ ] |
| 21 | Add "what if" auto-fork suggestion | `mindrian_chat.py` (message handler) | [ ] |
| 22 | Write unit tests for forking logic | `tests/test_forking.py` | [ ] |
| 23 | Write integration tests | `tests/test_forking_integration.py` | [ ] |

---

## 7. Test Cases

### 7.1 Unit Tests

```python
# tests/test_forking.py

import pytest
from utils.forking_types import ConversationBranch, BranchTree
from utils.forking_utils import (
    get_composed_history,
    generate_branch_title,
    build_branch_tree,
)


class TestBranchCreation:
    """Test branch creation and tree structure."""

    def test_create_root_branch(self):
        """First fork creates root branch from existing conversation."""
        history = [{"role": "user", "content": "Hello"}]
        # ... implementation

    def test_fork_preserves_shared_history(self):
        """Messages before fork point are shared, not duplicated."""
        pass

    def test_nested_branching(self):
        """Can create branch from a branch (grandchild of root)."""
        pass


class TestBranchSwitching:
    """Test branch switching behavior."""

    def test_switch_saves_current_state(self):
        """Switching branches saves current branch's state."""
        pass

    def test_switch_restores_target_state(self):
        """Switching restores target branch's full state."""
        pass

    def test_composed_history_correct_after_switch(self):
        """get_composed_history returns correct history after switch."""
        pass


class TestHistoryComposition:
    """Test history composition from shared + branch-local."""

    def test_root_branch_returns_full_history(self):
        """Root branch returns all messages."""
        pass

    def test_child_branch_composes_correctly(self):
        """Child branch: shared[0:fork_point] + branch_local."""
        pass

    def test_grandchild_branch_composes_correctly(self):
        """Grandchild composes through full ancestry chain."""
        pass


class TestMerging:
    """Test branch merging."""

    def test_merge_extracts_insights(self):
        """Merge correctly extracts key insights from source."""
        pass

    def test_merge_detects_conflicts(self):
        """Conflicting conclusions are identified."""
        pass

    def test_merge_archives_source(self):
        """Source branch is archived after merge by default."""
        pass


class TestPersistence:
    """Test branch persistence to storage."""

    async def test_branch_tree_persists(self):
        """Branch tree is saved and restored correctly."""
        pass

    async def test_resume_restores_active_branch(self):
        """on_chat_resume restores to correct active branch."""
        pass
```

### 7.2 Integration Tests

```python
# tests/test_forking_integration.py

import pytest
from unittest.mock import AsyncMock, patch


class TestForkingWorkflow:
    """End-to-end forking workflow tests."""

    async def test_full_fork_switch_merge_cycle(self):
        """
        Complete workflow:
        1. Start conversation
        2. Fork at message 5
        3. Add messages to both branches
        4. Switch between branches
        5. Merge insights back
        6. Verify merged content
        """
        pass

    async def test_fork_during_workshop(self):
        """Forking preserves and restores workshop phase state."""
        pass

    async def test_persistence_across_restart(self):
        """Branch state survives server restart."""
        pass
```

### 7.3 Manual QA Checklist

```markdown
## Manual QA: Conversation Forking

### Setup
- [ ] Start new conversation with Lawrence
- [ ] Send at least 5 messages to build history

### Fork Creation
- [ ] Click "Fork Here" on message 3
- [ ] Verify new branch appears in BranchSelector
- [ ] Verify shared history (messages 1-3) visible
- [ ] Verify branch-local history is empty
- [ ] Send new message in forked branch
- [ ] Verify message only in this branch

### Branch Switching
- [ ] Click on main branch in BranchSelector
- [ ] Verify context switches (forked messages gone)
- [ ] Verify main branch messages visible
- [ ] Send message in main branch
- [ ] Switch back to fork
- [ ] Verify fork's messages restored
- [ ] Verify main's new message not visible

### Branch Merging
- [ ] Switch to main branch
- [ ] Click "Merge" on forked branch
- [ ] Verify merge summary appears
- [ ] Verify key insights extracted
- [ ] Verify source branch marked as merged

### Persistence
- [ ] Refresh page
- [ ] Verify branch tree restored
- [ ] Verify active branch correct
- [ ] Verify history correct

### Edge Cases
- [ ] Try to delete active branch (should fail)
- [ ] Try to delete root branch (should fail)
- [ ] Create nested branch (fork from fork)
- [ ] Switch between 3+ branches
```

---

## 8. Open Questions

1. **UI Placement:** Where should BranchSelector appear?
   - Option A: Sidebar (persistent, like WorkshopRoadmap)
   - Option B: Modal (on-demand, cleaner)
   - Option C: Floating panel (middle ground)

2. **Auto-fork Detection:** Should we auto-suggest forking when detecting "what if" language?
   - Pro: Helpful UX
   - Con: Could be intrusive

3. **Branch Limits:** Should we limit number of branches?
   - Suggested: Max 10 active branches per conversation
   - Archived branches don't count toward limit

4. **Merge Granularity:** Should merges be:
   - All-or-nothing (current design)
   - Selective (choose which insights to merge)

5. **Branch-Specific Bots:** Should branches allow switching bots mid-branch?
   - Current design: Yes, each branch tracks its own `bot_id`
   - Alternative: Lock bot at fork time

---

## 9. Dependencies

### Wave 1 Features Required

| Feature | Status | Required For |
|---------|--------|--------------|
| `conversation_id` in session | In Progress | Branch tree linking |
| `last_checkpoint` tracking | In Progress | Branch activity tracking |
| `excluded_topics` in session | In Progress | Per-branch topic exclusions |
| Extended `save_cross_bot_context()` | In Progress | Branch persistence |

### New Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| None | - | Uses existing infrastructure |

---

## 10. Future Enhancements (Post-Wave 2)

1. **Branch Templates:** Pre-configured branch types ("Red Team", "Optimistic", "Budget-Constrained")
2. **Branch Comparison View:** Side-by-side diff of two branches
3. **Branch Sharing:** Share a branch with another user
4. **Time Travel:** "Undo to fork point" functionality
5. **Branch Analytics:** Track which branches led to insights

---

*End of Design Document*
