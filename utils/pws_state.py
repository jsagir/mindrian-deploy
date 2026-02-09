"""
PWS Consultant State Management

Formal LangGraph-style state schema with TypedDict for type safety.
Integrates with context_store for cross-bot persistence and
Supabase for cross-session persistence.

Design principles:
- Type safety via TypedDict (enables IDE autocomplete and static analysis)
- Immutable state updates (return new dicts, don't mutate)
- Sync to context_store on every state change
- Async persist to Supabase on stage transitions
- Captured context pattern for background tasks (no cl.user_session access)
"""

import logging
from typing import TypedDict, Literal, Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
import asyncio
import chainlit as cl

logger = logging.getLogger(__name__)


# ============================================
# Formal Type Definitions (LangGraph-style)
# ============================================

class DiagnosticAnswer(TypedDict):
    """Single diagnostic MCQ answer."""
    question_id: str
    question_text: str
    selected_option: str
    scores: Dict[str, int]  # {"Un-Defined": 1, "Ill-Defined": 0, ...}
    timestamp: str


class Diagnosis(TypedDict):
    """Problem type classification result."""
    primary: str  # "Un-Defined" | "Ill-Defined" | "Well-Defined" | "Wicked"
    secondary: Optional[str]
    confidence: float
    scores: Dict[str, int]
    manual_selection: bool


class Expert(TypedDict):
    """Single expert in the panel."""
    id: str
    name: str
    icon: str
    focus: str
    approach: str


class ExpertPanel(TypedDict):
    """Dynamically built expert panel."""
    domain: str
    subdomains: List[str]
    experts: List[Expert]
    problem_type: str
    trace: Dict[str, Any]


# ============================================
# Artifacts vs Frames (AGENTS.md Pattern)
# ============================================
# Artifacts: Validated evidence that persists across all agents/modes
# Frames: Agent-specific interpretations that don't leak

class Artifact(TypedDict):
    """
    Validated evidence that all agents can see.

    Artifacts persist across the entire session and represent
    confirmed facts, decisions, or validated insights.
    """
    id: str
    type: Literal["user_input", "challenge", "diagnosis", "validated_insight", "decision"]
    content: str
    source: str  # Which agent or "user" created it
    created_at: str
    validation_source: Optional[str]  # How it was validated (e.g., "diagnostic", "red_team")


class Frame(TypedDict):
    """
    Interpretation that only the creating agent/mode sees.

    Frames are scoped to specific contexts (e.g., expert mode)
    and should NOT leak into other contexts. They represent
    speculation, hypotheses, or working models.
    """
    id: str
    agent: str  # Which agent/expert created this frame
    type: Literal["hypothesis", "assumption", "speculation", "working_model", "expert_opinion"]
    content: str
    confidence: float
    created_at: str
    promoted_to_artifact: Optional[str]  # Artifact ID if promoted


class PWSConsultantState(TypedDict, total=False):
    """
    Formal state schema for PWS Consultant.

    Using total=False means all fields are optional, allowing partial updates.
    This matches LangGraph's pattern where nodes return partial state dicts.
    """
    # === Stage Machine ===
    stage: Literal["intro", "diagnostic", "consulting"]
    sub_mode: Literal["normal", "expert", "tool", "synthesis"]

    # === Intro Phase ===
    intro_turn_count: int
    challenge_description: str
    challenge_signals: Dict[str, Any]

    # === Diagnostic Phase ===
    diagnostic_answers: List[DiagnosticAnswer]
    diagnosis: Optional[Diagnosis]
    diagnostic_context: str

    # === Consulting Phase ===
    consulting_turn_count: int
    expert_consult_count: int
    active_expert_context: str
    hybrid_context: str

    # === Background Task Results ===
    expert_panel: Optional[ExpertPanel]
    domain_discovery: Optional[Dict[str, Any]]

    # === Artifacts vs Frames (AGENTS.md Pattern) ===
    # Artifacts persist across all modes, Frames are scoped
    artifacts: List[Artifact]
    frames: Dict[str, List[Frame]]  # agent_id -> list of frames

    # === Session Metadata ===
    user_id: str
    session_id: str
    context_key: str
    last_updated: str


# ============================================
# State Initialization
# ============================================

