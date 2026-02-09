"""
Conversation Forking - Wave 2 Implementation
=============================================

Enables "git-like" branching for conversations:
- Fork: Create alternative exploration path
- Switch: Navigate between branches
- Merge: Combine insights from branches

Light implementation focusing on UX essentials.
"""

import uuid
import re
import logging
from typing import TypedDict, Optional, List, Dict, Any
from datetime import datetime

logger = logging.getLogger("forking")


# === Type Definitions ===

class ConversationBranch(TypedDict):
    """A single branch in the conversation tree."""
    branch_id: str
    parent_branch_id: Optional[str]
    fork_point_index: int  # Where in parent history this branch forked
    title: str
    created_at: str
    status: str  # active, paused, merged, archived
    history: List[Dict[str, Any]]  # Branch-local messages (after fork point)
    bot_id: str
    message_count: int


class BranchTree(TypedDict):
    """Complete branch tree for a session."""
    root_branch_id: str
    branches: Dict[str, ConversationBranch]
    active_branch_id: str
    conversation_id: str


# === Core Functions ===

def create_branch_tree(conversation_id: str, bot_id: str = "lawrence") -> BranchTree:
    """Initialize a branch tree with root branch."""
    root_id = str(uuid.uuid4())[:8]

    root_branch: ConversationBranch = {
        "branch_id": root_id,
        "parent_branch_id": None,
        "fork_point_index": 0,
        "title": "Main Conversation",
        "created_at": datetime.now().isoformat(),
        "status": "active",
        "history": [],
        "bot_id": bot_id,
        "message_count": 0,
    }

    return {
        "root_branch_id": root_id,
        "branches": {root_id: root_branch},
        "active_branch_id": root_id,
        "conversation_id": conversation_id,
    }


def generate_branch_title(context: str, branch_count: int) -> str:
    """Generate descriptive branch title from context."""
    context_lower = context.lower()

    if re.search(r"what if|alternatively|suppose|imagine", context_lower):
        return f"What If #{branch_count}"
    elif re.search(r"devil|advocate|challenge|attack|red team", context_lower):
        return f"Red Team #{branch_count}"
    elif re.search(r"let me try|different|another way|option", context_lower):
        return f"Alternative #{branch_count}"
    elif re.search(r"explore|tangent|side|unrelated", context_lower):
        return f"Exploration #{branch_count}"
    else:
        return f"Branch #{branch_count}"


def fork_conversation(
    branch_tree: BranchTree,
    shared_history: List[Dict],
    fork_context: str = "",
    bot_id: str = ""
) -> tuple[BranchTree, str]:
    """
    Create a new branch from current position.

    Returns: (updated_tree, new_branch_id)
    """
    current_branch = branch_tree["branches"][branch_tree["active_branch_id"]]
    branch_count = len(branch_tree["branches"])

    # Generate new branch
    new_id = str(uuid.uuid4())[:8]
    title = generate_branch_title(fork_context, branch_count)

    new_branch: ConversationBranch = {
        "branch_id": new_id,
        "parent_branch_id": branch_tree["active_branch_id"],
        "fork_point_index": len(shared_history),
        "title": title,
        "created_at": datetime.now().isoformat(),
        "status": "active",
        "history": [],  # Starts empty - fork point is where parent history ends
        "bot_id": bot_id or current_branch["bot_id"],
        "message_count": 0,
    }

    # Update parent to paused
    current_branch["status"] = "paused"

    # Add to tree
    branch_tree["branches"][new_id] = new_branch
    branch_tree["active_branch_id"] = new_id

    logger.info(f"[FORK] Created branch '{title}' ({new_id}) from {branch_tree['active_branch_id']}")

    return branch_tree, new_id


