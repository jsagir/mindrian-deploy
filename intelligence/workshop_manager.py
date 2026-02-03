"""
Workshop Manager - LangGraph Implementation
===========================================
Replaces the ill-behaving workshop mode logic with LangGraph state management.

Benefits:
- Clean state transitions between phases
- Checkpointing for resume across sessions
- Human-in-the-loop for phase transitions
- Conditional logic based on conversation content

Workshop Types:
- TTA (Trending to the Absurd)
- JTBD (Jobs to Be Done)
- S-Curve Analysis
- Red Teaming
- Ackoff's Pyramid (DIKW)

Usage:
    from intelligence.workshop_manager import WorkshopManager

    manager = WorkshopManager("tta", session_id="user_123")
    result = await manager.process_message("Let's explore urban farming")
    print(result["response"])
    print(result["current_phase"])
"""

import os
import json
from typing import TypedDict, Annotated, List, Dict, Any, Optional
from operator import add
from datetime import datetime
from enum import Enum

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

# Try to use Postgres checkpointer if available
try:
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False


# =============================================================================
# WORKSHOP DEFINITIONS
# =============================================================================

class WorkshopPhase(Enum):
    """Standard workshop phases."""
    INTRODUCTION = "introduction"
    DISCOVERY = "discovery"
    ANALYSIS = "analysis"
    SYNTHESIS = "synthesis"
    ACTION = "action"
    COMPLETE = "complete"


WORKSHOP_CONFIGS = {
    "tta": {
        "name": "Trending to the Absurd",
        "phases": [
            {"id": "introduction", "name": "Introduction", "description": "Understand the trend to analyze"},
            {"id": "trend_identification", "name": "Trend Identification", "description": "Identify and quantify the trend"},
            {"id": "extrapolation", "name": "Extrapolation", "description": "Extend the trend to absurd endpoint"},
            {"id": "backcasting", "name": "Backcasting", "description": "Work backwards from absurd to find opportunities"},
            {"id": "synthesis", "name": "Synthesis", "description": "Synthesize opportunities and next steps"},
        ],
        "completion_signals": {
            "introduction": ["trend", "analyze", "explore", "topic"],
            "trend_identification": ["growth", "data", "statistics", "rate", "increase"],
            "extrapolation": ["absurd", "extreme", "endpoint", "100%", "everyone"],
            "backcasting": ["opportunity", "business", "solution", "when", "before"],
            "synthesis": ["action", "next step", "recommend", "summary"],
        }
    },
    "jtbd": {
        "name": "Jobs to Be Done",
        "phases": [
            {"id": "introduction", "name": "Introduction", "description": "Define the customer segment"},
            {"id": "job_discovery", "name": "Job Discovery", "description": "Identify jobs customers are hiring for"},
            {"id": "struggling_moments", "name": "Struggling Moments", "description": "Find where customers struggle"},
            {"id": "forces_analysis", "name": "Forces Analysis", "description": "Analyze push/pull forces"},
            {"id": "synthesis", "name": "Synthesis", "description": "Define value propositions"},
        ],
        "completion_signals": {
            "introduction": ["customer", "segment", "who", "target"],
            "job_discovery": ["job", "hire", "trying to", "progress", "outcome"],
            "struggling_moments": ["struggle", "frustrated", "workaround", "pain"],
            "forces_analysis": ["push", "pull", "anxiety", "habit", "switch"],
            "synthesis": ["solution", "value", "proposition", "offer"],
        }
    },
    "scurve": {
        "name": "S-Curve Analysis",
        "phases": [
            {"id": "introduction", "name": "Introduction", "description": "Identify the technology/market"},
            {"id": "curve_mapping", "name": "Curve Mapping", "description": "Map current position on S-curve"},
            {"id": "inflection_analysis", "name": "Inflection Analysis", "description": "Identify inflection points"},
            {"id": "next_curve", "name": "Next Curve", "description": "Explore successor technologies"},
            {"id": "synthesis", "name": "Synthesis", "description": "Strategic recommendations"},
        ],
        "completion_signals": {
            "introduction": ["technology", "market", "industry", "product"],
            "curve_mapping": ["early", "growth", "maturity", "decline", "position"],
            "inflection_analysis": ["inflection", "tipping", "change", "shift"],
            "next_curve": ["next", "successor", "emerging", "disrupt"],
            "synthesis": ["strategy", "timing", "invest", "exit"],
        }
    },
    "redteam": {
        "name": "Red Teaming",
        "phases": [
            {"id": "introduction", "name": "Introduction", "description": "Define the idea to challenge"},
            {"id": "assumption_extraction", "name": "Assumption Extraction", "description": "Extract key assumptions"},
            {"id": "attack_vectors", "name": "Attack Vectors", "description": "Identify weaknesses and risks"},
            {"id": "stress_testing", "name": "Stress Testing", "description": "Test assumptions under pressure"},
            {"id": "synthesis", "name": "Synthesis", "description": "Recommendations for strengthening"},
        ],
        "completion_signals": {
            "introduction": ["idea", "plan", "hypothesis", "assumption"],
            "assumption_extraction": ["assume", "belief", "expect", "think"],
            "attack_vectors": ["risk", "weakness", "fail", "wrong", "problem"],
            "stress_testing": ["what if", "scenario", "worst case", "test"],
            "synthesis": ["strengthen", "mitigate", "improve", "address"],
        }
    },
    "ackoff": {
        "name": "Ackoff's Pyramid (DIKW)",
        "phases": [
            {"id": "introduction", "name": "Introduction", "description": "Define the topic for analysis"},
            {"id": "data_gathering", "name": "Data", "description": "Raw data and observations"},
            {"id": "information_synthesis", "name": "Information", "description": "Patterns and relationships"},
            {"id": "knowledge_building", "name": "Knowledge", "description": "Contextualized understanding"},
            {"id": "wisdom_application", "name": "Wisdom", "description": "Actionable judgment"},
        ],
        "completion_signals": {
            "introduction": ["topic", "explore", "understand", "analyze"],
            "data_gathering": ["data", "number", "fact", "observe", "measure"],
            "information_synthesis": ["pattern", "relationship", "connect", "trend"],
            "knowledge_building": ["means", "context", "understand", "know"],
            "wisdom_application": ["should", "decide", "judgment", "action", "wisdom"],
        }
    },
}