def init_pws_state(user_id: str = "", session_id: str = "", context_key: str = "") -> PWSConsultantState:
    """
    Initialize PWS Consultant state with defaults.

    Returns a complete state dict with all fields set to sensible defaults.
    """
    return PWSConsultantState(
        # Stage machine
        stage="intro",
        sub_mode="normal",

        # Intro
        intro_turn_count=0,
        challenge_description="",
        challenge_signals={},

        # Diagnostic
        diagnostic_answers=[],
        diagnosis=None,
        diagnostic_context="",

        # Consulting
        consulting_turn_count=0,
        expert_consult_count=0,
        active_expert_context="",
        hybrid_context="",

        # Background results
        expert_panel=None,
        domain_discovery=None,

        # Artifacts vs Frames (AGENTS.md pattern)
        artifacts=[],
        frames={},

        # Metadata
        user_id=user_id,
        session_id=session_id,
        context_key=context_key,
        last_updated=datetime.utcnow().isoformat(),
    )


# ============================================
# State Access (from cl.user_session)
# ============================================

def get_pws_state() -> PWSConsultantState:
    """
    Get current PWS state from Chainlit session.

    Assembles state from individual cl.user_session values.
    Returns defaults for any missing values.
    """
    try:
        user = cl.user_session.get("user")
        user_id = user.identifier if user and hasattr(user, "identifier") else ""
    except Exception:
        user_id = ""

    try:
        session_id = cl.user_session.get("id", "")
    except Exception:
        session_id = ""

    # Compute context_key
    if user_id:
        context_key = f"user_{user_id}"
    elif session_id:
        context_key = f"session_{session_id}"
    else:
        import uuid
        context_key = f"anon_{uuid.uuid4().hex[:12]}"

    return PWSConsultantState(
        stage=cl.user_session.get("pws_stage", "intro"),
        sub_mode=cl.user_session.get("pws_sub_mode", "normal"),
        intro_turn_count=cl.user_session.get("pws_intro_turn_count", 0),
        challenge_description=cl.user_session.get("pws_challenge_description", ""),
        challenge_signals=cl.user_session.get("pws_challenge_signals", {}),
        diagnostic_answers=cl.user_session.get("pws_diagnostic_answers", []),
        diagnosis=cl.user_session.get("pws_diagnosis"),
        diagnostic_context=cl.user_session.get("pws_diagnostic_context", ""),
        consulting_turn_count=cl.user_session.get("pws_consulting_turn_count", 0),
        expert_consult_count=cl.user_session.get("pws_expert_consult_count", 0),
        active_expert_context=cl.user_session.get("pws_active_expert_context", ""),
        hybrid_context=cl.user_session.get("pws_hybrid_context", ""),
        expert_panel=cl.user_session.get("pws_expert_panel_data"),
        domain_discovery=cl.user_session.get("pws_domain_discovery"),
        user_id=user_id,
        session_id=session_id,
        context_key=context_key,
        last_updated=datetime.utcnow().isoformat(),
    )


def set_pws_state(state: PWSConsultantState, sync_to_context_store: bool = True) -> None:
    """
    Set PWS state to Chainlit session.

    Updates individual cl.user_session values from the state dict.
    Optionally syncs to context_store for cross-bot persistence.

    Args:
        state: Partial or complete state dict to apply
        sync_to_context_store: Whether to sync to global context_store
    """
    # Map state keys to session keys
    key_map = {
        "stage": "pws_stage",
        "sub_mode": "pws_sub_mode",
        "intro_turn_count": "pws_intro_turn_count",
        "challenge_description": "pws_challenge_description",
        "challenge_signals": "pws_challenge_signals",
        "diagnostic_answers": "pws_diagnostic_answers",
        "diagnosis": "pws_diagnosis",
        "diagnostic_context": "pws_diagnostic_context",
        "consulting_turn_count": "pws_consulting_turn_count",
        "expert_consult_count": "pws_expert_consult_count",
        "active_expert_context": "pws_active_expert_context",
        "hybrid_context": "pws_hybrid_context",
        "expert_panel": "pws_expert_panel_data",
        "domain_discovery": "pws_domain_discovery",
    }

    for state_key, session_key in key_map.items():
        if state_key in state:
            cl.user_session.set(session_key, state[state_key])

    if sync_to_context_store:
        sync_pws_to_context_store(state)


def update_pws_state(updates: PWSConsultantState, sync: bool = True) -> PWSConsultantState:
    """
    Apply partial updates to PWS state.

    This is the primary way to modify state - follows LangGraph pattern
    where nodes return partial state updates that get merged.

    Args:
        updates: Partial state dict with fields to update
        sync: Whether to sync to context_store

    Returns:
        The updated full state
    """
    # Get current state
    current = get_pws_state()

    # Merge updates
    new_state = {**current, **updates, "last_updated": datetime.utcnow().isoformat()}

    # Apply to session
    set_pws_state(new_state, sync_to_context_store=sync)

    return new_state


