"""
Context Manager - Artifacts vs Frames Separation

This module implements the core context separation pattern for multi-agent systems:
- Artifacts: Validated evidence that persists across all agents
- Frames: Agent-specific interpretations that don't leak to other agents

Key Principle: TTA speculation shouldn't become JTBD's "facts".
"""

from dataclasses import dataclass, field
from typing import Literal, Optional, Dict, List
from datetime import datetime
import uuid
import json
from pathlib import Path


ArtifactType = Literal["user_input", "research_finding", "validated_insight", "decision", "opportunity"]
FrameType = Literal["hypothesis", "assumption", "speculation", "working_model"]
ValidationSource = Literal["user_confirmed", "red_team_passed", "research_verified", "agent_consensus"]


@dataclass
class Artifact:
    """Evidence that all agents can see."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: ArtifactType = "user_input"
    content: str = ""
    source: str = ""  # Which agent or user created it
    created_at: datetime = field(default_factory=datetime.utcnow)
    validation_source: Optional[ValidationSource] = None
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "content": self.content,
            "source": self.source,
            "created_at": self.created_at.isoformat(),
            "validation_source": self.validation_source,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Artifact":
        data = data.copy()
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)


@dataclass
class Frame:
    """Interpretation that only the creating agent sees."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent: str = ""  # Which agent created this frame
    type: FrameType = "hypothesis"
    content: str = ""
    confidence: float = 0.5
    created_at: datetime = field(default_factory=datetime.utcnow)
    parent_artifact_id: Optional[str] = None  # What artifact this frame interprets
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "agent": self.agent,
            "type": self.type,
            "content": self.content,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat(),
            "parent_artifact_id": self.parent_artifact_id,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Frame":
        data = data.copy()
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)