# =============================================================================
# STATE DEFINITION
# =============================================================================

def merge_dicts(left: dict, right: dict) -> dict:
    """Reducer: merge dictionaries."""
    return {**left, **right}


class WorkshopState(TypedDict):
    """State for workshop management."""
    # Workshop config
    workshop_type: str
    workshop_name: str
    phases: list
    current_phase_idx: int
    current_phase_id: str

    # Conversation
    messages: Annotated[list, add]  # Full conversation history
    current_message: str
    response: str

    # Phase data
    phase_data: Annotated[dict, merge_dicts]  # {phase_id: extracted_data}
    phase_completion: Annotated[dict, merge_dicts]  # {phase_id: completion_score}

    # Control
    should_advance: bool
    advance_reason: str
    is_complete: bool

    # Metadata
    session_id: str
    started_at: str
    last_updated: str
    errors: Annotated[list, add]


# =============================================================================
# PHASE MANAGEMENT FUNCTIONS
# =============================================================================

def detect_phase_completion(
    message: str,
    response: str,
    phase_id: str,
    workshop_type: str
) -> tuple:
    """
    Detect if a phase should be considered complete.

    Returns (completion_score, should_advance, reason).
    """
    config = WORKSHOP_CONFIGS.get(workshop_type, {})
    signals = config.get("completion_signals", {}).get(phase_id, [])

    if not signals:
        return (0.5, False, "No completion signals defined")

    # Check message and response for signals
    combined_text = f"{message} {response}".lower()
    matches = sum(1 for signal in signals if signal in combined_text)
    completion_score = min(1.0, matches / max(len(signals) / 2, 1))

    # Threshold for advancement
    if completion_score >= 0.6:
        return (completion_score, True, f"Detected {matches}/{len(signals)} completion signals")
    elif completion_score >= 0.4:
        return (completion_score, False, f"Partial completion ({matches}/{len(signals)} signals)")
    else:
        return (completion_score, False, "Insufficient completion signals")


async def generate_workshop_response(
    state: WorkshopState,
    system_prompt: str = None
) -> str:
    """Generate response for current workshop phase."""
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

        workshop_type = state["workshop_type"]
        config = WORKSHOP_CONFIGS.get(workshop_type, {})
        phase = config.get("phases", [])[state["current_phase_idx"]]

        # Build context from conversation
        recent_messages = state.get("messages", [])[-10:]
        conversation = "\n".join([
            f"{'User' if m.get('role') == 'user' else 'Assistant'}: {m.get('content', '')[:500]}"
            for m in recent_messages
        ])

        # Default system prompt
        if not system_prompt:
            system_prompt = f"""You are guiding a {config.get('name', 'PWS')} workshop.

Current Phase: {phase.get('name', 'Unknown')}
Phase Goal: {phase.get('description', 'Guide the user through this phase')}

Be focused, Socratic, and guide the user toward phase completion.
Don't give all the answers - ask questions that lead to discovery."""

        prompt = f"""{system_prompt}

CONVERSATION SO FAR:
{conversation}

USER MESSAGE: {state["current_message"]}

Respond helpfully while guiding toward the phase goal. If ready to advance, acknowledge what was learned."""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[types.Content(role="user", parts=[types.Part(text=prompt)])],
        )

        return response.text

    except Exception as e:
        return f"Workshop response error: {str(e)}"


