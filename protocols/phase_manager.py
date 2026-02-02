"""
Phase Manager - Directed Graph Phase Transitions

This module implements the phase transition graph for the A2A orchestration system.

Key Principles:
- Explicit allowed transitions prevent infinite loops
- "Stuck" state forces acknowledgment rather than endless cycling
- Regression is allowed but tracked
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from datetime import datetime
import json
from pathlib import Path


class Phase(Enum):
    """
    Problem-solving phases in the A2A workflow.

    EXPLORING: Don't know what problem to solve yet (Un-Defined)
    FRAMING: Have identified opportunity, refining it (Ill-Defined)
    DEFINING: Creating well-defined problem statement (Well-Defined)
    SOLVING: Designing and building solution
    VALIDATING: Testing and validating solution
    COMPLETE: Successfully completed
    STUCK: Explicitly stuck, needs intervention
    """
    EXPLORING = "exploring"
    FRAMING = "framing"
    DEFINING = "defining"
    SOLVING = "solving"
    VALIDATING = "validating"
    COMPLETE = "complete"
    STUCK = "stuck"


# Allowed phase transitions (directed graph)
ALLOWED_TRANSITIONS = {
    Phase.EXPLORING: [Phase.FRAMING],  # Forward only from exploring
    Phase.FRAMING: [Phase.EXPLORING, Phase.DEFINING],  # Can regress to exploring
    Phase.DEFINING: [Phase.FRAMING, Phase.SOLVING],    # Can regress to framing
    Phase.SOLVING: [Phase.VALIDATING, Phase.DEFINING], # Can regress to defining
    Phase.VALIDATING: [Phase.COMPLETE, Phase.STUCK, Phase.FRAMING],  # Multiple outcomes
    Phase.STUCK: [Phase.FRAMING, Phase.EXPLORING],  # Explicit acknowledgment, restart
    Phase.COMPLETE: [],  # Terminal state
}

# Phase order for determining regression
PHASE_ORDER = [
    Phase.EXPLORING,
    Phase.FRAMING,
    Phase.DEFINING,
    Phase.SOLVING,
    Phase.VALIDATING,
    Phase.COMPLETE
]


@dataclass
class PhaseTransition:
    """Record of a phase transition."""
    from_phase: Phase
    to_phase: Phase
    reason: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    triggered_by: str = "system"  # agent name or "user"
    is_regression: bool = False
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "from_phase": self.from_phase.value,
            "to_phase": self.to_phase.value,
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat(),
            "triggered_by": self.triggered_by,
            "is_regression": self.is_regression,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PhaseTransition":
        data = data.copy()
        data["from_phase"] = Phase(data["from_phase"])
        data["to_phase"] = Phase(data["to_phase"])
        if isinstance(data["timestamp"], str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


class PhaseManager:
    """
    Manages phase transitions with explicit allowed transitions.

    Key behaviors:
    - Only allows transitions defined in ALLOWED_TRANSITIONS
    - Tracks regression (going backwards in the workflow)
    - Forces explicit acknowledgment of stuck states
    - Maintains full history for debugging and analytics
    """

    def __init__(
        self,
        session_id: str,
        initial_phase: Phase = Phase.EXPLORING,
        storage_dir: Optional[Path] = None
    ):
        self.session_id = session_id
        self.current_phase = initial_phase
        self.phase_history: List[PhaseTransition] = []
        self.storage_dir = storage_dir or Path("sessions")
        self._phase_start_time = datetime.utcnow()

    # === Transition Logic ===

    def can_transition(self, target: Phase) -> bool:
        """Check if transition to target phase is allowed."""
        return target in ALLOWED_TRANSITIONS.get(self.current_phase, [])

    def get_allowed_transitions(self) -> List[Phase]:
        """Get list of phases we can transition to from current phase."""
        return ALLOWED_TRANSITIONS.get(self.current_phase, [])

    def is_regression(self, target: Phase) -> bool:
        """Check if transition is going backwards in the workflow."""
        if self.current_phase not in PHASE_ORDER or target not in PHASE_ORDER:
            return False
        current_idx = PHASE_ORDER.index(self.current_phase)
        target_idx = PHASE_ORDER.index(target)
        return target_idx < current_idx

    def transition(
        self,
        target: Phase,
        reason: str,
        triggered_by: str = "system",
        metadata: dict = None
    ) -> Tuple[bool, str]:
        """
        Attempt to transition to a new phase.

        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.can_transition(target):
            allowed = [p.value for p in self.get_allowed_transitions()]
            return (
                False,
                f"Cannot transition from {self.current_phase.value} to {target.value}. "
                f"Allowed transitions: {allowed}"
            )

        is_regress = self.is_regression(target)

        transition = PhaseTransition(
            from_phase=self.current_phase,
            to_phase=target,
            reason=reason,
            triggered_by=triggered_by,
            is_regression=is_regress,
            metadata=metadata or {}
        )

        self.phase_history.append(transition)
        self.current_phase = target
        self._phase_start_time = datetime.utcnow()

        status = "regression" if is_regress else "forward"
        return (True, f"Transitioned to {target.value} ({status})")

    def force_transition(
        self,
        target: Phase,
        reason: str,
        triggered_by: str = "admin"
    ) -> Tuple[bool, str]:
        """
        Force a transition regardless of allowed transitions.
        Use with caution - only for admin/debug purposes.
        """
        is_regress = self.is_regression(target)

        transition = PhaseTransition(
            from_phase=self.current_phase,
            to_phase=target,
            reason=f"[FORCED] {reason}",
            triggered_by=triggered_by,
            is_regression=is_regress,
            metadata={"forced": True}
        )

        self.phase_history.append(transition)
        self.current_phase = target
        self._phase_start_time = datetime.utcnow()

        return (True, f"Forced transition to {target.value}")

    # === State Queries ===

    def is_terminal(self) -> bool:
        """Check if current phase is terminal (no further transitions)."""
        return len(self.get_allowed_transitions()) == 0

    def is_stuck(self) -> bool:
        """Check if in stuck state."""
        return self.current_phase == Phase.STUCK

    def is_complete(self) -> bool:
        """Check if workflow is complete."""
        return self.current_phase == Phase.COMPLETE

    def time_in_current_phase(self) -> float:
        """Get seconds spent in current phase."""
        return (datetime.utcnow() - self._phase_start_time).total_seconds()

    def get_regression_count(self) -> int:
        """Count how many times we've regressed."""
        return sum(1 for t in self.phase_history if t.is_regression)

    def get_phase_visit_count(self, phase: Phase) -> int:
        """Count how many times we've visited a phase."""
        count = 1 if self.current_phase == phase else 0
        count += sum(1 for t in self.phase_history if t.to_phase == phase)
        return count

    # === History Analysis ===

    def get_history_summary(self) -> List[dict]:
        """Get summarized history of transitions."""
        return [t.to_dict() for t in self.phase_history]

    def get_last_transition(self) -> Optional[PhaseTransition]:
        """Get the most recent transition."""
        return self.phase_history[-1] if self.phase_history else None

    def get_transitions_by_agent(self, agent: str) -> List[PhaseTransition]:
        """Get all transitions triggered by a specific agent."""
        return [t for t in self.phase_history if t.triggered_by == agent]

    # === Persistence ===

    def save(self) -> Path:
        """Save phase manager state to disk."""
        session_dir = self.storage_dir / self.session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        data = {
            "session_id": self.session_id,
            "current_phase": self.current_phase.value,
            "phase_history": [t.to_dict() for t in self.phase_history],
            "phase_start_time": self._phase_start_time.isoformat(),
            "saved_at": datetime.utcnow().isoformat()
        }

        filepath = session_dir / "phase_state.json"
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        return filepath

    @classmethod
    def load(cls, session_id: str, storage_dir: Optional[Path] = None) -> "PhaseManager":
        """Load phase manager state from disk."""
        storage_dir = storage_dir or Path("sessions")
        filepath = storage_dir / session_id / "phase_state.json"

        if not filepath.exists():
            return cls(session_id, storage_dir=storage_dir)

        with open(filepath) as f:
            data = json.load(f)

        manager = cls(
            session_id=session_id,
            initial_phase=Phase(data["current_phase"]),
            storage_dir=storage_dir
        )
        manager.phase_history = [
            PhaseTransition.from_dict(t) for t in data.get("phase_history", [])
        ]
        manager._phase_start_time = datetime.fromisoformat(data["phase_start_time"])

        return manager

    # === Summary ===

    def get_summary(self) -> dict:
        """Get summary of phase manager state."""
        return {
            "session_id": self.session_id,
            "current_phase": self.current_phase.value,
            "is_terminal": self.is_terminal(),
            "is_stuck": self.is_stuck(),
            "is_complete": self.is_complete(),
            "time_in_phase_seconds": self.time_in_current_phase(),
            "total_transitions": len(self.phase_history),
            "regression_count": self.get_regression_count(),
            "allowed_next_phases": [p.value for p in self.get_allowed_transitions()],
            "phase_visit_counts": {
                p.value: self.get_phase_visit_count(p) for p in Phase
            }
        }


# === Convenience Functions ===

def suggest_phase_from_classification(
    cynefin: str,
    pws: str
) -> Phase:
    """
    Suggest initial phase based on classification results.

    Args:
        cynefin: Cynefin domain (clear, complicated, complex, chaotic)
        pws: PWS problem type (un-defined, ill-defined, well-defined)

    Returns:
        Suggested initial phase
    """
    # PWS type is primary driver of phase
    pws_to_phase = {
        "un-defined": Phase.EXPLORING,
        "ill-defined": Phase.FRAMING,
        "well-defined": Phase.DEFINING
    }

    return pws_to_phase.get(pws, Phase.EXPLORING)
