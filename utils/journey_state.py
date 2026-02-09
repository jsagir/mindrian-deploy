"""
PWS Journey State Management
============================

LangGraph-style state management for Chainlit environment.
Implements the hybrid LLM Router integration with proper reducers,
cost tracking, caching, and checkpoint persistence.
"""

import os
import json
import hashlib
import asyncio
from typing import Annotated, TypedDict, Optional, List, Dict, Literal, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from functools import wraps

# ============================================================================
# CUSTOM REDUCERS
# ============================================================================

def merge_dicts(left: dict, right: dict) -> dict:
    """Merge dictionaries, right overwrites left."""
    if left is None:
        return right or {}
    if right is None:
        return left or {}
    return {**left, **right}


def append_list(left: list, right: list) -> list:
    """Append lists."""
    if left is None:
        return right or []
    if right is None:
        return left or []
    return left + right


def append_unique(left: list, right: list) -> list:
    """Append only unique items."""
    if left is None:
        return right or []
    if right is None:
        return left or []
    seen = set(str(x) for x in left)
    return left + [x for x in right if str(x) not in seen]


def sum_numbers(left: float, right: float) -> float:
    """Sum numeric values."""
    return (left or 0) + (right or 0)


# ============================================================================
# STATE SCHEMA
# ============================================================================

class CostState(TypedDict):
    """Cost tracking state (separate from journey for clean separation)."""
    total_cost_usd: float
    calls_by_provider: Dict[str, int]  # {anthropic: 5, google: 10, tavily: 3}
    costs_by_provider: Dict[str, float]  # {anthropic: 0.05, google: 0.001}
    costs_by_task: Dict[str, float]  # {orchestration: 0.04, bulk: 0.001}
    last_call_cost: float
    session_start: str


class PWSJourneyState(TypedDict):
    """
    Complete PWS Journey state with LangGraph-style reducers.

    Fields marked with Annotated have custom reducers:
    - merge_dicts: Dictionaries get merged
    - append_list: Lists get appended
    - append_unique: Lists append only unique items
    - (no annotation): Value overwrites
    """

    # === Identity (set once) ===
    journey_id: str
    user_id: str
    started_at: str

    # === Problem Input (overwrites) ===
    problem_statement: str
    user_context: str

    # === Classification (overwrites on reassessment) ===
    problem_type: Literal["undefined", "ill_defined", "well_defined", "wicked", None]
    cynefin_domain: Literal["clear", "complicated", "complex", "chaotic", None]
    wickedness_score: float
    classification_confidence: float
    classification_reasoning: str
    classification_evidence: Annotated[List[str], append_list]

    # === Current Phase (overwrites) ===
    current_phase: Literal["intake", "classify", "enrich", "generate_questions", "guide", "probe", "reassess", "checkpoint"]
    phase_iteration: int
    max_iterations: int

    # === Knowledge Enrichment (merge/append) ===
    neo4j_context: Annotated[Dict, merge_dicts]
    filesearch_context: Annotated[Dict, merge_dicts]
    recommended_tools: Annotated[List[str], append_unique]
    recommended_frameworks: Annotated[List[str], append_unique]

    # === Journey Progress (append) ===
    checkpoints: Annotated[List[Dict], append_list]
    insights: Annotated[List[Dict], append_list]
    probes_executed: Annotated[List[Dict], append_list]

    # === Beautiful Questions (append unique) ===
    why_questions: Annotated[List[Dict], append_unique]
    what_if_questions: Annotated[List[Dict], append_unique]
    how_questions: Annotated[List[Dict], append_unique]
    priority_question: str

    # === Reassessment Tracking ===
    reassessment_triggers: Annotated[List[str], append_list]
    domain_transitions: Annotated[List[Dict], append_list]

    # === Output ===
    guidance_message: str
    available_actions: List[str]

    # === Cost Tracking (separate substate) ===
    cost_state: CostState

    # === Error Handling ===
    last_error: Optional[str]
    error_count: int
    fallback_mode: bool  # True if using degraded model due to errors


# ============================================================================
# STATE MANAGER (Chainlit Adapter)
# ============================================================================