# =============================================================================
# PIPELINE NODES
# =============================================================================

async def process_message_node(state: WorkshopState) -> dict:
    """Process user message and generate response."""
    try:
        response = await generate_workshop_response(state)

        # Add messages to history
        new_messages = [
            {"role": "user", "content": state["current_message"]},
            {"role": "assistant", "content": response}
        ]

        return {
            "response": response,
            "messages": new_messages,
            "last_updated": datetime.now().isoformat()
        }

    except Exception as e:
        return {
            "response": f"Error: {str(e)}",
            "errors": [str(e)]
        }


async def check_phase_completion_node(state: WorkshopState) -> dict:
    """Check if current phase is complete."""
    completion_score, should_advance, reason = detect_phase_completion(
        state["current_message"],
        state["response"],
        state["current_phase_id"],
        state["workshop_type"]
    )

    phase_completion = {state["current_phase_id"]: completion_score}

    return {
        "phase_completion": phase_completion,
        "should_advance": should_advance,
        "advance_reason": reason
    }


def should_advance_phase(state: WorkshopState) -> str:
    """Conditional: check if we should advance to next phase."""
    if state.get("should_advance", False):
        return "advance"
    else:
        return "stay"


async def advance_phase_node(state: WorkshopState) -> dict:
    """Advance to next phase."""
    current_idx = state["current_phase_idx"]
    phases = state["phases"]

    next_idx = current_idx + 1

    if next_idx >= len(phases):
        # Workshop complete
        return {
            "current_phase_idx": current_idx,
            "is_complete": True,
            "response": state["response"] + "\n\n**Workshop Complete!** Great work completing all phases."
        }

    next_phase = phases[next_idx]

    transition_msg = f"\n\n---\n**Moving to Phase: {next_phase.get('name', 'Next')}**\n{next_phase.get('description', '')}"

    return {
        "current_phase_idx": next_idx,
        "current_phase_id": next_phase.get("id", f"phase_{next_idx}"),
        "response": state["response"] + transition_msg
    }


async def stay_phase_node(state: WorkshopState) -> dict:
    """Stay in current phase (no-op, just pass through)."""
    return {}


# =============================================================================
# PIPELINE CONSTRUCTION
# =============================================================================

def create_workshop_pipeline(checkpointer=None):
    """Create the workshop management pipeline."""
    graph = StateGraph(WorkshopState)

    # Add nodes
    graph.add_node("process_message", process_message_node)
    graph.add_node("check_completion", check_phase_completion_node)
    graph.add_node("advance_phase", advance_phase_node)
    graph.add_node("stay_phase", stay_phase_node)

    # Flow
    graph.add_edge(START, "process_message")
    graph.add_edge("process_message", "check_completion")

    # Conditional: advance or stay
    graph.add_conditional_edges(
        "check_completion",
        should_advance_phase,
        {
            "advance": "advance_phase",
            "stay": "stay_phase"
        }
    )

    graph.add_edge("advance_phase", END)
    graph.add_edge("stay_phase", END)

    # Use provided checkpointer or default to memory
    if checkpointer is None:
        checkpointer = MemorySaver()

    return graph.compile(checkpointer=checkpointer)


# =============================================================================
# WORKSHOP MANAGER CLASS
# =============================================================================