class ContextManager:
    """
    Manages context separation between artifacts and frames.

    Artifacts are validated evidence visible to all agents.
    Frames are agent-specific interpretations that stay scoped.
    """

    def __init__(self, session_id: str, storage_dir: Optional[Path] = None):
        self.session_id = session_id
        self.storage_dir = storage_dir or Path("sessions")
        self._artifacts: Dict[str, Artifact] = {}
        self._frames: Dict[str, Dict[str, Frame]] = {}  # agent -> frame_id -> frame
        self._promotion_log: List[dict] = []  # Track frame -> artifact promotions

    # === Artifact Operations ===

    def add_artifact(self, artifact: Artifact) -> str:
        """Add artifact that all agents can see."""
        self._artifacts[artifact.id] = artifact
        return artifact.id

    def create_artifact(
        self,
        content: str,
        source: str,
        artifact_type: ArtifactType = "user_input",
        validation_source: Optional[ValidationSource] = None,
        metadata: Dict = None
    ) -> str:
        """Create and add a new artifact."""
        artifact = Artifact(
            type=artifact_type,
            content=content,
            source=source,
            validation_source=validation_source,
            metadata=metadata or {}
        )
        return self.add_artifact(artifact)

    def get_artifact(self, artifact_id: str) -> Optional[Artifact]:
        """Get a specific artifact by ID."""
        return self._artifacts.get(artifact_id)

    def get_all_artifacts(self) -> List[Artifact]:
        """Get all artifacts, sorted by creation time."""
        return sorted(self._artifacts.values(), key=lambda a: a.created_at)

    def get_artifacts_by_type(self, artifact_type: ArtifactType) -> List[Artifact]:
        """Get artifacts of a specific type."""
        return [a for a in self._artifacts.values() if a.type == artifact_type]

    def get_artifacts_by_source(self, source: str) -> List[Artifact]:
        """Get artifacts created by a specific source/agent."""
        return [a for a in self._artifacts.values() if a.source == source]

    # === Frame Operations ===

    def add_frame(
        self,
        agent: str,
        content: str,
        frame_type: FrameType,
        confidence: float = 0.5,
        parent_artifact_id: Optional[str] = None,
        metadata: Dict = None
    ) -> str:
        """Add frame that only this agent sees."""
        frame = Frame(
            agent=agent,
            type=frame_type,
            content=content,
            confidence=confidence,
            parent_artifact_id=parent_artifact_id,
            metadata=metadata or {}
        )
        if agent not in self._frames:
            self._frames[agent] = {}
        self._frames[agent][frame.id] = frame
        return frame.id

    def get_frame(self, agent: str, frame_id: str) -> Optional[Frame]:
        """Get a specific frame for an agent."""
        return self._frames.get(agent, {}).get(frame_id)

    def get_agent_frames(self, agent: str) -> List[Frame]:
        """Get all frames for a specific agent."""
        return list(self._frames.get(agent, {}).values())

    def get_high_confidence_frames(self, agent: str, threshold: float = 0.7) -> List[Frame]:
        """Get frames above confidence threshold for an agent."""
        return [f for f in self.get_agent_frames(agent) if f.confidence >= threshold]

    def update_frame_confidence(self, agent: str, frame_id: str, new_confidence: float) -> bool:
        """Update confidence score for a frame."""
        frame = self.get_frame(agent, frame_id)
        if frame:
            frame.confidence = new_confidence
            return True
        return False

    # === Context Access ===

    def get_context_for_agent(self, agent: str) -> dict:
        """
        Get context visible to a specific agent.

        Returns artifacts (shared) and frames (agent-specific).
        """
        return {
            "artifacts": [a.to_dict() for a in self.get_all_artifacts()],
            "frames": [f.to_dict() for f in self.get_agent_frames(agent)],
            "session_id": self.session_id
        }

    def get_shared_context(self) -> dict:
        """Get only shared context (artifacts, no frames)."""
        return {
            "artifacts": [a.to_dict() for a in self.get_all_artifacts()],
            "session_id": self.session_id
        }

    # === Frame Promotion ===

    def promote_frame_to_artifact(
        self,
        agent: str,
        frame_id: str,
        validation_source: ValidationSource
    ) -> str:
        """
        Promote validated frame to artifact.

        This is the key operation: when a frame passes validation,
        it becomes a shared artifact that all agents can see.
        """
        frame = self.get_frame(agent, frame_id)
        if not frame:
            raise ValueError(f"Frame {frame_id} not found for agent {agent}")

        # Create artifact from frame
        artifact = Artifact(
            type="validated_insight",
            content=frame.content,
            source=agent,
            validation_source=validation_source,
            metadata={
                "promoted_from_frame": frame_id,
                "original_confidence": frame.confidence,
                "original_type": frame.type,
                **frame.metadata
            }
        )
        self._artifacts[artifact.id] = artifact

        # Log the promotion
        self._promotion_log.append({
            "frame_id": frame_id,
            "artifact_id": artifact.id,
            "agent": agent,
            "validation_source": validation_source,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Remove the frame
        del self._frames[agent][frame_id]

        return artifact.id

    def can_promote(self, agent: str, frame_id: str) -> bool:
        """Check if a frame exists and can be promoted."""
        return self.get_frame(agent, frame_id) is not None

    # === Persistence ===

    def save(self) -> Path:
        """Save context to disk."""
        session_dir = self.storage_dir / self.session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        data = {
            "session_id": self.session_id,
            "artifacts": {k: v.to_dict() for k, v in self._artifacts.items()},
            "frames": {
                agent: {fid: f.to_dict() for fid, f in frames.items()}
                for agent, frames in self._frames.items()
            },
            "promotion_log": self._promotion_log,
            "saved_at": datetime.utcnow().isoformat()
        }

        filepath = session_dir / "context.json"
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        return filepath

    @classmethod
    def load(cls, session_id: str, storage_dir: Optional[Path] = None) -> "ContextManager":
        """Load context from disk."""
        storage_dir = storage_dir or Path("sessions")
        filepath = storage_dir / session_id / "context.json"

        if not filepath.exists():
            return cls(session_id, storage_dir)

        with open(filepath) as f:
            data = json.load(f)

        manager = cls(session_id, storage_dir)
        manager._artifacts = {
            k: Artifact.from_dict(v) for k, v in data.get("artifacts", {}).items()
        }
        manager._frames = {
            agent: {fid: Frame.from_dict(f) for fid, f in frames.items()}
            for agent, frames in data.get("frames", {}).items()
        }
        manager._promotion_log = data.get("promotion_log", [])

        return manager

    # === Summary ===

    def get_summary(self) -> dict:
        """Get summary statistics about the context."""
        return {
            "session_id": self.session_id,
            "artifact_count": len(self._artifacts),
            "artifacts_by_type": {
                t: len(self.get_artifacts_by_type(t))
                for t in ["user_input", "research_finding", "validated_insight", "decision", "opportunity"]
            },
            "frame_count_by_agent": {
                agent: len(frames) for agent, frames in self._frames.items()
            },
            "promotion_count": len(self._promotion_log)
        }
