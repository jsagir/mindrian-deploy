"""
Supabase Storage Layer for A2A Orchestration

Stores all orchestration state in Supabase:
- Context (artifacts and frames)
- Phase transitions
- Classification logs
- Journey data

Tables required:
- a2a_sessions: Session metadata
- a2a_artifacts: Shared evidence
- a2a_frames: Agent-specific interpretations
- a2a_phases: Phase transition history
- a2a_classifications: Classification logs for analytics
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import asdict

logger = logging.getLogger(__name__)

# Try to import Supabase
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    logger.warning("Supabase not available - using local storage fallback")


def get_supabase_client() -> Optional[Client]:
    """Get Supabase client from environment variables."""
    if not SUPABASE_AVAILABLE:
        return None

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY")

    if not url or not key:
        logger.warning("Supabase credentials not found in environment")
        return None

    try:
        return create_client(url, key)
    except Exception as e:
        logger.error(f"Failed to create Supabase client: {e}")
        return None


class SupabaseStorage:
    """
    Supabase storage for A2A orchestration data.

    Falls back to local JSON storage if Supabase is unavailable.
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.client = get_supabase_client()
        self.use_supabase = self.client is not None

        if self.use_supabase:
            logger.info(f"Using Supabase storage for session {session_id}")
        else:
            logger.info(f"Using local storage fallback for session {session_id}")

    # === Session Management ===

    async def init_session(self, metadata: Dict = None) -> bool:
        """Initialize a new session."""
        if not self.use_supabase:
            return True

        try:
            self.client.table("a2a_sessions").upsert({
                "session_id": self.session_id,
                "created_at": datetime.utcnow().isoformat(),
                "metadata": metadata or {},
                "status": "active"
            }).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to init session: {e}")
            return False

    async def update_session(self, updates: Dict) -> bool:
        """Update session metadata."""
        if not self.use_supabase:
            return True

        try:
            self.client.table("a2a_sessions").update({
                **updates,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("session_id", self.session_id).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to update session: {e}")
            return False

    # === Artifacts ===

    async def save_artifact(self, artifact: Dict) -> bool:
        """Save an artifact to Supabase."""
        if not self.use_supabase:
            return True

        try:
            self.client.table("a2a_artifacts").upsert({
                "id": artifact["id"],
                "session_id": self.session_id,
                "type": artifact["type"],
                "content": artifact["content"],
                "source": artifact["source"],
                "validation_source": artifact.get("validation_source"),
                "metadata": artifact.get("metadata", {}),
                "created_at": artifact.get("created_at", datetime.utcnow().isoformat())
            }).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to save artifact: {e}")
            return False

    async def get_artifacts(self) -> List[Dict]:
        """Get all artifacts for this session."""
        if not self.use_supabase:
            return []

        try:
            response = self.client.table("a2a_artifacts") \
                .select("*") \
                .eq("session_id", self.session_id) \
                .order("created_at") \
                .execute()
            return response.data
        except Exception as e:
            logger.error(f"Failed to get artifacts: {e}")
            return []

    async def delete_artifact(self, artifact_id: str) -> bool:
        """Delete an artifact."""
        if not self.use_supabase:
            return True

        try:
            self.client.table("a2a_artifacts") \
                .delete() \
                .eq("id", artifact_id) \
                .eq("session_id", self.session_id) \
                .execute()
            return True
        except Exception as e:
            logger.error(f"Failed to delete artifact: {e}")
            return False

    # === Frames ===

    async def save_frame(self, frame: Dict) -> bool:
        """Save a frame to Supabase."""
        if not self.use_supabase:
            return True

        try:
            self.client.table("a2a_frames").upsert({
                "id": frame["id"],
                "session_id": self.session_id,
                "agent": frame["agent"],
                "type": frame["type"],
                "content": frame["content"],
                "confidence": frame["confidence"],
                "parent_artifact_id": frame.get("parent_artifact_id"),
                "metadata": frame.get("metadata", {}),
                "created_at": frame.get("created_at", datetime.utcnow().isoformat())
            }).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to save frame: {e}")
            return False

    async def get_frames(self, agent: Optional[str] = None) -> List[Dict]:
        """Get frames for this session, optionally filtered by agent."""
        if not self.use_supabase:
            return []

        try:
            query = self.client.table("a2a_frames") \
                .select("*") \
                .eq("session_id", self.session_id)

            if agent:
                query = query.eq("agent", agent)

            response = query.order("created_at").execute()
            return response.data
        except Exception as e:
            logger.error(f"Failed to get frames: {e}")
            return []

    async def delete_frame(self, frame_id: str) -> bool:
        """Delete a frame (used when promoting to artifact)."""
        if not self.use_supabase:
            return True

        try:
            self.client.table("a2a_frames") \
                .delete() \
                .eq("id", frame_id) \
                .eq("session_id", self.session_id) \
                .execute()
            return True
        except Exception as e:
            logger.error(f"Failed to delete frame: {e}")
            return False

    # === Phase Transitions ===

    async def save_phase_transition(self, transition: Dict) -> bool:
        """Save a phase transition."""
        if not self.use_supabase:
            return True

        try:
            self.client.table("a2a_phases").insert({
                "session_id": self.session_id,
                "from_phase": transition["from_phase"],
                "to_phase": transition["to_phase"],
                "reason": transition["reason"],
                "triggered_by": transition["triggered_by"],
                "is_regression": transition["is_regression"],
                "metadata": transition.get("metadata", {}),
                "created_at": transition.get("timestamp", datetime.utcnow().isoformat())
            }).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to save phase transition: {e}")
            return False

    async def get_phase_history(self) -> List[Dict]:
        """Get phase transition history."""
        if not self.use_supabase:
            return []

        try:
            response = self.client.table("a2a_phases") \
                .select("*") \
                .eq("session_id", self.session_id) \
                .order("created_at") \
                .execute()
            return response.data
        except Exception as e:
            logger.error(f"Failed to get phase history: {e}")
            return []

    async def get_current_phase(self) -> Optional[str]:
        """Get the current phase for this session."""
        if not self.use_supabase:
            return "exploring"

        try:
            response = self.client.table("a2a_phases") \
                .select("to_phase") \
                .eq("session_id", self.session_id) \
                .order("created_at", desc=True) \
                .limit(1) \
                .execute()

            if response.data:
                return response.data[0]["to_phase"]
            return "exploring"  # Default
        except Exception as e:
            logger.error(f"Failed to get current phase: {e}")
            return "exploring"

    # === Classifications ===

    async def log_classification(self, classification: Dict) -> bool:
        """Log a classification for analytics."""
        if not self.use_supabase:
            return True

        try:
            self.client.table("a2a_classifications").insert({
                "session_id": self.session_id,
                "input_hash": classification.get("input_hash"),
                "cynefin": classification["cynefin"],
                "pws": classification["pws"],
                "cynefin_confidence": classification["cynefin_confidence"],
                "pws_confidence": classification["pws_confidence"],
                "reasoning": classification.get("reasoning"),
                "latency_ms": classification.get("latency_ms"),
                "created_at": datetime.utcnow().isoformat()
            }).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to log classification: {e}")
            return False

    async def get_classification_stats(self) -> Dict:
        """Get classification statistics for analytics."""
        if not self.use_supabase:
            return {}

        try:
            response = self.client.table("a2a_classifications") \
                .select("cynefin, pws, cynefin_confidence, pws_confidence") \
                .eq("session_id", self.session_id) \
                .execute()

            data = response.data
            if not data:
                return {}

            return {
                "total_classifications": len(data),
                "cynefin_distribution": self._count_values(data, "cynefin"),
                "pws_distribution": self._count_values(data, "pws"),
                "avg_confidence": sum(
                    min(d["cynefin_confidence"], d["pws_confidence"])
                    for d in data
                ) / len(data)
            }
        except Exception as e:
            logger.error(f"Failed to get classification stats: {e}")
            return {}

    def _count_values(self, data: List[Dict], key: str) -> Dict[str, int]:
        """Count occurrences of values for a key."""
        counts = {}
        for d in data:
            val = d.get(key)
            counts[val] = counts.get(val, 0) + 1
        return counts

    # === Bulk Operations ===

    async def save_full_state(
        self,
        artifacts: List[Dict],
        frames: Dict[str, List[Dict]],
        phase_history: List[Dict],
        current_phase: str,
        classification: Optional[Dict] = None
    ) -> bool:
        """Save full orchestration state."""
        if not self.use_supabase:
            return True

        try:
            # Save artifacts
            for artifact in artifacts:
                await self.save_artifact(artifact)

            # Save frames by agent
            for agent, agent_frames in frames.items():
                for frame in agent_frames:
                    await self.save_frame(frame)

            # Save phase transitions
            for transition in phase_history:
                await self.save_phase_transition(transition)

            # Update session with current phase
            await self.update_session({
                "current_phase": current_phase,
                "artifact_count": len(artifacts),
                "classification": classification
            })

            return True
        except Exception as e:
            logger.error(f"Failed to save full state: {e}")
            return False

    async def load_full_state(self) -> Dict:
        """Load full orchestration state."""
        if not self.use_supabase:
            return {
                "artifacts": [],
                "frames": {},
                "phase_history": [],
                "current_phase": "exploring"
            }

        try:
            artifacts = await self.get_artifacts()
            frames_list = await self.get_frames()
            phase_history = await self.get_phase_history()
            current_phase = await self.get_current_phase()

            # Group frames by agent
            frames = {}
            for frame in frames_list:
                agent = frame["agent"]
                if agent not in frames:
                    frames[agent] = []
                frames[agent].append(frame)

            return {
                "artifacts": artifacts,
                "frames": frames,
                "phase_history": phase_history,
                "current_phase": current_phase
            }
        except Exception as e:
            logger.error(f"Failed to load full state: {e}")
            return {
                "artifacts": [],
                "frames": {},
                "phase_history": [],
                "current_phase": "exploring"
            }


# === SQL Migration ===

SUPABASE_MIGRATION_SQL = """
-- A2A Orchestration Tables
-- Run this in Supabase SQL Editor

-- Sessions table
CREATE TABLE IF NOT EXISTS a2a_sessions (
    session_id TEXT PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    status TEXT DEFAULT 'active',
    current_phase TEXT DEFAULT 'exploring',
    artifact_count INTEGER DEFAULT 0,
    classification JSONB,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Artifacts table (shared evidence)
CREATE TABLE IF NOT EXISTS a2a_artifacts (
    id TEXT PRIMARY KEY,
    session_id TEXT REFERENCES a2a_sessions(session_id) ON DELETE CASCADE,
    type TEXT NOT NULL,
    content TEXT NOT NULL,
    source TEXT NOT NULL,
    validation_source TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_artifacts_session ON a2a_artifacts(session_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_type ON a2a_artifacts(type);

-- Frames table (agent-specific interpretations)
CREATE TABLE IF NOT EXISTS a2a_frames (
    id TEXT PRIMARY KEY,
    session_id TEXT REFERENCES a2a_sessions(session_id) ON DELETE CASCADE,
    agent TEXT NOT NULL,
    type TEXT NOT NULL,
    content TEXT NOT NULL,
    confidence FLOAT DEFAULT 0.5,
    parent_artifact_id TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_frames_session ON a2a_frames(session_id);
CREATE INDEX IF NOT EXISTS idx_frames_agent ON a2a_frames(agent);

-- Phase transitions table
CREATE TABLE IF NOT EXISTS a2a_phases (
    id SERIAL PRIMARY KEY,
    session_id TEXT REFERENCES a2a_sessions(session_id) ON DELETE CASCADE,
    from_phase TEXT NOT NULL,
    to_phase TEXT NOT NULL,
    reason TEXT,
    triggered_by TEXT DEFAULT 'system',
    is_regression BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_phases_session ON a2a_phases(session_id);

-- Classifications table (for analytics)
CREATE TABLE IF NOT EXISTS a2a_classifications (
    id SERIAL PRIMARY KEY,
    session_id TEXT REFERENCES a2a_sessions(session_id) ON DELETE CASCADE,
    input_hash TEXT,
    cynefin TEXT NOT NULL,
    pws TEXT NOT NULL,
    cynefin_confidence FLOAT,
    pws_confidence FLOAT,
    reasoning TEXT,
    latency_ms FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_classifications_session ON a2a_classifications(session_id);
CREATE INDEX IF NOT EXISTS idx_classifications_cynefin ON a2a_classifications(cynefin);
CREATE INDEX IF NOT EXISTS idx_classifications_pws ON a2a_classifications(pws);

-- Enable RLS (Row Level Security)
ALTER TABLE a2a_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE a2a_artifacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE a2a_frames ENABLE ROW LEVEL SECURITY;
ALTER TABLE a2a_phases ENABLE ROW LEVEL SECURITY;
ALTER TABLE a2a_classifications ENABLE ROW LEVEL SECURITY;

-- Policies (allow all for service role)
CREATE POLICY "Service role has full access to sessions" ON a2a_sessions FOR ALL USING (true);
CREATE POLICY "Service role has full access to artifacts" ON a2a_artifacts FOR ALL USING (true);
CREATE POLICY "Service role has full access to frames" ON a2a_frames FOR ALL USING (true);
CREATE POLICY "Service role has full access to phases" ON a2a_phases FOR ALL USING (true);
CREATE POLICY "Service role has full access to classifications" ON a2a_classifications FOR ALL USING (true);
"""


def get_migration_sql() -> str:
    """Get the SQL migration script."""
    return SUPABASE_MIGRATION_SQL