class WorkshopManager:
    """
    High-level workshop manager using LangGraph.

    Handles state persistence, phase transitions, and message processing.
    """

    def __init__(
        self,
        workshop_type: str,
        session_id: str,
        use_postgres: bool = True
    ):
        """
        Initialize workshop manager.

        Args:
            workshop_type: Type of workshop (tta, jtbd, scurve, redteam, ackoff)
            session_id: Session ID for persistence
            use_postgres: Use Postgres for checkpointing
        """
        self.workshop_type = workshop_type
        self.session_id = session_id
        self.config = WORKSHOP_CONFIGS.get(workshop_type, WORKSHOP_CONFIGS["tta"])
        self.use_postgres = use_postgres

        # Initialize state
        self.state = self._create_initial_state()

        # Pipeline will be created lazily
        self._pipeline = None

    def _create_initial_state(self) -> WorkshopState:
        """Create initial workshop state."""
        phases = self.config.get("phases", [])
        first_phase = phases[0] if phases else {"id": "introduction", "name": "Introduction"}

        return {
            "workshop_type": self.workshop_type,
            "workshop_name": self.config.get("name", "Workshop"),
            "phases": phases,
            "current_phase_idx": 0,
            "current_phase_id": first_phase.get("id", "introduction"),
            "messages": [],
            "current_message": "",
            "response": "",
            "phase_data": {},
            "phase_completion": {},
            "should_advance": False,
            "advance_reason": "",
            "is_complete": False,
            "session_id": self.session_id,
            "started_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "errors": [],
        }

    async def _get_pipeline(self):
        """Get or create the pipeline."""
        if self._pipeline is None:
            checkpointer = None
            if self.use_postgres and POSTGRES_AVAILABLE:
                database_url = os.getenv("DATABASE_URL")
                if database_url:
                    try:
                        checkpointer = AsyncPostgresSaver.from_conn_string(database_url)
                        await checkpointer.setup()
                    except Exception:
                        pass

            if checkpointer is None:
                checkpointer = MemorySaver()

            self._pipeline = create_workshop_pipeline(checkpointer)

        return self._pipeline

    async def process_message(self, message: str) -> Dict[str, Any]:
        """
        Process a user message through the workshop.

        Args:
            message: User's message

        Returns:
            Dict with response, current_phase, is_complete, etc.
        """
        # Update state with new message
        self.state["current_message"] = message

        # Get pipeline
        pipeline = await self._get_pipeline()

        # Config for checkpointing
        config = {"configurable": {"thread_id": self.session_id}}

        # Run pipeline
        try:
            result = await pipeline.ainvoke(self.state, config)
            self.state = result  # Update state

            return {
                "response": result.get("response", ""),
                "current_phase": result.get("current_phase_id", "unknown"),
                "current_phase_idx": result.get("current_phase_idx", 0),
                "phase_name": self._get_phase_name(result.get("current_phase_idx", 0)),
                "is_complete": result.get("is_complete", False),
                "should_advance": result.get("should_advance", False),
                "advance_reason": result.get("advance_reason", ""),
                "completion_scores": result.get("phase_completion", {}),
            }

        except Exception as e:
            return {
                "response": f"Workshop error: {str(e)}",
                "current_phase": self.state.get("current_phase_id", "unknown"),
                "is_complete": False,
                "error": str(e)
            }

    def _get_phase_name(self, idx: int) -> str:
        """Get phase name by index."""
        phases = self.config.get("phases", [])
        if idx < len(phases):
            return phases[idx].get("name", f"Phase {idx + 1}")
        return "Complete"

    def get_progress(self) -> Dict[str, Any]:
        """Get workshop progress summary."""
        phases = self.config.get("phases", [])
        current_idx = self.state.get("current_phase_idx", 0)

        return {
            "workshop_type": self.workshop_type,
            "workshop_name": self.config.get("name", "Workshop"),
            "current_phase": self._get_phase_name(current_idx),
            "current_phase_idx": current_idx,
            "total_phases": len(phases),
            "progress_pct": (current_idx / len(phases) * 100) if phases else 0,
            "is_complete": self.state.get("is_complete", False),
            "phase_completion": self.state.get("phase_completion", {}),
            "phases": [
                {
                    "name": p.get("name"),
                    "status": "complete" if i < current_idx else ("current" if i == current_idx else "pending"),
                    "completion": self.state.get("phase_completion", {}).get(p.get("id"), 0)
                }
                for i, p in enumerate(phases)
            ]
        }

    def force_advance_phase(self) -> Dict[str, Any]:
        """Force advance to next phase."""
        current_idx = self.state.get("current_phase_idx", 0)
        phases = self.config.get("phases", [])

        if current_idx < len(phases) - 1:
            self.state["current_phase_idx"] = current_idx + 1
            self.state["current_phase_id"] = phases[current_idx + 1].get("id")

        return self.get_progress()

    def force_previous_phase(self) -> Dict[str, Any]:
        """Force go back to previous phase."""
        current_idx = self.state.get("current_phase_idx", 0)
        phases = self.config.get("phases", [])

        if current_idx > 0:
            self.state["current_phase_idx"] = current_idx - 1
            self.state["current_phase_id"] = phases[current_idx - 1].get("id")

        return self.get_progress()

    def reset(self) -> Dict[str, Any]:
        """Reset workshop to beginning."""
        self.state = self._create_initial_state()
        return self.get_progress()


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

async def run_workshop_turn(
    workshop_type: str,
    session_id: str,
    message: str
) -> Dict[str, Any]:
    """
    Run a single workshop turn.

    Convenience function for stateless usage.
    """
    manager = WorkshopManager(workshop_type, session_id)
    return await manager.process_message(message)


def get_workshop_types() -> List[Dict[str, str]]:
    """Get list of available workshop types."""
    return [
        {"id": wtype, "name": config.get("name", wtype)}
        for wtype, config in WORKSHOP_CONFIGS.items()
    ]