# ============================================
# Context Store Sync (L1 - In-Memory)
# ============================================

# Import context_store from main module (will be injected)
_context_store: Optional[Dict] = None


def set_context_store(store: Dict) -> None:
    """Inject the global context_store reference."""
    global _context_store
    _context_store = store


def sync_pws_to_context_store(state: Optional[PWSConsultantState] = None) -> None:
    """
    Sync PWS state to context_store for cross-bot persistence.

    This ensures PWS state survives bot switches within the same session.
    """
    global _context_store

    if _context_store is None:
        logger.debug("[PWS_STATE] context_store not injected, skipping sync")
        return

    if state is None:
        state = get_pws_state()

    context_key = state.get("context_key", "")
    if not context_key:
        logger.warning("[PWS_STATE] No context_key, cannot sync")
        return

    # Ensure entry exists
    if context_key not in _context_store:
        _context_store[context_key] = {}

    # Store PWS-specific state under pws_state key
    _context_store[context_key]["pws_state"] = {
        "stage": state.get("stage"),
        "sub_mode": state.get("sub_mode"),
        "challenge_description": state.get("challenge_description"),
        "challenge_signals": state.get("challenge_signals"),
        "diagnostic_answers": state.get("diagnostic_answers"),
        "diagnosis": state.get("diagnosis"),
        "diagnostic_context": state.get("diagnostic_context"),
        "expert_panel": state.get("expert_panel"),
        "domain_discovery": state.get("domain_discovery"),
        "consulting_turn_count": state.get("consulting_turn_count"),
        "last_updated": state.get("last_updated"),
    }

    logger.debug(f"[PWS_STATE] Synced to context_store: {context_key}")


def restore_pws_from_context_store(context_key: str) -> Optional[PWSConsultantState]:
    """
    Restore PWS state from context_store after bot switch or page refresh.

    Returns:
        Restored state if found, None otherwise
    """
    global _context_store

    if _context_store is None or context_key not in _context_store:
        return None

    pws_state = _context_store[context_key].get("pws_state")
    if not pws_state:
        return None

    logger.info(f"[PWS_STATE] Restored from context_store: {context_key}, stage={pws_state.get('stage')}")
    return pws_state


# ============================================
# Background Task Support (Captured Context)
# ============================================

@dataclass
class CapturedPWSContext:
    """
    Captured context for background tasks.

    This captures all necessary state BEFORE creating an async task,
    avoiding race conditions with cl.user_session which may change
    or become unavailable during task execution.
    """
    context_key: str
    user_id: str
    session_id: str
    challenge_description: str
    stage: str
    diagnosis: Optional[Dict]

    @classmethod
    def capture(cls) -> "CapturedPWSContext":
        """Capture current context from session."""
        state = get_pws_state()
        return cls(
            context_key=state.get("context_key", ""),
            user_id=state.get("user_id", ""),
            session_id=state.get("session_id", ""),
            challenge_description=state.get("challenge_description", ""),
            stage=state.get("stage", "intro"),
            diagnosis=state.get("diagnosis"),
        )


async def run_background_task_with_context(
    task_func,
    captured_context: CapturedPWSContext,
    *args,
    **kwargs
) -> Any:
    """
    Run a background task with captured context.

    The task function receives captured_context as its first argument,
    and should store results in context_store (not cl.user_session).

    Args:
        task_func: Async function to run
        captured_context: Pre-captured context
        *args, **kwargs: Additional arguments for task_func

    Returns:
        Result from task_func
    """
    global _context_store

    try:
        result = await task_func(captured_context, *args, **kwargs)

        # Store result in context_store if available
        if _context_store is not None and captured_context.context_key:
            if captured_context.context_key not in _context_store:
                _context_store[captured_context.context_key] = {}

            # Store the result under a task-specific key
            task_name = task_func.__name__
            if "pws_background_results" not in _context_store[captured_context.context_key]:
                _context_store[captured_context.context_key]["pws_background_results"] = {}
            _context_store[captured_context.context_key]["pws_background_results"][task_name] = {
                "result": result,
                "timestamp": datetime.utcnow().isoformat(),
            }

        # Also try to update session if still active
        try:
            if task_func.__name__ == "build_expert_panel_background":
                cl.user_session.set("pws_expert_panel_data", result)
            elif task_func.__name__ == "discover_domain_background":
                cl.user_session.set("pws_domain_discovery", result)
        except Exception:
            pass  # Session may have ended

        return result

    except Exception as e:
        logger.error(f"[PWS_STATE] Background task {task_func.__name__} failed: {e}")
        return None