def switch_branch(branch_tree: BranchTree, target_branch_id: str) -> BranchTree:
    """Switch to a different branch."""
    if target_branch_id not in branch_tree["branches"]:
        logger.warning(f"[SWITCH] Branch {target_branch_id} not found")
        return branch_tree

    # Pause current branch
    current = branch_tree["branches"][branch_tree["active_branch_id"]]
    if current["status"] == "active":
        current["status"] = "paused"

    # Activate target
    target = branch_tree["branches"][target_branch_id]
    target["status"] = "active"
    branch_tree["active_branch_id"] = target_branch_id

    logger.info(f"[SWITCH] Switched to branch '{target['title']}' ({target_branch_id})")

    return branch_tree


def get_composed_history(
    branch_tree: BranchTree,
    shared_history: List[Dict]
) -> List[Dict]:
    """
    Compose full history for active branch.

    Returns: shared history up to fork point + branch-local history
    """
    if not branch_tree:
        return shared_history

    active_branch = branch_tree["branches"].get(branch_tree["active_branch_id"])
    if not active_branch:
        return shared_history

    # For root branch, just return shared history
    if active_branch["parent_branch_id"] is None:
        return shared_history

    # For child branches, compose from fork point
    fork_point = active_branch["fork_point_index"]
    composed = shared_history[:fork_point] + active_branch["history"]

    return composed


def add_message_to_branch(
    branch_tree: BranchTree,
    message: Dict[str, Any]
) -> BranchTree:
    """Add a message to the active branch's history."""
    active_branch = branch_tree["branches"][branch_tree["active_branch_id"]]
    active_branch["history"].append(message)
    active_branch["message_count"] = len(active_branch["history"])
    return branch_tree


def get_branch_list_for_ui(branch_tree: BranchTree) -> List[Dict]:
    """Get branch list formatted for BranchSelector component."""
    if not branch_tree:
        return []

    branches = []
    for branch_id, branch in branch_tree["branches"].items():
        branches.append({
            "id": branch_id,
            "title": branch["title"],
            "messageCount": branch["message_count"],
            "status": branch["status"],
            "isActive": branch_id == branch_tree["active_branch_id"],
            "parentId": branch["parent_branch_id"],
            "createdAt": branch["created_at"],
        })

    return branches


def merge_branches(
    branch_tree: BranchTree,
    source_branch_id: str,
    target_branch_id: str,
    merge_summary: str = ""
) -> tuple[BranchTree, Dict]:
    """
    Merge insights from source into target branch.

    Returns: (updated_tree, merge_result)
    """
    source = branch_tree["branches"].get(source_branch_id)
    target = branch_tree["branches"].get(target_branch_id)

    if not source or not target:
        return branch_tree, {"success": False, "error": "Branch not found"}

    # Extract key messages from source (last 5 or all if less)
    insights = source["history"][-5:] if source["history"] else []

    # Mark source as merged
    source["status"] = "merged"

    # Add merge note to target
    merge_message = {
        "role": "system",
        "content": f"[Merged from '{source['title']}']\n{merge_summary}" if merge_summary else f"[Merged {len(insights)} messages from '{source['title']}']"
    }
    target["history"].append(merge_message)

    result = {
        "success": True,
        "source_title": source["title"],
        "target_title": target["title"],
        "insights_count": len(insights),
        "merge_summary": merge_summary,
    }

    logger.info(f"[MERGE] Merged '{source['title']}' into '{target['title']}'")

    return branch_tree, result


def delete_branch(branch_tree: BranchTree, branch_id: str) -> BranchTree:
    """Archive (soft-delete) a branch."""
    if branch_id == branch_tree["root_branch_id"]:
        logger.warning("[DELETE] Cannot delete root branch")
        return branch_tree

    branch = branch_tree["branches"].get(branch_id)
    if branch:
        branch["status"] = "archived"

        # If deleting active branch, switch to root
        if branch_id == branch_tree["active_branch_id"]:
            branch_tree["active_branch_id"] = branch_tree["root_branch_id"]
            branch_tree["branches"][branch_tree["root_branch_id"]]["status"] = "active"

    return branch_tree