class JourneyStateManager:
    """
    Manages PWS Journey state in Chainlit environment.
    Provides LangGraph-style state updates with reducers.
    """

    def __init__(self, cl_user_session):
        """Initialize with Chainlit user session."""
        self.session = cl_user_session
        self._cache = {}  # In-memory cache for expensive operations

    def get_state(self) -> PWSJourneyState:
        """Get current journey state."""
        return self.session.get("journey_state", self._create_initial_state())

    def _create_initial_state(self) -> PWSJourneyState:
        """Create initial empty state."""
        import uuid
        return {
            "journey_id": f"journey_{uuid.uuid4().hex[:8]}",
            "user_id": "",
            "started_at": datetime.now().isoformat(),
            "problem_statement": "",
            "user_context": "",
            "problem_type": None,
            "cynefin_domain": None,
            "wickedness_score": 0.0,
            "classification_confidence": 0.0,
            "classification_reasoning": "",
            "classification_evidence": [],
            "current_phase": "intake",
            "phase_iteration": 0,
            "max_iterations": 10,
            "neo4j_context": {},
            "filesearch_context": {},
            "recommended_tools": [],
            "recommended_frameworks": [],
            "checkpoints": [],
            "insights": [],
            "probes_executed": [],
            "why_questions": [],
            "what_if_questions": [],
            "how_questions": [],
            "priority_question": "",
            "reassessment_triggers": [],
            "domain_transitions": [],
            "guidance_message": "",
            "available_actions": [],
            "cost_state": {
                "total_cost_usd": 0.0,
                "calls_by_provider": {},
                "costs_by_provider": {},
                "costs_by_task": {},
                "last_call_cost": 0.0,
                "session_start": datetime.now().isoformat(),
            },
            "last_error": None,
            "error_count": 0,
            "fallback_mode": False,
        }

    def update_state(self, updates: Dict[str, Any]) -> PWSJourneyState:
        """
        Update state with LangGraph-style reducers.

        Args:
            updates: Partial state updates

        Returns:
            Updated full state
        """
        current = self.get_state()

        # Define which fields use which reducers
        MERGE_FIELDS = {"neo4j_context", "filesearch_context", "cost_state"}
        APPEND_FIELDS = {"classification_evidence", "checkpoints", "insights",
                        "probes_executed", "reassessment_triggers", "domain_transitions"}
        APPEND_UNIQUE_FIELDS = {"recommended_tools", "recommended_frameworks",
                               "why_questions", "what_if_questions", "how_questions"}

        for key, value in updates.items():
            if key in MERGE_FIELDS:
                current[key] = merge_dicts(current.get(key), value)
            elif key in APPEND_FIELDS:
                current[key] = append_list(current.get(key, []), value if isinstance(value, list) else [value])
            elif key in APPEND_UNIQUE_FIELDS:
                current[key] = append_unique(current.get(key, []), value if isinstance(value, list) else [value])
            else:
                # Overwrite
                current[key] = value

        # Save back to session
        self.session.set("journey_state", current)
        return current

    def record_cost(self, provider: str, task: str, cost: float):
        """Record an API call cost."""
        cost_state = self.get_state().get("cost_state", {})

        # Update totals
        cost_state["total_cost_usd"] = cost_state.get("total_cost_usd", 0) + cost
        cost_state["last_call_cost"] = cost

        # Update by provider
        calls = cost_state.get("calls_by_provider", {})
        calls[provider] = calls.get(provider, 0) + 1
        cost_state["calls_by_provider"] = calls

        costs = cost_state.get("costs_by_provider", {})
        costs[provider] = costs.get(provider, 0) + cost
        cost_state["costs_by_provider"] = costs

        # Update by task
        task_costs = cost_state.get("costs_by_task", {})
        task_costs[task] = task_costs.get(task, 0) + cost
        cost_state["costs_by_task"] = task_costs

        self.update_state({"cost_state": cost_state})

    def record_error(self, error: str, enter_fallback: bool = False):
        """Record an error and optionally enter fallback mode."""
        current = self.get_state()
        self.update_state({
            "last_error": error,
            "error_count": current.get("error_count", 0) + 1,
            "fallback_mode": enter_fallback or current.get("fallback_mode", False),
        })

    def clear_error(self):
        """Clear error state."""
        self.update_state({
            "last_error": None,
            "fallback_mode": False,
        })

    def get_cache_key(self, operation: str, *args) -> str:
        """Generate cache key for expensive operations."""
        content = f"{operation}:{':'.join(str(a)[:100] for a in args)}"
        return hashlib.md5(content.encode()).hexdigest()

    def get_cached(self, key: str) -> Optional[Any]:
        """Get cached result."""
        return self._cache.get(key)

    def set_cached(self, key: str, value: Any, ttl_seconds: int = 3600):
        """Cache a result (in-memory, session-scoped)."""
        self._cache[key] = {
            "value": value,
            "expires": datetime.now().timestamp() + ttl_seconds,
        }

    def is_cache_valid(self, key: str) -> bool:
        """Check if cache entry is still valid."""
        entry = self._cache.get(key)
        if not entry:
            return False
        return entry["expires"] > datetime.now().timestamp()