# ============================================
# Supabase Persistence (L2 - Cross-Session)
# ============================================

async def persist_pws_state_to_supabase(state: Optional[PWSConsultantState] = None) -> bool:
    """
    Persist PWS state to Supabase for cross-session recovery.

    Called on stage transitions and periodically during consulting.
    Uses the existing context_persistence infrastructure.
    """
    if state is None:
        state = get_pws_state()

    try:
        from utils.context_persistence import save_cross_bot_context

        context_key = state.get("context_key", "")
        if not context_key:
            return False

        # Get history from session
        history = cl.user_session.get("history", [])

        # Build context data including PWS state
        # BUG-001 FIX: Include excluded_topics in persistence
        excluded_topics = cl.user_session.get("excluded_topics", [])
        success = await save_cross_bot_context(
            user_key=context_key,
            history=history,
            bot_id="pws_consultant",
            bot_name="PWS Consultant",
            phases=[],  # PWS uses stages, not phases
            current_phase=0,
            excluded_topics=excluded_topics,
        )

        if success:
            logger.info(f"[PWS_STATE] Persisted to Supabase: {context_key}")

        return success

    except Exception as e:
        logger.error(f"[PWS_STATE] Failed to persist to Supabase: {e}")
        return False


# ============================================
# Stage Transition Helpers
# ============================================

def validate_transition(current_stage: str, target_stage: str) -> bool:
    """
    Validate that a stage transition is allowed.

    PWS Consultant has a linear stage machine:
    intro -> diagnostic -> consulting

    With restart option:
    consulting -> intro (via user action)
    """
    valid_transitions = {
        "intro": ["diagnostic"],
        "diagnostic": ["consulting", "intro"],  # Can restart
        "consulting": ["intro"],  # Can restart with new challenge
    }

    return target_stage in valid_transitions.get(current_stage, [])


async def transition_stage(
    target_stage: str,
    persist: bool = True
) -> PWSConsultantState:
    """
    Transition to a new stage with validation and persistence.

    Args:
        target_stage: Stage to transition to
        persist: Whether to persist to Supabase

    Returns:
        Updated state

    Raises:
        ValueError: If transition is invalid
    """
    current_state = get_pws_state()
    current_stage = current_state.get("stage", "intro")

    if not validate_transition(current_stage, target_stage):
        raise ValueError(f"Invalid transition: {current_stage} -> {target_stage}")

    # Apply transition
    new_state = update_pws_state({
        "stage": target_stage,
        "sub_mode": "normal",  # Reset sub_mode on stage change
    })

    logger.info(f"[PWS_STATE] Stage transition: {current_stage} -> {target_stage}")

    # Persist on stage transitions
    if persist:
        asyncio.create_task(persist_pws_state_to_supabase(new_state))

    return new_state


# ============================================
# Convenience Functions
# ============================================

def is_stage(stage: str) -> bool:
    """Check if current stage matches."""
    return get_pws_state().get("stage") == stage


def get_stage() -> str:
    """Get current stage."""
    return get_pws_state().get("stage", "intro")


def get_diagnosis() -> Optional[Diagnosis]:
    """Get current diagnosis if available."""
    return get_pws_state().get("diagnosis")


def get_expert_panel() -> Optional[ExpertPanel]:
    """Get expert panel if built."""
    return get_pws_state().get("expert_panel")


def increment_turn_count(stage: str = None) -> int:
    """
    Increment turn count for current or specified stage.

    Returns the new turn count.
    """
    if stage is None:
        stage = get_stage()

    if stage == "intro":
        current = cl.user_session.get("pws_intro_turn_count", 0)
        new_count = current + 1
        cl.user_session.set("pws_intro_turn_count", new_count)
    elif stage == "consulting":
        current = cl.user_session.get("pws_consulting_turn_count", 0)
        new_count = current + 1
        cl.user_session.set("pws_consulting_turn_count", new_count)
    else:
        new_count = 0

    return new_count


# ============================================
# Artifacts vs Frames (AGENTS.md Pattern)
# ============================================

