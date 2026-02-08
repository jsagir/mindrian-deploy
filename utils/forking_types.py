"""
Conversation Forking - Type Definitions
Wave 2 of Mindrian Session Management

Provides TypedDict definitions for:
- ConversationBranch: A single branch in the conversation tree
- BranchTree: Complete branch tree for a conversation
- MergeResult: Result of merging two branches
- BranchStatus: Branch lifecycle status enum
"""

from typing import TypedDict, Optional, List, Dict, Any
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
    error: Optional[str]                    # Error message if failed