# ============================================================================
# NODE EXECUTOR (LangGraph-style)
# ============================================================================

class JourneyNodeExecutor:
    """
    Executes journey nodes with proper error handling,
    cost tracking, and caching.
    """

    def __init__(self, state_manager: JourneyStateManager):
        self.state = state_manager
        self._nodes = {}

    def register_node(self, name: str, func: Callable):
        """Register a node function."""
        self._nodes[name] = func

    async def execute_node(self, node_name: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a node with error handling and cost tracking.

        Returns:
            Dict with {success, result, error, cost}
        """
        from utils.llm_router import cost_tracker

        if node_name not in self._nodes:
            return {"success": False, "error": f"Unknown node: {node_name}"}

        # Get cost before
        cost_before = cost_tracker.get_session_summary()["total_cost_usd"]

        try:
            # Check if in fallback mode
            current_state = self.state.get_state()
            if current_state.get("fallback_mode"):
                kwargs["fallback_mode"] = True

            # Execute node
            result = await self._nodes[node_name](current_state, **kwargs)

            # Calculate cost for this node
            cost_after = cost_tracker.get_session_summary()["total_cost_usd"]
            node_cost = cost_after - cost_before

            # Update state with result
            if isinstance(result, dict):
                self.state.update_state(result)

            # Record cost
            self.state.record_cost(
                provider="mixed",  # Node may use multiple providers
                task=node_name,
                cost=node_cost,
            )

            # Clear any previous errors on success
            self.state.clear_error()

            return {
                "success": True,
                "result": result,
                "cost": node_cost,
            }

        except Exception as e:
            import traceback
            error_msg = f"{type(e).__name__}: {str(e)}"

            # Record error
            self.state.record_error(error_msg)

            # Check if we should enter fallback mode
            error_count = self.state.get_state().get("error_count", 0)
            if error_count >= 3:
                self.state.record_error(error_msg, enter_fallback=True)

            return {
                "success": False,
                "error": error_msg,
                "traceback": traceback.format_exc(),
            }

    def get_next_node(self, current_phase: str, state: PWSJourneyState) -> str:
        """
        Determine next node based on current phase and state.
        Implements the journey graph routing.
        """
        # Check loop limits
        if state.get("phase_iteration", 0) >= state.get("max_iterations", 10):
            return "checkpoint"  # Force checkpoint to prevent infinite loop

        # Check for reassessment triggers
        if state.get("reassessment_triggers") and current_phase not in ["reassess", "intake"]:
            return "reassess"

        # Standard flow
        FLOW = {
            "intake": "classify",
            "classify": "enrich",
            "enrich": "generate_questions",
            "generate_questions": "guide",
            "guide": "await_user",  # Wait for user action
            "probe": "guide",  # After probe, return to guide
            "reassess": "enrich" if state.get("domain_transitions") else "guide",
            "checkpoint": "guide",
        }

        return FLOW.get(current_phase, "guide")


# ============================================================================
# CHECKPOINT PERSISTENCE
# ============================================================================

class CheckpointManager:
    """Manages checkpoint persistence for cross-session recovery."""

    @staticmethod
    async def save_checkpoint(state: PWSJourneyState, checkpoint_name: str = None) -> Dict:
        """Save a checkpoint to Supabase."""
        try:
            from supabase import create_client

            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_SERVICE_KEY")

            if not url or not key:
                return {"success": False, "error": "Supabase not configured"}

            supabase = create_client(url, key)

            checkpoint = {
                "journey_id": state["journey_id"],
                "checkpoint_name": checkpoint_name or f"checkpoint_{len(state.get('checkpoints', [])) + 1}",
                "phase": state["current_phase"],
                "problem_type": state["problem_type"],
                "cynefin_domain": state["cynefin_domain"],
                "full_state": state,
                "created_at": datetime.now().isoformat(),
            }

            result = supabase.table("pws_journey_checkpoints").upsert(checkpoint).execute()

            return {"success": True, "checkpoint_id": checkpoint["checkpoint_name"]}

        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    async def restore_checkpoint(journey_id: str, checkpoint_name: str = None) -> Optional[PWSJourneyState]:
        """Restore journey state from checkpoint."""
        try:
            from supabase import create_client

            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_SERVICE_KEY")

            if not url or not key:
                return None

            supabase = create_client(url, key)

            query = supabase.table("pws_journey_checkpoints") \
                .select("full_state") \
                .eq("journey_id", journey_id)

            if checkpoint_name:
                query = query.eq("checkpoint_name", checkpoint_name)
            else:
                query = query.order("created_at", desc=True).limit(1)

            result = query.execute()

            if result.data:
                return result.data[0]["full_state"]
            return None

        except Exception as e:
            print(f"[CHECKPOINT] Restore failed: {e}")
            return None

    @staticmethod
    async def list_checkpoints(journey_id: str) -> List[Dict]:
        """List all checkpoints for a journey."""
        try:
            from supabase import create_client

            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_SERVICE_KEY")

            if not url or not key:
                return []

            supabase = create_client(url, key)

            result = supabase.table("pws_journey_checkpoints") \
                .select("checkpoint_name, phase, problem_type, cynefin_domain, created_at") \
                .eq("journey_id", journey_id) \
                .order("created_at", desc=True) \
                .execute()

            return result.data if result.data else []

        except Exception as e:
            print(f"[CHECKPOINT] List failed: {e}")
            return []


# ============================================================================
# CACHING DECORATOR
# ============================================================================

def cached_llm_call(ttl_seconds: int = 3600):
    """
    Decorator for caching expensive LLM calls.

    Usage:
        @cached_llm_call(ttl_seconds=3600)
        async def classify_problem(state, problem):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(state_manager: JourneyStateManager, *args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = state_manager.get_cache_key(
                func.__name__,
                *args,
                *[f"{k}={v}" for k, v in sorted(kwargs.items())]
            )

            # Check cache
            if state_manager.is_cache_valid(cache_key):
                cached = state_manager.get_cached(cache_key)
                if cached:
                    print(f"[CACHE] Hit for {func.__name__}")
                    return cached["value"]

            # Execute function
            result = await func(state_manager, *args, **kwargs)

            # Cache result
            state_manager.set_cached(cache_key, result, ttl_seconds)
            print(f"[CACHE] Stored for {func.__name__}")

            return result

        return wrapper
    return decorator


# ============================================================================
# JOURNEY GRAPH DEFINITION
# ============================================================================

def create_journey_graph() -> Dict[str, Dict]:
    """
    Define the PWS Journey graph structure.

    Returns a dict describing nodes and edges for visualization.
    """
    return {
        "nodes": {
            "intake": {"description": "Capture and prepare problem statement"},
            "classify": {"description": "Classify problem type and Cynefin domain (Claude Opus)"},
            "enrich": {"description": "Enrich with Neo4j + FileSearch (parallel)"},
            "generate_questions": {"description": "Generate Beautiful Questions (Claude Opus)"},
            "guide": {"description": "Create guidance and available actions"},
            "probe": {"description": "Execute a probe and collect evidence"},
            "reassess": {"description": "Evaluate if reclassification needed"},
            "checkpoint": {"description": "Save progress for persistence"},
        },
        "edges": [
            ("START", "intake"),
            ("intake", "classify"),
            ("classify", "enrich"),
            ("enrich", "generate_questions"),
            ("generate_questions", "guide"),
            ("guide", "probe", "user_action == 'probe'"),
            ("guide", "checkpoint", "user_action == 'checkpoint'"),
            ("guide", "reassess", "user_action == 'reassess'"),
            ("guide", "END", "user_action == 'end'"),
            ("probe", "reassess", "reassessment_triggers"),
            ("probe", "guide", "no triggers"),
            ("reassess", "enrich", "domain_transition"),
            ("reassess", "guide", "no change"),
            ("checkpoint", "guide"),
        ],
        "loops": [
            ("probe", "reassess", "enrich", "guide", "probe"),  # Evidence loop
        ],
    }


def visualize_journey_graph() -> str:
    """Generate Mermaid diagram of journey graph."""
    return """```mermaid
graph TD
    START((Start)) --> intake[📥 Intake]
    intake --> classify[🔍 Classify<br/>Claude Opus]
    classify --> enrich[📚 Enrich<br/>Neo4j + FileSearch]
    enrich --> questions[❓ Beautiful Questions<br/>Claude Opus]
    questions --> guide[🧭 Guide]

    guide -->|probe| probe[🔬 Probe]
    guide -->|checkpoint| checkpoint[💾 Checkpoint]
    guide -->|reassess| reassess[🔄 Reassess]
    guide -->|end| END((End))

    probe -->|triggers| reassess
    probe -->|no triggers| guide

    reassess -->|domain change| enrich
    reassess -->|no change| guide

    checkpoint --> guide

    style classify fill:#f9f,stroke:#333
    style questions fill:#f9f,stroke:#333
    style enrich fill:#bbf,stroke:#333
    style probe fill:#bfb,stroke:#333
```"""