def add_artifact(
    content: str,
    artifact_type: str,
    source: str,
    validation_source: Optional[str] = None
) -> str:
    """
    Add a new artifact to the PWS state.

    Artifacts are validated evidence that persists across all modes.
    Call this when:
    - User provides validated information
    - Diagnosis is completed
    - An insight has been validated by Red Team
    - A decision has been made

    Returns:
        The artifact ID
    """
    import uuid

    artifact_id = str(uuid.uuid4())[:8]
    artifact = Artifact(
        id=artifact_id,
        type=artifact_type,
        content=content,
        source=source,
        created_at=datetime.utcnow().isoformat(),
        validation_source=validation_source,
    )

    # Get current artifacts from session
    artifacts = cl.user_session.get("pws_artifacts", [])
    artifacts.append(artifact)
    cl.user_session.set("pws_artifacts", artifacts)

    logger.debug(f"[PWS_STATE] Added artifact: {artifact_type} from {source}")
    return artifact_id


def add_frame(
    agent: str,
    content: str,
    frame_type: str,
    confidence: float = 0.5
) -> str:
    """
    Add a frame (scoped interpretation) for an agent.

    Frames are agent-specific interpretations that don't leak to other contexts.
    Call this when:
    - An expert provides an opinion
    - A hypothesis is formed
    - An assumption is made
    - A working model is proposed

    Returns:
        The frame ID
    """
    import uuid

    frame_id = str(uuid.uuid4())[:8]
    frame = Frame(
        id=frame_id,
        agent=agent,
        type=frame_type,
        content=content,
        confidence=confidence,
        created_at=datetime.utcnow().isoformat(),
        promoted_to_artifact=None,
    )

    # Get current frames from session
    frames = cl.user_session.get("pws_frames", {})
    if agent not in frames:
        frames[agent] = []
    frames[agent].append(frame)
    cl.user_session.set("pws_frames", frames)

    logger.debug(f"[PWS_STATE] Added frame: {frame_type} from {agent} (confidence: {confidence})")
    return frame_id


def promote_frame_to_artifact(
    agent: str,
    frame_id: str,
    validation_source: str = "user_confirmed"
) -> Optional[str]:
    """
    Promote a frame to an artifact after validation.

    This is the key transition in AGENTS.md pattern:
    Speculation (Frame) -> Validated Evidence (Artifact)

    Call this when:
    - User confirms an expert's hypothesis
    - Red Team validation passes
    - Evidence supports a working model

    Returns:
        The new artifact ID, or None if frame not found
    """
    frames = cl.user_session.get("pws_frames", {})
    agent_frames = frames.get(agent, [])

    # Find the frame
    frame_to_promote = None
    for i, f in enumerate(agent_frames):
        if f.get("id") == frame_id:
            frame_to_promote = f
            break

    if not frame_to_promote:
        logger.warning(f"[PWS_STATE] Frame {frame_id} not found for agent {agent}")
        return None

    # Create artifact from frame
    artifact_id = add_artifact(
        content=frame_to_promote["content"],
        artifact_type="validated_insight",
        source=agent,
        validation_source=validation_source,
    )

    # Mark frame as promoted
    frame_to_promote["promoted_to_artifact"] = artifact_id
    cl.user_session.set("pws_frames", frames)

    logger.info(f"[PWS_STATE] Promoted frame {frame_id} to artifact {artifact_id}")
    return artifact_id


def get_artifacts(artifact_type: Optional[str] = None) -> List[Artifact]:
    """Get all artifacts, optionally filtered by type."""
    artifacts = cl.user_session.get("pws_artifacts", [])
    if artifact_type:
        return [a for a in artifacts if a.get("type") == artifact_type]
    return artifacts


def get_frames(agent: Optional[str] = None) -> Dict[str, List[Frame]]:
    """Get all frames, optionally filtered by agent."""
    frames = cl.user_session.get("pws_frames", {})
    if agent:
        return {agent: frames.get(agent, [])}
    return frames


def get_unpromoted_frames(agent: str) -> List[Frame]:
    """Get frames for an agent that haven't been promoted to artifacts."""
    frames = cl.user_session.get("pws_frames", {})
    agent_frames = frames.get(agent, [])
    return [f for f in agent_frames if not f.get("promoted_to_artifact")]


def clear_agent_frames(agent: str) -> int:
    """
    Clear all frames for an agent (e.g., after leaving expert mode).

    Returns the number of frames cleared.
    """
    frames = cl.user_session.get("pws_frames", {})
    count = len(frames.get(agent, []))
    frames[agent] = []
    cl.user_session.set("pws_frames", frames)
    logger.debug(f"[PWS_STATE] Cleared {count} frames for agent {agent}")
    return count
