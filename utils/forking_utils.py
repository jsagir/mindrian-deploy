"""
Conversation Forking - Utility Functions
Wave 2 of Mindrian Session Management

Provides utilities for:
- History composition (shared + branch-local)
- Branch title auto-generation
- Branch state persistence helpers
"""

import re
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

from utils.forking_types import ConversationBranch, BranchTree, BranchStatus


def get_composed_history(user_session) -> List[Dict]:
    """
    Compose full history from shared + branch-local messages.

    If no branching: return history as-is
    If branched: return parent history up to fork + branch history

    This is the KEY function for maintaining correct LLM context
    when branches are involved.
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
    return _compose_branch_history(branch_tree, active_branch_id)


def _compose_branch_history(branch_tree: Dict, branch_id: str) -> List[Dict]:
    """
    Recursively compose history from ancestry chain.

    Handles nested branches (grandchildren of root).
    """
    branch = branch_tree["branches"].get(branch_id)
    if not branch:
        return []

    parent_branch_id = branch.get("parent_branch_id")
    if not parent_branch_id:
        # This is root - return full history
        return branch.get("history", [])

    parent = branch_tree["branches"].get(parent_branch_id)
    if not parent:
        # Parent missing - return just this branch's history
        return branch.get("history", [])

    # Get parent's composed history (recursive for nested branches)
    parent_history = _compose_branch_history(branch_tree, parent_branch_id)

    # Take history up to fork point
    fork_point = branch["fork_point_message_index"]
    shared_history = parent_history[:fork_point]

    # Add this branch's local history
    branch_history = branch.get("history", [])

    return shared_history + branch_history


def generate_branch_title(
    fork_context: str,
    parent_title: str,
    branch_count: int
) -> str:
    """
    Generate a descriptive branch title based on context.

    Examples:
    - "What if: No budget constraints"
    - "Red Team: Main Conversation"
    - "Alternative: Market Analysis"
    - "Exploration #3"

    Args:
        fork_context: Last few messages before fork (for pattern matching)
        parent_title: Parent branch title for context
        branch_count: Number of existing branches (for fallback naming)

    Returns:
        Human-readable branch title
    """
    # Quick pattern matching first (no API call)
    patterns = {
        r"what if|alternatively|suppose|imagine|hypothetically": "What if",
        r"devil'?s advocate|challenge|attack|red team|stress.?test": "Red Team",
        r"let me try|different approach|another way|let'?s try": "Alternative",
        r"explore|tangent|side note|unrelated|quick detour": "Exploration",
        r"pessimistic|worst case|conservative|skeptical": "Pessimistic",
        r"optimistic|best case|ideal|ambitious": "Optimistic",
        r"deep dive|dig deeper|focus on|zoom in": "Deep Dive",
        r"compare|versus|vs\.?|or instead": "Comparison",
    }

    context_lower = fork_context.lower()
    for pattern, prefix in patterns.items():
        if re.search(pattern, context_lower):
            # Extract a meaningful suffix from parent title or context
            suffix = _extract_topic_suffix(parent_title, fork_context)
            return f"{prefix}: {suffix}"

    # Fallback to numbered branch
    return f"Branch #{branch_count + 1}"


def _extract_topic_suffix(parent_title: str, context: str) -> str:
    """Extract a short topic suffix for branch title."""
    # If parent is "Main Conversation", try to extract from context
    if parent_title.lower() in ["main conversation", "root"]:
        # Take first non-trivial word from context
        words = context.split()
        for word in words:
            clean = re.sub(r'[^\w]', '', word)
            if len(clean) > 3 and clean.lower() not in ["what", "let's", "maybe", "could", "would", "should"]:
                return clean.capitalize()
        return "Analysis"

    # Otherwise use parent title
    return parent_title


def create_root_branch(
    history: List[Dict],
    bot_id: str,
    phases: List[Dict],
    current_phase: int,
    excluded_topics: List[str],
    conversation_id: str,
) -> Dict:
    """
    Create the root branch when first fork is made.

    The root branch represents the original conversation before any forking.
    """
    root_branch_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    root_branch = {
        "branch_id": root_branch_id,
        "parent_branch_id": None,
        "fork_point_message_index": 0,
        "title": "Main Conversation",
        "created_at": now,
        "status": BranchStatus.PAUSED.value,  # Will switch to new branch
        "is_active": False,
        "history": history.copy(),
        "bot_id": bot_id,
        "phases": [p.copy() for p in phases] if phases else [],
        "current_phase": current_phase,
        "excluded_topics": excluded_topics.copy() if excluded_topics else [],
        "message_count": len(history),
        "last_activity": now,
        "merge_target": None,
    }

    branch_tree = {
        "root_branch_id": root_branch_id,
        "branches": {root_branch_id: root_branch},
        "active_branch_id": root_branch_id,
        "fork_points": [],
        "conversation_id": conversation_id,
        "created_at": now,
        "last_modified": now,
    }

    return branch_tree


def create_new_branch(
    branch_tree: Dict,
    parent_branch_id: str,
    fork_at_index: int,
    title: str,
    bot_id: str,
    phases: List[Dict],
    current_phase: int,
    excluded_topics: List[str],
    copy_excluded: bool = True,
) -> str:
    """
    Create a new branch from an existing branch.

    Args:
        branch_tree: The existing branch tree
        parent_branch_id: Branch to fork from
        fork_at_index: Message index in parent where fork occurs
        title: Title for new branch
        bot_id: Current bot ID
        phases: Workshop phases
        current_phase: Current phase index
        excluded_topics: Topics to exclude
        copy_excluded: Whether to copy excluded topics from parent

    Returns:
        new_branch_id: UUID of the new branch
    """
    new_branch_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    new_branch = {
        "branch_id": new_branch_id,
        "parent_branch_id": parent_branch_id,
        "fork_point_message_index": fork_at_index,
        "title": title,
        "created_at": now,
        "status": BranchStatus.ACTIVE.value,
        "is_active": True,
        "history": [],  # New branch starts empty (inherits shared history)
        "bot_id": bot_id,
        "phases": [p.copy() for p in phases] if phases else [],
        "current_phase": current_phase,
        "excluded_topics": excluded_topics.copy() if copy_excluded and excluded_topics else [],
        "message_count": 0,
        "last_activity": now,
        "merge_target": None,
    }

    # Update parent branch status
    if parent_branch_id in branch_tree["branches"]:
        branch_tree["branches"][parent_branch_id]["status"] = BranchStatus.PAUSED.value
        branch_tree["branches"][parent_branch_id]["is_active"] = False

    # Add new branch
    branch_tree["branches"][new_branch_id] = new_branch
    branch_tree["active_branch_id"] = new_branch_id

    # Update fork points
    if fork_at_index not in branch_tree["fork_points"]:
        branch_tree["fork_points"].append(fork_at_index)
        branch_tree["fork_points"] = sorted(branch_tree["fork_points"])

    branch_tree["last_modified"] = now

    return new_branch_id


def switch_to_branch(
    branch_tree: Dict,
    target_branch_id: str,
    current_session: Dict,
) -> Dict:
    """
    Switch to a different branch, saving current state.

    Args:
        branch_tree: The branch tree
        target_branch_id: Branch to switch to
        current_session: Current session state dict with branch_history, bot_id, etc.

    Returns:
        Updated branch_tree
    """
    current_branch_id = branch_tree["active_branch_id"]
    now = datetime.utcnow().isoformat()

    # Save current branch state
    if current_branch_id in branch_tree["branches"]:
        current_branch = branch_tree["branches"][current_branch_id]
        current_branch["history"] = current_session.get("branch_history", [])
        current_branch["status"] = BranchStatus.PAUSED.value
        current_branch["is_active"] = False
        current_branch["last_activity"] = now
        current_branch["bot_id"] = current_session.get("bot_id", "lawrence")
        current_branch["phases"] = current_session.get("phases", [])
        current_branch["current_phase"] = current_session.get("current_phase", 0)
        current_branch["excluded_topics"] = current_session.get("excluded_topics", [])
        current_branch["message_count"] = len(current_branch["history"])

    # Activate target branch
    if target_branch_id in branch_tree["branches"]:
        target_branch = branch_tree["branches"][target_branch_id]
        target_branch["status"] = BranchStatus.ACTIVE.value
        target_branch["is_active"] = True

    branch_tree["active_branch_id"] = target_branch_id
    branch_tree["last_modified"] = now

    return branch_tree


def get_branch_children(branch_tree: Dict, branch_id: str) -> List[Dict]:
    """Get all direct children of a branch."""
    return [
        b for b in branch_tree["branches"].values()
        if b.get("parent_branch_id") == branch_id
    ]


def can_delete_branch(branch_tree: Dict, branch_id: str) -> tuple:
    """
    Check if a branch can be deleted.

    Returns:
        (can_delete: bool, reason: str)
    """
    # Cannot delete root
    if branch_id == branch_tree["root_branch_id"]:
        return False, "Cannot delete the main conversation branch"

    # Cannot delete active branch
    if branch_id == branch_tree["active_branch_id"]:
        return False, "Cannot delete the active branch. Switch to another branch first."

    # Cannot delete branch with children
    children = get_branch_children(branch_tree, branch_id)
    if children:
        return False, f"Cannot delete branch with {len(children)} child branch(es). Delete children first."

    return True, ""


def archive_branch(branch_tree: Dict, branch_id: str) -> Dict:
    """Archive (soft delete) a branch."""
    if branch_id in branch_tree["branches"]:
        branch_tree["branches"][branch_id]["status"] = BranchStatus.ARCHIVED.value
        branch_tree["branches"][branch_id]["is_active"] = False
        branch_tree["last_modified"] = datetime.utcnow().isoformat()
    return branch_tree


def delete_branch_permanent(branch_tree: Dict, branch_id: str) -> Dict:
    """Permanently delete a branch."""
    if branch_id in branch_tree["branches"]:
        del branch_tree["branches"][branch_id]
        branch_tree["last_modified"] = datetime.utcnow().isoformat()
    return branch_tree


def get_branch_count_at_point(branch_tree: Dict, message_index: int) -> int:
    """Count how many branches fork from a specific message index."""
    count = 0
    for branch in branch_tree["branches"].values():
        if branch.get("fork_point_message_index") == message_index:
            count += 1
    return count


def detect_fork_intent(message: str) -> bool:
    """
    Detect if user's message suggests they want to fork/explore alternatives.

    Returns True if message contains fork-suggesting language.
    """
    fork_patterns = [
        r"what if",
        r"alternatively",
        r"let me try a different",
        r"let's explore another",
        r"on the other hand",
        r"devil's advocate",
        r"suppose instead",
        r"imagine if",
        r"hypothetically",
        r"what about if we",
        r"could we also consider",
        r"let me think about this differently",
        r"branching off from that",
        r"tangent",
        r"side thought",
    ]

    message_lower = message.lower()
    for pattern in fork_patterns:
        if re.search(pattern, message_lower):
            return True
    return False
